# Data Preparation at Scale: Contracts, Synthetic Data and Privacy: labs

## Quick start

- Google Colab: open a notebook from the course page; its first cell clones this repository.
- Locally: clone the repository, then open the notebooks in `labs/` with Jupyter.

| Unit | Session | Notebook |
|---|---|---|
| Day 1 | Session 1 · Preparation breaks where producers disagree | [`D1_1_profile_three_producers.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D1_1_profile_three_producers.ipynb) |
| Day 1 | Session 2 · One contract, three producers | [`D1_2_write_shared_contract.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D1_2_write_shared_contract.ipynb) |
| Day 1 | Session 3 · Linking patients across producers | [`D1_3_generate_keyed_hash.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D1_3_generate_keyed_hash.ipynb) |
| Day 1 | Session 4 · Versions and breaking changes | [`D1_4_draft_policy_what.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D1_4_draft_policy_what.ipynb) |
| Day 2 | Session 1 · Columnar files and lazy execution | [`D2_1_rewrite_eager_cleaning.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D2_1_rewrite_eager_cleaning.ipynb) |
| Day 2 | Session 2 · Incremental and idempotent loads | [`D2_2_make_daily_load.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D2_2_make_daily_load.ipynb) |
| Day 2 | Session 3 · Tables with history | [`D2_3_rebuild_last_month.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D2_3_rebuild_last_month.ipynb) |
| Day 2 | Session 4 · Gates and lineage at scale | [`D2_4_run_blocking_rules.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D2_4_run_blocking_rules.ipynb) |
| Day 3 | Session 1 · When synthetic data fits | [`D3_1_decide_four_requests.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D3_1_decide_four_requests.ipynb) |
| Day 3 | Session 2 · Generating related tables | [`D3_2_fit_two_generators.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D3_2_fit_two_generators.ipynb) |
| Day 3 | Session 3 · Utility is measured against the analysis | [`D3_3_train_readmission_model.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D3_3_train_readmission_model.ipynb) |
| Day 3 | Session 4 · Privacy is measured by attack | [`D3_4_run_distance_closest.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D3_4_run_distance_closest.ipynb) |
| Day 4 | Session 1 · Disclosure risk in longitudinal records | [`D4_1_measure_re_identification.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D4_1_measure_re_identification.ipynb) |
| Day 4 | Session 2 · Privacy budgets over many releases | [`D4_2_allocate_budget_across.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D4_2_allocate_budget_across.ipynb) |
| Day 4 | Session 3 · Analysis without pooling records | [`D4_3_compute_cross_site.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D4_3_compute_cross_site.ipynb) |
| Day 4 | Session 4 · The release decision | [`D4_4_draft_decision_university.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ds-405/blob/main/labs/D4_4_draft_decision_university.ipynb) |

The notebooks are generated from the percent-format sources in `labs/_src/` by `labs/_tools/py2nb.py` (`uv run python _tools/py2nb.py` from `labs/`), which also writes the solutions to `labs/solutions/`. Edit the sources, not the notebooks.
