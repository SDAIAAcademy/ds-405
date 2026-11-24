# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "deltalake>=1.4", "pyarrow>=20.0", "numpy>=2.0", "psutil>=7.0", "pyyaml>=6.0"]
# ///
# %% [markdown]
# # Lab 2.3 · Rebuild last month
#
# Day 2 · Session 3 (Tables with history) · 25 min.
#
# In early January the study team built the December analysis set from the curated encounter
# table and sent figures to the release board. Since then, producers corrected some discharge
# dates and Rawdah delivered late December encounters. Dr. Fadwa Al-Qassabi asks: can you
# reproduce exactly what the board saw? You read the table's history, rebuild the analysis set
# from the version the run recorded, prove it identical, and measure what changed since.
#
# **Reference state.** The setup cell builds `artifacts/D2_3/encounters`, a Delta table with four
# versions, from the lake, and returns the scheduler's record of the analysis run. Nothing from Lab 2.2.
#
# **Tasks**
# - [ ] 1 · Read the table's history (4')
# - [ ] 2 · The analysis run record (4')
# - [ ] 3 · Rebuild from the recorded version (7')
# - [ ] 4 · Prove it identical, then diff with today (6')
# - [ ] 5 · What vacuuming would break (4')
# - [ ] ✱ Stretch · Restore the table to the recorded version and compare
# - [ ] ✱ Stretch question · Written but not found

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

import shutil

import polars as pl
from deltalake import DeltaTable
import rimah as U
import rimah_lake

rimah_lake.ensure_lake()
WORK = U.lab_dir("D2_3")
TABLE = WORK / "encounters"
RUN = rimah_lake.history_table(TABLE)
analysis_set = rimah_lake.december_analysis  # the study's December query: discharges and days by producer and ward

# %% [markdown]
# ## 1 · Read the table's history (4')
#
# An open table format keeps a log of commits; every commit is a version of the table. Print the
# version, operation and parameters of each commit, newest first.

# %%
hist = DeltaTable(str(TABLE)).history()
for h in hist:
    print(h["version"], h["operation"], {k: v for k, v in h.get("operationParameters", {}).items() if k in ("mode", "predicate")})
print("current version:", DeltaTable(str(TABLE)).version())

# %% [markdown]
# ## 2 · The analysis run record (4')
#
# The scheduler logged, with the December run, which table version it read and a fingerprint of
# what it produced. That one line is what makes the figures reproducible. 🔍 Without `version`,
# what would you have to do to answer Dr. Fadwa?

# %%
print(RUN)

# %% [markdown]
# ## 3 · Rebuild from the recorded version (7')
#
# ✏️ **Exercise** · `rebuild(version)`: read the table **as it was** at that version
# (`pl.read_delta(..., version=...)`) and apply `analysis_set`. Then rebuild from the current
# version too.

# %%
def rebuild(version: int | None) -> pl.DataFrame:
    # BEGIN SOLUTION
    df = pl.read_delta(str(TABLE), version=version) if version is not None else pl.read_delta(str(TABLE))
    return analysis_set(df)
    # END SOLUTION


# %%
try:
    then, now = rebuild(RUN["version"]), rebuild(None)
except NotImplementedError:
    then = analysis_set(pl.read_delta(str(TABLE), version=RUN["version"]))
    now = analysis_set(pl.read_delta(str(TABLE)))
print(then.head(5))

# %% [markdown]
# ## 4 · Prove it identical, then diff with today (6')
#
# ✏️ **Exercise** · Compare the fingerprint of your rebuild with the recorded one. Then join
# `then` and `now` on producer and ward and list the cells whose discharges or days changed.

# %%
def diff(then: pl.DataFrame, now: pl.DataFrame) -> pl.DataFrame:
    # BEGIN SOLUTION
    j = then.join(now, on=["producer", "ward"], suffix="_now")
    return (j.with_columns((pl.col("discharges_now").cast(pl.Int64) - pl.col("discharges").cast(pl.Int64)).alias("d_discharges"),
                           (pl.col("total_los_now") - pl.col("total_los")).alias("d_days"))
            .filter((pl.col("d_discharges") != 0) | (pl.col("d_days") != 0))
            .select("producer", "ward", "discharges", "d_discharges", "total_los", "d_days"))
    # END SOLUTION


# %%
rebuilt_fp = U.fingerprint(then)
U.check(rebuilt_fp == RUN["fingerprint"], f"the rebuilt December set is identical to what the board saw ({rebuilt_fp})")
U.check(U.fingerprint(now) != RUN["fingerprint"], "today's table gives different figures")
try:
    changes = diff(then, now)
except NotImplementedError:
    changes = then.join(now, on=["producer", "ward"], suffix="_now").filter(
        (pl.col("discharges_now") != pl.col("discharges")) | (pl.col("total_los_now") != pl.col("total_los")))
print(changes)
print("cells changed:", changes.height, "of", then.height)

# %% [markdown]
# 🔍 Which producer's discharges changed, and why only that one? Which cells changed only in days?

# %% [markdown]
# ## 5 · What vacuuming would break (4')
#
# Old versions live in data files the table no longer uses. **Vacuum** deletes such files after a
# retention period (seven days by default) to save storage. Ask for a dry run with retention zero
# on a copy, then vacuum the copy for real and try to read the recorded version.

# %%
copy = WORK / "encounters_copy"
shutil.copytree(TABLE, copy)
dt_copy = DeltaTable(str(copy))
would_go = dt_copy.vacuum(retention_hours=0, enforce_retention_duration=False, dry_run=True)
print(len(would_go), "files would be deleted")
dt_copy.vacuum(retention_hours=0, enforce_retention_duration=False, dry_run=False)
try:
    analysis_set(pl.read_delta(str(copy), version=RUN["version"]))
    survived = True
except Exception as e:  # the old version's files are gone
    survived = False
    print("reading the recorded version failed:", type(e).__name__)
U.check(not survived, "after a vacuum with zero retention the recorded version can no longer be rebuilt")

# %% [markdown]
# Set the retention to cover your reproducibility promise (the board may ask for a year), or
# snapshot what was released: a copy of the analysis set and its fingerprint, kept with the
# decision record.

# %% [markdown]
# ## ✱ Stretch · Restore to the recorded version
#
# `DeltaTable.restore(version)` makes a **new** commit whose content equals an old version.
# Restore a second copy and check that today's analysis on it equals the recorded fingerprint, and
# that the history still shows every version.

# %%
def restore_and_compare() -> tuple[bool, int]:
    # BEGIN SOLUTION
    c2 = WORK / "encounters_restored"
    shutil.copytree(TABLE, c2)
    t = DeltaTable(str(c2))
    t.restore(RUN["version"])
    ok = U.fingerprint(analysis_set(pl.read_delta(str(c2)))) == RUN["fingerprint"]
    return ok, len(DeltaTable(str(c2)).history())
    # END SOLUTION


try:
    print("restored equals the record:", *restore_and_compare())
except NotImplementedError:
    print("Stretch not attempted.")

# %% [markdown]
# ## ✱ Stretch question · Written but not found
#
# On a third copy, a transfer job has put Rawdah's first January encounters into the folder
# `month=2026-01/` as a plain Parquet file, and reported success. The study team says January is
# empty. ✏️ **Exercise** · `diagnose_and_register(table)`: count the Parquet files in January's
# folder and the January files the table's log lists, count January rows as the table sees them, then make the
# rows part of the table with a commit through the table's writer and count again. 🔍 Which count
# tells you the cause, and why would reading the folder with a glob have hidden it?

# %%
late_copy = WORK / "encounters_late"
shutil.copytree(TABLE, late_copy)
_dec = pl.read_delta(str(late_copy)).filter((pl.col("month") == "2025-12") & (pl.col("producer") == "RWD"))
_jan = _dec.head(max(5, _dec.height // 20)).with_columns((pl.col("encounter_id") + "J").alias("encounter_id"))
(late_copy / "month=2026-01").mkdir()
_jan.drop("month").write_parquet(late_copy / "month=2026-01" / "part-00000.parquet")  # no commit
JAN_SENT = _jan.height


def diagnose_and_register(table: Path) -> dict:
    # BEGIN SOLUTION
    on_disk = len(list((table / "month=2026-01").glob("*.parquet")))
    in_log = sum("month=2026-01" in f for f in DeltaTable(str(table)).file_uris())
    before = pl.read_delta(str(table)).filter(pl.col("month") == "2026-01").height
    stray = pl.read_parquet(table / "month=2026-01" / "part-00000.parquet").with_columns(pl.lit("2026-01").alias("month"))
    stray.select(pl.read_delta(str(table)).columns).write_delta(str(table), mode="append")
    after = pl.read_delta(str(table)).filter(pl.col("month") == "2026-01").height
    return {"files_on_disk": on_disk, "files_in_log": in_log, "january_before": before, "january_after": after}
    # END SOLUTION


try:
    found = diagnose_and_register(late_copy)
    print(found)
    U.check(found["files_on_disk"] == 1 and found["files_in_log"] == 0, "January's folder holds a file the table's log does not list")
    U.check(found["january_before"] == 0 and found["january_after"] == JAN_SENT,
            f"January was invisible until committed; now {JAN_SENT} rows")
except NotImplementedError:
    print("Stretch question not attempted.")

# %% [markdown]
# ## Checkpoint
#
# 1. The analysis log says "built on 2026-01-04" but not the version. Can you rebuild it exactly?
# 2. Why did the late Rawdah rows change the figures although nobody "edited" December?
# 3. Who should decide the vacuum retention: the platform team alone?
# 4. A job says it wrote January, and the table shows no January rows. What do you compare first?
#
# <details><summary>Answers</summary>
#
# 1. Only if the table keeps timestamps and you can map the time to a version; the version itself is the reliable reference, so log it.
# 2. December's set is defined by the data present; late deliveries add rows to a past period. Reported figures must say which version they used.
# 3. No: the retention is a promise to the people who rely on reproducing releases, so the release board and the data owner set it with the platform team.
# 4. The files in the folder against the files the table's metadata lists (the log here, the catalog's partitions for a catalogued table). A file outside the metadata is not in the table; a glob over the folder reads it anyway, which is why a quick check by glob says "the data is there". Register it by committing through the table's writer, or by the catalog's own command for a catalogued table.
# </details>
#
# **Carry forward.** Nothing: Lab 2.4 reads the lake.
