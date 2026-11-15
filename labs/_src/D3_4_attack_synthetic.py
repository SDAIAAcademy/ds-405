# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "numpy>=2.0", "scikit-learn>=1.5", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 3.4 · Attack each synthetic table
#
# Day 3 · Session 4 (Privacy is measured by attack) · 25 min.
#
# Attack each synthetic table and the linked records with distance to closest record and membership inference against a holdout, including a vendor's file that leaks.
#
# **Reference state.** The real training patients (the generators' input), the holdout patients
# (never shown to a generator) and the three reference synthetic pairs in
# `data/study/synthetic/`. Ghanem Al-Mutawakkil, the data protection officer, will not sign a
# synthetic release on the word "synthetic": he wants the attack results per table. Everything is
# written under `artifacts/D3_4/`.
#
# **Tasks**
# - [ ] 1 · Distances on each table (6')
# - [ ] 2 · Distance to closest record, per table (6')
# - [ ] 3 · Membership inference: the attack's AUC (7')
# - [ ] 4 · The vendor's file (3')
# - [ ] 5 · The attack report and thresholds (3')
# - [ ] ✱ Stretch · Attack the linked histories: a patient with all their stays as one record

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
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import NearestNeighbors
import rimah as U

WORK = U.lab_dir("D3_4")
train_p, train_e = U.study("train")
hold_p, hold_e = U.study("holdout")
GENERATORS = ["independent", "trees", "vendor"]
SYN = {name: U.synthetic(name) for name in GENERATORS}
TABLE_COLUMNS = {"patients": U.PARENT, "encounters": [c for c in U.CHILD]}

# Members: as many training patients as there are holdout patients, so a fair coin scores 0.5.
members = train_p.sample(hold_p.height, seed=405)
print(f"members {members.height} (from {train_p.height} training patients), non-members {hold_p.height}")

# %% [markdown]
# ## 1 · Distances on each table (6')
#
# An attack needs a distance between records. Each column is coded as a number and scaled by its
# spread in the real training data (`U.scaled`), so a year of birth and a creatinine value weigh
# alike; the distance is Euclidean. Encounters are compared as encounters, patients as patients.
#
# ✏️ **Exercise** · `nearest(reference, query)`: for each row of `query` (a matrix), the distance
# to its closest row in `reference`. Use `NearestNeighbors(n_neighbors=1)`.

# %%
def nearest(reference: np.ndarray, query: np.ndarray) -> np.ndarray:
    # BEGIN SOLUTION
    return NearestNeighbors(n_neighbors=1).fit(reference).kneighbors(query)[0][:, 0]
    # END SOLUTION


def tables(p: pl.DataFrame, e: pl.DataFrame) -> dict:
    return {"patients": p, "encounters": e}


real_tables = {"members": tables(members, train_e.join(members.select("study_id"), on="study_id")),
               "non_members": tables(hold_p, hold_e)}


def matrix(df: pl.DataFrame, table: str) -> np.ndarray:
    like = train_p if table == "patients" else train_e
    return U.scaled(df, TABLE_COLUMNS[table], like)


try:
    d = nearest(matrix(SYN["trees"][0], "patients"), matrix(members, "patients"))
except NotImplementedError:
    def nearest(reference, query):
        return NearestNeighbors(n_neighbors=1).fit(reference).kneighbors(query)[0][:, 0]
    d = nearest(matrix(SYN["trees"][0], "patients"), matrix(members, "patients"))
print(f"trees, patients: median distance of a member to the closest synthetic patient {np.median(d):.2f};",
      f"{(d == 0).mean():.0%} have an exact twin")

# %% [markdown]
# 🔍 About a quarter of the members have an exact synthetic twin on nine coarse attributes, and
# about a fifth of the non-members, whom no generator saw, have one too: exact matches alone prove
# little. The comparison with the holdout does.

# %% [markdown]
# ## 2 · Distance to closest record, per table (6')
#
# For every synthetic record, is its closest real record a member (training) or a non-member
# (holdout)? If the generator did not copy, members and non-members come from the same
# population and the share is about 0.5 (ties count half). Well above 0.5: it remembers.
#
# ✏️ **Exercise** · `dcr_share(syn, table)`: distances from each synthetic record to the members'
# table and to the non-members' table, and the share closer to members.

# %%
def dcr_share(syn: pl.DataFrame, table: str) -> float:
    # BEGIN SOLUTION
    s = matrix(syn, table)
    d_mem = nearest(matrix(real_tables["members"][table], table), s)
    d_non = nearest(matrix(real_tables["non_members"][table], table), s)
    return round(float(np.mean((d_mem < d_non) + 0.5 * (d_mem == d_non))), 3)
    # END SOLUTION


# %%
try:
    dcr = {g: {t: dcr_share(tables(*SYN[g])[t], t) for t in TABLE_COLUMNS} for g in GENERATORS}
except NotImplementedError:
    dcr = U.reference("lab_3_4")["dcr"]
U.show(pl.DataFrame([{"generator": g, **v} for g, v in dcr.items()]))
U.check(dcr["independent"]["patients"] < 0.55, "the baseline does not lean towards members")

# %% [markdown]
# Encounters: members' encounters and non-members' encounters differ in number, so compare like
# with like. The table above uses all of each: read the encounter column as a ranking between
# generators, not as a calibrated 0.5.

# %% [markdown]
# ## 3 · Membership inference: the attack's AUC (7')
#
# The attacker holds a real record and asks: was this person in the training data? The score:
# the closer the record's nearest synthetic record, the more likely a member. The AUC over
# members and non-members measures the attack: 0.5 is guessing, 1.0 is certainty.
#
# ✏️ **Exercise** · `mia_auc(syn, table)`: score every member and non-member record by minus its
# distance to the closest synthetic record; return `roc_auc_score` with members labelled 1.

# %%
def mia_auc(syn: pl.DataFrame, table: str) -> float:
    # BEGIN SOLUTION
    s = matrix(syn, table)
    d_mem = nearest(s, matrix(real_tables["members"][table], table))
    d_non = nearest(s, matrix(real_tables["non_members"][table], table))
    labels = np.r_[np.ones(len(d_mem)), np.zeros(len(d_non))]
    return round(float(roc_auc_score(labels, -np.r_[d_mem, d_non])), 3)
    # END SOLUTION


# %%
try:
    mia = {g: {t: mia_auc(tables(*SYN[g])[t], t) for t in TABLE_COLUMNS} for g in GENERATORS}
except NotImplementedError:
    mia = U.reference("lab_3_4")["mia"]
U.show(pl.DataFrame([{"generator": g, **v} for g, v in mia.items()]))
U.check(mia["independent"]["patients"] < 0.55, "the baseline: the attack is close to guessing")
U.check(mia["trees"]["encounters"] < mia["vendor"]["encounters"], "trees leak less than the vendor's file")

# %% [markdown]
# ## 4 · The vendor's file (3')
#
# The vendor called its file "fully synthetic, privacy-safe". Look at its encounters next to the
# real ones.

# %%
vend_e = SYN["vendor"][1]
d_v = nearest(matrix(vend_e, "encounters"), matrix(train_e, "encounters"))
print(f"vendor encounters: {np.mean(d_v < 0.05):.0%} of real training encounters have a vendor record within 0.05")
print(f"vendor: DCR share {dcr['vendor']}, membership AUC {mia['vendor']}")
U.check(mia["vendor"]["encounters"] > 0.8, "the vendor's file gives its training patients away")

# %% [markdown]
# 🔍 New identifiers and 1% noise on two laboratory values: every real stay is still there.
# "Synthetic" names a process, not a property; the attack is the evidence.

# %% [markdown]
# ## 5 · The attack report and thresholds (3')
#
# The thresholds below are the consortium's (set by the release board before looking at
# results). A release passes only if every table passes.

# %%
THRESHOLDS = {"dcr_share_max": 0.55, "mia_auc_max": 0.60}
report = pl.DataFrame([{"generator": g, "table": t, "dcr_share": dcr[g][t], "mia_auc": mia[g][t],
                        "passes": dcr[g][t] <= THRESHOLDS["dcr_share_max"] and mia[g][t] <= THRESHOLDS["mia_auc_max"]}
                       for g in GENERATORS for t in TABLE_COLUMNS])
U.show(report)
report.write_csv(WORK / "attacks.csv")
verdict = report.group_by("generator").agg(pl.col("passes").all()).sort("generator")
print(verdict)
U.check(not verdict.filter(pl.col("generator") == "vendor")["passes"][0], "the vendor's file fails")

# %% [markdown]
# ## ✱ Stretch · Attack the linked histories
#
# A person is more than one stay. Build one record per patient: the patient columns, the number
# of stays, and the months and diagnosis groups of the first three stays. Repeat the membership
# attack on these records. Does the trees generator still pass?

# %%
def history(p: pl.DataFrame, e: pl.DataFrame) -> pl.DataFrame:
    # BEGIN SOLUTION
    first = (e.sort("study_id", "enc_seq").group_by("study_id", maintain_order=True)
             .agg(pl.len().alias("n_enc"), *[pl.col("admit_month").str.slice(5, 2).cast(pl.Int64).get(i, null_on_oob=True).fill_null(0).alias(f"m{i}") for i in range(3)],
                  *[pl.col("dx_group").get(i, null_on_oob=True).fill_null("none").alias(f"dx{i}") for i in range(3)]))
    return p.join(first, on="study_id")
    # END SOLUTION


try:
    H_COLS = U.PARENT + ["n_enc", "m0", "m1", "m2", "dx0", "dx1", "dx2"]
    h_train = history(train_p, train_e)
    h_mem, h_non = history(members, train_e), history(hold_p, hold_e)
    for g in GENERATORS:
        h_syn = history(*SYN[g])
        s = U.scaled(h_syn, H_COLS, h_train)
        dm, dn = nearest(s, U.scaled(h_mem, H_COLS, h_train)), nearest(s, U.scaled(h_non, H_COLS, h_train))
        print(g, "linked histories, membership AUC:",
              round(roc_auc_score(np.r_[np.ones(len(dm)), np.zeros(len(dn))], -np.r_[dm, dn]), 3))
except NotImplementedError:
    print("Stretch not attempted.")

# %% [markdown]
# ## Checkpoint
#
# 1. A quarter of the training patients have an exact twin in a synthetic file. Is that a leak?
# 2. Why must the attack be run per table, and on the linked records?
# 3. What would you ask the vendor for before accepting their next file?
#
# <details><summary>Answers</summary>
#
# 1. Not by itself: a fifth of the holdout patients have one too. The leak is the difference, members closer than non-members (an AUC of 0.55 for the trees' patient table).
# 2. A generator can be safe on patients and copy encounters; and a sequence of stays is more identifying than any single row.
# 3. The method, the holdout they kept, and their DCR and membership results per table; better still, the right to run your own.
# </details>
#
# **Carry forward.** `attacks.csv` (Lab 4.4 cites it; the capstone defence re-runs one attack).
