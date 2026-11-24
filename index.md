---
course: "Data Preparation at Scale: Contracts, Synthetic Data and Privacy"
code: "DS-405"
version: "2027.2.0"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ds-405/index.html"
---

# Data Preparation at Scale: Contracts, Synthetic Data and Privacy

إعداد البيانات على نطاق واسع: عقود البيانات والبيانات الاصطناعية والخصوصية

Data Science Track · 4 teaching days + capstone day · 26 hours · Level 400

Contract and link several data producers, prepare 30 million rows idempotently on a laptop, and release health data only after measuring its utility and its risk

Participants run data preparation for the fictional Rimah Health Data Consortium: three hospital groups send encounter, laboratory and pharmacy extracts (about 30 million synthetic rows) for a readmission study, and a university partner wants a copy. They contract and link the producers, rebuild preparation as an incremental pipeline over partitioned columnar tables, generate and attack synthetic versions, compare privacy-enhancing methods for four requests, and write a release decision a privacy officer could sign. Single-table contracts come from DS-311; de-identification and basic differential privacy from DS-309.

**Who it is for:** Specialists. Data scientists who have completed the level 300 core and practicum, or can show equivalent work: an analysis they led from question to recommendation and defended.

**Format:** Intensive: 4 teaching days of four sessions and a capstone day, with guided pre-work and a tracked follow-up task

## The case study

**Rimah Health Data Consortium.** Rimah Health Data Consortium is a fictional consortium of three hospital groups (Sidra Hospitals, Ufuq Medical Group and Rawdah Hospitals) that send encounter, laboratory and pharmacy extracts for a 30-day readmission study, while a university partner asks for a copy. Participants contract and link the three producers, rebuild preparation as an incremental pipeline over partitioned columnar tables, generate and attack synthetic patient and encounter tables, spend a privacy budget over twelve monthly releases, pool a rate without pooling records, and write the release decision for the university. All data is synthetic, generated with a fixed seed, with planted identifiers and planted problems.

## The course

### Day 1: Contract the producers

Slides: https://sdaiaacademy.github.io/ds-405/slides/day1.md

- **Session 1: Preparation breaks where producers disagree**
  - Profile several extracts of the same entity side by side
  - Classify each disagreement as schema, code, unit or identifier
  - Write a disagreement register that a contract can resolve
  - [Lab 1.1: Profile three producers (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D1_1_profile_producers.ipynb)
- **Session 2: One contract, three producers**
  - Write a data contract in ODCS v3.2.0 for an entity with several producers
  - Express code maps and unit conversions as contract clauses
  - Run the contract against every producer and read which clause failed
  - [Lab 1.2: One contract for three producers (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D1_2_shared_contract.ipynb)
- **Session 3: Linking patients across producers**
  - Explain why a plain hash of a national identifier is not a pseudonym
  - Compute a keyed-hash linkage key at each producer after normalisation
  - Measure precision and recall of the linkage against a known truth
  - [Lab 1.3: A keyed linkage identifier (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D1_3_keyed_linkage.ipynb)
- **Session 4: Versions and breaking changes**
  - Classify schema and meaning changes as breaking or additive
  - Write a breaking-change policy with notice periods and approvers
  - Test the policy on a seeded producer change and decide the new version
  - [Lab 1.4: A breaking-change policy, tested (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D1_4_breaking_changes.ipynb)

### Day 2: Prepare at scale

Slides: https://sdaiaacademy.github.io/ds-405/slides/day2.md

- **Session 1: Columnar files and lazy execution**
  - Explain projection and predicate pushdown into partitioned Parquet
  - Rewrite an eager cleaning script as a lazy query
  - Measure wall time and peak memory of both on the same data
  - [Lab 2.1: From eager to lazy (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D2_1_lazy_columnar.ipynb)
- **Session 2: Incremental and idempotent loads**
  - Show that an append load is not idempotent
  - Make a daily load idempotent by partition overwrite or merge
  - Prove idempotence by loading one day twice and comparing table hashes
  - Choose log-based change data capture or a full reload for a source, from how often it is copied, how much changes and whether rows are deleted
  - [Lab 2.2: Load one day twice (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D2_2_idempotent_load.ipynb)
- **Session 3: Tables with history**
  - Read an earlier version of a table by version number
  - Rebuild an analysis set exactly from the recorded version
  - Explain what retention and vacuuming do to time travel
  - Diagnose data that was written but is not found, and register it through the table or its catalog
  - [Lab 2.3: Rebuild last month (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D2_3_table_snapshots.ipynb)
- **Session 4: Gates and lineage at scale**
  - Run blocking rules per partition and quarantine the failures
  - Emit OpenLineage run events for every job run
  - Trace a defect in an output to its producer and partition
  - [Lab 2.4: Gates and lineage per partition (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D2_4_gates_lineage.ipynb)

### Day 3: Synthesise and attack

Slides: https://sdaiaacademy.github.io/ds-405/slides/day3.md

- **Session 1: When synthetic data fits**
  - State what synthetic data can and cannot support
  - Compare synthetic data, a de-identified extract and a query service for a request
  - Record the residual risk of each option in a decision table
  - [Lab 3.1: Four requests, three options (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D3_1_choose_method.ipynb)
- **Session 2: Generating related tables**
  - Explain why tables generated separately break the parent-child relation
  - Fit a baseline generator and a conditional-tree generator to two related tables
  - Check referential integrity and child counts of the synthetic tables
  - [Lab 3.2: Two generators for related tables (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D3_2_relational_generators.ipynb)
- **Session 3: Utility is measured against the analysis**
  - Compute marginal and pairwise fidelity of a synthetic table
  - Score analytical utility by training on synthetic and testing on real data
  - Compare the study's key estimate on real and synthetic data
  - [Lab 3.3: Train on synthetic, test on real (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D3_3_synthetic_utility.ipynb)
- **Session 4: Privacy is measured by attack**
  - Compute distance-to-closest-record against a holdout baseline
  - Run a membership-inference test and read its AUC
  - Attack each synthetic table and the linked patient histories
  - [Lab 3.4: Attack each synthetic table (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D3_4_attack_synthetic.ipynb)

### Day 4: Protect and decide

Slides: https://sdaiaacademy.github.io/ds-405/slides/day4.md

- **Session 1: Disclosure risk in longitudinal records**
  - Measure uniqueness of encounter sequences as quasi-identifiers
  - Compare longitudinal risk with the single-table estimate
  - Reduce the risk by coarsening and truncation and measure the cost
  - [Lab 4.1: Sequences as quasi-identifiers (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D4_1_longitudinal_risk.ipynb)
- **Session 2: Privacy budgets over many releases**
  - Bound each person's contribution to a monthly statistic
  - Allocate one budget across twelve releases and keep a ledger
  - Plot error against budget and show why re-releases must be charged
  - [Lab 4.2: Twelve months, one budget (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D4_2_budget_ledger.ipynb)
- **Session 3: Analysis without pooling records**
  - Explain federated analysis, secure aggregation and clean rooms
  - Compute a pooled rate with a simulated secure-aggregation protocol
  - Identify what the pooled output still discloses
  - [Lab 4.3: A pooled rate without pooled records (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D4_3_secure_aggregation.ipynb)
- **Session 4: The release decision**
  - Test a data request against the sharing policy and the secondary-use rules
  - Write a release decision with method, residual risk, conditions and approver
  - Defend the decision against the strongest objection
  - [Lab 4.4: The decision for the university (25 min)](https://sdaiaacademy.github.io/ds-405/labs/D4_4_release_decision.ipynb)

### Capstone: Capstone: a release package and its defence

Slides: https://sdaiaacademy.github.io/ds-405/slides/capstone.md

## Capstone

A release package for one of three data requests (contracts, pipeline, protected or synthetic dataset with utility and attack report, release decision) in a public repository whose README reports measured results, defended in ten minutes

**What you submit:** A public GitHub repository holding the release package for one of the three requests: the contracts and the pipeline that build the data, the protected or synthetic dataset with its utility and attack report, and the release decision record. Its README reports the measured results with the commands that reproduce them. Then a ten-minute defence, questions included, in which the participant re-runs one attack on a table the assessor chooses.

**Rubric:**

- Contracts and pipeline: 25%
- Synthetic data validation: 25%
- Privacy method and risk: 25%
- Release decision: 15%
- Reproducibility: 10%

## Outcomes

- **LO1** Design shared data contracts, a pseudonymous linkage key and a breaking-change policy for a feed with several producers, given three producers whose extracts disagree on schema, codes and units (Performance) Evidence: contracts checked against all three producers, a linkage match rate measured against the planted truth, and a one-page policy
- **LO2** Implement an incremental, idempotent preparation pipeline over partitioned columnar tables with quality gates, given 30 million synthetic rows on a laptop (Applied) Evidence: identical output when a day is re-run, with time and memory measured
- **LO3** Evaluate a synthetic dataset for fidelity, analytical utility and disclosure risk, given two generators fitted to related patient and encounter tables (Performance) Evidence: a report with train-on-synthetic, test-on-real scores and attack results
- **LO4** Compute differentially private statistics under a budget shared across repeated releases, given twelve monthly statistics (Applied) Evidence: a budget ledger and a plot of error against budget
- **LO5** Select a privacy-enhancing method for each data request by comparing protection, utility and cost, given four requests, from an internal analyst to an external university (Performance) Evidence: a decision table stating the residual risk of each option
- **LO6** Decide whether to release a dataset and on what conditions, and defend the decision, given the university request and the measured results (Performance) Evidence: a release decision record defended live

## Tools

- **Larger-than-memory processing:** Polars, DuckDB
- **Open table format:** Apache Iceberg, Delta Lake, DuckLake
- **Data contracts and validation:** Open Data Contract Standard (ODCS), Pandera, Soda Core
- **Lineage events:** OpenLineage with Marquez, the orchestrator's built-in lineage
- **Synthetic relational data:** synthcity, Synthetic Data Vault
- **Disclosure risk and differential privacy:** ARX, sdcMicro, OpenDP

## Prerequisites

- DS-309 Responsible Data Science: Privacy, Fairness and Documentation
- Writes SQL with window functions and cleans data with a data-frame library
- Has written a data contract and blocking quality rules for one table (DS-311 or equivalent)
- Setup: a laptop CPU with uv, or Google Colab. No model and no API key is needed. Run 00_setup_check before Day 1; see labs/README.md.

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

---

SDAIA Academy · Data Science Track · Data Preparation at Scale: Contracts, Synthetic Data and Privacy

Course version 2027.2.0 · engine 1.0.0 · built 2026-11-24 · commit f643328
