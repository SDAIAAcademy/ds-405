# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 1.3 · A keyed linkage identifier
#
# Day 1 · Session 3 (Linking patients across producers) · 25 min.
#
# The readmission study needs to know that the patient discharged by Sidra on Monday is the one
# Ufuq admitted on Friday. The national identifier links them, and it must not travel. You show
# why a plain hash of it is no protection, then compute a **keyed-hash** linkage identifier at each
# producer after normalising the identifiers, and measure the match rate, precision and recall
# against the planted truth.
#
# **Reference state.** `data/producers/*.csv` and `data/truth/person_map.csv` (which local patient
# is which synthetic person: only the course has this; a real linkage never does). Nothing from
# another lab.
#
# **Tasks**
# - [ ] 1 · Reverse a plain hash of an identifier (5')
# - [ ] 2 · Normalise identifiers at each producer (7')
# - [ ] 3 · Keyed hash with a key the consortium never holds (5')
# - [ ] 4 · Match rate, precision and recall against the truth (5')
# - [ ] 5 · Add a second key for typing errors (3')
# - [ ] ✱ Stretch · Count the false matches the second key adds and decide whether to keep it

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

import hashlib
import hmac
import itertools
import re
import time

import polars as pl
import rimah as U

# Who each local patient is at each producer: identifier, name, birth date and sex as each desk typed them.
SPEC = {"SDR": ("sidra_encounters.csv", "patient_id", "national_id", "full_name", "birth_date", "%Y-%m-%d", "sex", {"M": "M", "F": "F"}),
        "UFQ": ("ufuq_encounters.csv", "MRN", "NationalID", "PatientName", "DOB", "%d/%m/%Y", "Gender", {"Male": "M", "Female": "F"}),
        "RWD": ("rawdah_encounters.csv", "pt_id", "nid", "name", "dob", "%Y%m%d", "sex", {"1": "M", "2": "F"})}


def identities(p: str) -> pl.DataFrame:
    f, lid, nid, name, dob, fmt, sex, codes = SPEC[p]
    df = U.load("producers/" + f)
    return df.select(pl.lit(p).alias("producer"), pl.col(lid).alias("local_id"), pl.col(nid).alias("nid"),
                     pl.col(name).alias("name"), pl.col(dob).str.to_date(fmt).alias("birth_date"),
                     pl.col(sex).replace_strict(codes).alias("sex")).unique("local_id").sort("local_id")


IDS = {p: identities(p) for p in SPEC}
TRUTH = U.load("truth/person_map.csv")
print({p: df.height for p, df in IDS.items()}, "local patients;", TRUTH["person_id"].n_unique(), "persons")

# %% [markdown]
# ## 1 · Reverse a plain hash of an identifier (5')
#
# A colleague proposes sending `sha256(national_id)` instead of the identifier. Suppose an attacker
# has one such hash and knows the identifier's first four digits (they are not random: the first
# digit says citizen or resident). Then there are only a million candidates.
#
# ✏️ **Exercise** · Write `reverse(target, prefix)`: hash every ten-digit candidate that starts with
# `prefix` and return the one that matches. Time it.

# %%
victim = IDS["SDR"]["nid"][0]
TARGET = hashlib.sha256(victim.encode()).hexdigest()
PREFIX = victim[:U.pick(4, 5)]  # quick mode knows one more digit


def reverse(target: str, prefix: str) -> str | None:
    # BEGIN SOLUTION
    width = 10 - len(prefix)
    for i in range(10 ** width):
        cand = f"{prefix}{i:0{width}d}"
        if hashlib.sha256(cand.encode()).hexdigest() == target:
            return cand
    return None
    # END SOLUTION


# %%
t0 = time.perf_counter()
try:
    found = reverse(TARGET, PREFIX)
except NotImplementedError:
    found = victim
seconds = time.perf_counter() - t0
rate = int(victim[len(PREFIX):]) / max(seconds, 1e-9)
print(f"found {found} in {seconds:.2f} s, about {rate:,.0f} hashes a second on one core")
print(f"the whole space of 2 billion identifiers at that rate: {2e9 / rate / 3600:.1f} hours on one core")
U.check(found == victim, "a plain hash of an identifier is reversed by enumeration")

# %% [markdown]
# 🔍 The space is small and structured, so hashing is not pseudonymisation by itself. The SDAIA
# guideline on anonymisation and pseudonymisation treats pseudonymised data as personal data and asks
# that the extra information needed to re-identify is kept separately: here, that is the **key**.

# %% [markdown]
# ## 2 · Normalise identifiers at each producer (7')
#
# A keyed hash of `1012 345 678` and of `1012345678` are unrelated, so normalise **before** hashing,
# the same way at every producer. ✏️ **Exercise** · `norm_nid(s)`: Arabic-Indic digits to ASCII,
# then keep digits only; return `None` unless exactly ten digits remain. `norm_name(s)`: lower case,
# letters only (so `Al-Harbi`, `Al Harbi` and `ALHARBI` agree).

# %%
def norm_nid(s: str | None) -> str | None:
    # BEGIN SOLUTION
    if s is None:
        return None
    d = re.sub(r"[^0-9]", "", s.translate(U.ARABIC_INDIC))
    return d if len(d) == 10 else None
    # END SOLUTION


def norm_name(s: str | None) -> str | None:
    # BEGIN SOLUTION
    return None if s is None else re.sub(r"[^a-z]", "", s.lower())
    # END SOLUTION


# %%
SAMPLES = ["1012 345 678", "SA-1012345678", "١٠١٢٣٤٥٦٧٨", "1012345678", "101234567"]
try:
    NORM_SAMPLE = {s: norm_nid(s) for s in SAMPLES} | {"Al-Harbi": norm_name("Al-Harbi"), "AL HARBI": norm_name("AL HARBI")}
except NotImplementedError:
    NORM_SAMPLE = U.reference("lab_1_3")["norm"]
    norm_nid = lambda s: (lambda d: d if len(d) == 10 else None)(re.sub(r"[^0-9]", "", (s or "").translate(U.ARABIC_INDIC)))
    norm_name = lambda s: None if s is None else re.sub(r"[^a-z]", "", s.lower())
print(NORM_SAMPLE)
U.check(NORM_SAMPLE["1012 345 678"] == NORM_SAMPLE["SA-1012345678"] == NORM_SAMPLE["١٠١٢٣٤٥٦٧٨"] == "1012345678", "three formats, one identifier")
U.check(NORM_SAMPLE["101234567"] is None, "a nine-digit value is rejected, not padded")
U.check(NORM_SAMPLE["Al-Harbi"] == NORM_SAMPLE["AL HARBI"], "two spellings of a family name agree")

# %% [markdown]
# ## 3 · Keyed hash with a key the consortium never holds (5')
#
# HMAC-SHA-256 with a secret key turns the normalised identifier into a pseudonym that nobody
# without the key can recompute or enumerate. The key is generated by a linkage unit, given to the
# three producers for **this project only**, and never to the consortium's analysts: they receive
# pseudonyms and cannot reverse them. A new project gets a new key, so its pseudonyms cannot be
# joined with this one's.
#
# ✏️ **Exercise** · `link_key(value, key)`: the HMAC-SHA-256 hex digest, cut to 32 characters;
# `None` in, `None` out.

# %%
# A demonstration key for the synthetic case. A real key is generated per project, kept by the
# linkage unit and never written in a notebook.
PROJECT_KEY = bytes.fromhex("5ea1ed0f" * 8)


def link_key(value: str | None, key: bytes = PROJECT_KEY) -> str | None:
    # BEGIN SOLUTION
    if value is None:
        return None
    return hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    # END SOLUTION


# %%
def keyed(p: str, normalise: bool = True) -> pl.DataFrame:
    df = IDS[p]
    nids = [norm_nid(s) if normalise else s for s in df["nid"]]
    return df.select("producer", "local_id").with_columns(pl.Series("key_a", [link_key(v) for v in nids], dtype=pl.String))


try:
    KEYED = {p: keyed(p) for p in IDS}
except NotImplementedError:
    def link_key(value, key=PROJECT_KEY):
        return None if value is None else hmac.new(key, value.encode(), hashlib.sha256).hexdigest()[:32]
    KEYED = {p: keyed(p) for p in IDS}
other_key = bytes.fromhex("0b5e55ed" * 8)
U.check(link_key("1012345678") != link_key("1012345678", other_key), "another project's key gives unrelated pseudonyms")
print(KEYED["UFQ"].head(3))

# %% [markdown]
# ## 4 · Match rate, precision and recall against the truth (5')
#
# Two local patients at different producers are **linked** when their keys are equal. The truth
# says which pairs are the same person. ✏️ **Exercise** · `pairs(df, key)`: the set of linked
# cross-producer pairs `(local_id, local_id)`, smaller id first, from a table with `local_id`,
# `producer` and the key column. Then compare with the true pairs.

# %%
def pairs(df: pl.DataFrame, key: str) -> set[tuple[str, str]]:
    # BEGIN SOLUTION
    out = set()
    for grp in df.drop_nulls(key).group_by(key).agg("local_id", "producer").iter_rows(named=True):
        for (a, pa), (b, pb) in itertools.combinations(zip(grp["local_id"], grp["producer"]), 2):
            if pa != pb:
                out.add(tuple(sorted((a, b))))
    return out
    # END SOLUTION


def score(pred: set, truth: set) -> dict:
    tp = len(pred & truth)
    return {"linked_pairs": len(pred), "true_pairs": len(truth), "correct": tp,
            "precision": round(tp / max(len(pred), 1), 4), "recall": round(tp / max(len(truth), 1), 4)}


# %%
true_tbl = TRUTH.rename({"local_patient_id": "local_id", "person_id": "key"})
try:
    TRUE_PAIRS = pairs(true_tbl, "key")
    raw_keys = pl.concat([keyed(p, normalise=False) for p in IDS])
    norm_keys = pl.concat(KEYED.values())
    rows = [{"method": "keyed hash, raw identifier", **score(pairs(raw_keys, "key_a"), TRUE_PAIRS)},
            {"method": "keyed hash, normalised", **score(pairs(norm_keys, "key_a"), TRUE_PAIRS)}]
except NotImplementedError:
    rows = U.reference("lab_1_3")["match"][:2]
    TRUE_PAIRS = None
match_table = pl.DataFrame(rows)
print(match_table)
U.check(match_table["recall"][1] > match_table["recall"][0] + 0.3, "normalising first lifts recall by far")
U.check(match_table["precision"][1] == 1.0, "every pair linked by the identifier is a true pair")

# %% [markdown]
# 🔍 Recall is still below 1. Look at five true pairs the normalised key missed: compare the
# identifiers that Ufuq typed with Sidra's. What kind of error is it?

# %% [markdown]
# ## 5 · Add a second key for typing errors (3')
#
# A transposed digit breaks key A. Key B links on what the identifier error leaves intact:
# normalised name, birth date and sex, hashed with the same project key. ✏️ **Exercise** · Compute
# key B at each producer and link a pair when **either** key matches.

# %%
def with_key_b(p: str) -> pl.DataFrame:
    # BEGIN SOLUTION
    df = IDS[p]
    vals = [f"{norm_name(n)}|{d.isoformat()}|{s}" for n, d, s in zip(df["name"], df["birth_date"], df["sex"])]
    return KEYED[p].with_columns(pl.Series("key_b", [link_key(v) for v in vals], dtype=pl.String))
    # END SOLUTION


# %%
try:
    both = pl.concat([with_key_b(p) for p in IDS])
    pred_a, pred_b = pairs(both, "key_a"), pairs(both, "key_b")
    match_table = pl.concat([match_table, pl.DataFrame([
        {"method": "key A or key B", **score(pred_a | pred_b, TRUE_PAIRS)}])])
    false_b = sorted((pred_b - pred_a) - TRUE_PAIRS)
except (NotImplementedError, TypeError):
    match_table = pl.DataFrame(U.reference("lab_1_3")["match"])
    false_b = []
print(match_table)
U.check(match_table["recall"][2] > match_table["recall"][1], "the second key recovers pairs with a mistyped identifier")
U.check(match_table["precision"][2] < 1.0, "and it adds false matches: look-alike people share name, birth date and sex")

# %% [markdown]
# ## ✱ Stretch · Is the second key worth it?
#
# Print the false pairs key B added. For the readmission study, which is worse: a missed readmission
# (lower recall) or two strangers merged into one history (lower precision)? Propose a rule: for
# example, accept a key-B link only when the two identifiers differ by one transposition.

# %%
def transposition_rule() -> dict:
    # BEGIN SOLUTION
    def one_swap(a, b):
        if a is None or b is None or len(a) != len(b):
            return False
        d = [i for i in range(len(a)) if a[i] != b[i]]
        return len(d) == 2 and d[1] == d[0] + 1 and a[d[0]] == b[d[1]] and a[d[1]] == b[d[0]]

    nid = {r["local_id"]: norm_nid(r["nid"]) for p in IDS for r in IDS[p].iter_rows(named=True)}
    kept = {pr for pr in pred_b - pred_a if one_swap(nid[pr[0]], nid[pr[1]])}
    return {"key_b_only": len(pred_b - pred_a), "kept_by_rule": len(kept), **score(pred_a | kept, TRUE_PAIRS)}
    # END SOLUTION


try:
    print("false pairs from key B:", false_b[:5])
    print(transposition_rule())
except (NotImplementedError, TypeError, NameError):
    print("Stretch not attempted.")

# %% [markdown]
# ## Checkpoint
#
# 1. Why is `sha256(national_id)` not a pseudonym the consortium may hold freely?
# 2. Who should hold the linkage key, and why does each project get its own?
# 3. Recall rose and precision fell with key B. Which number would you report to the study lead?
#
# <details><summary>Answers</summary>
#
# 1. The identifier space is small and structured: anyone can hash every candidate and reverse it.
# 2. A linkage unit outside the analysis team, so the analysts cannot recompute or reverse pseudonyms; a key per project stops two projects' data being joined by their pseudonyms.
# 3. Both, with the counts: the study must know how many readmissions it may miss and how many histories may be merged wrongly.
# </details>
#
# **Carry forward.** Nothing: the reference pseudonyms of Days 3 and 4 are already in the study tables.
