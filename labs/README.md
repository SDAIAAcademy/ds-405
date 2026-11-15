# Data Preparation at Scale: Contracts, Synthetic Data and Privacy: labs

## Quick start

- Google Colab: open a notebook from the course page; its first cell clones this repository.
- Locally: clone the repository, then open the notebooks in `labs/` with Jupyter.

| Unit | Session | Notebook |
|---|---|---|
| Day 1 | Session 1 · Preparation breaks where producers disagree | [`D1_1_profile_producers.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D1_1_profile_producers.ipynb) |
| Day 1 | Session 2 · One contract, three producers | [`D1_2_shared_contract.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D1_2_shared_contract.ipynb) |
| Day 1 | Session 3 · Linking patients across producers | [`D1_3_keyed_linkage.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D1_3_keyed_linkage.ipynb) |
| Day 1 | Session 4 · Versions and breaking changes | [`D1_4_breaking_changes.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D1_4_breaking_changes.ipynb) |
| Day 2 | Session 1 · Columnar files and lazy execution | [`D2_1_lazy_columnar.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D2_1_lazy_columnar.ipynb) |
| Day 2 | Session 2 · Incremental and idempotent loads | [`D2_2_idempotent_load.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D2_2_idempotent_load.ipynb) |
| Day 2 | Session 3 · Tables with history | [`D2_3_table_snapshots.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D2_3_table_snapshots.ipynb) |
| Day 2 | Session 4 · Gates and lineage at scale | [`D2_4_gates_lineage.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D2_4_gates_lineage.ipynb) |
| Day 3 | Session 1 · When synthetic data fits | [`D3_1_choose_method.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D3_1_choose_method.ipynb) |
| Day 3 | Session 2 · Generating related tables | [`D3_2_relational_generators.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D3_2_relational_generators.ipynb) |
| Day 3 | Session 3 · Utility is measured against the analysis | [`D3_3_synthetic_utility.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D3_3_synthetic_utility.ipynb) |
| Day 3 | Session 4 · Privacy is measured by attack | [`D3_4_attack_synthetic.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D3_4_attack_synthetic.ipynb) |
| Day 4 | Session 1 · Disclosure risk in longitudinal records | [`D4_1_longitudinal_risk.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D4_1_longitudinal_risk.ipynb) |
| Day 4 | Session 2 · Privacy budgets over many releases | [`D4_2_budget_ledger.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D4_2_budget_ledger.ipynb) |
| Day 4 | Session 3 · Analysis without pooling records | [`D4_3_secure_aggregation.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D4_3_secure_aggregation.ipynb) |
| Day 4 | Session 4 · The release decision | [`D4_4_release_decision.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D4_4_release_decision.ipynb) |

The notebooks are generated from the percent-format sources in `labs/_src/` by `labs/_tools/py2nb.py` (`uv run python _tools/py2nb.py` from `labs/`), which also writes the solutions to `labs/solutions/`. Edit the sources, not the notebooks.
