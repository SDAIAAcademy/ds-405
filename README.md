<!-- academy:title -->
# Data Preparation at Scale: Contracts, Synthetic Data and Privacy

إعداد البيانات على نطاق واسع: عقود البيانات والبيانات الاصطناعية والخصوصية

Data Science Track · SDAIA Academy · DS-405 · Level 400

Contract and link several data producers, prepare 30 million rows idempotently on a laptop, and release health data only after measuring its utility and its risk

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
| Capstone | Capstone: a release package and its defence |  | [`slides/capstone.html`](slides/capstone.html) |
<!-- /academy:units -->

## Case study

**Rimah Health Data Consortium** (fictional). Rimah Health Data Consortium is a fictional consortium of three hospital groups (Sidra Hospitals, Ufuq Medical Group and Rawdah Hospitals) that send encounter, laboratory and pharmacy extracts for a 30-day readmission study, while a university partner asks for a copy. Participants contract and link the three producers, rebuild preparation as an incremental pipeline over partitioned columnar tables, generate and attack synthetic patient and encounter tables, spend a privacy budget over twelve monthly releases, pool a rate without pooling records, and write the release decision for the university. All data is synthetic, generated with a fixed seed, with planted identifiers and planted problems.

| Persona | Role |
|---|---|
| Dr. Fadwa Al-Qassabi | Consortium director; chairs the release board |
| Ghanem Al-Mutawakkil | Data protection officer; signs the release decision |
| Ihab Al-Qadi, Kinan Al-Rakhees, Ashjan Al-Essa | Data engineers of the three producers (Sidra, Ufuq, Rawdah) |
| Atiyah Al-Maghlouth | Epidemiologist who leads the readmission study |
| Prof. Adnan Al-Shuwaiman | University partner who requests a copy |
| Yousra Al-Dahmash | Data preparation and privacy engineer: the participant's role |

No lab calls a language model or downloads one; everything runs on a laptop processor or in Google Colab. The Day 2 lake is written on demand (30 million rows at full size, 1% with `RIMAH_QUICK=1`).

<!-- academy:labs -->
## Labs

Every lab is a notebook in `labs/`. Open it in Google Colab from the course page, or run it locally with `uv`. Exercises raise `NotImplementedError` until they are done; the reference versions are in `labs/solutions/`.

| | Session | Lab | File |
|---|---|---|---|
| 1.1 | Day 1 · Session 1 | Profile three producers | [`D1_1_profile_producers.ipynb`](labs/D1_1_profile_producers.ipynb) |
| 1.2 | Day 1 · Session 2 | One contract for three producers | [`D1_2_shared_contract.ipynb`](labs/D1_2_shared_contract.ipynb) |
| 1.3 | Day 1 · Session 3 | A keyed linkage identifier | [`D1_3_keyed_linkage.ipynb`](labs/D1_3_keyed_linkage.ipynb) |
| 1.4 | Day 1 · Session 4 | A breaking-change policy, tested | [`D1_4_breaking_changes.ipynb`](labs/D1_4_breaking_changes.ipynb) |
| 2.1 | Day 2 · Session 1 | From eager to lazy | [`D2_1_lazy_columnar.ipynb`](labs/D2_1_lazy_columnar.ipynb) |
| 2.2 | Day 2 · Session 2 | Load one day twice | [`D2_2_idempotent_load.ipynb`](labs/D2_2_idempotent_load.ipynb) |
| 2.3 | Day 2 · Session 3 | Rebuild last month | [`D2_3_table_snapshots.ipynb`](labs/D2_3_table_snapshots.ipynb) |
| 2.4 | Day 2 · Session 4 | Gates and lineage per partition | [`D2_4_gates_lineage.ipynb`](labs/D2_4_gates_lineage.ipynb) |
| 3.1 | Day 3 · Session 1 | Four requests, three options | [`D3_1_choose_method.ipynb`](labs/D3_1_choose_method.ipynb) |
| 3.2 | Day 3 · Session 2 | Two generators for related tables | [`D3_2_relational_generators.ipynb`](labs/D3_2_relational_generators.ipynb) |
| 3.3 | Day 3 · Session 3 | Train on synthetic, test on real | [`D3_3_synthetic_utility.ipynb`](labs/D3_3_synthetic_utility.ipynb) |
| 3.4 | Day 3 · Session 4 | Attack each synthetic table | [`D3_4_attack_synthetic.ipynb`](labs/D3_4_attack_synthetic.ipynb) |
| 4.1 | Day 4 · Session 1 | Sequences as quasi-identifiers | [`D4_1_longitudinal_risk.ipynb`](labs/D4_1_longitudinal_risk.ipynb) |
| 4.2 | Day 4 · Session 2 | Twelve months, one budget | [`D4_2_budget_ledger.ipynb`](labs/D4_2_budget_ledger.ipynb) |
| 4.3 | Day 4 · Session 3 | A pooled rate without pooled records | [`D4_3_secure_aggregation.ipynb`](labs/D4_3_secure_aggregation.ipynb) |
| 4.4 | Day 4 · Session 4 | The decision for the university | [`D4_4_release_decision.ipynb`](labs/D4_4_release_decision.ipynb) |
<!-- /academy:labs -->

## Capstone

A release package for one of three data requests (contracts, pipeline, protected or synthetic dataset with utility and attack report, release decision) in a public repository whose README reports measured results, defended in ten minutes

**Submission:** A public GitHub repository holding the release package for one of the three requests: the contracts and the pipeline that build the data, the protected or synthetic dataset with its utility and attack report, and the release decision record. Its README reports the measured results with the commands that reproduce them. Then a ten-minute defence, questions included, in which the participant re-runs one attack on a table the assessor chooses.

The three requests: **R-A**, the university partner's copy for readmission modelling; **R-B**, a teaching dataset for a public data challenge; **R-C**, monthly readmission statistics for a ministry dashboard. Each participant chooses one.

**Assessment.** Supervised entry and exit checks of fundamentals without AI assistance (20%); the capstone rubric: contracts and pipeline 25, synthetic data validation 25, privacy method and risk 25, release decision 15, reproducibility 10 (60%); the live defence of the release decision (20%). Passing: 70% overall and at least 60% on the capstone rubric. In the defence the participant re-runs one attack on a table the assessor chooses; run logs and commit history are the evidence of authorship.

**AI use.** AI off for the supervised checks and the first contract (Lab 1.2). In the other labs an AI tutor may explain errors but writes no generator or attack code. AI is allowed in full for the capstone, which is defended live.

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

### Contracts, pipelines and lineage

- [Open Data Contract Standard (ODCS), latest version](https://bitol-io.github.io/open-data-contract-standard/latest/)
- [ODCS: data quality section](https://bitol-io.github.io/open-data-contract-standard/latest/data-quality/)
- [Polars user guide: the lazy API](https://docs.pola.rs/user-guide/lazy/)
- [Polars user guide: streaming](https://docs.pola.rs/user-guide/concepts/streaming/)
- [Delta Lake for Python and Rust (delta-rs)](https://delta-io.github.io/delta-rs/)
- [DuckLake](https://ducklake.select/)
- [Apache Iceberg](https://iceberg.apache.org/)
- [OpenLineage: object model](https://openlineage.io/docs/spec/object-model)
- [Marquez](https://marquezproject.ai/)
- [Pandera](https://pandera.readthedocs.io/en/stable/)
- [Soda Core](https://github.com/sodadata/soda-core)
- [Delta Lake transaction log protocol](https://github.com/delta-io/delta/blob/master/PROTOCOL.md)
- [Apache Spark SQL: REPAIR TABLE](https://spark.apache.org/docs/latest/sql-ref-syntax-ddl-repair-table.html)
- [Apache Spark SQL: ALTER TABLE (ADD PARTITION)](https://spark.apache.org/docs/latest/sql-ref-syntax-ddl-alter-table.html)
- [Debezium: log-based change data capture features](https://debezium.io/documentation/reference/stable/features.html)

### Linkage, synthetic data and privacy

- [Schnell, Bachteler, Reiher: Privacy-preserving record linkage using Bloom filters (2009)](https://bmcmedinformdecismak.biomedcentral.com/articles/10.1186/1472-6947-9-41)
- [Stadler, Oprisanu, Troncoso: Synthetic Data, Anonymisation Groundhog Day (USENIX Security 2022)](https://www.usenix.org/conference/usenixsecurity22/presentation/stadler)
- [Nowok, Raab, Dibben: synthpop, bespoke creation of synthetic data in R (J. Stat. Softw. 2016)](https://www.jstatsoft.org/article/view/v074i11)
- [Synthetic Data Vault: HMASynthesizer](https://docs.sdv.dev/sdv/multi-table-data/modeling/synthesizers/hmasynthesizer)
- [synthcity](https://github.com/vanderschaarlab/synthcity)
- [Dwork and Roth: The Algorithmic Foundations of Differential Privacy](https://www.cis.upenn.edu/~aaroth/Papers/privacybook.pdf)
- [NIST SP 800-226: Guidelines for Evaluating Differential Privacy Guarantees](https://csrc.nist.gov/pubs/sp/800/226/final)
- [OpenDP documentation](https://docs.opendp.org/en/stable/)
- [Bonawitz et al.: Practical Secure Aggregation for Privacy-Preserving Machine Learning](https://eprint.iacr.org/2017/281)
- [ARX Data Anonymization Tool](https://arx.deidentifier.org/)
- [sdcMicro](https://sdctools.github.io/sdcMicro/)

### National references

- [Personal Data Protection Law](https://sdaia.gov.sa/en/SDAIA/about/Documents/PersonalDataProtectionLaw.pdf)
- [Implementing Regulation of the Personal Data Protection Law](https://sdaia.gov.sa/en/SDAIA/about/Documents/ImplementingRegulationPersonalDataProtectionLaw.pdf)
- [Personal Data Destruction, Anonymization and Pseudonymisation Guideline](https://sdaia.gov.sa/Documents/PersonalDataDestructionAnonymizationAndEncryptionGuideline.pdf)
- [General Rules for Secondary Use of Data](https://sdaia.gov.sa/Documents/GeneralRulesForSecondaryUseOfData_EN.pdf)
- [Data Sharing Policy (National Data Management Office)](https://sdaia.gov.sa/en/SDAIA/about/Documents/DataSharingPolicyEN.pdf)
- [Data Classification Policy (National Data Management Office)](https://sdaia.gov.sa/en/SDAIA/about/Documents/DataClassificationPolicy.pdf)
<!-- /academy:sources -->

### National references

- Personal Data Protection Law and its implementing regulations: <https://sdaia.gov.sa/en/SDAIA/about/Documents/PersonalDataProtectionLaw.pdf> and <https://sdaia.gov.sa/en/SDAIA/about/Documents/ImplementingRegulationPersonalDataProtectionLaw.pdf>
- SDAIA PDPL guideline on destruction, anonymisation and pseudonymisation of personal data: <https://sdaia.gov.sa/Documents/PersonalDataDestructionAnonymizationAndEncryptionGuideline.pdf>
- General Rules for Secondary Use of Data: <https://sdaia.gov.sa/Documents/GeneralRulesForSecondaryUseOfData_EN.pdf>
- NDMO Data Sharing Policy: <https://sdaia.gov.sa/en/SDAIA/about/Documents/DataSharingPolicyEN.pdf>
- NDMO Data Classification Policy: <https://sdaia.gov.sa/en/SDAIA/about/Documents/DataClassificationPolicy.pdf>
