# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "deltalake>=1.4", "pyarrow>=20.0", "numpy>=2.0", "psutil>=7.0", "pyyaml>=6.0"]
# ///
# %% [markdown]
# # Lab 2.2 · Load one day twice
#
# Day 2 · Session 2 (Incremental and idempotent loads) · 25 min.
#
# Every morning the three producers drop the previous day's laboratory results into a landing
# folder, and the consortium loads them into a curated Delta table. Loads fail half-way, get
# re-run, and producers send a day again. A load is **idempotent** when running it twice leaves
# the table exactly as running it once. You prove the append load is not, make it so by partition
# overwrite and then by merging on the business key, and prove it by loading every day twice.
#
# **Reference state.** `data/lake/landing/day=2026-01-01` to `day=2026-01-05`, written by the setup
# cell. Ufuq sends 2026-01-03 again with corrections (`UFQ_labs.r2.parquet`); Sidra's 2026-01-05
# delivery corrects 15 results of 2026-01-02. Every table is written under `artifacts/D2_2/`.
#
# **Tasks**
# - [ ] 1 · The append load and its duplicates (5')
# - [ ] 2 · A table fingerprint (4')
# - [ ] 3 · Idempotent: overwrite the day's partition (6')
# - [ ] 4 · Corrections: merge on the business key (6')
# - [ ] 5 · Load every day twice and compare (4')
# - [ ] ✱ Stretch · Keep a load log so a day is skipped when its file has not changed

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/ds-405.git"
    if not Path("/content/ds-405").exists():
        subprocess.run(["git", "clone", "-q", REPO_URL, "/content/ds-405"], check=True)
    os.chdir("/content/ds-405/labs")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"], check=True)
else:
    while not Path("rimah.py").exists() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")  # solutions/ notebooks run from labs/
sys.path.insert(0, os.getcwd())

import hashlib

import polars as pl
from deltalake import DeltaTable
import rimah as U
import rimah_lake

LAKE = rimah_lake.ensure_lake()
LANDING = LAKE / "landing"
DAYS = [f"2026-01-0{d}" for d in range(1, 6)]
KEY = ["encounter_id", "test_code", "result_seq"]
WORK = U.lab_dir("D2_2")


def delivery(day: str) -> pl.DataFrame:
    """The day's files from all producers. When a producer sent a day again (`.r2`), the newest file wins."""
    parts = []
    for p in ["SDR", "UFQ", "RWD"]:
        files = sorted((LANDING / f"day={day}").glob(f"{p}_labs*.parquet"))
        parts.append(pl.read_parquet(files[-1]).with_columns(pl.lit(p).alias("producer"), pl.lit(day).alias("delivered_day")))
    return pl.concat(parts)


def read(table: Path) -> pl.DataFrame:
    return pl.read_delta(str(table))


print({d: delivery(d).height for d in DAYS})

# %% [markdown]
# ## 1 · The append load and its duplicates (5')
#
# The inherited load appends whatever arrived. Load 2026-01-01, then load it again as a re-run
# after a failure would, and count rows and duplicate keys.

# %%
def load_append(table: Path, day: str):
    delivery(day).write_delta(str(table), mode="append")


t_append = WORK / "labs_append"
load_append(t_append, DAYS[0])
once = read(t_append).height
load_append(t_append, DAYS[0])
twice = read(t_append)
dups = twice.height - twice.unique(KEY).height
print(f"once: {once} rows; twice: {twice.height} rows; duplicate keys: {dups}")
U.check(twice.height == 2 * once, "appending a day twice doubles it: the load is not idempotent")

# %% [markdown]
# ## 2 · A table fingerprint (4')
#
# "Same table" must mean same content, whatever the files or the row order. ✏️ **Exercise** ·
# Write `table_hash(df)`: sort by the business key, keep the columns in a fixed order, and hash
# the rows. (`U.fingerprint` does the same thing; write your own first.)

# %%
COLS = ["encounter_id", "test_code", "result_seq", "value", "result_date", "producer"]


def table_hash(df: pl.DataFrame) -> str:
    # BEGIN SOLUTION
    d = df.select(COLS).sort(KEY)
    return hashlib.sha256(d.write_csv().encode("utf-8")).hexdigest()[:16]
    # END SOLUTION


# %%
try:
    h1 = table_hash(delivery(DAYS[0]))
    h2 = table_hash(delivery(DAYS[0]).sample(fraction=1.0, shuffle=True, seed=1))
except NotImplementedError:
    def table_hash(df):
        return U.fingerprint(df.select(COLS), KEY)
    h1, h2 = table_hash(delivery(DAYS[0])), table_hash(delivery(DAYS[0]).sample(fraction=1.0, shuffle=True, seed=1))
U.check(h1 == h2, f"row order does not change the fingerprint ({h1})")
U.check(table_hash(twice) != table_hash(twice.unique(KEY)), "duplicates do change it")

# %% [markdown]
# ## 3 · Idempotent: overwrite the day's partition (6')
#
# Write the table partitioned by `delivered_day`, and make each load **replace** its own day:
# Delta Lake's overwrite with a predicate rewrites only the rows that match it.
#
# ✏️ **Exercise** · `load_overwrite(table, day)` with `write_delta(..., mode="overwrite",
# delta_write_options={"predicate": ..., "partition_by": ["delivered_day"]})`. Hint: the first
# write creates the table, so the predicate is only needed when the table exists.

# %%
def load_overwrite(table: Path, day: str):
    # BEGIN SOLUTION
    df = delivery(day)
    if not (table / "_delta_log").exists():
        df.write_delta(str(table), mode="append", delta_write_options={"partition_by": ["delivered_day"]})
    else:
        df.write_delta(str(table), mode="overwrite",
                       delta_write_options={"predicate": f"delivered_day = '{day}'", "partition_by": ["delivered_day"]})
    # END SOLUTION


# %%
t_over = WORK / "labs_overwrite"
try:
    load_overwrite(t_over, DAYS[0]); a = table_hash(read(t_over))
    load_overwrite(t_over, DAYS[0]); b = table_hash(read(t_over))
    U.check(a == b, f"loading 2026-01-01 twice leaves the same table ({a})")
    for d in DAYS:
        load_overwrite(t_over, d)
    over = read(t_over)
    dup_keys = over.height - over.unique(KEY).height
    print(f"days 1 to 5 by overwrite: {over.height} rows, {dup_keys} duplicate keys")
    U.check(dup_keys == 15, "but Sidra's 15 corrections of 2026-01-02 now sit beside the originals")
except NotImplementedError:
    print("Exercise not done: step 4 does not depend on it.")

# %% [markdown]
# 🔍 Partition overwrite makes a re-run safe, and Ufuq's re-sent day simply replaces the first
# version. It cannot handle a correction that arrives on a **later** day for an earlier result:
# the corrected row lands in 2026-01-05's partition and the old one stays in 2026-01-02's.

# %% [markdown]
# ## 4 · Corrections: merge on the business key (6')
#
# A merge matches incoming rows to existing rows on the business key: matched rows are updated,
# new rows inserted. Corrections replace what they correct, whenever they arrive.
#
# ✏️ **Exercise** · `load_merge(table, day)`: create the table on the first load; afterwards
# `DeltaTable(...).merge(source, predicate=..., source_alias="s", target_alias="t")`, then
# `.when_matched_update_all().when_not_matched_insert_all().execute()`.

# %%
def load_merge(table: Path, day: str):
    # BEGIN SOLUTION
    df = delivery(day)
    if not (table / "_delta_log").exists():
        df.write_delta(str(table), mode="append")
        return
    pred = " AND ".join(f"t.{k} = s.{k}" for k in KEY)
    (DeltaTable(str(table)).merge(df.to_arrow(), predicate=pred, source_alias="s", target_alias="t")
     .when_matched_update_all().when_not_matched_insert_all().execute())
    # END SOLUTION


# %%
t_merge = WORK / "labs_merge"
try:
    for d in DAYS:
        load_merge(t_merge, d)
    merged = read(t_merge)
except NotImplementedError:
    import shutil
    shutil.rmtree(t_merge, ignore_errors=True)
    rows = pl.concat([delivery(d) for d in DAYS]).unique(KEY, keep="last", maintain_order=True)
    rows.write_delta(str(t_merge))
    merged = read(t_merge)
dup_keys = merged.height - merged.unique(KEY).height
fixed = merged.join(delivery(DAYS[4]).filter(pl.col("producer") == "SDR"), on=KEY).filter(pl.col("delivered_day") == DAYS[4]).height
print(f"days 1 to 5 by merge: {merged.height} rows, {dup_keys} duplicate keys")
U.check(dup_keys == 0, "no duplicate keys")
U.check(fixed >= 15, "Sidra's corrected values replaced the originals")

# %% [markdown]
# ## 5 · Load every day twice and compare (4')
#
# The proof the outcome asks for: a fresh table loaded once per day, and another loaded with every
# day twice (and day 3 three times), give the same fingerprint.

# %%
def build(table: Path, order: list[str]) -> str:
    import shutil
    shutil.rmtree(table, ignore_errors=True)
    for d in order:
        try:
            load_merge(table, d)
        except NotImplementedError:  # safety net: rewrite the whole table, newest row per key wins
            new = delivery(d)
            old = read(table).select(new.columns) if (table / "_delta_log").exists() else new.clear()
            pl.concat([old, new]).unique(KEY, keep="last", maintain_order=True).write_delta(str(table), mode="overwrite")
    return table_hash(read(table))


once_h = build(WORK / "once", DAYS)
twice_h = build(WORK / "twice", DAYS + DAYS + [DAYS[2]])
print("once:", once_h, "| every day twice:", twice_h)
U.check(once_h == twice_h, "identical output when days are re-run: the load is idempotent")
history = DeltaTable(str(WORK / "twice")).history()
print(len(history), "versions in the table's log; operations:", sorted({h["operation"] for h in history}))

# %% [markdown]
# ## ✱ Stretch · Skip a day whose files have not changed
#
# Idempotent does not mean free: a merge still reads and rewrites files. Keep a load log of the
# hash of each delivered file, and skip a day whose files all have a logged hash.

# %%
def load_with_log(table: Path, day: str, log: dict) -> bool:
    # BEGIN SOLUTION
    files = sorted((LANDING / f"day={day}").glob("*.parquet"))
    digest = hashlib.sha256(b"".join(f.read_bytes() for f in files)).hexdigest()
    if log.get(day) == digest:
        return False
    load_merge(table, day)
    log[day] = digest
    return True
    # END SOLUTION


try:
    log = {}
    ran = [load_with_log(WORK / "logged", d, log) for d in DAYS + DAYS]
    print("loads run:", sum(ran), "of", len(ran))
except NotImplementedError:
    print("Stretch not attempted.")

# %% [markdown]
# ## Checkpoint
#
# 1. A load appends, then crashes before it writes "done"; the scheduler retries. What do you find tomorrow?
# 2. Ufuq sends a day again. Which approach handles it: overwrite, merge, or both?
# 3. Sidra corrects a result three days later. Which handles that?
#
# <details><summary>Answers</summary>
#
# 1. That day twice: duplicate rows and inflated counts, with no error anywhere.
# 2. Both: overwrite replaces the day's partition; merge updates the matching keys and inserts the rest (the extra rows of the re-sent day stay, which is right only if they are real).
# 3. Only merge on the business key: the correction belongs to an earlier day's rows.
# </details>
#
# **Carry forward.** Nothing: Lab 2.3 builds its own table with history.
