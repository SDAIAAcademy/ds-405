"""Write the reference results that the safety-net cells fall back to.

    uv run python _tools/make_references.py            # every lab
    uv run python _tools/make_references.py D1_1        # one lab

Each lab's source (labs/_src/<name>.py) holds the solution, so running it as a script computes the
reference result. This tool runs the source in quick mode and saves the variables listed in SPEC
to labs/data/reference/<key>.json. Run it after prepare_data.py and after changing a solution.
"""
from __future__ import annotations

import json
import os
import runpy
import shutil
import sys
from pathlib import Path

LABS = Path(__file__).resolve().parents[1]

# lab source prefix -> (reference key, {json field: global variable or callable on the globals})
SPEC = {
    "D1_1": ("lab_1_1", {"column_map": "COLUMN_MAP", "code_sets": "sets", "dx_shapes": "dx_shapes",
                         "weight": "weight", "creatinine": "creat", "register": "reg"}),
    "D1_2": ("lab_1_2", {"clauses": "clauses", "per_property": "per_property", "table_rules": "table_rules", "results": "results"}),
    "D1_3": ("lab_1_3", {"norm": "NORM_SAMPLE", "match": "match_table"}),
    "D1_4": ("lab_1_4", {"policy": "POLICY", "diff_changes": "diff_changes", "changes": "changes", "decision": "decision"}),
    "D2_1": ("lab_2_1", {"result": "lazy_result_sample"}),
    "D2_3": ("lab_2_3", {"rebuilt_fingerprint": "rebuilt_fp"}),
    "D2_4": ("lab_2_4", {"gates": "gates", "trace": "traced"}),
    "D3_1": ("lab_3_1", {"rare": "rare", "uniqueness": "uniq", "decisions": "decisions"}),
    "D3_3": ("lab_3_3", {"fidelity": "fidelity", "tstr": "tstr", "estimates": "estimates"}),
    "D3_4": ("lab_3_4", {"dcr": "dcr", "mia": "mia"}),
    "D4_1": ("lab_4_1", {"single": "single", "by_known": "by_known", "coarse": "coarse"}),
    "D4_2": ("lab_4_2", {"true_monthly": "true_monthly"}),
    "D4_3": ("lab_4_3", {"site_counts": "site_counts", "pooled": "pooled"}),
    "D4_4": ("lab_4_4", {"checklist": "checklist", "record": "record"}),
}

# outputs of a solution run that later labs start from
COPIES = {
    "D1_2": [("artifacts/D1_2/encounter.odcs.yaml", "data/contracts/encounter.v1.odcs.yaml")],
}


def to_json(v):
    try:
        import polars as pl
        if isinstance(v, pl.DataFrame):
            return v.to_dicts()
    except ImportError:
        pass
    if hasattr(v, "item") and not isinstance(v, (list, dict)):
        return v.item()
    return v


def run(prefix: str):
    key, fields = SPEC[prefix]
    src = next((LABS / "_src").glob(prefix + "_*.py"))
    os.chdir(LABS)
    sys.path.insert(0, str(LABS))
    g = runpy.run_path(str(src), run_name="__main__")
    out = {name: to_json(g[var]) for name, var in fields.items()}
    path = LABS / "data" / "reference" / f"{key}.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
    print("wrote", path.relative_to(LABS))
    for src_rel, dst_rel in COPIES.get(prefix, []):
        shutil.copyfile(LABS / src_rel, LABS / dst_rel)
        print("copied", dst_rel)


if __name__ == "__main__":
    os.environ.setdefault("RIMAH_QUICK", "1")
    for prefix in (sys.argv[1:] or list(SPEC)):
        run(prefix)
