# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 4.1 · Sequences as quasi-identifiers
#
# Day 4 · Session 1 (Disclosure risk in longitudinal records) · 25 min.
#
# Measure re-identification risk when encounter sequences act as quasi-identifiers and compare it with the single-table estimate, then coarsen and measure again.
#
# **Reference state.** The pseudonymised training tables in `data/study/` (4,151 patients,
# 9,156 stays). Imagine them as the extract the university asked for. Everything is written
# under `artifacts/D4_1/`.
#
# **Tasks**
# - [ ] 1 · The single-table estimate (5')
# - [ ] 2 · Sequences an adversary could know (7')
# - [ ] 3 · Risk by number of known encounters (5')
# - [ ] 4 · Coarsen and truncate, then measure again (6')
# - [ ] 5 · The risk table (2')
# - [ ] ✱ Stretch · Which patients stay unique after coarsening, and why

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

WORK = U.lab_dir("D4_1")
patients, encounters = U.study("train")
print(f"{patients.height} patients, {encounters.height} stays")

# %% [markdown]
# ## 1 · The single-table estimate (5')
#
# The usual risk estimate looks at one table: the share of patients whose combination of
# quasi-identifiers is unique. ✏️ **Exercise** · `unique_share(df, qi)` (as in Lab 3.1).

# %%
QI = ["sex", "birth_year", "region"]


def unique_share(df: pl.DataFrame, qi: list[str]) -> float:
    # BEGIN SOLUTION
    return round(df.group_by(qi).len().filter(pl.col("len") == 1).height / df.height, 3)
    # END SOLUTION


# %%
try:
    single = unique_share(patients, QI)
except NotImplementedError:
    single = U.reference("lab_4_1")["single"]
print(f"unique on {', '.join(QI)}: {single:.1%}")

# %% [markdown]
# ## 2 · Sequences an adversary could know (7')
#
# A colleague, a relative or an employer knows more than a year of birth: they know you were in
# hospital in March for your heart, and again in July. Each stay becomes a **token**: its month and
# diagnosis group. A patient is unique if no other patient with the same known facts has all the
# tokens the adversary knows.
#
# ✏️ **Exercise** · `unique_given(p, e, demo, k, token)`: for every patient with at least `k` stays,
# take the tokens of their first `k` stays as what the adversary knows, together with the columns
# `demo`; count the patients (including themselves) whose demographics match and whose stays
# contain all those tokens; return the share with exactly one match. Hint: join the known tokens
# to every patient's tokens on `demo + ["tok"]`, count distinct matched tokens per candidate.

# %%
MONTH_DX = pl.col("admit_month") + "|" + pl.col("dx_group")


def unique_given(p: pl.DataFrame, e: pl.DataFrame, demo: list[str], k: int, token: pl.Expr = MONTH_DX) -> float:
    # BEGIN SOLUTION
    t = e.join(p, on="study_id").with_columns(token.alias("tok")).select(["study_id", "enc_seq", "tok"] + demo)
    known = t.filter(pl.col("enc_seq") <= k)
    eligible = known.group_by("study_id").len().filter(pl.col("len") == k).select("study_id")
    known = known.join(eligible, on="study_id")
    need = known.group_by("study_id").agg(pl.col("tok").n_unique().alias("need"))
    cand = t.select(["study_id", "tok"] + demo).unique()
    hits = (known.join(cand, on=["tok"] + demo, suffix="_c")
            .group_by("study_id", "study_id_c").agg(pl.col("tok").n_unique().alias("got"))
            .join(need, on="study_id").filter(pl.col("got") == pl.col("need")))
    matches = hits.group_by("study_id").len()
    return round(matches.filter(pl.col("len") == 1).height / eligible.height, 3)
    # END SOLUTION


# %%
try:
    one_stay = unique_given(patients, encounters, ["sex", "birth_year"], 1)
except NotImplementedError:
    def unique_given(p, e, demo, k, token=MONTH_DX):
        return U.reference("lab_4_1")["by_known"][f"{'demo' if demo else 'stays'}_{k}"]
    unique_given.is_reference = True
    one_stay = unique_given(patients, encounters, ["sex", "birth_year"], 1)
print(f"sex, year of birth and one stay (month, diagnosis group): {one_stay:.1%} unique")
U.check(one_stay > 5 * single, "one known stay makes far more patients unique than the single-table estimate")

# %% [markdown]
# ## 3 · Risk by number of known encounters (5')
#
# Two adversaries: one knows only stays, the other also the sex and year of birth. Measure for one,
# two and three known stays (among patients with at least that many).

# %%
by_known = {}
for k in [1, 2, 3]:
    by_known[f"stays_{k}"] = unique_given(patients, encounters, [], k)
    by_known[f"demo_{k}"] = unique_given(patients, encounters, ["sex", "birth_year"], k)
eligible = {k: encounters.group_by("study_id").len().filter(pl.col("len") >= k).height for k in [1, 2, 3]}
U.show(pl.DataFrame([{"known stays": k, "patients with that many": eligible[k],
                      "stays only": by_known[f"stays_{k}"], "+ sex, year of birth": by_known[f"demo_{k}"]} for k in [1, 2, 3]]))
U.check(by_known["stays_3"] > 0.5, "three known stays alone single out most patients who have them")

# %% [markdown]
# 🔍 The single-table estimate says 4%. With what a relative knows, the same extract singles out
# nearly every patient who was admitted more than once. Longitudinal records are their own
# quasi-identifier.

# %% [markdown]
# ## 4 · Coarsen and truncate, then measure again (6')
#
# Two levers: **coarsen** (month to quarter, year of birth to decade) and **truncate** (release at
# most two stays per patient). Each has a cost to the study and an effect on risk: measure both.
#
# ✏️ **Exercise** · `coarsen(p, e)`: return `(p2, e2)` with `birth_year` floored to its decade
# and `admit_month` replaced by its quarter (`2025-Q1` ...). Then `truncate(e, n)` keeps the first
# `n` stays of each patient.

# %%
def coarsen(p: pl.DataFrame, e: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    # BEGIN SOLUTION
    p2 = p.with_columns((pl.col("birth_year") // 10 * 10).alias("birth_year"))
    q = (pl.col("admit_month").str.slice(5, 2).cast(pl.Int64) - 1) // 3 + 1
    e2 = e.with_columns((pl.col("admit_month").str.slice(0, 4) + "-Q" + q.cast(pl.String)).alias("admit_month"))
    return p2, e2
    # END SOLUTION


def truncate(e: pl.DataFrame, n: int) -> pl.DataFrame:
    # BEGIN SOLUTION
    return e.filter(pl.col("enc_seq") <= n)
    # END SOLUTION


# %%
try:
    if getattr(unique_given, "is_reference", False):
        raise NotImplementedError  # the reference cannot measure coarsened tables
    cp, ce = coarsen(patients, encounters)
    te = truncate(ce, 2)
    coarse = {"demo_1": unique_given(cp, ce, ["sex", "birth_year"], 1),
              "demo_2": unique_given(cp, ce, ["sex", "birth_year"], 2),
              "demo_3": unique_given(cp, ce, ["sex", "birth_year"], 3),
              "truncated_demo_2": unique_given(cp, te, ["sex", "birth_year"], 2),
              "stays_dropped": round(1 - te.height / encounters.height, 3)}
except NotImplementedError:
    coarse = U.reference("lab_4_1")["coarse"]
print(coarse)
U.check(coarse["demo_2"] < by_known["demo_2"] / 2, "coarsening more than halves the risk at two known stays")
U.check(coarse["demo_3"] > 0.5, "but three known stays still single out most of those patients")
U.check(coarse["truncated_demo_2"] > coarse["demo_2"], "truncation removes the crowd: two known stays now single out more patients")

# %% [markdown]
# 🔍 Truncation is neither free nor safe here. It drops a quarter of the stays, the repeat stays
# where readmissions happen, and it **raises** the risk at two known stays: other patients' later
# stays were the crowd a person hid in. Coarsening months to quarters costs the monthly trend.
# Measure every lever; do not assume its direction.

# %% [markdown]
# ## 5 · The risk table (2')

# %%
risk = pl.DataFrame([
    {"release": "patients only (sex, year of birth, region)", "adversary knows": "3 attributes", "unique": single},
    {"release": "patients and stays, as is", "adversary knows": "sex, year of birth, 1 stay", "unique": by_known["demo_1"]},
    {"release": "patients and stays, as is", "adversary knows": "sex, year of birth, 2 stays", "unique": by_known["demo_2"]},
    {"release": "coarsened (decade, quarter)", "adversary knows": "sex, decade, 2 stays", "unique": coarse["demo_2"]},
    {"release": "coarsened (decade, quarter)", "adversary knows": "sex, decade, 3 stays", "unique": coarse["demo_3"]},
    {"release": "coarsened, at most 2 stays", "adversary knows": "sex, decade, 2 stays", "unique": coarse["truncated_demo_2"]},
])
U.show(risk)
risk.write_csv(WORK / "risk.csv")
print(f"truncation drops {coarse['stays_dropped']:.0%} of the stays")

# %% [markdown]
# ## ✱ Stretch · Which patients stay unique after coarsening, and why
#
# List ten patients still unique on sex, decade and two coarsened stays. What do they have in
# common (age, diagnosis groups, region)? What would a further coarsening cost?

# %%
def still_unique(p, e, k=2):
    # BEGIN SOLUTION
    t = e.join(p, on="study_id").with_columns(MONTH_DX.alias("tok"))
    first = t.filter(pl.col("enc_seq") <= k).group_by("study_id").agg(pl.col("tok").sort().str.join(";").alias("seq"), pl.len().alias("n"))
    first = first.filter(pl.col("n") == k).join(p, on="study_id")
    sizes = first.group_by("sex", "birth_year", "seq").len()
    return first.join(sizes.filter(pl.col("len") == 1), on=["sex", "birth_year", "seq"]).select("study_id", "sex", "birth_year", "seq").head(10)
    # END SOLUTION


try:
    U.show(still_unique(*coarsen(patients, encounters)))
except NotImplementedError:
    print("Stretch not attempted.")

# %% [markdown]
# ## Checkpoint
#
# 1. The single-table uniqueness of the extract is 4%. Why is that the wrong number to report?
# 2. Truncating to two stays per patient: what did it cost, and what did it do to the risk?
# 3. What would you tell the university about releasing the stays as they are?
#
# <details><summary>Answers</summary>
#
# 1. An adversary who knows two stays of a person singles out almost every patient with two stays: the sequence is the quasi-identifier.
# 2. It dropped 24% of the stays, the repeat stays the study is about, and raised uniqueness at two known stays from 21% to 47%: fewer stays per patient means a thinner crowd.
# 3. Not as an extract: record-level histories are personal data with high risk; synthetic data or a query service fits better (Lab 4.4).
# </details>
#
# **Carry forward.** `risk.csv` (Lab 4.4 cites it).
