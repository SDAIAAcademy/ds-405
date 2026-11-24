"""Numbers for two Day 2 teaching examples that are not lab answers.

    uv run python _tools/day2_examples.py          # from labs/; prints JSON

1. Session 2, "reload or capture": a simulated pharmacy dispensing table at Ufuq that the
   consortium copies every 15 minutes (96 refreshes a day), compared under three ways of copying
   it: a full reload, a query on an updated-at column, and log-based change data capture. A second
   source, Rawdah's ward reference table, copied once a week, is the contrast.
2. Session 3, "written but not found": a small curated pharmacy table in Delta format, three months
   committed, then a January file copied into the table's folder without a commit. The script
   counts what the folder holds, what the table holds, and what changes after a commit.

Everything is synthetic, with a fixed seed. The slides `reload-or-capture`, `change-log`,
`written-not-found` and `register-partitions` in slides/day2.html quote these results; the last
one also uses the check of a misspelt partition folder (month=2026-1).
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import numpy as np
import polars as pl
from deltalake import DeltaTable

SEED = 4052


def cdc_example() -> dict:
    r = np.random.default_rng(SEED)
    start_rows = 480_000
    refreshes = 96  # every 15 minutes for a day
    live = set(range(start_rows))
    next_key = start_rows
    full_reload_rows = 0
    events = []  # (seq, op, key)
    seq = 0
    query_rows = 0
    deletes = 0
    lost_intermediate = 0
    for w in range(refreshes):
        busy = 1.0 if 28 <= w < 80 else 0.25  # daytime windows are busier
        n_ins, n_upd, n_del = r.poisson(70 * busy), r.poisson(30 * busy), r.poisson(2.0 * busy)
        touched: dict[int, int] = {}
        for _ in range(n_ins):
            k = next_key
            next_key += 1
            live.add(k)
            seq += 1
            events.append((seq, "insert", k, w))
            touched[k] = touched.get(k, 0) + 1
        pool = np.fromiter(live, dtype=np.int64)
        recent = [e[2] for e in events[-400:] if e[2] in live]
        for i in range(n_upd):
            # a third of updates hit a line inserted or changed in the last few windows
            k = int(r.choice(recent)) if recent and r.random() < 0.33 else int(r.choice(pool))
            seq += 1
            events.append((seq, "update", k, w))
            touched[k] = touched.get(k, 0) + 1
        for _ in range(n_del):
            k = int(r.choice(recent)) if recent and r.random() < 0.5 else int(r.choice(pool))
            if k not in live:
                continue
            live.discard(k)
            seq += 1
            events.append((seq, "delete", k, w))
            deletes += 1
            touched[k] = touched.get(k, 0) + 1
        # an updated-at query sees the final state of every live key changed in the window
        query_rows += sum(1 for k in touched if k in live)
        lost_intermediate += sum(c - 1 for k, c in touched.items() if c > 1 and k in live)
        full_reload_rows += len(live)
    by_op = {op: sum(1 for e in events if e[1] == op) for op in ("insert", "update", "delete")}
    # one key whose history in the log shows why order matters: inserted, updated, deleted
    hist = {}
    for s, op, k, w in events:
        hist.setdefault(k, []).append((s, op, w))
    story = next(k for k, h in hist.items() if [x[1] for x in h][:1] == ["insert"]
                 and "update" in [x[1] for x in h] and h[-1][1] == "delete")
    weekly = {"rows": 1_840, "refreshes_per_week": 1}
    rw = np.random.default_rng(SEED + 1)
    weekly_changes = int(rw.poisson(9))
    return {
        "source_rows_start": start_rows, "source_rows_end": len(live), "refreshes_per_day": refreshes,
        "full_reload_rows_per_day": full_reload_rows, "log_events_per_day": len(events), "log_events_by_op": by_op,
        "updated_at_rows_per_day": query_rows, "deletes_missed_by_updated_at": deletes,
        "intermediate_states_missed_by_updated_at": lost_intermediate,
        "reload_to_log_ratio": round(full_reload_rows / len(events)),
        "story_key": story, "story_events": [{"seq": s, "op": op, "window": w} for s, op, w in hist[story]],
        "weekly_reference": {**weekly, "changes_per_week": weekly_changes},
    }


def pharmacy_month(r: np.random.Generator, month: str, n: int) -> pl.DataFrame:
    return pl.DataFrame({
        "line_id": [f"SDR-RX-{month.replace('-', '')}-{i:05d}" for i in range(n)],
        "atc_code": r.choice(["C03CA01", "C09AA05", "A10BA02", "B01AC06", "N02BE01"], n),
        "quantity": r.integers(1, 60, n).astype(np.int16),
        "month": [month] * n})


def registration_example() -> dict:
    r = np.random.default_rng(SEED + 2)
    tmp = Path(tempfile.mkdtemp(prefix="d2ex-"))
    try:
        table = tmp / "pharmacy"
        sizes = {m: int(r.integers(9_000, 9_600)) for m in ("2025-10", "2025-11", "2025-12", "2026-01")}
        for m in ("2025-10", "2025-11", "2025-12"):
            pharmacy_month(r, m, sizes[m]).write_delta(str(table), mode="append",
                                                       delta_write_options={"partition_by": ["month"]})
        jan = pharmacy_month(r, "2026-01", sizes["2026-01"])
        stray = table / "month=2026-01" / "part-00000.parquet"
        stray.parent.mkdir(parents=True)
        jan.drop("month").write_parquet(stray)  # copied in by a job, no commit

        dt = DeltaTable(str(table))
        on_disk = sorted(p.relative_to(table).as_posix() for p in table.rglob("*.parquet"))
        in_table = sorted(dt.file_uris())
        jan_on_disk = sum(f.startswith("month=2026-01/") for f in on_disk)
        jan_in_table = sum("month=2026-01" in f for f in in_table)
        df = pl.read_delta(str(table))
        jan_rows_before = df.filter(pl.col("month") == "2026-01").height
        months_before = sorted(df["month"].unique().to_list())
        glob_rows = pl.scan_parquet(str(table / "**" / "*.parquet"), hive_partitioning=True) \
            .filter(pl.col("month") == "2026-01").select(pl.len()).collect().item()

        # the fix in a table format: commit the data through the table's writer
        pl.read_parquet(stray).with_columns(pl.lit("2026-01").alias("month")).write_delta(
            str(table), mode="append", delta_write_options={"partition_by": ["month"]})
        dt2 = DeltaTable(str(table))
        jan_rows_after = pl.read_delta(str(table)).filter(pl.col("month") == "2026-01").height

        # a folder read by its name (hive partitioning): month=2026-1 is another value than 2026-01
        folders = tmp / "folders"
        for name in ("month=2025-12", "month=2026-1"):
            (folders / name).mkdir(parents=True)
            jan.drop("month").write_parquet(folders / name / "part-0.parquet")
        scan = pl.scan_parquet(str(folders / "**" / "*.parquet"), hive_partitioning=True)
        misspelt_rows_found = scan.filter(pl.col("month").cast(pl.String) == "2026-01").select(pl.len()).collect().item()
        misspelt_values = sorted(scan.select(pl.col("month").cast(pl.String).unique()).collect()["month"].to_list())
        return {
            "rows_per_month": sizes, "parquet_files_on_disk": len(on_disk), "files_in_table": len(in_table),
            "jan_files_on_disk": jan_on_disk, "jan_files_in_table": jan_in_table,
            "months_visible_before": months_before, "jan_rows_visible_before": jan_rows_before,
            "jan_rows_by_folder_scan": glob_rows,
            "version_after_commit": dt2.version(), "files_in_table_after": len(dt2.file_uris()),
            "jan_rows_visible_after": jan_rows_after,
            "misspelt_folder_values": misspelt_values, "misspelt_folder_rows_found_by_2026_01": misspelt_rows_found,
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print(json.dumps({"cdc": cdc_example(), "registration": registration_example()}, indent=1))
