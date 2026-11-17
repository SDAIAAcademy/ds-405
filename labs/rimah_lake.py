# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "numpy>=2.0"]
# ///
"""The Day 2 lake: about 30 million synthetic rows in partitioned Parquet, written on demand.

    uv run python rimah_lake.py            # full size: 30 million rows (a few minutes, about 1 GB on disk)
    RIMAH_QUICK=1 uv run python rimah_lake.py   # 1 percent: about 300,000 rows (seconds)

Layout (hive partitions):
    data/lake/raw/encounters/producer=SDR/month=2025-01/part-0.parquet
    data/lake/raw/labs/...        18 results per encounter (six tests, three rounds)
    data/lake/raw/pharmacy/...    6 dispensing lines per encounter
    data/lake/landing/day=2026-01-0N/<producer>_labs.parquet   daily laboratory deliveries (Lab 2.2)

Planted: Rawdah's September 2025 laboratory partition carries creatinine in mg/dL while its unit
column still says umol/L (Lab 2.4). Ufuq sends 2026-01-03 again with corrections; Sidra's 2026-01-05
delivery corrects results of 2026-01-02 (Lab 2.2).

Fixed seed: the same rows on every run for the same scale.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
LAKE = Path(os.environ.get("RIMAH_LAKE", HERE / "data" / "lake"))  # another folder: set RIMAH_LAKE
SEED = 405
PRODUCERS = ["SDR", "UFQ", "RWD"]
MONTHS = [f"2025-{m:02d}" for m in range(1, 13)]
WARDS = ["MED", "SURG", "CARD", "ICU", "OBS"]
DX = ["cardio", "renal", "metabolic", "respiratory", "infection", "surgical", "obstetric", "other"]
TESTS = {  # code: (unit, log-mean, log-sd)
    "CREAT": ("umol/L", np.log(90), 0.45), "GLU": ("mmol/L", np.log(6.4), 0.30), "HB": ("g/L", np.log(128), 0.15),
    "NA": ("mmol/L", np.log(139), 0.03), "K": ("mmol/L", np.log(4.2), 0.10), "WBC": ("10^9/L", np.log(8.0), 0.35)}
ATC = ["C03CA01", "C07AB07", "C09AA05", "A10BA02", "A10AE04", "B01AC06", "C10AA05", "J01CR02", "N02BE01", "H02AB06"]
ENC_PER_PM = 33_334  # encounters per producer and month at full size: 1.2 million in all


def scale_default() -> float:
    return 0.01 if os.environ.get("RIMAH_QUICK", "0") == "1" else 1.0


def _rng(*parts) -> np.random.Generator:
    return np.random.default_rng([SEED, *[hash_int(p) for p in parts]])


def hash_int(s) -> int:
    import hashlib
    return int(hashlib.sha256(str(s).encode("utf-8")).hexdigest()[:8], 16)


def _partition(table: str, producer: str, month: str) -> Path:
    return LAKE / "raw" / table / f"producer={producer}" / f"month={month}" / "part-0.parquet"


def encounters_for(producer: str, month: str, n: int) -> pl.DataFrame:
    r = _rng("enc", producer, month)
    y, m = map(int, month.split("-"))
    first = dt.date(y, m, 1)
    days = ((dt.date(y + (m == 12), m % 12 + 1, 1)) - first).days
    adm = np.array(first, dtype="datetime64[D]") + r.integers(0, days, n)
    los = (1 + r.gamma(1.8, 2.2, n)).astype(np.int16).clip(1, 60)
    return pl.DataFrame({
        "encounter_id": [f"{producer}-{month[2:4]}{month[5:]}-{i:06d}" for i in range(n)],
        "study_id": r.integers(1, 400_000, n).astype(np.int64),
        "admit_date": adm, "discharge_date": adm + los.astype("timedelta64[D]"),
        "ward": r.choice(WARDS, n, p=[0.45, 0.2, 0.15, 0.08, 0.12]),
        "dx_group": r.choice(DX, n), "los_days": los})


def labs_for(enc: pl.DataFrame, producer: str, month: str) -> pl.DataFrame:
    r = _rng("labs", producer, month)
    n = enc.height
    codes = list(TESTS)
    k = len(codes) * 3
    idx = np.repeat(np.arange(n), k)
    test = np.tile(np.repeat(codes, 3), n)
    seq = np.tile(np.tile([1, 2, 3], len(codes)), n).astype(np.int8)
    mu = np.array([TESTS[c][1] for c in codes]).repeat(3)
    sd = np.array([TESTS[c][2] for c in codes]).repeat(3)
    vals = np.exp(np.tile(mu, n) + np.tile(sd, n) * r.standard_normal(n * k)).astype(np.float32)
    if producer == "RWD" and month == "2025-09":  # the planted unit flip: mg/dL under a umol/L label
        vals = np.where(test == "CREAT", vals / 88.42, vals).astype(np.float32)
    adm = enc["admit_date"].to_numpy()[idx]
    los = enc["los_days"].to_numpy()[idx].astype(np.int64)
    offs = np.minimum((seq.astype(np.int64) - 1) * np.maximum(los // 2, 1), los)
    return pl.DataFrame({
        "encounter_id": enc["encounter_id"].gather(idx), "test_code": test, "result_seq": seq,
        "value": np.round(vals, 2), "unit": np.array([TESTS[c][0] for c in codes]).repeat(3)[np.tile(np.arange(k), n)],
        "result_date": adm + offs.astype("timedelta64[D]")})


def pharmacy_for(enc: pl.DataFrame, producer: str, month: str) -> pl.DataFrame:
    r = _rng("rx", producer, month)
    n = enc.height
    idx = np.repeat(np.arange(n), 6)
    return pl.DataFrame({
        "encounter_id": enc["encounter_id"].gather(idx), "atc_code": r.choice(ATC, n * 6),
        "dispensed_date": enc["admit_date"].to_numpy()[idx] + r.integers(0, 3, n * 6).astype("timedelta64[D]"),
        "quantity": r.integers(1, 60, n * 6).astype(np.int16)})


def landing(scale: float):
    """Five days of laboratory deliveries for Lab 2.2, with a re-delivery and a late correction."""
    n = max(60, int(20_000 * scale))
    base = LAKE / "landing"
    for d in range(1, 6):
        day = f"2026-01-0{d}"
        for p in PRODUCERS:
            r = _rng("landing", p, day)
            enc_ids = [f"{p}-2601-{d:02d}{i:05d}" for i in range(n // 6)]
            rows = len(enc_ids) * 6
            df = pl.DataFrame({"encounter_id": np.repeat(enc_ids, 6), "test_code": np.tile(list(TESTS), len(enc_ids)),
                               "result_seq": np.ones(rows, np.int8),
                               "value": np.round(np.exp(np.tile([TESTS[c][1] for c in TESTS], len(enc_ids))
                                                        + 0.2 * r.standard_normal(rows)), 2).astype(np.float32),
                               "result_date": np.full(rows, np.datetime64(day, "D"))})
            if p == "SDR" and d == 5:  # Sidra corrects 15 creatinine results it sent on 2026-01-02
                prev = pl.read_parquet(base / "day=2026-01-02" / "SDR_labs.parquet")
                fix = prev.filter(pl.col("test_code") == "CREAT").head(15).with_columns((pl.col("value") * 1.1).round(2))
                df = pl.concat([df, fix])
            out = base / f"day={day}" / f"{p}_labs.parquet"
            out.parent.mkdir(parents=True, exist_ok=True)
            df.write_parquet(out)
            if p == "UFQ" and d == 3:  # Ufuq sends the same day again: 20 values corrected, 6 rows added
                again = df.with_columns(pl.when(pl.int_range(pl.len()) < 20).then((pl.col("value") * 0.9).round(2))
                                        .otherwise(pl.col("value")).alias("value"))
                extra = df.head(6).with_columns(pl.col("encounter_id") + "X")
                pl.concat([again, extra]).write_parquet(out.with_name("UFQ_labs.r2.parquet"))


def ensure_lake(scale: float | None = None, force: bool = False) -> Path:
    """Write the lake unless a lake of the same scale is already there. Returns its folder."""
    scale = scale_default() if scale is None else scale
    marker = LAKE / "_lake.json"
    if marker.exists() and not force:
        info = json.loads(marker.read_text(encoding="utf-8"))
        if info.get("scale") == scale:
            return LAKE
    if LAKE.exists():
        shutil.rmtree(LAKE)
    n = max(30, int(ENC_PER_PM * scale))
    counts = {"encounters": 0, "labs": 0, "pharmacy": 0}
    for p in PRODUCERS:
        for m in MONTHS:
            enc = encounters_for(p, m, n)
            for table, df in (("encounters", enc), ("labs", labs_for(enc, p, m)), ("pharmacy", pharmacy_for(enc, p, m))):
                path = _partition(table, p, m)
                path.parent.mkdir(parents=True, exist_ok=True)
                df.write_parquet(path, row_group_size=256_000)
                counts[table] += df.height
    landing(scale)
    marker.write_text(json.dumps({"scale": scale, "rows": counts, "total": sum(counts.values())}, indent=2) + "\n",
                      encoding="utf-8", newline="\n")
    return LAKE


def lake_info() -> dict:
    return json.loads((LAKE / "_lake.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    import time
    t0 = time.perf_counter()
    ensure_lake(force="--force" in sys.argv)
    print(lake_info(), f"{time.perf_counter() - t0:.1f} s")


def december_analysis(enc: pl.DataFrame) -> pl.DataFrame:
    """The December analysis set of the readmission study: discharges and length of stay by producer and ward."""
    return (enc.filter(pl.col("month") == "2025-12").group_by("producer", "ward")
            .agg(discharges=pl.len(), total_los=pl.col("los_days").cast(pl.Int64).sum())
            .sort("producer", "ward"))


def history_table(table: Path) -> dict:
    """Lab 2.3: a curated encounter table with four versions, and the record of an analysis run.

    v0  October and November     v1  December arrives; the December analysis set is built here
    v2  corrections of 2% of December discharges (merge)     v3  Rawdah's late December encounters
    Returns the analysis run record, as the scheduler logged it."""
    from deltalake import DeltaTable
    if table.exists():
        shutil.rmtree(table)
    scan = pl.scan_parquet(LAKE / "raw" / "encounters" / "**" / "*.parquet", hive_partitioning=True)
    enc = scan.filter(pl.col("month") >= "2025-10").collect().sort("encounter_id")
    enc.filter(pl.col("month") < "2025-12").write_delta(str(table), delta_write_options={"partition_by": ["month"]})
    enc.filter(pl.col("month") == "2025-12").write_delta(str(table), mode="append")
    import rimah
    v = DeltaTable(str(table)).version()
    built = december_analysis(pl.read_delta(str(table), version=v))
    record = {"analysis": "december_discharges", "table": "curated/encounters", "version": v,
              "rows": built.height, "fingerprint": rimah.fingerprint(built)}
    r = np.random.default_rng(SEED)
    dec = enc.filter(pl.col("month") == "2025-12")
    fix = dec.filter(pl.Series(r.random(dec.height) < 0.02)).with_columns(
        (pl.col("discharge_date") + pl.duration(days=2)).alias("discharge_date"), (pl.col("los_days") + 2).alias("los_days"))
    (DeltaTable(str(table)).merge(fix.to_arrow(), predicate="t.encounter_id = s.encounter_id", source_alias="s", target_alias="t")
     .when_matched_update_all().execute())
    late = dec.filter(pl.col("producer") == "RWD").head(max(3, dec.height // 100)).with_columns(pl.col("encounter_id") + "L")
    late.write_delta(str(table), mode="append")
    return record
