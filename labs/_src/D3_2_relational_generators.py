# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "numpy>=2.0", "scikit-learn>=1.5", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 3.2 · Two generators for related tables
#
# Day 3 · Session 2 (Generating related tables) · 25 min.
#
# Fit two generators to the patient and encounter tables, an independent baseline and conditional trees that keep the parent-child relation, and check what each kept.
#
# **Reference state.** `data/study/patients_train.parquet` (one row per patient) and
# `encounters_train.parquet` (one row per hospital stay, `study_id` points to the patient). The
# holdout patients are never shown to a generator: Labs 3.3 and 3.4 need them untouched. If an
# exercise is not finished, the next cells use the reference synthetic files
# `data/study/synthetic/{independent,trees}_*.parquet`, made by the same methods.
#
# **Tasks**
# - [ ] 1 · The relation: encounters per patient (4')
# - [ ] 2 · Baseline: each column on its own (5')
# - [ ] 3 · Conditional trees: parents with their child counts (7')
# - [ ] 4 · Children conditioned on their parent (6')
# - [ ] 5 · Integrity and relation checks (3')
# - [ ] ✱ Stretch · Fit SDV's HMASynthesizer to the same tables in Colab

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
from sklearn.tree import DecisionTreeRegressor
import rimah as U

WORK = U.lab_dir("D3_2")
SEED = 405
patients, encounters = U.study("train")
PARENT, CHILD = U.PARENT, U.CHILD
print(patients.columns)
print(encounters.columns)

# %% [markdown]
# ## 1 · The relation: encounters per patient (4')
#
# The parent table (patients) and the child table (encounters) are linked by `study_id`. The
# number of children per parent is itself information: patients with heart failure come back
# more often. Generating the two tables separately, then giving each encounter a random patient,
# keeps neither the counts nor who comes back.

# %%
def child_counts(p: pl.DataFrame, e: pl.DataFrame) -> pl.DataFrame:
    n = e.group_by("study_id").agg(pl.len().cast(pl.Int64).alias("n_enc"))
    return p.join(n, on="study_id", how="left").with_columns(pl.col("n_enc").fill_null(0))


real_counts = child_counts(patients, encounters)
print(real_counts.group_by("heart_failure").agg(patients=pl.len(), mean_encounters=pl.col("n_enc").mean().round(2)).sort("heart_failure"))
rng = np.random.default_rng(SEED)
random_parent = encounters.with_columns(pl.Series("study_id", rng.choice(patients["study_id"].to_numpy(), encounters.height)))
naive = child_counts(patients, random_parent)
print(naive.group_by("heart_failure").agg(mean_encounters=pl.col("n_enc").mean().round(2)).sort("heart_failure"))
print("patients with no encounter: real", (real_counts["n_enc"] == 0).sum(), "| random parent", (naive["n_enc"] == 0).sum())

# %% [markdown]
# ## 2 · Baseline: each column on its own (5')
#
# The simplest generator draws every column from its own distribution: realistic columns, no
# relationships. It is the floor every better generator must beat.
#
# ✏️ **Exercise** · `independent(p, e, seed)`: draw each parent column and `n_enc` from the real
# values (`rng.choice`), give the patients new identifiers `S000001`, ..., repeat each identifier
# `n_enc` times for the encounters, and draw each child column on its own. Return
# `finish(sp, se)`, which numbers the encounters of each patient by month.

# %%
def new_ids(n: int) -> pl.Series:
    return pl.Series("study_id", [f"S{i:06d}" for i in range(1, n + 1)])


def finish(sp: pl.DataFrame, se: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    se = (se.sort("study_id", "admit_month", maintain_order=True)
          .with_columns(pl.int_range(1, pl.len() + 1).over("study_id").cast(pl.Int64).alias("enc_seq"))
          .select(["study_id", "enc_seq"] + CHILD))
    return sp.select(["study_id"] + PARENT), se


def independent(p: pl.DataFrame, e: pl.DataFrame, seed: int = SEED) -> tuple[pl.DataFrame, pl.DataFrame]:
    # BEGIN SOLUTION
    rng = np.random.default_rng(seed)
    pc = child_counts(p, e)
    sp = pl.DataFrame([pl.Series(c, rng.choice(pc[c].to_numpy(), pc.height)) for c in PARENT + ["n_enc"]])
    sp = sp.with_columns(new_ids(pc.height))
    ids = np.repeat(sp["study_id"].to_numpy(), sp["n_enc"].to_numpy())
    se = pl.DataFrame([pl.Series("study_id", ids)] + [pl.Series(c, rng.choice(e[c].to_numpy(), len(ids))) for c in CHILD])
    return finish(sp, se)
    # END SOLUTION


# %%
try:
    ind_p, ind_e = independent(patients, encounters)
except NotImplementedError:
    ind_p, ind_e = U.synthetic("independent")
    print("Exercise not done: using the reference file.")
print(f"independent: {ind_p.height} patients, {ind_e.height} encounters")

# %% [markdown]
# ## 3 · Conditional trees: parents with their child counts (7')
#
# Conditional trees (the CART method of synthpop) draw the columns one after another. For column
# *k*, fit a decision tree that predicts it from the columns before it on the real rows; drop
# each synthetic row into the same tree; give it the value of a random **real** row of the same
# leaf. A leaf holds at least 25 real rows, so no value comes from fewer than 25 people's context.
# The parent table is drawn this way with `n_enc` as its **last** column: the child count then
# depends on the patient's conditions.
#
# ✏️ **Exercise** · `draw_column(values, y_real, X_real, X_syn, rng)`: fit
# `DecisionTreeRegressor(min_samples_leaf=25)` on `(X_real, y_real)`, find the leaf of every real
# row and every synthetic row with `.apply`, and for each synthetic row pick one of `values` from a
# random real row of its leaf. Hint: sort the real rows by leaf, then `np.searchsorted` gives each
# leaf's start and end.

# %%
LEAF = 25


def draw_column(values: np.ndarray, y_real: np.ndarray, X_real: np.ndarray, X_syn: np.ndarray, rng) -> np.ndarray:
    # BEGIN SOLUTION
    tree = DecisionTreeRegressor(min_samples_leaf=LEAF, random_state=int(rng.integers(1 << 30))).fit(X_real, y_real)
    leaf_r, leaf_s = tree.apply(X_real), tree.apply(X_syn)
    order = np.argsort(leaf_r, kind="stable")
    lo = np.searchsorted(leaf_r[order], leaf_s, "left")
    hi = np.searchsorted(leaf_r[order], leaf_s, "right")
    return values[order[lo + (rng.random(len(X_syn)) * (hi - lo)).astype(int)]]
    # END SOLUTION


def draw_columns(real: pl.DataFrame, columns: list[str], rng, ctx_real=None, ctx_syn=None, n=None) -> pl.DataFrame:
    """Column after column; without context, the first column comes from its marginal."""
    n = ctx_syn.height if ctx_syn is not None else n
    Xr = [U.codes(ctx_real[c]).to_numpy() for c in ctx_real.columns] if ctx_real is not None else []
    Xs = [U.codes(ctx_syn[c], ctx_real[c]).to_numpy() for c in ctx_syn.columns] if ctx_syn is not None else []
    out = {}
    for col in columns:
        values = real[col].to_numpy()
        if Xr:
            out[col] = draw_column(values, U.codes(real[col]).to_numpy(), np.column_stack(Xr), np.column_stack(Xs), rng)
        else:
            out[col] = rng.choice(values, n)
        Xr.append(U.codes(real[col]).to_numpy())
        Xs.append(U.codes(pl.Series(col, out[col]), real[col]).to_numpy())
    return pl.DataFrame(out)


# %%
rng = np.random.default_rng(SEED)
pc = child_counts(patients, encounters)
try:
    tree_p = draw_columns(pc, PARENT + ["n_enc"], rng, n=pc.height).with_columns(new_ids(pc.height))
except NotImplementedError:
    ref_p, ref_e = U.synthetic("trees")
    tree_p = child_counts(ref_p, ref_e)
    print("Exercise not done: using the reference file.")
print(tree_p.group_by("heart_failure").agg(patients=pl.len(), mean_encounters=pl.col("n_enc").mean().round(2)).sort("heart_failure"))

# %% [markdown]
# ## 4 · Children conditioned on their parent (6')
#
# Each synthetic patient now has a number of encounters. The encounters are drawn with the same
# trees, but every tree also sees the **parent's** columns and the encounter's place in the
# history (`enc_seq`): the second stay of a heart-failure patient is drawn from real second stays
# of similar patients.
#
# ✏️ **Exercise** · `child_context(sp)`: one row per synthetic encounter, the parent's columns
# repeated `n_enc` times, plus `enc_seq` = 1, 2, ..., `n_enc` within each patient. (The real
# context is built for you the same way from the join.)

# %%
def child_context(sp: pl.DataFrame) -> pl.DataFrame:
    # BEGIN SOLUTION
    counts = sp["n_enc"].to_numpy()
    ctx = pl.DataFrame({c: np.repeat(sp[c].to_numpy(), counts) for c in PARENT + ["n_enc"]})
    return ctx.with_columns(pl.Series("enc_seq", np.concatenate([np.arange(1, k + 1) for k in counts])))
    # END SOLUTION


# %%
joined = encounters.join(pc, on="study_id")
ctx_real = joined.select(PARENT + ["n_enc", "enc_seq"])
try:
    ctx_syn = child_context(tree_p)
    sc = draw_columns(joined, CHILD, rng, ctx_real, ctx_syn)
    ids = np.repeat(tree_p["study_id"].to_numpy(), tree_p["n_enc"].to_numpy())
    tree_p, tree_e = finish(tree_p, pl.concat([pl.DataFrame({"study_id": ids}), sc], how="horizontal"))
except NotImplementedError:
    tree_p, tree_e = U.synthetic("trees")
    print("Exercise not done (here or in step 3): using the reference file.")
print(f"trees: {tree_p.height} patients, {tree_e.height} encounters")
tree_p.write_parquet(WORK / "trees_patients.parquet")
tree_e.write_parquet(WORK / "trees_encounters.parquet")

# %% [markdown]
# ## 5 · Integrity and relation checks (3')
#
# Before anyone measures utility: every encounter points to a patient, each patient's encounters
# are numbered 1..n, and the relations that the study depends on are there.

# %%
def integrity(p: pl.DataFrame, e: pl.DataFrame) -> dict:
    orphans = e.join(p, on="study_id", how="anti").height
    seq_ok = e.group_by("study_id").agg((pl.col("enc_seq").sort() == pl.int_range(1, pl.len() + 1)).all().alias("ok"))["ok"].all()
    j = e.join(p, on="study_id")
    hf = j.group_by("heart_failure").agg(pl.col("readmit_30d").mean()).sort("heart_failure")["readmit_30d"].to_list()
    rep = j.group_by(pl.col("enc_seq") > 1).agg(pl.col("readmit_30d").mean()).sort("enc_seq")["readmit_30d"].to_list()
    return {"orphans": orphans, "enc_seq_ok": bool(seq_ok),
            "enc_per_patient_hf": round(child_counts(p, e).filter(pl.col("heart_failure") == 1)["n_enc"].mean(), 2),
            "readmit_hf_vs_not": round(hf[1] / hf[0], 2), "readmit_repeat_vs_first": round(rep[1] / rep[0], 2),
            "corr_ckd_creatinine": round(j.select(pl.corr("ckd", "creatinine")).item(), 2)}


checks = pl.DataFrame([{"data": n, **integrity(p, e)} for n, (p, e) in
                       {"real": (patients, encounters), "independent": (ind_p, ind_e), "trees": (tree_p, tree_e)}.items()])
U.show(checks)
row = {r["data"]: r for r in checks.to_dicts()}
U.check(row["trees"]["orphans"] == 0 and row["trees"]["enc_seq_ok"], "trees: every encounter has its patient, numbered 1..n")
U.check(abs(row["trees"]["readmit_hf_vs_not"] - row["real"]["readmit_hf_vs_not"]) < 0.5, "trees keep the heart-failure effect on readmission")
U.check(abs(row["independent"]["readmit_hf_vs_not"] - 1) < abs(row["real"]["readmit_hf_vs_not"] - 1) / 2, "the baseline loses it")

# %% [markdown]
# 🔍 Matching columns and integrity say nothing yet about whether an analysis on the synthetic
# file gives the analyst's answer (Lab 3.3), or whether it gives away the patients it learnt
# from (Lab 3.4).

# %% [markdown]
# ## ✱ Stretch · Fit SDV's HMASynthesizer to the same tables in Colab
#
# The Synthetic Data Vault's hierarchical model learns the parent table with the child counts and
# child-table parameters, then samples both. It installs a large stack, so run it in Colab only.
# Compare its `integrity()` row with the two above.

# %%
if IN_COLAB:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "sdv"], check=True)
    from sdv.metadata import Metadata
    from sdv.multi_table import HMASynthesizer
    data = {"patients": patients.to_pandas(), "encounters": encounters.to_pandas()}
    metadata = Metadata.detect_from_dataframes(data)
    hma = HMASynthesizer(metadata)
    hma.fit(data)
    out = hma.sample(scale=1.0)
    hp, he = pl.from_pandas(out["patients"]), pl.from_pandas(out["encounters"])
    print(integrity(hp, he))
else:
    print("Stretch runs in Colab: it installs SDV and its dependencies.")

# %% [markdown]
# ## Checkpoint
#
# 1. Why draw `n_enc` as a column of the patient table rather than separately?
# 2. What does the leaf size of 25 protect, and what does it cost?
# 3. The trees keep the heart-failure effect. Why is that not yet evidence that the file is useful?
#
# <details><summary>Answers</summary>
#
# 1. The number of stays depends on the patient's conditions; drawn with them, sicker synthetic patients come back more often, as real ones do.
# 2. No value is drawn from a context shared by fewer than 25 real rows, which limits copying of rare people; larger leaves blur relationships the analysis needs.
# 3. A handful of ratios is not the analysis: the study's model and estimates must be checked on real holdout data (Lab 3.3).
# </details>
#
# **Carry forward.** `artifacts/D3_2/trees_*.parquet` are yours; Labs 3.3 and 3.4 start from the reference files so that everyone compares the same data.
