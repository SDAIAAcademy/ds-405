# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 3.1 · Four requests, three options
#
# Day 3 · Session 1 (When synthetic data fits) · 25 min.
#
# For four data requests, decide between synthetic data, a de-identified extract and a query service, with the evidence for each decision measured on the study tables.
#
# **Reference state.** The pseudonymised study tables `data/study/patients_train.parquet` and
# `encounters_train.parquet` (4,151 patients, about 9,150 encounters), and a reference synthetic
# pair made from them by conditional trees, `data/study/synthetic/trees_*.parquet` (you build
# your own in Lab 3.2). Everything is written under `artifacts/D3_1/`.
#
# **Tasks**
# - [ ] 1 · Read the four requests and what each needs (4')
# - [ ] 2 · What a synthetic file gets wrong: rare cells (7')
# - [ ] 3 · What an extract leaks: unique records (6')
# - [ ] 4 · The decision table with residual risk (8')
# - [ ] ✱ Stretch · Price each option in staff days and compute

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

WORK = U.lab_dir("D3_1")
patients, encounters = U.study("train")
syn_p, syn_e = U.synthetic("trees")
print(f"real: {patients.height} patients, {encounters.height} encounters | synthetic: {syn_p.height}, {syn_e.height}")

# %% [markdown]
# ## 1 · Read the four requests and what each needs (4')
#
# Four requests reached Dr. Fadwa Al-Qassabi's release board this month. For each, note what the
# requester must get **exactly right** and how bad a wrong number would be.

# %%
REQUESTS = pl.DataFrame([
    {"id": "Q1", "from": "Prof. Adnan Al-Shuwaiman (university)", "wants": "patient-level rows to develop a readmission model",
     "must_be_exact": "relationships between risk factors and readmission"},
    {"id": "Q2", "from": "Atiyah Al-Maghlouth (consortium epidemiologist)", "wants": "renal readmissions by region and month for the ministry",
     "must_be_exact": "every count, including small ones"},
    {"id": "Q3", "from": "a public data challenge for students", "wants": "a teaching file anyone can download",
     "must_be_exact": "realistic structure; no real person in it"},
    {"id": "Q4", "from": "a pharmacovigilance team", "wants": "the obstetric patients with chronic kidney disease, for case review",
     "must_be_exact": "the actual patients in a rare group"},
])
U.show(REQUESTS)

# %% [markdown]
# ## 2 · What a synthetic file gets wrong: rare cells (7')
#
# A generator learns the common patterns well and the rare ones badly: small cells disappear,
# and cells that never occurred appear. ✏️ **Exercise** · `cell_errors(real, syn, keys)`: count
# encounters per combination of `keys` in both files, join them (missing = 0), and return per
# **band** of the real count (`0`, `1-9`, `10-49`, `50+`): the number of cells, the mean absolute
# relative error, the cells lost (real > 0, synthetic 0) and the cells invented (real 0, synthetic > 0).

# %%
KEYS = ["region", "dx_group", "ckd"]


def band(n: pl.Expr) -> pl.Expr:
    return (pl.when(n == 0).then(pl.lit("0")).when(n < 10).then(pl.lit("1-9"))
            .when(n < 50).then(pl.lit("10-49")).otherwise(pl.lit("50+")))


def cell_errors(real: pl.DataFrame, syn: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
    # BEGIN SOLUTION
    r = real.group_by(keys).agg(pl.len().cast(pl.Int64).alias("real"))
    s = syn.group_by(keys).agg(pl.len().cast(pl.Int64).alias("synthetic"))
    c = r.join(s, on=keys, how="full", coalesce=True).fill_null(0)
    return (c.with_columns(band(pl.col("real")).alias("band"),
                           ((pl.col("synthetic") - pl.col("real")).abs() / pl.col("real").clip(1)).alias("rel_error"))
            .group_by("band").agg(cells=pl.len(), mean_rel_error=pl.col("rel_error").mean().round(3),
                                  lost=((pl.col("real") > 0) & (pl.col("synthetic") == 0)).sum(),
                                  invented=((pl.col("real") == 0) & (pl.col("synthetic") > 0)).sum())
            .sort("band"))
    # END SOLUTION


# %%
real_rows = encounters.join(patients, on="study_id")
syn_rows = syn_e.join(syn_p, on="study_id")
try:
    rare = cell_errors(real_rows, syn_rows, KEYS)
except NotImplementedError:
    rare = pl.DataFrame(U.reference("lab_3_1")["rare"])
U.show(rare)
small = rare.filter(pl.col("band") == "1-9").row(0, named=True)
large = rare.filter(pl.col("band") == "50+").row(0, named=True)
U.check(small["mean_rel_error"] > 3 * large["mean_rel_error"], "small cells are off far more than large ones")
U.check(rare["invented"].sum() + rare["lost"].sum() > 0, "some cells are lost or invented")
print(real_rows.filter(pl.col("dx_group") == "obstetric", pl.col("ckd") == 1).height, "real obstetric encounters with CKD;",
      syn_rows.filter(pl.col("dx_group") == "obstetric", pl.col("ckd") == 1).height, "synthetic")

# %% [markdown]
# 🔍 The synthetic count of a rare group is noise around a pattern, not a count: no use for Q2
# (every count exact) or Q4 (the actual patients).

# %% [markdown]
# ## 3 · What an extract leaks: unique records (6')
#
# A de-identified extract drops names and identifiers but keeps the attributes the analysis
# needs. Someone who knows a person's sex, year of birth and region (a colleague, a neighbour) can
# find that person if the combination is **unique**. ✏️ **Exercise** · `unique_share(df, qi)`: the
# share of patients whose combination of the quasi-identifiers `qi` occurs once.

# %%
def unique_share(df: pl.DataFrame, qi: list[str]) -> float:
    # BEGIN SOLUTION
    sizes = df.group_by(qi).agg(pl.len().alias("k"))
    return round(sizes.filter(pl.col("k") == 1).height / df.height, 4)
    # END SOLUTION


# %%
QI_SETS = {"sex, region": ["sex", "region"],
           "sex, birth year, region": ["sex", "birth_year", "region"],
           "+ nationality": ["sex", "birth_year", "region", "nationality"],
           "+ nationality, site": ["sex", "birth_year", "region", "nationality", "site"]}
try:
    uniq = {name: unique_share(patients, qi) for name, qi in QI_SETS.items()}
except NotImplementedError:
    uniq = U.reference("lab_3_1")["uniqueness"]
for name, share in uniq.items():
    print(f"{name:28} {share:6.1%} unique")
U.check(uniq["+ nationality, site"] > uniq["sex, birth year, region"], "each added attribute makes more patients unique")

# %% [markdown]
# 🔍 Patient attributes alone make a sizeable share unique; Day 4 adds the encounter history,
# which is far worse. An extract is personal data under a pseudonym: it needs a lawful basis,
# an agreement and controls, not just the removal of names.

# %% [markdown]
# ## 4 · The decision table with residual risk (8')
#
# ✏️ **Exercise** · Complete `decide()`: for each request the option (`synthetic`, `extract`,
# `query service`), the measured evidence from steps 2 and 3, and the risk that remains.

# %%
OPTIONS = {"synthetic", "extract", "query service"}


def decide() -> dict:
    """{request id: {"option", "evidence", "residual_risk"}}."""
    # BEGIN SOLUTION
    return {
        "Q1": {"option": "synthetic",
               "evidence": "a synthetic file to develop the model; the final model is fitted by the consortium on the real data (or by query service)",
               "residual_risk": "privacy is only claimed after the attacks of Lab 3.4; relationships it loses bias the model"},
        "Q2": {"option": "query service",
               "evidence": f"small synthetic cells are off by {small['mean_rel_error']:.0%} on average; the ministry needs exact counts",
               "residual_risk": "small published counts can identify people: suppress or add noise (Day 4)"},
        "Q3": {"option": "synthetic",
               "evidence": "teaching needs structure, not exact values; anyone will download it",
               "residual_risk": "must pass the attacks with margin, since the file is public forever"},
        "Q4": {"option": "extract",
               "evidence": f"the rare group is lost or invented in synthetic data; {uniq['+ nationality, site']:.0%} of patients are unique on five attributes",
               "residual_risk": "named-purpose agreement, minimum columns, access controls, no onward sharing"},
    }
    # END SOLUTION

# %%
try:
    decisions = decide()
except NotImplementedError:
    decisions = U.reference("lab_3_1")["decisions"]
U.check(set(decisions) == {"Q1", "Q2", "Q3", "Q4"}, "one decision per request")
U.check(all(d["option"] in OPTIONS and d["evidence"] and d["residual_risk"] for d in decisions.values()),
        "each has an option, evidence and a residual risk")
U.check(decisions["Q2"]["option"] == "query service", "exact small counts come from the real data")
U.check(decisions["Q4"]["option"] != "synthetic", "synthetic data cannot return the actual patients of a rare group")
table = pl.DataFrame([{"id": k, **v} for k, v in decisions.items()])
table.write_csv(WORK / "decisions.csv")
U.show(table.select("id", "option"))

# %% [markdown]
# ## ✱ Stretch · Price each option in staff days and compute
#
# Add a `cost` to each decision: staff days to set up (generator and attacks, agreement and
# controls, query service and its review) and recurring cost. Does the cheapest option change
# any decision?

# %%
COST = {"synthetic": {"setup_days": 8, "per_request_days": 1},   # trainer's estimate: replace with yours
        "extract": {"setup_days": 5, "per_request_days": 3},
        "query service": {"setup_days": 15, "per_request_days": 0.5}}
print(pl.DataFrame([{"id": k, "option": v["option"], **COST[v["option"]]} for k, v in decisions.items()]))

# %% [markdown]
# ## Checkpoint
#
# 1. The ministry wants the exact number of renal readmissions per region. Why not a synthetic file?
# 2. Why is a de-identified extract still personal data?
# 3. Which request is synthetic data best suited to, and what must happen before it goes out?
#
# <details><summary>Answers</summary>
#
# 1. Synthetic counts are draws from a model: cells under 10 are off by more than their own size on average (large cells by about 10%), and some appear or vanish.
# 2. Its records still describe real people, and a share of them are unique on a few attributes anyone may know.
# 3. The public teaching file (Q3): structure matters, not exact values. It goes out only after the attacks of Lab 3.4 pass.
# </details>
#
# **Carry forward.** `decisions.csv`; Lab 4.4 returns to Q1 with the evidence of Days 3 and 4.
