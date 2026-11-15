"""Reference generators for Day 3: they write labs/data/study/synthetic/ for Labs 3.1, 3.3, 3.4 and 4.4.

Participants write their own versions in Lab 3.2; these are the same methods, used to give every
participant the same starting files. Three synthetic pairs (patients, encounters), each fitted on
the training patients only:

    independent   every column drawn on its own; child counts from their marginal
    trees         conditional trees (the CART method of synthpop): each parent column drawn from the
                  leaf of a tree fitted on the parent columns before it, the number of encounters
                  last; then each encounter column from a tree on its parent's columns, its place in
                  the history (enc_seq) and the encounter columns before it
    vendor        what an external vendor delivered: real training rows lightly perturbed (it leaks)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl
from sklearn.tree import DecisionTreeRegressor

SEED = 405
PARENT = ["sex", "birth_year", "region", "nationality", "diabetes", "ckd", "heart_failure", "prior_admissions", "site"]
CHILD = ["admit_month", "los_days", "ward", "dx_group", "n_meds", "creatinine", "glucose", "discharge", "readmit_30d"]
LEAF = 25  # smallest leaf: every drawn value is shared by at least 25 real rows of the same context


def codes(s: pl.Series) -> np.ndarray:
    """Numbers as they are; text as the position of its value in sorted order."""
    if s.dtype == pl.String:
        cats = sorted(s.unique().to_list())
        return s.replace_strict({c: i for i, c in enumerate(cats)}, return_dtype=pl.Float64).to_numpy()
    return s.cast(pl.Float64).to_numpy()


def child_counts(patients: pl.DataFrame, encounters: pl.DataFrame) -> pl.DataFrame:
    n = encounters.group_by("study_id").agg(pl.len().cast(pl.Int64).alias("n_enc"))
    return patients.join(n, on="study_id", how="left").with_columns(pl.col("n_enc").fill_null(0))


def _finish(sp: pl.DataFrame, se: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    se = (se.sort("study_id", "admit_month", maintain_order=True)
          .with_columns(pl.int_range(1, pl.len() + 1).over("study_id").cast(pl.Int64).alias("enc_seq"))
          .select(["study_id", "enc_seq"] + CHILD))
    return sp.select(["study_id"] + PARENT), se


def _ids(n: int) -> pl.Series:
    return pl.Series("study_id", [f"S{i:06d}" for i in range(1, n + 1)])


def independent(patients: pl.DataFrame, encounters: pl.DataFrame, seed: int = SEED) -> tuple[pl.DataFrame, pl.DataFrame]:
    rng = np.random.default_rng(seed)
    p = child_counts(patients, encounters)
    sp = pl.DataFrame([pl.Series(c, rng.choice(p[c].to_numpy(), p.height)) for c in PARENT + ["n_enc"]])
    sp = sp.with_columns(_ids(p.height))
    ids = np.repeat(sp["study_id"].to_numpy(), sp["n_enc"].to_numpy())
    se = pl.DataFrame([pl.Series("study_id", ids)] + [pl.Series(c, rng.choice(encounters[c].to_numpy(), len(ids))) for c in CHILD])
    return _finish(sp, se)


def draw_columns(real: pl.DataFrame, columns: list[str], rng, ctx_real: pl.DataFrame | None = None,
                 ctx_syn: pl.DataFrame | None = None, n: int | None = None, leaf: int = LEAF) -> pl.DataFrame:
    """Draw `columns` one after another. Column k: fit a tree on the context and the columns before k
    (real rows), drop each synthetic row into the tree, and copy the value of a random real row of the
    same leaf. Without context the first column is drawn from its marginal."""
    n = ctx_syn.height if ctx_syn is not None else n
    Xr = [codes(ctx_real[c]) for c in ctx_real.columns] if ctx_real is not None else []
    Xs = [codes(ctx_syn[c]) for c in ctx_syn.columns] if ctx_syn is not None else []
    out = {}
    for col in columns:
        values = real[col].to_numpy()
        if not Xr:
            out[col] = rng.choice(values, n)
        else:
            tree = DecisionTreeRegressor(min_samples_leaf=leaf, random_state=int(rng.integers(1 << 30)))
            tree.fit(np.column_stack(Xr), codes(real[col]))
            leaf_r, leaf_s = tree.apply(np.column_stack(Xr)), tree.apply(np.column_stack(Xs))
            order = np.argsort(leaf_r, kind="stable")
            lo = np.searchsorted(leaf_r[order], leaf_s, "left")
            hi = np.searchsorted(leaf_r[order], leaf_s, "right")
            out[col] = values[order[lo + (rng.random(n) * (hi - lo)).astype(int)]]
        Xr.append(codes(real[col]))
        Xs.append(codes(pl.Series(col, out[col])))
    return pl.DataFrame(out)


def trees(patients: pl.DataFrame, encounters: pl.DataFrame, seed: int = SEED) -> tuple[pl.DataFrame, pl.DataFrame]:
    rng = np.random.default_rng(seed)
    p = child_counts(patients, encounters)
    pcols = PARENT + ["n_enc"]
    sp = draw_columns(p, pcols, rng, n=p.height).with_columns(_ids(p.height))
    counts = sp["n_enc"].to_numpy()
    j = encounters.join(p, on="study_id")
    ctx_real = j.select(pcols + ["enc_seq"])
    ctx_syn = pl.DataFrame({c: np.repeat(sp[c].to_numpy(), counts) for c in pcols}).with_columns(
        pl.Series("enc_seq", np.concatenate([np.arange(1, k + 1) for k in counts])))
    sc = draw_columns(j, CHILD, rng, ctx_real, ctx_syn)
    se = pl.concat([pl.DataFrame({"study_id": np.repeat(sp["study_id"].to_numpy(), counts)}), sc], how="horizontal")
    return _finish(sp, se)


def vendor(patients: pl.DataFrame, encounters: pl.DataFrame, seed: int = SEED) -> tuple[pl.DataFrame, pl.DataFrame]:
    """A memorising 'generator': real rows with new identifiers and a little noise on two lab values."""
    rng = np.random.default_rng(seed + 7)
    ids = {s: f"V{i:06d}" for i, s in enumerate(patients["study_id"].to_list(), start=1)}
    sp = patients.with_columns(pl.col("study_id").replace_strict(ids))
    se = encounters.with_columns(
        pl.col("study_id").replace_strict(ids),
        (pl.col("creatinine") * pl.Series(1 + 0.01 * rng.standard_normal(encounters.height))).round(1),
        (pl.col("glucose") * pl.Series(1 + 0.01 * rng.standard_normal(encounters.height))).round(1))
    return sp.select(["study_id"] + PARENT), se.select(["study_id", "enc_seq"] + CHILD)


def write_reference_synthetic(data: Path):
    pts = pl.read_parquet(data / "study" / "patients_train.parquet")
    enc = pl.read_parquet(data / "study" / "encounters_train.parquet")
    out = data / "study" / "synthetic"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.parquet"):
        old.unlink()
    for name, fn in (("independent", independent), ("trees", trees), ("vendor", vendor)):
        sp, se = fn(pts, enc)
        sp.write_parquet(out / f"{name}_patients.parquet")
        se.write_parquet(out / f"{name}_encounters.parquet")
