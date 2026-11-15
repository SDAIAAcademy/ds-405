# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pandas>=2.2", "pyarrow>=20.0", "duckdb>=1.4", "numpy>=2.0", "psutil>=7.0", "pyyaml>=6.0"]
# ///
# %% [markdown]
# # Lab 2.1 · From eager to lazy
#
# Day 2 · Session 1 (Columnar files and lazy execution) · 25 min.
#
# The consortium's lake holds a year of encounters, laboratory results and pharmacy lines from the
# three producers: about 30 million rows at full size, partitioned by producer and month. The
# preparation script Atiyah's team inherited reads everything into memory, then filters. You
# rewrite it as a lazy query that reads only the columns and partitions it needs, check that the
# result is the same, and measure wall time and peak memory of both.
#
# **Reference state.** The lake, written by the setup cell (`rimah_lake.py`, fixed seed): full size
# by default, 1 percent with `RIMAH_QUICK=1`. Nothing from Day 1.
#
# **Tasks**
# - [ ] 1 · Run the eager script and measure it (5')
# - [ ] 2 · Read the lake's partitions and the query plan (5')
# - [ ] 3 · Write the lazy query (8')
# - [ ] 4 · Same result, less time and memory (4')
# - [ ] 5 · Streaming for the full size (3')
# - [ ] ✱ Stretch · The same query in DuckDB SQL over the same files

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

import pandas as pd
import polars as pl
import rimah as U
import rimah_lake

LAKE = rimah_lake.ensure_lake()
info = rimah_lake.lake_info()
print(f"lake: {info['total']:,} rows at scale {info['scale']}", info["rows"])

# %% [markdown]
# ## 1 · Run the eager script and measure it (5')
#
# The study needs, for each producer and month of the second half of 2025, the number of
# encounters, the mean of each encounter's highest creatinine, and the share of encounters with a
# glucose above 11.1 mmol/L. This is the inherited script: read it, run it, note the numbers.

# %%
def eager_clean() -> pd.DataFrame:
    labs = pd.read_parquet(LAKE / "raw" / "labs")              # every partition, every column
    enc = pd.read_parquet(LAKE / "raw" / "encounters")
    labs = labs[labs["test_code"].isin(["CREAT", "GLU"])]
    labs = labs[labs["month"].astype(str) >= "2025-07"]
    wide = labs.pivot_table(index="encounter_id", columns="test_code", values="value", aggfunc="max").reset_index()
    out = enc.merge(wide, on="encounter_id")
    out["high_glucose"] = out["GLU"] > 11.1
    out["producer"], out["month"] = out["producer"].astype(str), out["month"].astype(str)
    res = out.groupby(["producer", "month"]).agg(encounters=("encounter_id", "size"), max_creat=("CREAT", "mean"),
                                                 high_glucose=("high_glucose", "mean")).reset_index()
    return res.sort_values(["producer", "month"]).reset_index(drop=True)


eager, t_eager, m_eager = U.measure(eager_clean)
print(f"eager: {t_eager:.2f} s, peak memory +{m_eager:,.0f} MB")
print(eager.head(6))

# %% [markdown]
# ## 2 · Read the lake's partitions and the query plan (5')
#
# Hive partitions put the producer and the month in the folder names, so a query that filters on
# them can skip whole files. Parquet stores each column apart, so a query that needs three columns
# reads three. A **lazy** frame records the query and lets the optimiser push the filters and the
# column list down into the scan. Count the files, then read the plan of a small query.

# %%
files = sorted((LAKE / "raw" / "labs").rglob("*.parquet"))
print(len(files), "laboratory files, for example", files[0].relative_to(LAKE))
q = (pl.scan_parquet(LAKE / "raw" / "labs" / "**" / "*.parquet", hive_partitioning=True)
     .filter(pl.col("month") == "2025-09", pl.col("test_code") == "CREAT")
     .select("encounter_id", "value"))
print(q.explain())

# %% [markdown]
# 🔍 In the plan, find the line that says which columns the scan reads and the line with the
# filter. How many of the 36 laboratory files does this query need to open?

# %% [markdown]
# ## 3 · Write the lazy query (8')
#
# ✏️ **Exercise** · Write `lazy_query()` returning a **LazyFrame** with the same result as the eager
# script: columns `producer`, `month`, `encounters`, `max_creat`, `high_glucose`, sorted by producer
# and month. Filter on the month **before** the join, keep only the two tests, and take the maximum
# of each test per encounter with a conditional aggregation (`pl.col("value").filter(...).max()`).

# %%
def lazy_query() -> pl.LazyFrame:
    # BEGIN SOLUTION
    labs = pl.scan_parquet(LAKE / "raw" / "labs" / "**" / "*.parquet", hive_partitioning=True)
    enc = pl.scan_parquet(LAKE / "raw" / "encounters" / "**" / "*.parquet", hive_partitioning=True)
    wide = (labs.filter(pl.col("month") >= "2025-07", pl.col("test_code").is_in(["CREAT", "GLU"]))
            .group_by("encounter_id")
            .agg(CREAT=pl.col("value").filter(pl.col("test_code") == "CREAT").max(),
                 GLU=pl.col("value").filter(pl.col("test_code") == "GLU").max()))
    return (enc.filter(pl.col("month") >= "2025-07").select("encounter_id", "producer", "month")
            .join(wide, on="encounter_id")
            .group_by("producer", "month")
            .agg(encounters=pl.len(), max_creat=pl.col("CREAT").mean(), high_glucose=(pl.col("GLU") > 11.1).mean())
            .sort("producer", "month"))
    # END SOLUTION


# %%
try:
    lazy_plan = lazy_query()
except NotImplementedError:
    lazy_plan = None
if lazy_plan is not None:
    lazy, t_lazy, m_lazy = U.measure(lambda: lazy_plan.collect())
else:
    lazy, t_lazy, m_lazy = pl.DataFrame(U.reference("lab_2_1")["result"]), float("nan"), float("nan")
    print("(the reference result, not a measurement)")
print(f"lazy: {t_lazy:.2f} s, peak memory +{m_lazy:,.0f} MB")
print(lazy.head(6))

# %% [markdown]
# ## 4 · Same result, less time and memory (4')
#
# A faster query that gives another answer is a bug. Compare the two results value by value,
# then put the measurements side by side.

# %%
e = pl.from_pandas(eager)
same = (e["producer"].to_list() == lazy["producer"].to_list() and e["month"].to_list() == lazy["month"].to_list()
        and e["encounters"].to_list() == lazy["encounters"].to_list()
        and max(abs(a - b) for a, b in zip(e["max_creat"], lazy["max_creat"])) < 1e-3
        and max(abs(a - b) for a, b in zip(e["high_glucose"], lazy["high_glucose"])) < 1e-9)
U.check(same, "the lazy query gives the eager script's result")
timing = pl.DataFrame({"query": ["eager (pandas)", "lazy (polars)"], "seconds": [round(t_eager, 2), round(t_lazy, 2)],
                       "peak_mb": [round(m_eager), round(m_lazy) if m_lazy == m_lazy else None]})
print(timing)
lazy_result_sample = lazy

# %% [markdown]
# ## 5 · Streaming for the full size (3')
#
# The default engine still holds the joined data in memory. The streaming engine processes the
# files in batches, so the peak no longer grows with the lake. Run the same plan with
# `collect(engine="streaming")` and compare the peak. In quick mode the lake is too small for the
# difference to show; the slide has the full-size numbers.

# %%
if lazy_plan is not None:
    streamed, t_s, m_s = U.measure(lambda: lazy_plan.collect(engine="streaming"))
    U.check(streamed.equals(lazy), "the streaming engine gives the same result")
    timing = pl.concat([timing, pl.DataFrame({"query": ["lazy, streaming"], "seconds": [round(t_s, 2)], "peak_mb": [round(m_s)]})])
print(timing)
U.save_json({"scale": info["scale"], "rows": info["total"], "timing": timing.to_dicts()}, U.lab_dir("D2_1") / "timing.json")

# %% [markdown]
# ## ✱ Stretch · The same query in DuckDB SQL
#
# DuckDB reads the same Parquet files with SQL and the same pushdowns. Write the query with
# `read_parquet(..., hive_partitioning = true)` and compare the result and the time.

# %%
def duckdb_query() -> pl.DataFrame:
    # BEGIN SOLUTION
    import duckdb
    labs = (LAKE / "raw" / "labs" / "**" / "*.parquet").as_posix()
    enc = (LAKE / "raw" / "encounters" / "**" / "*.parquet").as_posix()
    sql = f"""
    WITH wide AS (
      SELECT encounter_id, max(value) FILTER (WHERE test_code = 'CREAT') AS creat,
             max(value) FILTER (WHERE test_code = 'GLU') AS glu
      FROM read_parquet('{labs}', hive_partitioning = true)
      WHERE month >= '2025-07' AND test_code IN ('CREAT', 'GLU')
      GROUP BY encounter_id)
    SELECT e.producer, e.month, count(*) AS encounters, avg(w.creat) AS max_creat, avg((w.glu > 11.1)::INT) AS high_glucose
    FROM read_parquet('{enc}', hive_partitioning = true) e JOIN wide w USING (encounter_id)
    WHERE e.month >= '2025-07' GROUP BY ALL ORDER BY 1, 2"""
    return duckdb.sql(sql).pl()
    # END SOLUTION


try:
    d, t_d, m_d = U.measure(duckdb_query)
    print(f"duckdb: {t_d:.2f} s, peak +{m_d:,.0f} MB; same counts: {d['encounters'].to_list() == lazy['encounters'].to_list()}")
except NotImplementedError:
    print("Stretch not attempted.")

# %% [markdown]
# ## Checkpoint
#
# 1. Your lazy query filters on `month` after the join. Is the result different? Is the cost?
# 2. Why does reading 3 of 8 columns save more in Parquet than in CSV?
# 3. When is the eager script good enough?
#
# <details><summary>Answers</summary>
#
# 1. The result is the same; the optimiser often pushes the filter down anyway, but write it before the join so that you do not depend on it, and check the plan.
# 2. Parquet stores each column separately, so unread columns are never read from disk; a CSV row must be read whole.
# 3. When the data fits comfortably in memory and runs once; the lazy form costs little to write and keeps working when the lake grows.
# </details>
#
# **Carry forward.** `artifacts/D2_1/timing.json`. Lab 2.2 starts from the landing files, not from this result.
