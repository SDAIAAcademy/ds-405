# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "numpy>=2.0", "scikit-learn>=1.5", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 3.3 · Train on synthetic, test on real
#
# Day 3 · Session 3 (Utility is measured against the analysis) · 25 min.
#
# Train the readmission model on each synthetic dataset, test it on real holdout data, and compare with fidelity scores and the study's own estimate.
#
# **Reference state.** The real training and holdout tables in `data/study/`, and three
# reference synthetic pairs fitted on the training patients: `independent`, `trees` and the
# `vendor` file an outside company delivered. The study (Atiyah Al-Maghlouth's) asks one
# question: by how much does heart failure raise the risk of readmission within 30 days, and
# which patients should get a follow-up call. Everything is written under `artifacts/D3_3/`.
#
# **Tasks**
# - [ ] 1 · Fidelity: marginals and correlations (6')
# - [ ] 2 · The real baseline: train real, test real (5')
# - [ ] 3 · Train synthetic, test real (7')
# - [ ] 4 · The study's own estimate on each dataset (4')
# - [ ] 5 · The utility report (3')
# - [ ] ✱ Stretch · Repeat with a gradient-boosted model and see whether the ranking changes

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

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import rimah as U

WORK = U.lab_dir("D3_3")
real = U.study("train")
holdout = U.study("holdout")
DATASETS = {"real": real, "independent": U.synthetic("independent"), "trees": U.synthetic("trees"), "vendor": U.synthetic("vendor")}
COLUMNS = U.PARENT + [c for c in U.CHILD]


def rows(p: pl.DataFrame, e: pl.DataFrame) -> pl.DataFrame:
    """One row per encounter with its patient's columns."""
    return e.join(p, on="study_id")


print({k: rows(*v).height for k, v in DATASETS.items()})

# %% [markdown]
# ## 1 · Fidelity: marginals and correlations (6')
#
# Fidelity compares distributions. For one column: the **Kolmogorov-Smirnov** statistic for
# numbers (largest gap between the two cumulative distributions) and the **total variation
# distance** for categories (half the sum of absolute differences of the shares). Both are 0 for
# identical distributions and 1 for disjoint ones.
#
# ✏️ **Exercise** · `marginal_distance(a, b)` for two Series of the same column.

# %%
def marginal_distance(a: pl.Series, b: pl.Series) -> float:
    # BEGIN SOLUTION
    if a.dtype == pl.String or a.n_unique() <= 12:
        pa = a.value_counts(normalize=True, name="pa")
        pb = b.value_counts(normalize=True, name="pb")
        j = pa.join(pb, on=a.name, how="full", coalesce=True).fill_null(0)
        return float(0.5 * (j["pa"] - j["pb"]).abs().sum())
    x, y = np.sort(a.to_numpy()), np.sort(b.to_numpy())
    grid = np.concatenate([x, y])
    cdf_x = np.searchsorted(x, grid, side="right") / len(x)
    cdf_y = np.searchsorted(y, grid, side="right") / len(y)
    return float(np.abs(cdf_x - cdf_y).max())
    # END SOLUTION


def pairwise_gap(r: pl.DataFrame, s: pl.DataFrame) -> float:
    """Mean absolute difference between the correlation matrices (columns coded as numbers)."""
    cr = np.corrcoef(np.column_stack([U.codes(r[c], r[c]).to_numpy() for c in COLUMNS]), rowvar=False)
    cs = np.corrcoef(np.column_stack([U.codes(s[c], r[c]).to_numpy() for c in COLUMNS]), rowvar=False)
    iu = np.triu_indices(len(COLUMNS), 1)
    return float(np.nanmean(np.abs(cr[iu] - cs[iu])))


# %%
r_rows = rows(*real)
fidelity = {}
for name in ["independent", "trees", "vendor"]:
    s_rows = rows(*DATASETS[name])
    try:
        marg = float(np.mean([marginal_distance(r_rows[c], s_rows[c]) for c in COLUMNS]))
    except NotImplementedError:
        marg = U.reference("lab_3_3")["fidelity"][name]["marginal"]
    fidelity[name] = {"marginal": round(marg, 3), "pairwise": round(pairwise_gap(r_rows, s_rows), 3)}
U.show(pl.DataFrame([{"data": k, **v} for k, v in fidelity.items()]))
U.check(fidelity["independent"]["marginal"] < 0.05, "the baseline's columns look right one by one")
U.check(fidelity["independent"]["pairwise"] > 2 * fidelity["trees"]["pairwise"], "but its correlations are gone")

# %% [markdown]
# 🔍 By marginals alone, the baseline is nearly perfect. Fidelity scores rank generators; they do
# not say whether the study's answer survives.

# %% [markdown]
# ## 2 · The real baseline: train real, test real (5')
#
# The study's model: logistic regression on the features of `U.model_rows` (heart failure, CKD,
# age, prior admissions, length of stay, medicines, discharge against advice, a repeat stay, and
# CKD times length of stay). Fit it on the real training patients and score it on the holdout:
# that AUC (TRTR) is the ceiling a synthetic file can reach.

# %%
def xy(p: pl.DataFrame, e: pl.DataFrame):
    m = U.model_rows(p, e)
    return m.select(U.FEATURES).to_numpy().astype(float), m["readmit_30d"].to_numpy()


X_hold, y_hold = xy(*holdout)


def fit(p, e):
    X, y = xy(p, e)
    return LogisticRegression(max_iter=3000).fit(X, y)


trtr = round(roc_auc_score(y_hold, fit(*real).predict_proba(X_hold)[:, 1]), 3)
print("TRTR AUC on the holdout:", trtr)

# %% [markdown]
# ## 3 · Train synthetic, test real (7')
#
# ✏️ **Exercise** · `tstr(p, e)`: fit the same model on a synthetic pair and return its AUC on the
# real holdout. Then compare each with TRTR.

# %%
def tstr(p: pl.DataFrame, e: pl.DataFrame) -> float:
    # BEGIN SOLUTION
    return round(roc_auc_score(y_hold, fit(p, e).predict_proba(X_hold)[:, 1]), 3)
    # END SOLUTION


# %%
try:
    tstr_scores = {name: tstr(*DATASETS[name]) for name in ["independent", "trees", "vendor"]}
except NotImplementedError:
    tstr_scores = U.reference("lab_3_3")["tstr"]
tstr_table = {"real (TRTR)": trtr, **tstr_scores}
for k, v in tstr_table.items():
    print(f"{k:12} AUC {v:.3f}   gap to TRTR {trtr - v:+.3f}")
U.check(trtr - tstr_scores["trees"] < 0.02, "trees: within 0.02 of the real model")
U.check(tstr_scores["independent"] < tstr_scores["trees"], "the baseline does worse")
tstr = tstr_table

# %% [markdown]
# 🔍 The baseline's AUC is above 0.5 even though its outcome is random: a model that adds up
# risk factors with any positive weights already ranks real patients somewhat. The gap, not the
# number, is the evidence. The vendor's file matches TRTR exactly: a warning, not a success.

# %% [markdown]
# ## 4 · The study's own estimate on each dataset (4')
#
# The study reports a **risk ratio**: the readmission rate after stays of heart-failure patients
# divided by the rate for the others, with a 95% interval. ✏️ **Exercise** · `risk_ratio(p, e)`:
# with a readmissions out of n stays among the exposed and c out of m among the others,
# RR = (a/n)/(c/m) and the interval is exp(ln RR ± 1.96·√(1/a − 1/n + 1/c − 1/m)).

# %%
def risk_ratio(p: pl.DataFrame, e: pl.DataFrame, exposure: str = "heart_failure") -> dict:
    # BEGIN SOLUTION
    g = rows(p, e).group_by(exposure).agg(k=pl.col("readmit_30d").sum(), n=pl.len())
    a, n = g.filter(pl.col(exposure) == 1).select("k", "n").row(0)
    c, m = g.filter(pl.col(exposure) == 0).select("k", "n").row(0)
    rr = (a / n) / (c / m)
    se = np.sqrt(1 / a - 1 / n + 1 / c - 1 / m)
    return {"rr": round(rr, 2), "lo": round(float(np.exp(np.log(rr) - 1.96 * se)), 2), "hi": round(float(np.exp(np.log(rr) + 1.96 * se)), 2)}
    # END SOLUTION


# %%
try:
    estimates = {name: risk_ratio(*d) for name, d in DATASETS.items()}
except NotImplementedError:
    estimates = U.reference("lab_3_3")["estimates"]
for k, v in estimates.items():
    inside = estimates["real"]["lo"] <= v["rr"] <= estimates["real"]["hi"]
    print(f"{k:12} RR {v['rr']:.2f}  [{v['lo']:.2f}, {v['hi']:.2f}]  {'inside' if inside else 'OUTSIDE'} the real interval")
U.check(estimates["real"]["lo"] <= estimates["trees"]["rr"] <= estimates["real"]["hi"], "trees: the estimate falls inside the real interval")
U.check(estimates["independent"]["rr"] < estimates["real"]["lo"], "the baseline shrinks it towards no effect")

# %% [markdown]
# ## 5 · The utility report (3')
#
# One table the release board can read, saved for Lab 4.4.

# %%
report = pl.DataFrame([{"data": n, "marginal_distance": fidelity.get(n, {}).get("marginal", 0.0),
                        "correlation_gap": fidelity.get(n, {}).get("pairwise", 0.0),
                        "auc_on_real_holdout": tstr_table["real (TRTR)" if n == "real" else n],
                        "risk_ratio": estimates[n]["rr"], "rr_interval": f"{estimates[n]['lo']}-{estimates[n]['hi']}"}
                       for n in DATASETS])
U.show(report)
report.write_csv(WORK / "utility.csv")

# %% [markdown]
# ## ✱ Stretch · A gradient-boosted model
#
# `sklearn.ensemble.HistGradientBoostingClassifier` finds interactions the logistic model is
# given by hand. Does the gap between trees and TRTR grow?

# %%
from sklearn.ensemble import HistGradientBoostingClassifier
for name in ["real", "trees"]:
    X, y = xy(*DATASETS[name])
    hgb = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.05, random_state=405).fit(X, y)
    print(name, "gradient boosting AUC on holdout:", round(roc_auc_score(y_hold, hgb.predict_proba(X_hold)[:, 1]), 3))

# %% [markdown]
# ## Checkpoint
#
# 1. The baseline scores nearly 0 on marginal distance. What does that tell you about its utility?
# 2. Why test on the real holdout rather than on the real training data?
# 3. The vendor's file matches the real model exactly. Good news?
#
# <details><summary>Answers</summary>
#
# 1. Nothing: each column matches, the relationships the study needs are gone (its risk ratio shrinks towards 1).
# 2. The generator learnt from the training patients; testing on them rewards copying. The holdout was never shown to any generator.
# 3. No: a file that reproduces the real data that closely may be copying it. Lab 3.4 checks.
# </details>
#
# **Carry forward.** `utility.csv` (Lab 4.4 cites it).
