# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 1.2 · One contract for three producers
#
# Day 1 · Session 2 (One contract, three producers) · 25 min. **AI off**: this is the course's first
# contract and the supervised checks ask for the same skill without an assistant.
#
# You complete the consortium's shared encounter contract in the Open Data Contract Standard
# (ODCS v3.2.0): the code maps and unit rules each producer needs, the quality rules every delivery
# must pass, and the freshness the study needs. Then you run the one contract against all three
# extracts and read which clause failed, for which producer, on how many rows.
#
# **Reference state.** `data/contracts/encounter.skeleton.odcs.yaml` (schema, SLA, column maps and
# date formats already written) and `data/producers/`. Nothing from Lab 1.1.
#
# **Tasks**
# - [ ] 1 · Read the skeleton: schema, properties, SLA (4')
# - [ ] 2 · Add the code maps and unit rules for each producer (7')
# - [ ] 3 · Add the quality rules (6')
# - [ ] 4 · Run it on the three extracts (5')
# - [ ] 5 · Read the failures: producer, clause, rows (3')
# - [ ] ✱ Stretch · Express one rule as a Soda check in the contract's custom block

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

import copy
import datetime as dt
import json

import polars as pl
import yaml
import rimah as U

# %% [markdown]
# ## 1 · Read the skeleton: schema, properties, SLA (4')
#
# The contract is data. Read it as a dictionary and print what it promises today: eleven properties,
# a latency of two days, and a block of producer clauses under `customProperties`. That block is
# where a contract with several producers says how each one's columns become the shared schema.

# %%
skeleton = U.load_contract(U.DATA / "contracts" / "encounter.skeleton.odcs.yaml")
props = skeleton["schema"][0]["properties"]
print(skeleton["apiVersion"], skeleton["kind"], skeleton["version"], skeleton["status"])
print(pl.DataFrame([{k: p.get(k) for k in ["name", "logicalType", "required", "classification"]} for p in props]))
print("SLA:", [(s["property"], s["value"], s.get("unit")) for s in skeleton["slaProperties"]])
print("producer clauses so far:", {p: sorted(v) for p, v in skeleton["customProperties"][0]["value"].items()})

RAW = {"SDR": U.load("producers/sidra_encounters.csv"), "UFQ": U.load("producers/ufuq_encounters.csv"),
       "RWD": U.load("producers/rawdah_encounters.csv")}

# %% [markdown]
# ## 2 · Add the code maps and unit rules for each producer (7')
#
# The helper `U.conform(raw, producer, contract)` reads only the contract. For each producer it
# understands four clauses: `columns` (already there), `date_formats` (already there), `codes`
# (a value map per property), `transforms` (`upper`, or `icd10_dot` that upper-cases and puts the
# dot back) and `units` (a factor per numeric property).
#
# ✏️ **Exercise** · Return the clauses for Ufuq and Rawdah. Ufuq: `Male`/`Female`, departments,
# dispositions `1` to `4`, diagnosis without the dot, creatinine in mg/dL (× 88.42). Rawdah: `1`/`2`,
# one-letter units, dispositions `01` to `04`, lower-case diagnosis, weight in pounds (× 0.453592).
# The producers confirmed that `1`/`01` is HOME, `2`/`02` TRANSFER, `3`/`03` DIED, `4`/`04` LAMA.

# %%
def producer_clauses() -> dict:
    # BEGIN SOLUTION
    wards_u = {"INT-MED": "MED", "GEN-SURG": "SURG", "CARDIO": "CARD", "ICU": "ICU", "OBGYN": "OBS"}
    wards_r = {"M": "MED", "S": "SURG", "C": "CARD", "I": "ICU", "O": "OBS"}
    return {
        "SDR": {"transforms": {"primary_dx": "icd10_dot"}},
        "UFQ": {"codes": {"sex": {"Male": "M", "Female": "F"}, "ward": wards_u,
                          "disposition": {"1": "HOME", "2": "TRANSFER", "3": "DIED", "4": "LAMA"}},
                "transforms": {"primary_dx": "icd10_dot"},
                "units": {"creatinine_umol_l": 88.42}},
        "RWD": {"codes": {"sex": {"1": "M", "2": "F"}, "ward": wards_r,
                          "disposition": {"01": "HOME", "02": "TRANSFER", "03": "DIED", "04": "LAMA"}},
                "transforms": {"primary_dx": "icd10_dot"},
                "units": {"weight_kg": 0.453592}},
    }
    # END SOLUTION


# %%
try:
    clauses = producer_clauses()
except NotImplementedError:
    clauses = U.reference("lab_1_2")["clauses"]
contract = copy.deepcopy(skeleton)
block = contract["customProperties"][0]["value"]
for p, extra in clauses.items():
    block[p].update(extra)
conformed = {p: U.conform(RAW[p], p, contract) for p in RAW}
for p, df in conformed.items():
    print(p, df.select("sex", "ward", "primary_dx", "disposition", "weight_kg", "creatinine_umol_l").row(0))
medians = {p: round(df["weight_kg"].median(), 1) for p, df in conformed.items()}
U.check(max(medians.values()) - min(medians.values()) < 3, f"weights agree after the unit rule {medians}")
U.check(conformed["UFQ"]["primary_dx"][0][3] == ".", "Ufuq's diagnosis codes have their dot back")

# %% [markdown]
# ## 3 · Add the quality rules (6')
#
# ODCS has **library metrics** that any engine can run: `nullValues`, `missingValues`,
# `invalidValues` (with `validValues` or a `pattern`), `duplicateValues`, `rowCount`; each with
# `mustBe`, `mustBeLessThan` or `mustBeBetween`. A rule ODCS has no metric for can be `type: sql`,
# with `{object}` standing for the table. (The helper also accepts `minimum` and `maximum` as
# arguments of `invalidValues`: an extension of this course, marked as such in the contract.)
#
# ✏️ **Exercise** · Return the rules: valid values for sex, ward and disposition; a pattern for the
# diagnosis; plausible ranges for weight (1 to 350 kg) and creatinine (20 to 1,500 µmol/L), each
# allowing at most 0.5% of rows outside; and two table rules: no duplicate `encounter_id`, and no
# discharge before admission.

# %%
def quality_rules() -> tuple[dict, list]:
    # BEGIN SOLUTION
    per_property = {
        "sex": [{"id": "sex_valid", "metric": "invalidValues", "arguments": {"validValues": ["M", "F"]}, "mustBe": 0}],
        "ward": [{"id": "ward_valid", "metric": "invalidValues",
                  "arguments": {"validValues": ["MED", "SURG", "CARD", "ICU", "OBS"]}, "mustBe": 0}],
        "disposition": [{"id": "disposition_valid", "metric": "invalidValues",
                         "arguments": {"validValues": ["HOME", "TRANSFER", "DIED", "LAMA"]}, "mustBe": 0}],
        "primary_dx": [{"id": "dx_icd10", "metric": "invalidValues",
                        "arguments": {"pattern": r"^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$"}, "mustBe": 0}],
        "weight_kg": [{"id": "weight_plausible", "metric": "invalidValues", "arguments": {"minimum": 1, "maximum": 350},
                       "mustBeLessThan": 0.5, "unit": "percent", "description": "minimum and maximum: course extension"}],
        "creatinine_umol_l": [{"id": "creatinine_plausible", "metric": "invalidValues",
                               "arguments": {"minimum": 20, "maximum": 1500}, "mustBeLessThan": 0.5, "unit": "percent",
                               "description": "minimum and maximum: course extension"}],
    }
    table = [
        {"id": "encounter_unique", "metric": "duplicateValues", "arguments": {"properties": ["encounter_id"]}, "mustBe": 0},
        {"id": "discharge_after_admit", "type": "sql",
         "query": "SELECT COUNT(*) FROM {object} WHERE discharge_date < admit_date", "mustBe": 0},
        {"id": "not_empty", "metric": "rowCount", "mustBeGreaterThan": 0},
    ]
    return per_property, table
    # END SOLUTION


# %%
try:
    per_property, table_rules = quality_rules()
except NotImplementedError:
    ref = U.reference("lab_1_2")
    per_property, table_rules = ref["per_property"], ref["table_rules"]
for prop in contract["schema"][0]["properties"]:
    if prop["name"] in per_property:
        prop["quality"] = per_property[prop["name"]]
contract["schema"][0]["quality"] = table_rules
contract["version"], contract["status"] = "1.0.0", "active"
path = U.lab_dir("D1_2") / "encounter.odcs.yaml"
path.write_text(yaml.safe_dump(contract, sort_keys=False, allow_unicode=True), encoding="utf-8", newline="\n")
U.check(len(per_property) >= 6 and len(table_rules) >= 2, f"{sum(map(len, per_property.values())) + len(table_rules)} rules written to {path.name}")

# %% [markdown]
# ## 4 · Run it on the three extracts (5')
#
# One contract, three runs. ✏️ **Exercise** · Write `run_all()`: for each producer, conform the
# extract, run the rules (`U.run_contract`) and add the freshness clause (`U.freshness` with the
# newest admission and the delivery date from `manifest.json`). Return one table.

# %%
MANIFEST = json.loads((U.DATA / "producers" / "manifest.json").read_text())
DELIVERED = {d["producer"]: dt.date.fromisoformat(d["delivered_on"]) for d in MANIFEST["deliveries"]}


def run_all() -> pl.DataFrame:
    # BEGIN SOLUTION
    parts = []
    for p in RAW:
        df = U.conform(RAW[p], p, contract)
        res = U.run_contract(df, contract, producer=p)
        ok, lag = U.freshness(contract, df["admit_date"].max(), DELIVERED[p])
        fresh = pl.DataFrame([{"producer": p, "property": "encounter", "rule": "latency", "metric": "sla",
                               "value": float(lag), "passed": ok, "severity": "error"}])
        parts.append(pl.concat([res, fresh]))
    return pl.concat(parts)
    # END SOLUTION


# %%
try:
    results = run_all()
except NotImplementedError:
    results = pl.DataFrame(U.reference("lab_1_2")["results"])
summary = results.group_by("producer").agg(pl.len().alias("rules"), pl.col("passed").sum().alias("passed")).sort("producer")
print(summary)
failed = results.filter(~pl.col("passed"))
print(failed.select("producer", "rule", "value"))
U.check(set(failed["producer"]) == {"UFQ", "RWD"} and results.filter(pl.col("producer") == "SDR")["passed"].all(),
        "Sidra passes every clause; Ufuq and Rawdah fail some")

# %% [markdown]
# ## 5 · Read the failures: producer, clause, rows (3')
#
# A failure is useful when it names the producer, the clause and the rows. Show three rows behind
# each failed rule, then decide who acts: the producer fixes and re-sends, or the contract changes.

# %%
c_ufq, c_rwd = U.conform(RAW["UFQ"], "UFQ", contract), U.conform(RAW["RWD"], "RWD", contract)
dups = c_ufq.filter(pl.col("encounter_id").is_duplicated()).sort("encounter_id")
print("Ufuq duplicate encounters:", dups["encounter_id"].n_unique(), "\n", dups.head(4).select("encounter_id", "admit_date", "ward"))
swapped = c_rwd.filter(pl.col("discharge_date") < pl.col("admit_date"))
print("Rawdah discharge before admission:", swapped.height, "\n", swapped.head(3).select("encounter_id", "admit_date", "discharge_date"))
print("Ufuq's newest admission:", c_ufq["admit_date"].max(), "delivered", DELIVERED["UFQ"])

# %% [markdown]
# 🔍 Ufuq's newest admission is nine days before its delivery: the extract stopped early, so the
# last week of December is missing from Ufuq. A pooled readmission rate for December would quietly
# be low. That is why freshness is a contract clause and not a remark in an email.

# %% [markdown]
# ## ✱ Stretch · One rule as a Soda check
#
# ODCS lets a rule be handed to another engine (`type: custom`, `engine: soda`, an `implementation`
# block). Write the duplicate rule that way and add it beside the library rule. This course's helper
# does not run custom blocks: they document a check another engine runs.

# %%
def soda_rule() -> dict:
    # BEGIN SOLUTION
    return {"id": "encounter_unique_soda", "type": "custom", "engine": "soda",
            "implementation": "type: duplicate_count\ncolumns:\n  - encounter_id\nmust_be: 0\n"}
    # END SOLUTION


try:
    print(yaml.safe_dump(soda_rule(), sort_keys=False))
except NotImplementedError:
    print("Stretch not attempted.")

# %% [markdown]
# ## Checkpoint
#
# 1. A contract lists every column with its type and nothing else. What did it fail to promise?
# 2. Why is the unit factor a clause of the contract and not a line in the pipeline code?
# 3. Ufuq fails on duplicates and freshness. Does the whole delivery stop, or only the bad rows?
#
# <details><summary>Answers</summary>
#
# 1. Meaning: codes, units, ranges, uniqueness and freshness. A typed column of pounds is still pounds.
# 2. So that the producer and every consumer read the same rule, and a change to it is a versioned change.
# 3. It is the consortium's policy to decide; this course's rule is that an `error` rule blocks the delivery and the producer re-sends. Day 2 blocks per partition so one bad delivery stops alone.
# </details>
#
# **Carry forward.** `artifacts/D1_2/encounter.odcs.yaml`. The reference contract for later labs is
# `data/contracts/encounter.v1.odcs.yaml`.
