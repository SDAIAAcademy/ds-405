# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 1.1 · Profile three producers
#
# Day 1 · Session 1 (Preparation breaks where producers disagree) · 25 min.
#
# Three hospital groups send the Rimah Health Data Consortium their encounter extracts for the
# readmission study: Sidra Hospitals (SDR), Ufuq Medical Group (UFQ) and Rawdah Hospitals (RWD).
# Each extract describes the same thing, a hospital stay, and no two agree on how. You profile them
# side by side and write the **disagreement register** that the shared contract of Lab 1.2 will
# resolve. You map nothing yet: profile first, then decide.
#
# **Reference state.** `data/producers/*.csv` and `data/producers/manifest.json`. Nothing from another lab.
# Every person, identifier and record is synthetic.
#
# **Tasks**
# - [ ] 1 · Load the three extracts and compare their columns (5')
# - [ ] 2 · Match columns to the study's fields (5')
# - [ ] 3 · Compare code sets: sex, diagnosis, disposition (6')
# - [ ] 4 · Find the unit differences from the distributions (5')
# - [ ] 5 · Write the disagreement register (4')
# - [ ] ✱ Stretch · Find the identifier formats that would break a join

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

# %% [markdown]
# ## 1 · Load the three extracts and compare their columns (5')
#
# Read every column as text: a reader that guesses types hides problems (a leading zero dropped
# from an identifier, a date read as a number). Then print the columns side by side.

# %%
FILES = {"SDR": "producers/sidra_encounters.csv", "UFQ": "producers/ufuq_encounters.csv",
         "RWD": "producers/rawdah_encounters.csv"}
raw = {p: U.load(f) for p, f in FILES.items()}
for p, df in raw.items():
    print(f"{p}: {df.height:,} rows, {df.width} columns")
    print("   ", ", ".join(df.columns))

# %% [markdown]
# 🔍 Look at the first two rows of each. Which producer writes dates day first? Which one keeps a
# prefix in front of the national identifier? Which encounter ids would lose characters if read as numbers?

# %%
for p, df in raw.items():
    U.show(df, 2)

# %% [markdown]
# ## 2 · Match columns to the study's fields (5')
#
# The study needs eleven fields. ✏️ **Exercise** · Complete `COLUMN_MAP`: for each study field,
# the column that holds it at each producer. Sidra's names are almost the study's own; Ufuq and
# Rawdah are not.

# %%
FIELDS = ["encounter_id", "patient_local_id", "birth_date", "sex", "admit_date", "discharge_date",
          "ward", "primary_dx", "disposition", "weight", "creatinine"]


def column_map() -> dict[str, dict[str, str]]:
    # BEGIN SOLUTION
    return {
        "SDR": {"encounter_id": "encounter_id", "patient_local_id": "patient_id", "birth_date": "birth_date",
                "sex": "sex", "admit_date": "admit_date", "discharge_date": "discharge_date", "ward": "ward",
                "primary_dx": "primary_dx", "disposition": "disposition", "weight": "weight_kg",
                "creatinine": "creatinine_umol_l"},
        "UFQ": {"encounter_id": "EncounterNo", "patient_local_id": "MRN", "birth_date": "DOB", "sex": "Gender",
                "admit_date": "AdmissionDate", "discharge_date": "DischargeDate", "ward": "Department",
                "primary_dx": "DiagnosisCode", "disposition": "DischargeStatus", "weight": "WeightKg",
                "creatinine": "Creatinine_mgdl"},
        "RWD": {"encounter_id": "enc_id", "patient_local_id": "pt_id", "birth_date": "dob", "sex": "sex",
                "admit_date": "adm_dt", "discharge_date": "dis_dt", "ward": "unit", "primary_dx": "icd10",
                "disposition": "disp", "weight": "weight_lb", "creatinine": "creat_umol"},
    }
    # END SOLUTION


# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
try:
    COLUMN_MAP = column_map()
except NotImplementedError:
    COLUMN_MAP = U.reference("lab_1_1")["column_map"]
for p in raw:
    missing = [f for f in FIELDS if COLUMN_MAP[p].get(f) not in raw[p].columns]
    U.check(not missing, f"{p}: every study field found {missing or ''}")


def field(p: str, f: str) -> pl.Series:
    """One study field at one producer, as text."""
    return raw[p][COLUMN_MAP[p][f]]


# %% [markdown]
# ## 3 · Compare code sets: sex, diagnosis, disposition (6')
#
# ✏️ **Exercise** · Write `code_sets(f)`: for one field, the sorted distinct values at each producer.
# For the diagnosis, compare the **shape** of the codes, not the codes: replace every letter with
# `A` and every digit with `9` (so `I50.9` becomes `A99.9`).

# %%
def code_sets(f: str, shape: bool = False) -> dict[str, list[str]]:
    # BEGIN SOLUTION
    out = {}
    for p in raw:
        s = field(p, f)
        if shape:
            s = s.str.replace_all(r"[A-Za-z]", "A").str.replace_all(r"[0-9]", "9")
        out[p] = sorted(s.drop_nulls().unique().to_list())
    return out
    # END SOLUTION


# %%
try:
    sets = {f: code_sets(f) for f in ["sex", "disposition", "ward"]}
    dx_shapes = code_sets("primary_dx", shape=True)
except NotImplementedError:
    ref = U.reference("lab_1_1")
    sets, dx_shapes = ref["code_sets"], ref["dx_shapes"]
for f, s in sets.items():
    print(f"{f:12}", s)
print("dx shapes   ", dx_shapes)
U.check(sets["sex"]["UFQ"] == ["Female", "Male"] and sets["sex"]["RWD"] == ["1", "2"], "sex is coded three ways")
U.check(dx_shapes["UFQ"] != dx_shapes["SDR"], "Ufuq writes diagnosis codes without the dot")

# %% [markdown]
# 🔍 Rawdah writes `i50.9`: the same code, lower case. A join on the raw code would silently drop
# every Rawdah encounter. Ufuq's `1` to `4` are dispositions, but which number is "died"? Only the
# producer can say: that is a question for Kinan Al-Rakhees at Ufuq, and the answer goes into the contract.

# %% [markdown]
# ## 4 · Find the unit differences from the distributions (5')
#
# Column names do not always carry units, and when they do they can be wrong. Compare the median
# and the 5th and 95th percentiles of weight and creatinine at each producer.
#
# ✏️ **Exercise** · Write `spread(f)` returning one row per producer with `p05`, `median`, `p95`.

# %%
def spread(f: str) -> pl.DataFrame:
    # BEGIN SOLUTION
    rows = []
    for p in raw:
        s = field(p, f).cast(pl.Float64, strict=False)
        rows.append({"producer": p, "p05": s.quantile(0.05), "median": s.median(), "p95": s.quantile(0.95)})
    return pl.DataFrame(rows)
    # END SOLUTION


# %%
try:
    weight, creat = spread("weight"), spread("creatinine")
except NotImplementedError:
    ref = U.reference("lab_1_1")
    weight, creat = pl.DataFrame(ref["weight"]), pl.DataFrame(ref["creatinine"])
print("weight\n", weight, "\ncreatinine\n", creat)
med_w = dict(zip(weight["producer"], weight["median"]))
med_c = dict(zip(creat["producer"], creat["median"]))
U.check(med_w["RWD"] / med_w["SDR"] > 2.0, f"Rawdah's weights are about 2.2 times the others: pounds ({med_w['RWD']:.0f} vs {med_w['SDR']:.0f})")
U.check(med_c["SDR"] / med_c["UFQ"] > 50, f"Ufuq's creatinine is about 88 times smaller: mg/dL, not µmol/L ({med_c['UFQ']:.2f} vs {med_c['SDR']:.0f})")

# %% [markdown]
# ## 5 · Write the disagreement register (4')
#
# One row per disagreement: the field, the producer, the **kind** (`schema`, `code`, `unit`,
# `format` or `identifier`), what you saw and the fix the contract should state. Sidra is the
# reference: list what differs from it. ✏️ **Exercise** · Fill `register()`; at least ten rows,
# every kind present.

# %%
def register() -> list[dict]:
    # BEGIN SOLUTION
    R = []

    def add(f, p, kind, seen, fix):
        R.append({"field": f, "producer": p, "kind": kind, "seen": seen, "fix": fix})

    add("all", "UFQ", "schema", "PascalCase names (EncounterNo, MRN, DOB)", "map columns in the contract")
    add("all", "RWD", "schema", "short names (enc_id, adm_dt, dis_dt)", "map columns in the contract")
    add("birth_date", "UFQ", "format", "dd/mm/yyyy", "parse with %d/%m/%Y")
    add("birth_date", "RWD", "format", "yyyymmdd without separators", "parse with %Y%m%d")
    add("admit_date", "UFQ", "format", "dd/mm/yyyy", "parse with %d/%m/%Y")
    add("sex", "UFQ", "code", "Male / Female", "map to M / F")
    add("sex", "RWD", "code", "1 / 2", "map 1 to M, 2 to F (confirm with Rawdah)")
    add("ward", "UFQ", "code", "INT-MED, GEN-SURG, CARDIO, ICU, OBGYN", "map to MED, SURG, CARD, ICU, OBS")
    add("ward", "RWD", "code", "one-letter units M, S, C, I, O", "map to MED, SURG, CARD, ICU, OBS")
    add("primary_dx", "UFQ", "format", "ICD-10 without the dot (I509)", "insert the dot after three characters")
    add("primary_dx", "RWD", "format", "ICD-10 in lower case (i50.9)", "upper case")
    add("disposition", "UFQ", "code", "numbers 1 to 4", "map 1 HOME, 2 TRANSFER, 3 DIED, 4 LAMA (confirm)")
    add("disposition", "RWD", "code", "01 to 04", "map 01 HOME, 02 TRANSFER, 03 DIED, 04 LAMA (confirm)")
    add("weight", "RWD", "unit", "median about 170: pounds", "multiply by 0.453592")
    add("creatinine", "UFQ", "unit", "median about 1: mg/dL", "multiply by 88.42 to get µmol/L")
    add("encounter_id", "RWD", "format", "leading zeros (0000001)", "read as text, never as a number")
    add("national_id", "UFQ", "identifier", "spaces and Arabic-Indic digits", "normalise before hashing (Lab 1.3)")
    add("national_id", "RWD", "identifier", "SA- prefix", "normalise before hashing (Lab 1.3)")
    return R
    # END SOLUTION


# %%
try:
    reg = pl.DataFrame(register())
except NotImplementedError:
    reg = pl.DataFrame(U.reference("lab_1_1")["register"])
out = U.lab_dir("D1_1") / "disagreements.csv"
reg.write_csv(out)
print(reg.group_by("kind").len().sort("kind"))
U.check(reg.height >= 10, f"{reg.height} disagreements recorded")
U.check({"schema", "code", "unit", "format"} <= set(reg["kind"]), "schema, code, unit and format disagreements all present")
U.check(reg.filter((pl.col("kind") == "unit")).height >= 2, "both unit problems recorded")
print("saved:", out.relative_to(U.LABS))

# %% [markdown]
# ## ✱ Stretch · Find the identifier formats that would break a join
#
# Count, per producer, how many national identifiers are exactly ten ASCII digits. What else do you
# find, and what would a join on the raw value do to the patients seen at two groups?

# %%
def id_formats() -> dict:
    # BEGIN SOLUTION
    cols = {"SDR": "national_id", "UFQ": "NationalID", "RWD": "nid"}
    out = {}
    for p, c in cols.items():
        s = raw[p][c]
        out[p] = {"ten_ascii_digits": int(s.str.contains(r"^[0-9]{10}$").sum()),
                  "with_spaces": int(s.str.contains(" ").sum()),
                  "arabic_indic_digits": int(s.str.contains(r"[٠-٩]").sum()),
                  "with_prefix": int(s.str.contains(r"^[A-Z]").sum()), "rows": s.len()}
    return out
    # END SOLUTION


try:
    print(id_formats())
except NotImplementedError:
    print("Stretch not attempted.")

# %% [markdown]
# ## Checkpoint
#
# 1. Two producers' weight columns both pass a "number between 1 and 500" check. Is the weight field safe to pool?
# 2. Why read every column as text first?
# 3. Which disagreements can you fix alone, and which need the producer to confirm?
#
# <details><summary>Answers</summary>
#
# 1. No. Rawdah's pounds pass a wide range check; only the distribution (or the producer) tells you the unit.
# 2. A type guess silently changes values: leading zeros vanish from `0000001`, `01/10/2025` may be read month first.
# 3. Formats (dates, dots, case) you can fix; the meaning of codes (`3` is died?) and units must be confirmed by the producer and written into the contract.
# </details>
#
# **Carry forward.** `artifacts/D1_1/disagreements.csv`. Lab 1.2 starts from a supplied skeleton, not from this file.
