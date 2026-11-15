"""Shared helpers for the DS-405 labs on the Rimah Health Data Consortium case.

Everything here is synthetic. Nothing calls a language model or downloads one.

    import rimah as U
    df = U.load("producers/sidra_encounters.csv")
    U.pick(full, quick)          # the small value when RIMAH_QUICK=1
    U.reference("lab_1_1")       # the reference result a safety-net cell falls back to
    U.measure(fn)                # (result, seconds, peak resident memory in MB)
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
import threading
import time
import uuid
from pathlib import Path

import polars as pl

LABS = Path(__file__).resolve().parent
DATA = LABS / "data"
ARTIFACTS = LABS / "artifacts"
SEED = 405
QUICK = os.environ.get("RIMAH_QUICK", "0") == "1"
PRODUCERS = {"SDR": "Sidra Hospitals", "UFQ": "Ufuq Medical Group", "RWD": "Rawdah Hospitals"}


def pick(full, quick):
    """The full-size value, or the small one in quick mode (RIMAH_QUICK=1)."""
    return quick if QUICK else full


def load(name: str, **kw) -> pl.DataFrame:
    """Read a file under labs/data/ (CSV as text columns unless told otherwise, Parquet as typed)."""
    path = DATA / name
    if path.suffix == ".parquet":
        return pl.read_parquet(path)
    kw.setdefault("infer_schema", False)
    return pl.read_csv(path, **kw)


def reference(name: str):
    """The reference result of an exercise, written by prepare_data.py (used by the safety nets)."""
    return json.loads((DATA / "reference" / f"{name}.json").read_text(encoding="utf-8"))


def lab_dir(name: str, reset: bool = True) -> Path:
    """A fresh working folder for one lab under labs/artifacts/ (delete artifacts/ before academy check)."""
    d = ARTIFACTS / name
    if reset and d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True, exist_ok=True)
    return d


def check(cond, msg: str):
    """Print a tick or a cross; a cross stops the notebook so the problem is fixed where it starts."""
    if cond:
        print("✅", msg)
    else:
        print("❌", msg)
        raise AssertionError(msg)


# ---------------------------------------------------------------- time and memory
def measure(fn, *args, interval: float = 0.005, **kw):
    """Run fn and return (result, seconds, peak resident memory of this process in MB above the start).

    The peak is sampled every few milliseconds, so it sees memory held by Polars and Arrow too,
    which tracemalloc does not."""
    import psutil

    proc = psutil.Process()
    start = proc.memory_info().rss
    peak = [start]
    done = threading.Event()

    def sample():
        while not done.is_set():
            peak[0] = max(peak[0], proc.memory_info().rss)
            time.sleep(interval)

    t = threading.Thread(target=sample, daemon=True)
    t.start()
    t0 = time.perf_counter()
    try:
        result = fn(*args, **kw)
    finally:
        seconds = time.perf_counter() - t0
        done.set()
        t.join()
    peak[0] = max(peak[0], proc.memory_info().rss)
    return result, seconds, (peak[0] - start) / 1e6


def fingerprint(df: pl.DataFrame, key: list[str] | None = None) -> str:
    """A content hash of a table that does not depend on row order or on file layout."""
    cols = sorted(df.columns)
    d = df.select(cols).sort(key or cols)
    h = hashlib.sha256()
    for col in cols:
        h.update(col.encode())
        h.update(d[col].hash(seed=SEED).to_numpy().tobytes())
    return h.hexdigest()[:16]


# ---------------------------------------------------------------- contracts (ODCS v3.2.0 subset)
def load_contract(path) -> dict:
    import yaml

    text = Path(path).read_text(encoding="utf-8") if not isinstance(path, dict) else None
    return yaml.safe_load(text) if text is not None else path


def _producer_block(contract: dict, producer: str) -> dict:
    for cp in contract.get("customProperties", []):
        if cp.get("property") == "producers":
            return cp["value"][producer]
    raise KeyError(f"no producers block for {producer} in the contract's customProperties")


def conform(raw: pl.DataFrame, producer: str, contract: dict) -> pl.DataFrame:
    """Turn one producer's extract into the contract's schema, using the contract's own clauses:
    column names, date formats, code maps and unit factors, all under customProperties.producers."""
    p = _producer_block(contract, producer)
    obj = contract["schema"][0]
    out = []
    for prop in obj["properties"]:
        name = prop["name"]
        src = p.get("columns", {}).get(name)
        if src is None:
            out.append(pl.lit(None, dtype=pl.String).alias(name))
            continue
        e = pl.col(src).cast(pl.String).str.strip_chars()
        if name in p.get("codes", {}):
            mapping = {str(k): str(v) for k, v in p["codes"][name].items()}
            e = e.replace_strict(mapping, default=None)
        if name in p.get("transforms", {}):
            e = _transform(e, p["transforms"][name])
        lt = prop.get("logicalType", "string")
        if lt == "date":
            fmt = p.get("date_formats", {}).get(name, "%Y-%m-%d")
            e = e.str.to_date(fmt, strict=False)
        elif lt in ("number", "integer"):
            e = e.cast(pl.Float64, strict=False)
            factor = p.get("units", {}).get(name)
            if factor is not None:
                e = (e * float(factor)).round(2)
            if lt == "integer":
                e = e.round(0).cast(pl.Int64)
        out.append(e.alias(name))
    return raw.select(out).with_columns(pl.lit(producer).alias("producer"))


def _transform(e: pl.Expr, how: str) -> pl.Expr:
    if how == "upper":
        return e.str.to_uppercase()
    if how == "icd10_dot":  # I509 or i50.9 -> I50.9
        e = e.str.to_uppercase().str.replace_all(r"\.", "")
        return pl.when(e.str.len_chars() > 3).then(e.str.slice(0, 3) + "." + e.str.slice(3)).otherwise(e)
    raise ValueError(f"unknown transform {how}")


def _metric_value(df: pl.DataFrame, col: str | None, q: dict) -> float:
    n = df.height
    m = q["metric"]
    if m == "rowCount":
        return float(n)
    if m == "nullValues":
        v = df[col].null_count()
    elif m == "missingValues":
        miss = q.get("arguments", {}).get("missingValues", [None, ""])
        vals = [x for x in miss if x is not None]
        v = df[col].null_count() + (df[col].cast(pl.String).is_in(vals).sum() if vals else 0)
    elif m == "invalidValues":
        a = q.get("arguments", {})
        s = df[col]
        ok = pl.Series([True] * n)
        if "validValues" in a:
            ok = ok & s.cast(pl.String).is_in([str(x) for x in a["validValues"]])
        if "pattern" in a:
            ok = ok & s.cast(pl.String).str.contains(a["pattern"])
        if "minimum" in a:
            ok = ok & (s >= a["minimum"])
        if "maximum" in a:
            ok = ok & (s <= a["maximum"])
        v = int((~ok.fill_null(True) & s.is_not_null()).sum())
    elif m == "duplicateValues":
        cols = q.get("arguments", {}).get("properties") or [col]
        v = n - df.select(cols).unique().height
    else:
        raise ValueError(f"metric {m} is not run by this helper")
    if q.get("unit") == "percent":
        return 100.0 * v / max(n, 1)
    return float(v)


def _passes(value: float, q: dict) -> bool:
    if "mustBe" in q:
        return value == q["mustBe"]
    if "mustBeLessThan" in q:
        return value < q["mustBeLessThan"]
    if "mustBeLessOrEqualTo" in q:
        return value <= q["mustBeLessOrEqualTo"]
    if "mustBeGreaterThan" in q:
        return value > q["mustBeGreaterThan"]
    if "mustBeBetween" in q:
        lo, hi = q["mustBeBetween"]
        return lo <= value <= hi
    raise ValueError("a quality rule needs mustBe, mustBeLessThan, mustBeGreaterThan or mustBeBetween")


def _sql_value(df: pl.DataFrame, q: dict) -> float:
    sql = q["query"].replace("{object}", "t")
    return float(pl.SQLContext(t=df).execute(sql, eager=True).item())


def run_contract(df: pl.DataFrame, contract: dict, producer: str = "") -> pl.DataFrame:
    """Run the library and SQL quality rules of the contract's first object on a conformed table.
    One row per rule: producer, property, rule id, metric, value, passed, severity."""
    obj = contract["schema"][0]
    rows = []

    def add(col, q):
        if q.get("type") == "sql":
            value = _sql_value(df, q)
            metric = "sql"
        else:
            value = _metric_value(df, col, q)
            metric = q["metric"]
        rows.append({"producer": producer, "property": col or obj["name"], "rule": q.get("id", metric),
                     "metric": metric, "value": round(value, 3), "passed": _passes(value, q),
                     "severity": q.get("severity", "error")})

    for prop in obj["properties"]:
        for q in prop.get("quality", []) or []:
            add(prop["name"], q)
        if prop.get("required"):
            add(prop["name"], {"id": f"{prop['name']}_required", "metric": "nullValues", "mustBe": 0})
    for q in obj.get("quality", []) or []:
        add(None, q)
    return pl.DataFrame(rows)


def freshness(contract: dict, newest_record: dt.date, delivered_on: dt.date) -> tuple[bool, int]:
    """The contract's latency SLA: days between the newest record and the delivery, against the limit."""
    lim = next(s for s in contract.get("slaProperties", []) if s["property"] == "latency")
    lag = (delivered_on - newest_record).days
    return lag <= int(lim["value"]), lag


# ---------------------------------------------------------------- lineage (OpenLineage run events)
OL_SCHEMA = "https://openlineage.io/spec/2-0-2/OpenLineage.json#/$defs/RunEvent"
OL_PRODUCER = "https://github.com/SDAIAAcademy/ds-405/labs"
_clock = [dt.datetime(2026, 1, 6, tzinfo=dt.timezone.utc)]


def ol_event(event_type: str, job: str, run_id: str, inputs: list[str], outputs: list[str],
             namespace: str = "rimah", run_facets: dict | None = None) -> dict:
    """One OpenLineage RunEvent as a dict: eventType START, COMPLETE or FAIL; job; run; datasets.
    Event times come from a fixed clock so that a re-run writes the same file."""
    _clock[0] += dt.timedelta(seconds=1)
    return {
        "eventType": event_type,
        "eventTime": _clock[0].isoformat().replace("+00:00", "Z"),
        "run": {"runId": run_id, "facets": run_facets or {}},
        "job": {"namespace": namespace, "name": job},
        "inputs": [{"namespace": "rimah-lake", "name": n} for n in inputs],
        "outputs": [{"namespace": "rimah-lake", "name": n} for n in outputs],
        "producer": OL_PRODUCER,
        "schemaURL": OL_SCHEMA,
    }


def run_id(*parts) -> str:
    """A deterministic run id (a UUID made from the job and its partition)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "rimah/" + "/".join(map(str, parts))))


def write_events(events: list[dict], path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in events), encoding="utf-8", newline="\n")
    return path


def read_events(path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------- small utilities
ARABIC_INDIC = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def show(df: pl.DataFrame, n: int = 10):
    with pl.Config(tbl_rows=n, tbl_cols=20, fmt_str_lengths=40, tbl_width_chars=160):
        print(df.head(n))


def save_json(obj, path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True, default=str), encoding="utf-8", newline="\n")
    return path


def months(year: int = 2025) -> list[str]:
    return [f"{year}-{m:02d}" for m in range(1, 13)]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
