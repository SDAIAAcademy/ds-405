# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 4.4 · The decision for the university
#
# Day 4 · Session 4 (The release decision) · 25 min.
#
# Draft the decision for the university request (method, residual risk, conditions, approver) from the measured results, and test the request against the national rules for sharing and secondary use.
#
# **Reference state.** Prof. Adnan Al-Shuwaiman's request (below) and the measured results of
# Labs 3.3, 3.4 and 4.1 in `data/reference/` (the same numbers your own runs gave, within noise).
# The release board meets on Thursday: Dr. Fadwa Al-Qassabi chairs it, Ghanem Al-Mutawakkil
# (data protection officer) advises. The decision record is written to `artifacts/D4_4/`.
#
# **Tasks**
# - [ ] 1 · Read the request and the measured results (4')
# - [ ] 2 · Test the request against the sharing principles and secondary-use rules (7')
# - [ ] 3 · Choose the method and state the residual risk (6')
# - [ ] 4 · Conditions and approver (5')
# - [ ] 5 · Validate and write the record (3')
# - [ ] ✱ Stretch · Write the strongest objection and your answer

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

import yaml
import polars as pl
import rimah as U

WORK = U.lab_dir("D4_4")

# %% [markdown]
# ## 1 · Read the request and the measured results (4')

# %%
REQUEST = yaml.safe_load("""
id: REQ-2026-031
applicant: Prof. Adnan Al-Shuwaiman, department of health informatics, a university partner
submitted_by: the applicant, by email to the consortium director
purpose: >
  Develop and validate a model that predicts 30-day readmission, for a doctoral thesis and
  journal publications; the model may later be offered to hospitals.
data_requested: all patient and encounter columns of the readmission study, record level, 2025
duration: 24 months
access: copied to the research group's shared drive; available to the group's students
institutional_approval: not attached ("the ethics committee approval will follow")
request_form: free text email; the Data-Sharing Request Form is not used
""")
utility = U.reference("lab_3_3")
attacks = U.reference("lab_3_4")
risk = U.reference("lab_4_1")
for k, v in REQUEST.items():
    print(f"{k:22} {str(v).strip()}")
print()
print("TSTR AUC (trees / real):", utility["tstr"]["trees"], "/", utility["tstr"]["real (TRTR)"],
      "| risk ratio trees / real:", utility["estimates"]["trees"]["rr"], "/", utility["estimates"]["real"]["rr"])
print("membership AUC, trees:", attacks["mia"]["trees"], "| vendor:", attacks["mia"]["vendor"])
print("record-level stays, unique on sex, year of birth and two known stays:", risk["by_known"]["demo_2"])

# %% [markdown]
# ## 2 · Test the request against the sharing principles and secondary-use rules (7')
#
# The national Data Sharing Policy names eight principles; the General Rules for Secondary Use of
# Data add requirements for the applicant. Each line gets a status (`met`, `not met`,
# `condition`) and the evidence from the request.
#
# ✏️ **Exercise** · Complete `assess(request)`: five lines are given; write the five marked
# `TODO` with their status and evidence.

# %%
STATUSES = {"met", "not met", "condition"}


def assess(request: dict) -> list[dict]:
    given = [
        {"rule": "Sharing principle: Legitimate Purpose", "status": "condition",
         "evidence": "research on readmission serves the public interest; 'may later be offered to hospitals' must not become profit-oriented use"},
        {"rule": "Sharing principle: Authorized Access", "status": "not met",
         "evidence": "copied to a shared drive open to students: no named users or access control"},
        {"rule": "Sharing principle: Data Security", "status": "not met",
         "evidence": "a shared drive is not an approved secure environment"},
        {"rule": "Sharing principle: Transparency", "status": "condition",
         "evidence": "the purpose is stated; the consortium must record what is shared, with whom and why"},
        {"rule": "Secondary use: request through the data source entity", "status": "met",
         "evidence": "sent to the consortium, which holds the study tables"},
    ]
    # BEGIN SOLUTION
    todo = [
        {"rule": "Secondary use: minimum necessary data", "status": "not met",
         "evidence": "all columns at record level requested; a readmission model needs eleven features"},
        {"rule": "Secondary use: academic applicant applies through the institution, with written approval", "status": "not met",
         "evidence": "sent by the applicant personally; institutional approval not attached"},
        {"rule": "Secondary use: complete Data-Sharing Request Form", "status": "not met",
         "evidence": "free-text email instead of the form"},
        {"rule": "Sharing principle: Collective Accountability", "status": "condition",
         "evidence": "the university and the consortium must both sign the agreement and its obligations"},
        {"rule": "Sharing principle: Ethical Data Use", "status": "condition",
         "evidence": "ethics committee approval must be attached before any data moves"},
    ]
    # END SOLUTION
    return given + todo


# %%
try:
    checklist = assess(REQUEST)
except NotImplementedError:
    checklist = U.reference("lab_4_4")["checklist"]
U.show(pl.DataFrame(checklist).select("status", "rule"), 12)
U.check(all(c["status"] in STATUSES and c["evidence"] for c in checklist), "every line has a status and evidence")
by_rule = {c["rule"]: c["status"] for c in checklist}
U.check(by_rule.get("Secondary use: academic applicant applies through the institution, with written approval") == "not met",
        "the missing institutional approval is found")
U.check(by_rule.get("Secondary use: minimum necessary data") != "met", "'all columns' is not the minimum necessary")

# %% [markdown]
# 🔍 Five requirements are not met before any question of method arises: three secondary-use rules
# for the applicant, and authorised access and data security. The decision cannot be
# "approved"; it can say exactly what must change and what will then be released.

# %% [markdown]
# ## 3 · Choose the method and state the residual risk (6')
#
# ✏️ **Exercise** · `method_and_risk()`: the method (what leaves the consortium, and in what
# form) and the residual risk, each with the measured numbers that support it.

# %%
def method_and_risk() -> dict:
    # BEGIN SOLUTION
    return {
        "method": ("a synthetic pair (conditional trees, leaf 25) of the eleven model features for model development; "
                   "final fitting and validation run by the consortium on the real data from code the group submits"),
        "why_not_extract": (f"record-level stays: {risk['by_known']['demo_2']:.0%} of patients with two stays are unique "
                            "on sex, year of birth and those two stays"),
        "utility_evidence": (f"TSTR AUC {utility['tstr']['trees']} against {utility['tstr']['real (TRTR)']} on real data; "
                             f"heart-failure risk ratio {utility['estimates']['trees']['rr']} inside the real interval "
                             f"{utility['estimates']['real']['lo']}-{utility['estimates']['real']['hi']}"),
        "residual_risk": (f"membership AUC {attacks['mia']['trees']['patients']} (patients) and "
                          f"{attacks['mia']['trees']['encounters']} (encounters), under the board's 0.60; "
                          "the synthetic file is still derived from personal data and is shared under agreement, not published"),
    }
    # END SOLUTION


# %%
try:
    method = method_and_risk()
except NotImplementedError:
    method = {k: v for k, v in U.reference("lab_4_4")["record"].items() if k in {"method", "why_not_extract", "utility_evidence", "residual_risk"}}
for k, v in method.items():
    print(f"{k}: {v}\n")
U.check(any(ch.isdigit() for ch in method["residual_risk"]), "the residual risk is stated with a measured number")

# %% [markdown]
# ## 4 · Conditions and approver (5')
#
# ✏️ **Exercise** · `conditions()`: the conditions under which the release goes ahead (each
# checkable), the decision, the approver and who was consulted.

# %%
def conditions() -> dict:
    # BEGIN SOLUTION
    return {
        "decision": "conditional approval: nothing is released until conditions 1 to 3 are met",
        "conditions": [
            "1. the request is resubmitted by the university on the Data-Sharing Request Form",
            "2. written approval of the university's academic authority and its ethics committee is attached",
            "3. a data-sharing agreement names the users, the purpose (no commercial use without a new request) and the 24-month term",
            "4. only the synthetic pair of the eleven model features leaves the consortium; no real record is copied",
            "5. no onward sharing; the file is deleted at the end of the term and deletion is confirmed in writing",
            "6. any publication reports results from the consortium's run on real data, not from the synthetic file",
        ],
        "classification": "source tables Restricted; the synthetic pair handled as Restricted under the agreement (board's assessment)",
        "approver": "Dr. Fadwa Al-Qassabi, director, chair of the release board",
        "consulted": ["Ghanem Al-Mutawakkil, data protection officer"],
        "review_date": "at resubmission, and before any extension of the term",
    }
    # END SOLUTION


# %%
try:
    terms = conditions()
except NotImplementedError:
    terms = {k: v for k, v in U.reference("lab_4_4")["record"].items()
             if k in {"decision", "conditions", "classification", "approver", "consulted", "review_date"}}
U.check(not terms["decision"].lower().startswith("approved"), "the decision is not an unconditional approval")
U.check(len(terms["conditions"]) >= 3, "at least three checkable conditions")

# %% [markdown]
# ## 5 · Validate and write the record (3')

# %%
REQUIRED = ["request", "decision", "method", "why_not_extract", "utility_evidence", "residual_risk",
            "conditions", "classification", "approver", "consulted", "checklist", "evidence_files"]
record = {"request": REQUEST["id"], **terms, **method, "checklist": checklist,
          "evidence_files": ["artifacts/D3_3/utility.csv", "artifacts/D3_4/attacks.csv", "artifacts/D4_1/risk.csv"]}
missing = [k for k in REQUIRED if not record.get(k)]
U.check(not missing, f"every required field is filled {missing or ''}")
path = WORK / "decision.yaml"
path.write_text(yaml.safe_dump(record, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8", newline="\n")
print(path.read_text(encoding="utf-8")[:1200])

# %% [markdown]
# ## ✱ Stretch · Write the strongest objection and your answer
#
# Prof. Adnan replies: "A model trained on synthetic data is worthless for a journal." Write his
# strongest form of the objection, and the board's answer, in two sentences each.

# %%
def objection() -> dict:
    # BEGIN SOLUTION
    return {
        "objection": "Reviewers will reject a model whose coefficients were fitted on generated data, and the group cannot "
                     "study errors on real patients it never sees.",
        "answer": "The published model is fitted and validated by the consortium on the real data from the group's own code, "
                  "so the paper reports real-data results; the synthetic pair, whose model scored within 0.001 AUC of the real "
                  "one, is for building and debugging that code.",
    }
    # END SOLUTION


try:
    print(objection())
except NotImplementedError:
    print("Stretch not attempted.")

# %% [markdown]
# ## Checkpoint
#
# 1. Which missing item stops the request before any question of method?
# 2. Why is "approved" the wrong decision even if the synthetic file passes every attack?
# 3. Who signs, and who advises?
#
# <details><summary>Answers</summary>
#
# 1. The written approval of the applicant's academic authority: an academic applicant applies through the institution (and the form, and the minimum-necessary test).
# 2. The conditions are the protection: users, purpose, term, no onward sharing and deletion are what keep the residual risk at what was measured.
# 3. The chair of the release board approves; the data protection officer advises. The record names both.
# </details>
#
# **Carry forward.** `decision.yaml` is the model for the capstone's release decision (15 points).
