# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "numpy>=2.0", "opendp>=0.12", "matplotlib>=3.8", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 4.2 · Twelve months, one budget
#
# Day 4 · Session 2 (Privacy budgets over many releases) · 25 min.
#
# Allocate one privacy budget across twelve monthly readmission statistics with a ledger, plot error against budget, and show why a re-release must be charged.
#
# **Reference state.** All 6,000 study patients and their stays (`data/study/`, train and holdout
# together: the ministry's dashboard counts everyone). The statistic: the number of patients
# readmitted within 30 days after a stay that began in each month of 2025. The consortium's
# release board set one budget for the year: ε = 1. Noise comes from OpenDP, so your numbers
# differ from your neighbour's and from run to run; the checks use averages. Everything is
# written under `artifacts/D4_2/`.
#
# **Tasks**
# - [ ] 1 · The privacy unit and the contribution bound (5')
# - [ ] 2 · The ledger that refuses to overspend (6')
# - [ ] 3 · Twelve releases under two allocations (6')
# - [ ] 4 · Error against budget (5')
# - [ ] 5 · The averaging attack on free re-releases (3')
# - [ ] ✱ Stretch · The same releases with Gaussian noise under zero-concentrated accounting

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
import opendp.prelude as dp
import rimah as U

dp.enable_features("contrib")
WORK = U.lab_dir("D4_2")
TOTAL_EPSILON = 1.0
p_tr, e_tr = U.study("train")
p_ho, e_ho = U.study("holdout")
stays = pl.concat([e_tr, e_ho])
print(f"{stays.height} stays of {stays['study_id'].n_unique()} patients")

# %% [markdown]
# ## 1 · The privacy unit and the contribution bound (5')
#
# The **privacy unit** is a patient: a release must hide whether any one patient is in the data.
# Counting readmitted *stays* lets one patient move a month's count by as much as the number of
# their readmitted stays that month. Count readmitted *patients* instead and each patient moves
# each month's count by at most 1: the **contribution bound**, which sets the noise.
#
# ✏️ **Exercise** · `monthly_counts(e)`: per `admit_month`, the number of distinct patients with
# at least one readmitted stay. Also report the most readmitted stays one patient has in a month.

# %%
def monthly_counts(e: pl.DataFrame) -> pl.DataFrame:
    # BEGIN SOLUTION
    return (e.filter(pl.col("readmit_30d") == 1).group_by("admit_month")
            .agg(pl.col("study_id").n_unique().cast(pl.Int64).alias("patients")).sort("admit_month"))
    # END SOLUTION


# %%
worst = stays.filter(pl.col("readmit_30d") == 1).group_by("admit_month", "study_id").len()["len"].max()
try:
    true = monthly_counts(stays)
except NotImplementedError:
    true = pl.DataFrame(U.reference("lab_4_2")["true_monthly"])
true_monthly = true
print(f"one patient has up to {worst} readmitted stays in a month; counting patients bounds each to 1")
U.show(true, 12)
U.check(true.height == 12, "twelve monthly counts")
CONTRIBUTION = 1  # each patient changes each month's count by at most 1

# %% [markdown]
# ## 2 · The ledger that refuses to overspend (6')
#
# Every release spends part of the budget, and by sequential composition the spends **add up**.
# OpenDP computes what a measurement spends: `meas.map(d_in)` is its ε for a contribution `d_in`.
#
# ✏️ **Exercise** · `Ledger.charge(name, meas)`: compute the measurement's ε with
# `meas.map(CONTRIBUTION)`, refuse (raise `ValueError`) if it would take the total above the
# budget, otherwise record it and return the ε.

# %%
class Ledger:
    def __init__(self, total: float):
        self.total, self.entries = total, []

    @property
    def spent(self) -> float:
        return sum(e["epsilon"] for e in self.entries)

    def charge(self, name: str, meas) -> float:
        # BEGIN SOLUTION
        eps = float(meas.map(CONTRIBUTION))
        if self.spent + eps > self.total + 1e-9:
            raise ValueError(f"refused: {name} needs ε={eps:.4f}, {self.total - self.spent:.4f} left")
        self.entries.append({"release": name, "epsilon": eps})
        return eps
        # END SOLUTION


def laplace(scale: float):
    return dp.m.make_laplace(dp.atom_domain(T=int), dp.absolute_distance(T=int), scale=scale)


# %%
try:
    demo = Ledger(TOTAL_EPSILON)
    demo.charge("January", laplace(12.0))
except NotImplementedError:
    class Ledger(Ledger):  # safety net: the reference behaviour
        def charge(self, name, meas):
            eps = float(meas.map(CONTRIBUTION))
            if self.spent + eps > self.total + 1e-9:
                raise ValueError(f"refused: {name} needs ε={eps:.4f}, {self.total - self.spent:.4f} left")
            self.entries.append({"release": name, "epsilon": eps})
            return eps
    demo = Ledger(TOTAL_EPSILON)
    demo.charge("January", laplace(12.0))
print(f"Laplace noise of scale 12 on a count with bound 1 spends ε = {demo.spent:.4f}")
refused = False
try:
    demo.charge("everything at once", laplace(1.0))
except ValueError as err:
    refused = True
    print(err)
U.check(refused, "the ledger refuses a release that would overspend")

# %% [markdown]
# ## 3 · Twelve releases under two allocations (6')
#
# **A**: twelve monthly counts, ε = 1/12 each (Laplace scale 12). **B**: four quarterly counts,
# ε = 1/4 each (scale 4). Same total, different questions answered.

# %%
def release(ledger: Ledger, name: str, value: int, epsilon: float) -> int:
    meas = laplace(CONTRIBUTION / epsilon)
    ledger.charge(name, meas)
    return int(meas(int(value)))


ledger_a = Ledger(TOTAL_EPSILON)
monthly = true.with_columns(pl.Series("released", [release(ledger_a, m, v, TOTAL_EPSILON / 12)
                                                   for m, v in true.select("admit_month", "patients").rows()]))
quarters = (true.with_columns(("Q" + ((pl.col("admit_month").str.slice(5, 2).cast(pl.Int64) - 1) // 3 + 1).cast(pl.String)).alias("quarter"))
            .group_by("quarter").agg(pl.col("patients").sum()).sort("quarter"))
ledger_b = Ledger(TOTAL_EPSILON)
quarterly = quarters.with_columns(pl.Series("released", [release(ledger_b, q, v, TOTAL_EPSILON / 4) for q, v in quarters.rows()]))
U.show(monthly.with_columns((pl.col("released") - pl.col("patients")).alias("error")), 12)
U.show(quarterly.with_columns((pl.col("released") - pl.col("patients")).alias("error")))
print(f"A spent {ledger_a.spent:.3f}, B spent {ledger_b.spent:.3f}")
U.check(abs(ledger_a.spent - TOTAL_EPSILON) < 1e-6 and abs(ledger_b.spent - TOTAL_EPSILON) < 1e-6, "both allocations spend exactly the budget")
U.save_json({"A": ledger_a.entries, "B": ledger_b.entries}, WORK / "ledger.json")

# %% [markdown]
# 🔍 The expected absolute error of Laplace noise is its scale: 12 patients per month under A (about
# 7% of a month of about 170), 4 per quarter under B (under 1% of about 500). The board chooses
# which question deserves the budget; the ledger keeps the choice honest.

# %% [markdown]
# ## 4 · Error against budget (5')
#
# Repeat allocation A for yearly budgets from 0.1 to 4, 200 times each, and plot the mean absolute
# error of a monthly count against the budget.

# %%
budgets = [0.1, 0.25, 0.5, 1.0, 2.0, 4.0]
values = true["patients"].to_list()
mae = []
for eps in budgets:
    meas = laplace(CONTRIBUTION / (eps / 12))
    errs = [abs(meas(v) - v) for _ in range(200) for v in values]
    mae.append(float(np.mean(errs)))
curve = pl.DataFrame({"yearly_epsilon": budgets, "mae_monthly": [round(x, 1) for x in mae],
                      "expected": [round(12 / e, 1) for e in budgets]})
U.show(curve)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6, 3.6))
ax.plot(budgets, mae, marker="o", color="#0f766e")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("yearly budget ε (twelve monthly releases)"); ax.set_ylabel("mean absolute error, patients")
ax.set_title("Monthly readmitted patients: error against budget")
ax.grid(True, which="both", alpha=0.3)
fig.tight_layout(); fig.savefig(WORK / "error_budget.png", dpi=120)
U.check(all(abs(m - e) / e < 0.15 for m, e in zip(mae, curve["expected"])), "measured error matches scale = 12 / ε within 15%")

# %% [markdown]
# ## 5 · The averaging attack on free re-releases (3')
#
# A dashboard that recomputes January every night with fresh noise, without charging the ledger,
# hands out a new noisy copy each time. Average enough of them and the noise is gone.

# %%
jan = values[0]
meas = laplace(CONTRIBUTION / (TOTAL_EPSILON / 12))
copies = [meas(jan) for _ in range(365)]
for n in [1, 10, 100, 365]:
    print(f"average of {n:3d} free re-releases: {np.mean(copies[:n]):7.1f}   (true {jan})")
U.check(abs(np.mean(copies) - jan) < 3, "a year of nightly re-releases recovers January within 3 patients")
charged = Ledger(TOTAL_EPSILON)
n_ok = 0
try:
    for i in range(365):
        charged.charge(f"January, night {i + 1}", meas)
        n_ok += 1
except ValueError as err:
    print(f"charged to the ledger: {n_ok} nights, then {err}")
U.check(n_ok == 12, "charged, the budget allows twelve releases at ε = 1/12, and no more")

# %% [markdown]
# ## ✱ Stretch · Gaussian noise under zero-concentrated accounting
#
# zCDP composes more tightly over many releases. Release the twelve months with Gaussian noise
# of scale 10, add up ρ, and convert the total to (ε, δ) with δ = 10⁻⁶.

# %%
gauss = dp.m.make_gaussian(dp.atom_domain(T=int), dp.absolute_distance(T=int), scale=10.0)
rho = gauss.map(CONTRIBUTION)
total = dp.c.make_composition([gauss] * 12)
eps_delta = dp.c.make_fix_delta(dp.c.make_zCDP_to_approxDP(total), 1e-6).map(CONTRIBUTION)
print(f"one month ρ = {rho:.4f}; twelve months ρ = {total.map(CONTRIBUTION):.4f}; as (ε, δ): ({eps_delta[0]:.2f}, {eps_delta[1]:g})")

# %% [markdown]
# ## Checkpoint
#
# 1. Why count readmitted patients rather than readmitted stays?
# 2. The dashboard recomputes last month every night with new noise. What must happen?
# 3. The board wants monthly counts twice as accurate. What does it cost?
#
# <details><summary>Answers</summary>
#
# 1. A patient can have several readmitted stays in a month; counting patients bounds each one's effect to 1, which is what the noise is calibrated to.
# 2. Each recomputation is a release and is charged; or the first noisy value is stored and served again, which costs nothing.
# 3. Half the noise scale: twice the ε per month, so a yearly budget of 2, or fewer releases.
# </details>
#
# **Carry forward.** `ledger.json` and `error_budget.png` (the capstone's R-C request starts from them).
