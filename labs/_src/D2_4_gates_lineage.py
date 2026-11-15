# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "numpy>=2.0", "psutil>=7.0", "pyyaml>=6.0"]
# ///
# %% [markdown]
# # Lab 2.4 · Gates and lineage per partition
#
# Day 2 · Session 4 (Gates and lineage at scale) · 25 min.
#
# Yesterday's monthly creatinine figures for the study show a dip in September, and nobody knows
# where it comes from. You run the contract's blocking rules on every partition of the lake (one
# producer, one month), quarantine what fails and publish the rest, emit an OpenLineage run event
# for every job run, and walk yesterday's events backwards from the figure to the producer and
# partition that caused it.
#
# **Reference state.** The lake (setup cell) and `yesterday_events()`, which writes the lineage
# events of yesterday's run, the one without gates. Nothing from Labs 2.1 to 2.3.
#
# **Tasks**
# - [ ] 1 · Contract rules as per-partition gates (7')
# - [ ] 2 · Quarantine and publish the rest (5')
# - [ ] 3 · Emit OpenLineage run events (6')
# - [ ] 4 · Trace the defect back through the events (7')
# - [ ] ✱ Stretch · A gate on the distribution, not only on the values

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

import polars as pl
import rimah as U
import rimah_lake

LAKE = rimah_lake.ensure_lake()
WORK = U.lab_dir("D2_4")
LABS = pl.scan_parquet(LAKE / "raw" / "labs" / "**" / "*.parquet", hive_partitioning=True)


def part(producer: str, month: str, zone: str = "raw") -> str:
    """The dataset name of one partition, as lineage events name it."""
    return f"{zone}/labs/producer={producer}/month={month}"


def yesterday_events() -> Path:
    """Yesterday's run, before gates: every raw partition published as is, then the monthly figure."""
    ev = []
    for p in ["SDR", "UFQ", "RWD"]:
        for m in U.months():
            rid = U.run_id("publish", p, m, "yesterday")
            ev.append(U.ol_event("START", "rimah.labs_publish", rid, [part(p, m)], []))
            ev.append(U.ol_event("COMPLETE", "rimah.labs_publish", rid, [part(p, m)], [part(p, m, "curated")]))
    rid = U.run_id("monthly_creatinine", "yesterday")
    ins = [part(p, m, "curated") for p in ["SDR", "UFQ", "RWD"] for m in U.months()]
    ev.append(U.ol_event("START", "rimah.monthly_creatinine", rid, ins, []))
    ev.append(U.ol_event("COMPLETE", "rimah.monthly_creatinine", rid, ins, ["analysis/monthly_creatinine"]))
    return U.write_events(ev, WORK / "yesterday.jsonl")


monthly = (LABS.filter(pl.col("test_code") == "CREAT").group_by("month").agg(median_creat=pl.col("value").median())
           .sort("month").collect())
print("yesterday's figure (no gates):\n", monthly.transpose(include_header=False, column_names="month"))

# %% [markdown]
# ## 1 · Contract rules as per-partition gates (7')
#
# The contract's plausible ranges become gates: in each partition, at most 0.5% of a test's
# results may fall outside its range. One lazy query computes every partition at once.
#
# ✏️ **Exercise** · `gate_table()`: one row per producer and month with `rows`, `invalid` (results
# outside the range of their test), `share` (percent) and `passed`.

# %%
RANGES = {"CREAT": (20, 1500), "GLU": (1, 60), "HB": (30, 250), "NA": (100, 180), "K": (1.5, 9), "WBC": (0.1, 200)}
MAX_SHARE = 0.5  # percent


def gate_table() -> pl.DataFrame:
    # BEGIN SOLUTION
    rng = pl.DataFrame({"test_code": list(RANGES), "lo": [float(v[0]) for v in RANGES.values()],
                        "hi": [float(v[1]) for v in RANGES.values()]}).lazy()
    return (LABS.join(rng, on="test_code")
            .with_columns(bad=~pl.col("value").is_between(pl.col("lo"), pl.col("hi")) | pl.col("value").is_null())
            .group_by("producer", "month").agg(rows=pl.len(), invalid=pl.col("bad").sum())
            .with_columns(share=(100 * pl.col("invalid") / pl.col("rows")).round(3))
            .with_columns(passed=pl.col("share") <= MAX_SHARE)
            .sort("producer", "month").collect(engine="streaming"))
    # END SOLUTION


# %%
try:
    gates = gate_table()
except NotImplementedError:
    gates = pl.DataFrame(U.reference("lab_2_4")["gates"])
blocked = gates.filter(~pl.col("passed"))
print(f"{gates.height} partitions, {blocked.height} blocked")
print(blocked)
U.check(gates.height == 36, "36 partitions gated one by one")
U.check(blocked.select("producer", "month").rows() == [("RWD", "2025-09")], "one partition fails: Rawdah, September")

# %% [markdown]
# ## 2 · Quarantine and publish the rest (5')
#
# A gate per partition means one bad delivery stops alone: the other 35 partitions are published,
# Rawdah's September waits in quarantine until Rawdah sends it again. The study's figure is
# rebuilt from what was published, and says what is missing.

# %%
passed = gates.filter(pl.col("passed")).select("producer", "month")
published = LABS.join(passed.lazy(), on=["producer", "month"])
today = (published.filter(pl.col("test_code") == "CREAT").group_by("month")
         .agg(median_creat=pl.col("value").median(), producers=pl.col("producer").n_unique()).sort("month").collect())
U.save_json(blocked.to_dicts(), WORK / "quarantine.json")
print(today.filter(pl.col("month").is_in(["2025-08", "2025-09", "2025-10"])))
U.check(today.filter(pl.col("month") == "2025-09")["producers"].item() == 2, "September is published from two producers and says so")

# %% [markdown]
# ## 3 · Emit OpenLineage run events (6')
#
# OpenLineage describes a run with events: `START`, then `COMPLETE` or `FAIL`, each naming the job,
# the run and its input and output datasets. A lineage backend (Marquez, or the orchestrator's own)
# stitches them into a graph. Here they go to a file.
#
# ✏️ **Exercise** · `gate_events(gates)`: for each partition a START event, then COMPLETE with the
# curated partition as output when it passed, or FAIL with the quarantine partition as output when
# it did not. Use `U.ol_event`, `U.run_id("gate", producer, month)` and `part(...)`.

# %%
def gate_events(gates: pl.DataFrame) -> list[dict]:
    # BEGIN SOLUTION
    ev = []
    for g in gates.iter_rows(named=True):
        p, m = g["producer"], g["month"]
        rid = U.run_id("gate", p, m)
        facets = {"gate": {"invalid": g["invalid"], "rows": g["rows"], "share_percent": g["share"]}}
        ev.append(U.ol_event("START", "rimah.labs_gate", rid, [part(p, m)], []))
        out = part(p, m, "curated" if g["passed"] else "quarantine")
        ev.append(U.ol_event("COMPLETE" if g["passed"] else "FAIL", "rimah.labs_gate", rid, [part(p, m)], [out], run_facets=facets))
    return ev
    # END SOLUTION


# %%
try:
    events = gate_events(gates)
except NotImplementedError:
    events = []
path = U.write_events(events, WORK / "today.jsonl")
kinds = {}
for e in events:
    kinds[e["eventType"]] = kinds.get(e["eventType"], 0) + 1
print(kinds, "written to", path.name)
print(next((e for e in events if e["eventType"] == "FAIL"), "no FAIL event"))
if events:
    U.check(kinds.get("FAIL") == 1 and kinds.get("START") == 36, "36 runs, one of them failed")

# %% [markdown]
# ## 4 · Trace the defect back through the events (7')
#
# Start from yesterday's figure, `analysis/monthly_creatinine`, and walk the events backwards:
# which runs wrote it, what did they read, and what wrote those? ✏️ **Exercise** · `upstream(events,
# dataset)`: every dataset that `dataset` depends on, directly or through other runs (only
# COMPLETE events produced outputs). Then keep the September raw partitions and look at their data.

# %%
def upstream(events: list[dict], dataset: str) -> set[str]:
    # BEGIN SOLUTION
    writers = {}
    for e in events:
        if e["eventType"] == "COMPLETE":
            for o in e["outputs"]:
                writers.setdefault(o["name"], []).append([i["name"] for i in e["inputs"]])
    seen, todo = set(), [dataset]
    while todo:
        d = todo.pop()
        for inputs in writers.get(d, []):
            for i in inputs:
                if i not in seen:
                    seen.add(i)
                    todo.append(i)
    return seen
    # END SOLUTION


# %%
yesterday = U.read_events(yesterday_events())
try:
    deps = upstream(yesterday, "analysis/monthly_creatinine")
except NotImplementedError:
    deps = {part(p, m, z) for p in ["SDR", "UFQ", "RWD"] for m in U.months() for z in ("raw", "curated")}
suspects = sorted(d for d in deps if d.startswith("raw/") and d.endswith("month=2025-09"))
print(len(deps), "upstream datasets;", "September raw partitions:", suspects)
medians = {s: LABS.filter(pl.col("producer") == s.split("producer=")[1].split("/")[0], pl.col("month") == "2025-09",
                          pl.col("test_code") == "CREAT").select(pl.col("value").median()).collect().item() for s in suspects}
for s, v in medians.items():
    print(f"{s}: median creatinine {v:.2f}")
traced = min(medians, key=medians.get)
print("the defect comes from:", traced)
U.check(traced == part("RWD", "2025-09"), "traced to Rawdah's September partition: the one the gate quarantined")

# %% [markdown]
# 🔍 A median of about 1 is creatinine in mg/dL under a label that still says µmol/L: the unit flip
# of Day 1, delivered by a partition this time. Who acts now? Rawdah re-sends September in µmol/L;
# the gate publishes it; the figure is rebuilt and its record names the new version.

# %% [markdown]
# ## ✱ Stretch · A gate on the distribution
#
# A unit flip in a test whose range is wide (or a flip by a factor of 2) can pass a range rule.
# Compare each partition's median with the same producer's median over the other months, and
# block a partition whose median moved by more than half.

# %%
def drift_gate(test: str = "CREAT") -> pl.DataFrame:
    # BEGIN SOLUTION
    med = (LABS.filter(pl.col("test_code") == test).group_by("producer", "month")
           .agg(median=pl.col("value").median()).collect())
    ref = med.group_by("producer").agg(ref=pl.col("median").median())
    return (med.join(ref, on="producer").with_columns(ratio=(pl.col("median") / pl.col("ref")).round(3))
            .filter((pl.col("ratio") < 0.5) | (pl.col("ratio") > 1.5)).sort("producer", "month"))
    # END SOLUTION


try:
    print(drift_gate())
except NotImplementedError:
    print("Stretch not attempted.")
traced = {"dataset": traced, "medians": medians}

# %% [markdown]
# ## Checkpoint
#
# 1. One partition fails its gate. Why not stop the whole load?
# 2. Which events would you need to answer "which releases used Rawdah's bad September?"
# 3. A gate on value ranges passed, yet the figure moved. What gate is missing?
#
# <details><summary>Answers</summary>
#
# 1. The other partitions are good and the study needs them; the figure is published with a note of what is missing, and the bad partition waits for a corrected delivery.
# 2. The downstream direction of the same graph: every run whose inputs include that partition, and every output they wrote, up to the releases.
# 3. A distribution gate (the stretch): a change of scale inside the plausible range passes value rules.
# </details>
#
# **Carry forward.** `artifacts/D2_4/today.jsonl` and `quarantine.json`.
