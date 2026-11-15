<!-- academy:title -->
# Data Preparation at Scale: Contracts, Synthetic Data and Privacy

إعداد البيانات على نطاق واسع: عقود البيانات والبيانات الاصطناعية والخصوصية

Data Science Track · SDAIA Academy · DS-405 · Level 400

REPLACE: one line under the title: what participants can do after the course

Participants run data preparation for the fictional Rimah Health Data Consortium: three hospital groups send encounter, laboratory and pharmacy extracts (about 30 million synthetic rows) for a readmission study, and a university partner wants a copy. They contract and link the producers, rebuild preparation as an incremental pipeline over partitioned columnar tables, generate and attack synthetic versions, compare privacy-enhancing methods for four requests, and write a release decision a privacy officer could sign. Single-table contracts come from DS-311; de-identification and basic differential privacy from DS-309.

**Format:** Intensive: 4 teaching days of four sessions and a capstone day, with guided pre-work and a tracked follow-up task

**Course page:** https://sdaiaacademy.github.io/ds-405/
<!-- /academy:title -->

## Outcomes

| | Outcomes | Level | Evidence |
|---|---|---|---|
| LO1 | Design shared data contracts, a pseudonymous linkage key and a breaking-change policy for a feed with several producers, given three producers whose extracts disagree on schema, codes and units | Performance | contracts checked against all three producers, a linkage match rate measured against the planted truth, and a one-page policy |
| LO2 | Implement an incremental, idempotent preparation pipeline over partitioned columnar tables with quality gates, given 30 million synthetic rows on a laptop | Applied | identical output when a day is re-run, with time and memory measured |
| LO3 | Evaluate a synthetic dataset for fidelity, analytical utility and disclosure risk, given two generators fitted to related patient and encounter tables | Performance | a report with train-on-synthetic, test-on-real scores and attack results |
| LO4 | Compute differentially private statistics under a budget shared across repeated releases, given twelve monthly statistics | Applied | a budget ledger and a plot of error against budget |
| LO5 | Select a privacy-enhancing method for each data request by comparing protection, utility and cost, given four requests, from an internal analyst to an external university | Performance | a decision table stating the residual risk of each option |
| LO6 | Decide whether to release a dataset and on what conditions, and defend the decision, given the university request and the measured results | Performance | a release decision record defended live |

<!-- academy:units -->
## Units

| Unit | Title | Sessions | Slides |
|---|---|---|---|
| Day 1 | Contract the producers | Preparation breaks where producers disagree; One contract, three producers; Linking patients across producers; Versions and breaking changes | [`slides/day1.html`](slides/day1.html) |
| Day 2 | Prepare at scale | Columnar files and lazy execution; Incremental and idempotent loads; Tables with history; Gates and lineage at scale | [`slides/day2.html`](slides/day2.html) |
| Day 3 | Synthesise and attack | When synthetic data fits; Generating related tables; Utility is measured against the analysis; Privacy is measured by attack | [`slides/day3.html`](slides/day3.html) |
| Day 4 | Protect and decide | Disclosure risk in longitudinal records; Privacy budgets over many releases; Analysis without pooling records; The release decision | [`slides/day4.html`](slides/day4.html) |
| Capstone | Capstone project presentations |  | [`slides/capstone.html`](slides/capstone.html) |
<!-- /academy:units -->

## Case study

**REPLACE: the name of the fictional organisation every lab works on.** REPLACE: two sentences on the case study and its synthetic data

<!-- academy:labs -->
## Labs

Every lab is a notebook in `labs/`. Open it in Google Colab from the course page, or run it locally with `uv`. Exercises raise `NotImplementedError` until they are done; the reference versions are in `labs/solutions/`.

| | Session | Lab | File |
|---|---|---|---|
| 1.1 | Day 1 · Session 1 | Profile three producers' encounter extracts and list where schema, codes and units disagree | [`D1_1_profile_three_producers.ipynb`](labs/D1_1_profile_three_producers.ipynb) |
| 1.2 | Day 1 · Session 2 | Write a shared contract in an open standard with code mappings, unit rules and freshness, and run it against all three extracts | [`D1_2_write_shared_contract.ipynb`](labs/D1_2_write_shared_contract.ipynb) |
| 1.3 | Day 1 · Session 3 | Generate a keyed-hash linkage identifier at each producer and measure the match rate against the planted truth | [`D1_3_generate_keyed_hash.ipynb`](labs/D1_3_generate_keyed_hash.ipynb) |
| 1.4 | Day 1 · Session 4 | Draft the policy (what counts as breaking, notice periods, who approves) and test it on a seeded producer change | [`D1_4_draft_policy_what.ipynb`](labs/D1_4_draft_policy_what.ipynb) |
| 2.1 | Day 2 · Session 1 | Rewrite an eager cleaning script as a lazy query over partitioned files and compare time and memory | [`D2_1_rewrite_eager_cleaning.ipynb`](labs/D2_1_rewrite_eager_cleaning.ipynb) |
| 2.2 | Day 2 · Session 2 | Make the daily load idempotent and prove it by loading one day twice | [`D2_2_make_daily_load.ipynb`](labs/D2_2_make_daily_load.ipynb) |
| 2.3 | Day 2 · Session 3 | Rebuild last month's analysis set from a table snapshot | [`D2_3_rebuild_last_month.ipynb`](labs/D2_3_rebuild_last_month.ipynb) |
| 2.4 | Day 2 · Session 4 | Run blocking rules per partition and trace a seeded defect to its producer and partition through lineage events | [`D2_4_run_blocking_rules.ipynb`](labs/D2_4_run_blocking_rules.ipynb) |
| 3.1 | Day 3 · Session 1 | Decide for four requests between synthetic data, a de-identified extract and a query service | [`D3_1_decide_four_requests.ipynb`](labs/D3_1_decide_four_requests.ipynb) |
| 3.2 | Day 3 · Session 2 | Fit two generators to the patient and encounter tables, keeping the parent-child relation | [`D3_2_fit_two_generators.ipynb`](labs/D3_2_fit_two_generators.ipynb) |
| 3.3 | Day 3 · Session 3 | Train the readmission model on synthetic data, test on real data and compare | [`D3_3_train_readmission_model.ipynb`](labs/D3_3_train_readmission_model.ipynb) |
| 3.4 | Day 3 · Session 4 | Run distance-to-closest-record and membership-inference tests on each synthetic table | [`D3_4_run_distance_closest.ipynb`](labs/D3_4_run_distance_closest.ipynb) |
| 4.1 | Day 4 · Session 1 | Measure re-identification risk when encounter sequences act as quasi-identifiers and compare it with the single-table estimate | [`D4_1_measure_re_identification.ipynb`](labs/D4_1_measure_re_identification.ipynb) |
| 4.2 | Day 4 · Session 2 | Allocate a budget across twelve monthly statistics and plot error against budget | [`D4_2_allocate_budget_across.ipynb`](labs/D4_2_allocate_budget_across.ipynb) |
| 4.3 | Day 4 · Session 3 | Compute a cross-site readmission rate with a simulated secure-aggregation protocol | [`D4_3_compute_cross_site.ipynb`](labs/D4_3_compute_cross_site.ipynb) |
| 4.4 | Day 4 · Session 4 | Draft the decision for the university request: method, residual risk, conditions, approver | [`D4_4_draft_decision_university.ipynb`](labs/D4_4_draft_decision_university.ipynb) |
<!-- /academy:labs -->

## Capstone

A release package for one of three data requests (contracts, pipeline, protected or synthetic dataset with utility and attack report, release decision) in a public repository whose README reports measured results, defended in ten minutes

**Submission:** REPLACE: what participants submit and how: a public repository link, or a shared folder for a course without code

## Prerequisites

- DS-309 Responsible Data Science: Privacy, Fairness and Documentation
- Writes SQL with window functions and cleans data with a data-frame library
- Has written a data contract and blocking quality rules for one table (DS-311 or equivalent)

<!-- academy:tools -->
## Tools

Each line is a capability; the examples are interchangeable.

- **Larger-than-memory processing:** Polars, DuckDB
- **Open table format:** Apache Iceberg, Delta Lake, DuckLake
- **Data contracts and validation:** Open Data Contract Standard (ODCS), Pandera, Soda Core
- **Lineage events:** OpenLineage with Marquez, the orchestrator's built-in lineage
- **Synthetic relational data:** synthcity, Synthetic Data Vault
- **Disclosure risk and differential privacy:** ARX, sdcMicro, OpenDP
<!-- /academy:tools -->

<!-- academy:sources -->
## Sources

- REPLACE: every source the course cites, with its address, in course.json under "sources"; this list is written from there
<!-- /academy:sources -->

### National references

- Personal Data Protection Law and its implementing regulations: REPLACE: the address of the official text
- SDAIA PDPL guideline on destruction, anonymisation and pseudonymisation of personal data: REPLACE: the address of the official text
- General Rules for Secondary Use of Data: REPLACE: the address of the official text
- NDMO Data Sharing Policy: REPLACE: the address of the official text
- NDMO Data Classification Policy: REPLACE: the address of the official text
