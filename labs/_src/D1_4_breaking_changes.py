# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 1.4 · A breaking-change policy, tested
#
# Day 1 · Session 4 (Versions and breaking changes) · 25 min.
#
# In January Ufuq Medical Group upgraded its hospital system and the extract changed without a word.
# You draft the consortium's change policy as data (what counts as breaking, how much notice, who
# approves), then test it on Ufuq's version 2 sample: find every change, including the one no
# schema comparison shows, classify each with the policy, and decide the contract's next version.
#
# **Reference state.** `data/producers/ufuq_encounters.csv` (version 1), `data/producers/ufuq_v2_sample.csv`
# (version 2) and `data/contracts/encounter.v1.odcs.yaml` (the contract from Lab 1.2's solution).
#
# **Tasks**
# - [ ] 1 · Draft the policy as data (6')
# - [ ] 2 · Diff the old and new extract (7')
# - [ ] 3 · Catch the change no schema diff shows (5')
# - [ ] 4 · Apply the policy: version, notice, approver (5')
# - [ ] 5 · One-page policy text (2')
# - [ ] ✱ Stretch · Write the deprecation notice Ufuq should have sent

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
import yaml
import rimah as U

V1 = U.load("producers/ufuq_encounters.csv")
V2 = U.load("producers/ufuq_v2_sample.csv")
CONTRACT = U.load_contract(U.DATA / "contracts" / "encounter.v1.odcs.yaml")
print("v1:", V1.columns, "\nv2:", V2.columns)

# %% [markdown]
# ## 1 · Draft the policy as data (6')
#
# A policy that lives in a document is argued about; a policy that is data is applied the same way
# every time. ✏️ **Exercise** · Return `POLICY` with:
# - `breaking`: the change kinds that break a consumer (at least: a removed column, a renamed column,
#   a changed type, a changed unit, a changed format, a new value in a closed code set);
# - `additive`: kinds that do not (at least: a new optional column);
# - `notice_days`: for each class, how long before the change the producer must announce it;
# - `approvers`: for each class, who must agree;
# - `version_bump`: for each class, which part of the contract version moves (`major` or `minor`).

# %%
def draft_policy() -> dict:
    # BEGIN SOLUTION
    return {
        "breaking": ["removed_column", "renamed_column", "type_change", "unit_change", "format_change",
                     "new_code_in_closed_set", "meaning_change"],
        "additive": ["new_optional_column", "new_code_in_open_set", "looser_rule"],
        "notice_days": {"breaking": 60, "additive": 14},
        "approvers": {"breaking": ["consortium data board (chair: Dr. Fadwa Al-Qassabi)", "consumer owner: readmission study",
                                   "data protection officer if a personal-data field changes"],
                      "additive": ["contract owner"]},
        "version_bump": {"breaking": "major", "additive": "minor"},
        "parallel_run_days": 30,
    }
    # END SOLUTION


# %%
try:
    POLICY = draft_policy()
except NotImplementedError:
    POLICY = U.reference("lab_1_4")["policy"]
U.check({"removed_column", "renamed_column", "unit_change", "format_change", "new_code_in_closed_set"} <= set(POLICY["breaking"]),
        "the policy names the breaking kinds")
U.check(POLICY["notice_days"]["breaking"] > POLICY["notice_days"]["additive"], "breaking changes need longer notice")

# %% [markdown]
# ## 2 · Diff the old and new extract (7')
#
# ✏️ **Exercise** · Write `diff_extracts(old, new, closed_sets, date_cols)` returning a list of
# changes `{"kind", "column", "detail"}`:
# - columns removed and added (`removed_column`, `new_optional_column`);
# - for each column in `closed_sets`, values in `new` that `old` never had (`new_code_in_closed_set`);
# - for each column in `date_cols`, whether the old format (`%d/%m/%Y`) still parses every value (`format_change`).

# %%
CLOSED = ["Gender", "Department", "DischargeStatus"]
DATES = ["DOB", "AdmissionDate", "DischargeDate"]


def diff_extracts(old: pl.DataFrame, new: pl.DataFrame, closed_sets: list[str], date_cols: list[str]) -> list[dict]:
    # BEGIN SOLUTION
    ch = []
    for c in old.columns:
        if c not in new.columns:
            ch.append({"kind": "removed_column", "column": c, "detail": "absent in the new extract"})
    for c in new.columns:
        if c not in old.columns:
            ch.append({"kind": "new_optional_column", "column": c,
                       "detail": f"{new[c].null_count()} nulls in {new.height} rows"})
    for c in closed_sets:
        extra = sorted(set(new[c].drop_nulls()) - set(old[c].drop_nulls()))
        if extra:
            ch.append({"kind": "new_code_in_closed_set", "column": c, "detail": f"new values {extra}"})
    for c in date_cols:
        bad = new[c].str.to_date("%d/%m/%Y", strict=False).null_count() - new[c].null_count()
        if bad:
            ch.append({"kind": "format_change", "column": c, "detail": f"{bad} of {new.height} values no longer parse as dd/mm/yyyy"})
    return ch
    # END SOLUTION


# %%
try:
    changes = diff_extracts(V1, V2, CLOSED, DATES)
except NotImplementedError:
    changes = U.reference("lab_1_4")["diff_changes"]
diff_changes = list(changes)
print(pl.DataFrame(changes))
kinds = {c["kind"] for c in changes}
U.check({"removed_column", "new_optional_column", "new_code_in_closed_set", "format_change"} <= kinds,
        "removed and added columns, a new code and a new date format found")

# %% [markdown]
# ## 3 · Catch the change no schema diff shows (5')
#
# The diff says `Creatinine_mgdl` was removed and `Creatinine` added. Is that a column dropped and
# another added, or the same measurement renamed, and in which unit? Names cannot say; values can.
#
# ✏️ **Exercise** · Compare the median of the removed column with the median of the added numeric
# column. If the ratio is near a known unit factor (88.42 for creatinine, 2.20462 for weight),
# record a `renamed_column` **and** a `unit_change`.

# %%
FACTORS = {"creatinine mg/dL to µmol/L": 88.42, "weight kg to lb": 2.20462}


def rename_and_unit(old: pl.DataFrame, new: pl.DataFrame, removed: str, added: str) -> list[dict]:
    # BEGIN SOLUTION
    a = old[removed].cast(pl.Float64, strict=False).median()
    b = new[added].cast(pl.Float64, strict=False).median()
    ratio = b / a
    out = [{"kind": "renamed_column", "column": f"{removed} -> {added}", "detail": f"median {a:.2f} -> {b:.1f}"}]
    for name, f in FACTORS.items():
        if abs(ratio / f - 1) < 0.05:
            out.append({"kind": "unit_change", "column": added, "detail": f"{name} (ratio {ratio:.1f})"})
    return out
    # END SOLUTION


# %%
try:
    hidden = rename_and_unit(V1, V2, "Creatinine_mgdl", "Creatinine")
except NotImplementedError:
    hidden = [c for c in U.reference("lab_1_4")["changes"] if c["kind"] in ("renamed_column", "unit_change")]
changes = [c for c in changes if c["column"] not in ("Creatinine_mgdl", "Creatinine")] + hidden
print(pl.DataFrame(changes))
U.check(any(c["kind"] == "unit_change" for c in changes), "the unit change hidden in a rename is caught")

# %% [markdown]
# 🔍 Run Lab 1.2's contract on version 2 in your head: `Creatinine_mgdl` is gone, so the column map
# fails loudly; that is good. The dangerous version is the one where Ufuq kept the old **name** and
# changed the unit: every type check passes and creatinine jumps 88-fold. Only the plausible-range
# rule of the contract (20 to 1,500 µmol/L) would notice, and only for some values.

# %% [markdown]
# ## 4 · Apply the policy: version, notice, approver (5')
#
# ✏️ **Exercise** · `decide(changes, policy, current)`: classify each change, then return the
# overall class (breaking if any change is), the next contract version, the notice period, the
# approvers, and the list of breaking changes.

# %%
def decide(changes: list[dict], policy: dict, current: str) -> dict:
    # BEGIN SOLUTION
    breaking = [c for c in changes if c["kind"] in policy["breaking"]]
    cls = "breaking" if breaking else "additive"
    major, minor, patch = map(int, current.split("."))
    nxt = f"{major + 1}.0.0" if policy["version_bump"][cls] == "major" else f"{major}.{minor + 1}.0"
    return {"class": cls, "current": current, "next_version": nxt, "notice_days": policy["notice_days"][cls],
            "approvers": policy["approvers"][cls], "breaking_changes": [f"{c['kind']}: {c['column']}" for c in breaking]}
    # END SOLUTION


# %%
try:
    decision = decide(changes, POLICY, CONTRACT["version"])
except NotImplementedError:
    decision = U.reference("lab_1_4")["decision"]
print(yaml.safe_dump(decision, sort_keys=False, allow_unicode=True))
U.check(decision["class"] == "breaking" and decision["next_version"] == "2.0.0", "Ufuq version 2 is a breaking change: contract 2.0.0")

# %% [markdown]
# ## 5 · One-page policy text (2')
#
# The evidence for this outcome is a one-page policy. Write it from `POLICY`, so the text and the data
# never disagree, and save it beside the change report.

# %%
d = U.lab_dir("D1_4")
lines = ["# Rimah encounter feed: change policy", "",
         f"Breaking changes ({', '.join(POLICY['breaking'])}) are announced {POLICY['notice_days']['breaking']} days ahead, "
         f"approved by {'; '.join(POLICY['approvers']['breaking'])}, and move the major version.",
         f"Additive changes ({', '.join(POLICY['additive'])}) are announced {POLICY['notice_days']['additive']} days ahead, "
         f"approved by {'; '.join(POLICY['approvers']['additive'])}, and move the minor version.",
         f"During a breaking change the producer sends both versions for {POLICY.get('parallel_run_days', 30)} days.",
         "A delivery that breaks the contract without notice is rejected and the producer re-sends it."]
(d / "policy.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
U.save_json({"changes": changes, "decision": decision}, d / "change_report.json")
print("\n".join(lines))

# %% [markdown]
# ## ✱ Stretch · The notice Ufuq should have sent
#
# Draft the deprecation notice: what changes, from which date, the contract version, the parallel
# run, and whom to contact. Keep it to six lines; the policy's numbers come from `POLICY`.

# %%
def notice() -> str:
    # BEGIN SOLUTION
    return "\n".join([
        "To: consumers of the Rimah encounter feed (contract rimah-encounter 1.0.0)",
        "From: Ufuq Medical Group, data engineering (Kinan Al-Rakhees)",
        f"What: Creatinine_mgdl becomes Creatinine in µmol/L; DOB becomes yyyy-mm-dd; DischargeStatus adds 5 (home health care); Nationality is added.",
        f"When: version 2 starts {POLICY['notice_days']['breaking']} days after this notice; both versions are sent for {POLICY.get('parallel_run_days', 30)} days.",
        "Contract: proposed 2.0.0, for approval by the consortium data board.",
        "Contact: the contract owner, through the consortium's data channel."])
    # END SOLUTION


try:
    print(notice())
except NotImplementedError:
    print("Stretch not attempted.")

# %% [markdown]
# ## Checkpoint
#
# 1. Ufuq adds a fifth discharge code. Why is a new value in a code set breaking for the study?
# 2. Which change in version 2 would have passed every type check if Ufuq had kept the column name?
# 3. Why does a breaking change get a parallel run and not only a notice?
#
# <details><summary>Answers</summary>
#
# 1. The study's mapping is closed: an unknown code becomes null or is dropped, and "home health care" discharges vanish from the rate.
# 2. The unit change of creatinine: a number is still a number.
# 3. Consumers can test their code on the new version against the old one before the old one stops.
# </details>
#
# **Carry forward.** `artifacts/D1_4/policy.md` and `change_report.json`.
