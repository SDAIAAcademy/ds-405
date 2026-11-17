---
course: "Data Preparation at Scale: Contracts, Synthetic Data and Privacy"
code: "DS-405"
version: "2027.1.0"
scope: "course"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ds-405/"
---

# Data Preparation at Scale: Contracts, Synthetic Data and Privacy

Contract and link several data producers, prepare 30 million rows idempotently on a laptop, and release health data only after measuring its utility and its risk

Participants run data preparation for the fictional Rimah Health Data Consortium: three hospital groups send encounter, laboratory and pharmacy extracts (about 30 million synthetic rows) for a readmission study, and a university partner wants a copy. They contract and link the producers, rebuild preparation as an incremental pipeline over partitioned columnar tables, generate and attack synthetic versions, compare privacy-enhancing methods for four requests, and write a release decision a privacy officer could sign. Single-table contracts come from DS-311; de-identification and basic differential privacy from DS-309.

- **Audience:** Specialists. Data scientists who have completed the level 300 core and practicum, or can show equivalent work: an analysis they led from question to recommendation and defended.
- **Prerequisites:** DS-309 Responsible Data Science: Privacy, Fairness and Documentation; Writes SQL with window functions and cleans data with a data-frame library; Has written a data contract and blocking quality rules for one table (DS-311 or equivalent); Setup: a laptop CPU with uv, or Google Colab. No model and no API key is needed. Run 00_setup_check before Day 1; see labs/README.md.
- **Case study:** Rimah Health Data Consortium: Rimah Health Data Consortium is a fictional consortium of three hospital groups (Sidra Hospitals, Ufuq Medical Group and Rawdah Hospitals) that send encounter, laboratory and pharmacy extracts for a 30-day readmission study, while a university partner asks for a copy. Participants contract and link the three producers, rebuild preparation as an incremental pipeline over partitioned columnar tables, generate and attack synthetic patient and encounter tables, spend a privacy budget over twelve monthly releases, pool a rate without pooling records, and write the release decision for the university. All data is synthetic, generated with a fixed seed, with planted identifiers and planted problems.

## Outcomes

- LO1 (Performance): Design shared data contracts, a pseudonymous linkage key and a breaking-change policy for a feed with several producers, given three producers whose extracts disagree on schema, codes and units
- LO2 (Applied): Implement an incremental, idempotent preparation pipeline over partitioned columnar tables with quality gates, given 30 million synthetic rows on a laptop
- LO3 (Performance): Evaluate a synthetic dataset for fidelity, analytical utility and disclosure risk, given two generators fitted to related patient and encounter tables
- LO4 (Applied): Compute differentially private statistics under a budget shared across repeated releases, given twelve monthly statistics
- LO5 (Performance): Select a privacy-enhancing method for each data request by comparing protection, utility and cost, given four requests, from an internal analyst to an external university
- LO6 (Performance): Decide whether to release a dataset and on what conditions, and defend the decision, given the university request and the measured results

## Day 1: Contract the producers

Three producers, one contract, one linkage key, one change policy

#### [day1#title] Contract the producers

*SDAIA Academy · Data Preparation at Scale: Contracts, Synthetic Data and Privacy*

Day 1: Three producers, one contract, one linkage key, one change policy

Data Science Track · 4 teaching days + capstone day · 4 sessions · 4 labs · DS-405

#### [day1#agenda] Contract the producers

*Today*

- **Session 1 · Preparation breaks where producers disagree**: Where three producers disagree on names, formats, codes, units and identifiers, found by profiling before mapping
- **Session 2 · One contract, three producers**: A shared contract in the Open Data Contract Standard with code maps, unit rules, quality rules and freshness, run on every producer
- **Session 3 · Linking patients across producers**: Keyed pseudonyms computed at each producer, normalised first, measured against a planted truth
- **Session 4 · Versions and breaking changes**: Versions for contracts, what counts as breaking, notice periods and approvers, tested on a real producer change

### Session 1: Preparation breaks where producers disagree

#### [day1#s1] Preparation breaks where producers disagree

*Session 1*

- Profile several extracts of the same entity side by side
- Classify each disagreement as schema, code, unit or identifier
- Write a disagreement register that a contract can resolve

#### [day1#rimah-case] Rimah pools three hospital groups for one readmission study

*The case this week*

- **Sidra Hospitals.** 3,850 encounters this quarter. Ihab Al-Qadi runs the extract.
- **Ufuq Medical Group.** 3,216 rows. Kinan Al-Rakhees runs the extract.
- **Rawdah Hospitals.** 3,252 rows. Ashjan Al-Essa runs the extract.

- **The consumer:** Atiyah Al-Maghlouth's 30-day readmission study, and next month a university partner.
- **Your role:** Yousra Al-Dahmash, the consortium's data preparation and privacy engineer.

#### [day1#duties] Producers promise; the consumer states what it needs

*Who owes what*

- **The producer owes.** The agreed columns, codes and units; deliveries on time; notice before a change; an answer when a delivery fails a rule.
- **The consumer owes.** A written statement of what the analysis needs; the rules it will apply; no silent "fixes" of a producer's data downstream.

> **What goes wrong.** Each consumer quietly repairs each producer in its own code. Three studies, three different repairs, and nobody tells the producer.

#### [day1#four-kinds] Four kinds of disagreement, each fixed in a different place

*Where producers disagree*

| Kind | At Rimah | Fixed by |
| --- | --- | --- |
| **Schema**: names, formats | `AdmissionDate` as dd/mm/yyyy at Ufuq | a column map and a parse rule |
| **Codes**: the same idea, other values | sex as M/F, Male/Female, 1/2 | a code map the producer confirms |
| **Units**: the same number, other scale | weight in pounds at Rawdah | a unit factor in the contract |
| **Identifiers**: the same person, other spelling | `SA-` prefix, spaces, Arabic-Indic digits | normalisation before linkage (session 3) |

#### [day1#profile-first] Read every column as text before you trust a type

*Lab 1.1 · step 1*

```python
# file: Lab 1.1
raw = {p: U.load(f) for p, f in FILES.items()}
# U.load reads CSV with infer_schema=False:
# every column is a string until you decide
```

- Rawdah's `enc_id` is `0000001`: read as a number, it becomes 1.
- Ufuq's `01/10/2025` is 1 October; a guessing reader may say 10 January.
- Profiling on text shows what is there, not what a reader assumed.

#### [day1#units-in-distribution] A unit difference hides in the distribution, not in the type

*Lab 1.1 · step 4*

| Median at | Sidra | Ufuq | Rawdah |
| --- | --- | --- | --- |
| Weight column | 78.3 | 78.1 | 171.7 |
| Creatinine column | 89.9 | 1.00 | 89.7 |

> **Rawdah: pounds.** 171.7 / 78.3 is 2.2, the kg-to-lb factor.

> **Ufuq: mg/dL.** 89.9 / 1.00 is about 90, close to 88.4, the mg/dL-to-µmol/L factor.

#### [day1#codes-differ] Compare the shape of codes, not only their values

*Lab 1.1 · step 3*

- **Sidra.** `I50.9`: shape `A99.9`
- **Ufuq.** `I509`: the dot is gone
- **Rawdah.** `i50.9`: lower case

A join of diagnosis codes across the three returns Sidra's rows only. Nothing errors; the study shrinks by two thirds.

#### [day1#register] The disagreement register is the contract's to-do list

*Lab 1.1 · step 5*

**18** disagreements in the reference register

| Kind | Rows |
| --- | --- |
| code | 6 |
| format | 6 |
| schema, identifier, unit | 2 each |

Each row: field, producer, kind, what you saw, the fix. Rows marked "confirm" go to the producer before the contract is signed.

#### [day1#check-units] A check that passes

*Checkpoint*

**Question:** All three producers' weight columns pass "a number between 1 and 500". What do you do before pooling them?

- A. Pool them: the rule passed for every producer
- B. Divide Rawdah's values by 2.2 in the study notebook
- C. Compare the distributions by producer and confirm the unit with each producer
- D. Drop weight from the study

#### [day1#lab-1-1] Profile three producers

Lab 1.1 · 25 min

Profile the encounter extracts of Sidra, Ufuq and Rawdah side by side and write a register of where schema, codes, units and identifiers disagree.

[D1_1_profile_producers.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D1_1_profile_producers.ipynb)

- [ ] Load the three extracts and compare their columns (5 min)
- [ ] Match columns to the study's fields (5 min)
- [ ] Compare code sets: sex, diagnosis, disposition (6 min)
- [ ] Find the unit differences from the distributions (5 min)
- [ ] Write the disagreement register (4 min)
- [ ] ✱ Stretch: Find the identifier formats that would break a join

### Session 2: One contract, three producers

#### [day1#s2] One contract, three producers

*Session 2*

- Write a data contract in ODCS v3.2.0 for an entity with several producers
- Express code maps and unit conversions as contract clauses
- Run the contract against every producer and read which clause failed

#### [day1#contract-promises] A contract promises meaning, not only columns

*A contract*

- **Schema:** names, types, required fields, keys.
- **Meaning:** code sets, units, plausible ranges.
- **Quality:** rules every delivery must pass.
- **Service:** freshness and frequency.
- **People:** the owner, the consumers, who approves a change.

- **The test.** If Rawdah sent pounds tomorrow, would the contract say it was wrong? A list of typed columns would not.

#### [day1#odcs-anatomy] ODCS v3.2.0: the contract is a YAML document anyone can read

*An open standard*

```yaml
# file: data/contracts/encounter.skeleton.odcs.yaml
apiVersion: v3.2.0
kind: DataContract
id: rimah-encounter
version: 0.1.0
schema:
  - name: encounter
    properties:
      - name: weight_kg
        logicalType: number
        description: Body weight in kilograms.
slaProperties:
  - property: latency
    value: 2
    unit: d
```

#### [day1#producer-clauses] Each producer's differences become clauses in the one contract

*Lab 1.2 · step 2*

```yaml
# file: customProperties: producers
UFQ:
  columns: {admit_date: AdmissionDate, creatinine_umol_l: Creatinine_mgdl}
  date_formats: {admit_date: "%d/%m/%Y"}
  codes: {sex: {Male: M, Female: F}, disposition: {"1": HOME, "3": DIED}}
  transforms: {primary_dx: icd10_dot}
  units: {creatinine_umol_l: 88.42}
RWD:
  units: {weight_kg: 0.453592}
```

> **Custom properties.** ODCS has no section for per-producer mappings; `customProperties` is where the standard lets you add one. Say so in the contract.

#### [day1#library-metrics] Library metrics run on any engine; SQL covers the rest

*Lab 1.2 · step 3*

| Metric | At Rimah |
| --- | --- |
| `invalidValues` with `validValues` | sex, ward, disposition in their code sets |
| `invalidValues` with `pattern` | ICD-10 with the dot |
| `duplicateValues` | one row per `encounter_id` |
| `type: sql` | no discharge before admission |
| ranges (course extension) | weight 1 to 350 kg, creatinine 20 to 1,500 µmol/L |

#### [day1#contract-results] One contract, three runs: 19 clauses each

*Lab 1.2 · step 4*

| Producer | Passed | Failed clause | Value |
| --- | --- | --- | --- |
| Sidra | 19 of 19 | none |  |
| Ufuq | 17 of 19 | duplicate encounter ids; latency | 37 rows; 9 days |
| Rawdah | 18 of 19 | discharge before admission | 16 rows |

Each failure names the producer, the clause and the rows: the producer can act on it.

#### [day1#freshness] Freshness is a clause, because missing days look like fewer patients

*Service levels*

**9 days** between Ufuq's newest admission and its delivery; the contract allows 2

- A late file is easy to see; a file that stops early is not.
- `slaProperties` latency: the newest record against the delivery date.
- The rule blocks the delivery; the producer re-sends a complete one.

#### [day1#ai-off-contract] The first contract is written without an assistant

*How this lab runs*

- **AI off.** Lab 1.2 and the supervised checks: the decisions in a contract (what counts as valid, what blocks) are the skill being tested.
- **AI tutor.** The other labs: an assistant may explain an error message. It does not write generator or attack code.

#### [day1#check-contract] Where the factor lives

*Checkpoint*

**Question:** Ufuq confirms its creatinine is in mg/dL. Where should the factor 88.42 be written?

- A. In the contract, as a unit clause for Ufuq's creatinine
- B. In the preparation pipeline's cleaning step
- C. In Ufuq's hospital system, by changing its unit
- D. In the study's analysis notebook, with a comment

#### [day1#lab-1-2] One contract for three producers

Lab 1.2 · 25 min

Write the shared encounter contract in ODCS with code mappings, unit rules, quality rules and freshness, without AI assistance, and run it against all three extracts.

[D1_2_shared_contract.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D1_2_shared_contract.ipynb)

- [ ] Read the skeleton: schema, properties, SLA (4 min)
- [ ] Add the code maps and unit rules for each producer (7 min)
- [ ] Add the quality rules (6 min)
- [ ] Run it on the three extracts (5 min)
- [ ] Read the failures: producer, clause, rows (3 min)
- [ ] ✱ Stretch: Express one rule as a Soda check in the contract's custom block

### Session 3: Linking patients across producers

#### [day1#s3] Linking patients across producers

*Session 3*

- Explain why a plain hash of a national identifier is not a pseudonym
- Compute a keyed-hash linkage key at each producer after normalisation
- Measure precision and recall of the linkage against a known truth

#### [day1#why-link] A readmission is often at another hospital group

*The study's need*

- 1,953 pairs of local patients in this quarter's extracts are the same person at two groups.
- Without linkage those readmissions are invisible to the study.
- The national identifier links them; it may not travel to the consortium.

- **The constraint.** Health data is sensitive data under the Personal Data Protection Law. The study needs the link, not the identity.

#### [day1#pseudonym-vs-anonymous] A pseudonym is still personal data; anonymous data is not

*Words that matter*

|  | Pseudonymised | Anonymised |
| --- | --- | --- |
| Who can re-identify | whoever holds the extra information | nobody, irreversibly |
| Still personal data | yes | no |
| At Rimah | the linkage key | a release that passes Day 3 and 4 tests |

> **The extra information is kept apart.** SDAIA's guideline asks that what is needed to re-identify is held separately, under controls.

#### [day1#plain-hash-reversed] A plain hash of an identifier is reversed by enumeration

*Lab 1.3 · step 1*

**2.2 s** to reverse one SHA-256 of a national identifier when the first four digits are known

- About 175,000 hashes a second on one laptop core, in plain Python.
- All 2 billion candidates: about 3 hours on one core; far less on a graphics card.
- The identifier's space is small and structured: hashing hides nothing.

#### [day1#keyed-hash] A keyed hash with a key the consortium never holds

*Lab 1.3 · step 3*

1. **Linkage unit** creates a key for this project
2. **Each producer** normalises, then HMAC-SHA-256
3. **Consortium** receives pseudonyms only

- Without the key nobody can recompute or enumerate the pseudonyms.
- A new project gets a new key: its pseudonyms cannot be joined with this one's.

#### [day1#normalise-first] Normalise first, or one person gets three pseudonyms

*Lab 1.3 · step 2*

| As typed | Normalised |
| --- | --- |
| `1012 345 678` (Ufuq) | `1012345678` |
| `SA-1012345678` (Rawdah) | `1012345678` |
| Arabic-Indic digits (Ufuq) | `1012345678` |
| `101234567` | rejected, not padded |

The rule is part of the contract: every producer normalises the same way before hashing.

#### [day1#match-rates] Measure linkage against a truth: recall and precision

*Lab 1.3 · steps 4 and 5*

| Method | Linked pairs | Precision | Recall |
| --- | --- | --- | --- |
| Keyed hash, raw identifier | 225 | 1.000 | 0.115 |
| Keyed hash, normalised | 1,939 | 1.000 | 0.993 |
| Key A or key B (name, birth date, sex) | 1,977 | 0.988 | 1.000 |

Of 1,953 true pairs. Key B recovers the 14 missed by a mistyped identifier and adds 24 look-alike strangers.

#### [day1#check-hash] Safe to send?

*Checkpoint*

**Question:** Ufuq offers to send SHA-256 of each national identifier instead of the identifier. What do you answer?

- A. Accept: hashed data is anonymous
- B. Accept if they remove spaces first
- C. Ask for the plain identifier and hash it centrally
- D. Ask for a keyed hash of the normalised identifier, with a project key the consortium does not hold

#### [day1#lab-1-3] A keyed linkage identifier

Lab 1.3 · 25 min

Reverse a plain hash by enumeration, then generate a keyed-hash linkage identifier at each producer after normalising identifiers, and measure the match rate against the planted truth.

[D1_3_keyed_linkage.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D1_3_keyed_linkage.ipynb)

- [ ] Reverse a plain hash of an identifier (5 min)
- [ ] Normalise identifiers at each producer (7 min)
- [ ] Keyed hash with a key the consortium never holds (5 min)
- [ ] Match rate, precision and recall against the truth (5 min)
- [ ] Add a second key for typing errors (3 min)
- [ ] ✱ Stretch: Count the false matches the second key adds and decide whether to keep it

### Session 4: Versions and breaking changes

#### [day1#s4] Versions and breaking changes

*Session 4*

- Classify schema and meaning changes as breaking or additive
- Write a breaking-change policy with notice periods and approvers
- Test the policy on a seeded producer change and decide the new version

#### [day1#contracts-change] A producer's upgrade is your incident unless the change was agreed

*Contracts change*

- **January at Ufuq.** A new hospital system; the extract changed four ways; nobody was told.

- Versions tell consumers what kind of change it is.
- Notice gives them time to adapt.
- Approval makes the consortium, not one engineer, accept the change.

#### [day1#semver-contracts] Major for breaking, minor for additive

*Semantic versions*

| Change | Class | Version |
| --- | --- | --- |
| A column removed or renamed | breaking | 1.0.0 to 2.0.0 |
| A type, unit or format changed | breaking | major |
| A new value in a closed code set | breaking | major |
| A new optional column | additive | 1.0.0 to 1.1.0 |

#### [day1#hidden-change] A rename can hide a unit change that no schema diff shows

*Lab 1.4 · step 3*

- schema diff: `Creatinine_mgdl` removed, `Creatinine` added
- values: median 1.00 becomes 89.3: ratio 89.3, the mg/dL-to-µmol/L factor
- finding: renamed and unit changed: two breaking changes

> **The worse case.** Had Ufuq kept the old name, every type check would pass and creatinine would jump 88-fold.

#### [day1#policy-as-data] Write the policy as data, so it is applied the same way every time

*Lab 1.4 · step 1*

```python
# file: Lab 1.4
POLICY = {
  "breaking": ["removed_column", "renamed_column", "type_change", "unit_change",
               "format_change", "new_code_in_closed_set", "meaning_change"],
  "additive": ["new_optional_column", "new_code_in_open_set", "looser_rule"],
  "notice_days": {"breaking": 60, "additive": 14},
  "version_bump": {"breaking": "major", "additive": "minor"},
  "parallel_run_days": 30,
}
```

#### [day1#ufuq-v2-decision] Ufuq version 2: four breaking changes, contract 2.0.0

*Lab 1.4 · step 4*

| Change found | Class |
| --- | --- |
| `DOB`: 600 of 600 values no longer dd/mm/yyyy | breaking |
| `DischargeStatus`: new value 5 | breaking |
| `Creatinine_mgdl` renamed `Creatinine` | breaking |
| `Creatinine` now in µmol/L | breaking |
| `Nationality` added | additive |

60 days' notice, approval by the data board and the study owner, 30 days of both versions.

#### [day1#parallel-run] Notice, a parallel run, then retire the old version

*After the decision*

1. **Announce** what, when, contract version
2. **Parallel run** both versions for 30 days
3. **Retire** version 1 after consumers confirm

> **Unannounced breaking delivery:** rejected by the gate, re-sent by the producer.

#### [day1#check-breaking] Minor or major?

*Checkpoint*

**Question:** Rawdah plans to rename `weight_lb` to `weight` and send kilograms. Its engineer calls it a minor clean-up. How do you classify it?

- A. Minor: one column, same data
- B. Breaking: a rename and a unit change; major version, notice and a parallel run
- C. Additive: the new unit is better
- D. Whatever Rawdah decides: it owns the data

#### [day1#lab-1-4] A breaking-change policy, tested

Lab 1.4 · 25 min

Draft the consortium's change policy (what counts as breaking, notice periods, who approves) and test it on Ufuq's seeded version 2 extract.

[D1_4_breaking_changes.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D1_4_breaking_changes.ipynb)

- [ ] Draft the policy as data (6 min)
- [ ] Diff the old and new extract (7 min)
- [ ] Catch the change no schema diff shows (5 min)
- [ ] Apply the policy: version, notice, approver (5 min)
- [ ] One-page policy text (2 min)
- [ ] ✱ Stretch: Write the deprecation notice Ufuq should have sent

#### [day1#wrap-up] Three things to keep

*Day 1 · wrap-up*

- **Meaning fails silently.** Units and codes pass type checks. Profile the distributions and write the fix into the contract.
- **Link, do not identify.** Normalise, then a keyed hash with a key held elsewhere. Measure recall and precision.
- **Change has a process.** Breaking or additive by policy; versions, notice, approval, a parallel run.

#### [day1#next] Day 2: Prepare at scale

*Next*

Thirty million rows on a laptop: lazy queries over partitioned files, loads you can run twice, tables with history, and gates per partition. Set RIMAH_QUICK=1 if your laptop has less than 8 GB of free memory.

## Day 2: Prepare at scale

Thirty million rows on a laptop, loaded once, rebuilt exactly, gated per partition

#### [day2#title] Prepare at scale

*SDAIA Academy · Data Preparation at Scale: Contracts, Synthetic Data and Privacy*

Day 2: Thirty million rows on a laptop, loaded once, rebuilt exactly, gated per partition

Data Science Track · 4 teaching days + capstone day · 4 sessions · 4 labs · DS-405

#### [day2#agenda] Prepare at scale

*Today*

- **Session 1 · Columnar files and lazy execution**: Partitioned columnar files and lazy plans that read only what the query needs, measured in time and peak memory
- **Session 2 · Incremental and idempotent loads**: Loads that give the same table however often they run, by partition overwrite or merge on a key
- **Session 3 · Tables with history**: Snapshots and versions in an open table format, and an analysis that records the version it read
- **Session 4 · Gates and lineage at scale**: Blocking rules per partition so one bad delivery stops alone, and lineage events that lead back to the producer

#### [day2#review-day1] Yesterday in one decision

*Review of Day 1*

**Question:** Rawdah tells you that from next month its weight column will hold kilograms, under the same name. What do you do first?

- A. Classify it under the policy as a breaking unit change: new major version, notice, a parallel run
- B. Thank them and remove the unit clause from the contract the same day
- C. Add an if-statement on the date in the study's pipeline
- D. Nothing: the range rule will catch any problem

### Session 1: Columnar files and lazy execution

#### [day2#s1] Columnar files and lazy execution

*Session 1*

- Explain projection and predicate pushdown into partitioned Parquet
- Rewrite an eager cleaning script as a lazy query
- Measure wall time and peak memory of both on the same data

#### [day2#the-lake] Thirty million rows in 88 MB of partitioned Parquet

*The data today*

| Table | Rows |
| --- | --- |
| encounters | 1,200,024 |
| labs (six tests, three rounds) | 21,600,432 |
| pharmacy | 7,200,144 |
| total | 30,000,600 |

```
# file: data/lake/raw
labs/producer=SDR/month=2025-01/part-0.parquet
labs/producer=SDR/month=2025-02/part-0.parquet
...
labs/producer=RWD/month=2025-12/part-0.parquet
```

#### [day2#rows-vs-columns] A query that needs three columns should read three columns

*Columnar files*

- **A row file (CSV).** Every row is read whole to find three fields in it. Types are guessed on every read.
- **A column file (Parquet).** Each column is stored apart, typed and compressed, with statistics per block, so a reader skips columns and blocks it does not need.

Partitions add a third skip: whole files, by the values in the folder names.

#### [day2#lazy-plans] A lazy query is a plan the optimiser can push into the scan

*Lab 2.1 · step 2*

```
# file: q.explain()
simple π 2/2 ["encounter_id", "value"]
  Parquet SCAN [.../producer=RWD/month=2025-09/part-0.parquet, ... 2 other sources]
  PROJECT 4/8 COLUMNS
  SELECTION: (col("month") == "2025-09") & (col("test_code") == "CREAT")
```

- **3 of 36 files** opened: the month filter pruned the rest.
- **4 of 8 columns** read: the select and the filter need no more.

#### [day2#eager-vs-lazy] Same answer: 40 times faster, a 25th of the memory

*Lab 2.1 · steps 1, 4 and 5*

| Query on 30 million rows | Seconds | Peak memory, MB |
| --- | --- | --- |
| Eager script (pandas, reads everything) | 19.6 | 2,693 |
| Lazy query (Polars) | 0.58 | 391 |
| Lazy, streaming engine | 0.47 | 112 |
| DuckDB SQL, same files (stretch) | 1.70 | 198 |

One run on a 14-thread laptop with 34 GB of memory. Your numbers will differ; the order will not.

#### [day2#same-result-first] A faster query with another answer is a bug

*Lab 2.1 · step 4*

- Compare every key and value, with a tolerance stated for floats.
- Watch joins: an inner join on a filtered side silently drops rows.
- Watch nulls: `mean` skips them in both tools, `len` counts them.

- **Already in the output.** Rawdah, September: mean highest creatinine **1.57**, other months about 140. Lab 2.4 finds out why.

#### [day2#streaming] Streaming processes the files in batches, so memory stays flat

*Larger than memory*

1. **Scan** a batch of row groups
2. **Filter and project** in the batch
3. **Partial aggregates** kept, batch dropped

> **Not every operation streams.** A global sort or a wide join may fall back to memory. Check the plan, and measure at full size once.

#### [day2#check-lazy] Where the filter goes

*Checkpoint*

**Question:** Your lazy query on the lake is fast but its peak memory is the same as the eager script's. Which change most likely helps?

- A. Rewrite the lake as one unpartitioned Parquet file, so fewer files are opened
- B. Run it on more CPU cores
- C. Collect the labs table first, then filter it
- D. Read the plan: put the month and test filters on the scan and select only needed columns

#### [day2#lab-2-1] From eager to lazy

Lab 2.1 · 25 min

Rewrite an eager cleaning script as a lazy query over the partitioned lake and compare time, peak memory and the result.

[D2_1_lazy_columnar.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D2_1_lazy_columnar.ipynb)

- [ ] Run the eager script and measure it (5 min)
- [ ] Read the lake's partitions and the query plan (5 min)
- [ ] Write the lazy query (8 min)
- [ ] Same result, less time and memory (4 min)
- [ ] Streaming for the full size (3 min)
- [ ] ✱ Stretch: The same query in DuckDB SQL over the same files

### Session 2: Incremental and idempotent loads

#### [day2#s2] Incremental and idempotent loads

*Session 2*

- Show that an append load is not idempotent
- Make a daily load idempotent by partition overwrite or merge
- Prove idempotence by loading one day twice and comparing table hashes

#### [day2#loads-run-twice] Every load will run twice one day

*Real schedules*

- **Retry.** The load wrote, then failed before saying "done"; the scheduler runs it again.
- **Re-delivery.** Ufuq sends 2026-01-03 again with 20 values corrected.
- **Late correction.** Sidra's 2026-01-05 file corrects 15 results of 2026-01-02.

**Idempotent:** running a load twice leaves the table exactly as running it once.

#### [day2#append-doubles] An append load run twice doubles the day, with no error anywhere

*Lab 2.2 · step 1*

**59,994 → 119,988** rows after loading 2026-01-01 a second time

- Every key duplicated; counts and rates downstream double for that day.
- Nothing fails: the file is valid, the table accepts it.

#### [day2#fingerprint] "Same table" means same content, in any order and any files

*Lab 2.2 · step 2*

```python
# file: Lab 2.2
def table_hash(df):
    d = df.select(COLS).sort(KEY)          # fixed columns, fixed order
    return hashlib.sha256(d.write_csv().encode()).hexdigest()[:16]
```

Two tables with the same fingerprint hold the same rows. That is the proof the outcome asks for: identical output when a day is re-run.

#### [day2#partition-overwrite] Overwrite the day's partition: a re-run replaces, never adds

*Lab 2.2 · step 3*

```python
# file: Lab 2.2
df.write_delta(table, mode="overwrite",
    delta_write_options={"predicate": f"delivered_day = '{day}'",
                         "partition_by": ["delivered_day"]})
```

> **Its limit.** Days 1 to 5 by overwrite: 299,991 rows, **15 duplicate keys**: Sidra's corrections landed in day 5's partition, the originals stayed in day 2's.

#### [day2#merge-on-key] Merge on the business key: corrections replace what they correct

*Lab 2.2 · step 4*

```python
# file: Lab 2.2
DeltaTable(table).merge(df.to_arrow(),
    predicate="t.encounter_id = s.encounter_id AND t.test_code = s.test_code "
              "AND t.result_seq = s.result_seq",
    source_alias="s", target_alias="t") \
  .when_matched_update_all().when_not_matched_insert_all().execute()
```

Days 1 to 5 by merge: 299,976 rows, **0 duplicate keys**.

#### [day2#proof-twice] The proof: every day loaded twice gives the same fingerprint

*Lab 2.2 · step 5*

- once: days 1, 2, 3, 4, 5 → `fa71c591dcabaeb1`
- twice: days 1 to 5, again 1 to 5, and day 3 a third time → `fa71c591dcabaeb1`
- result: identical output when a day is re-run

> **Order still matters.** Replaying day 2 after day 5 puts the old values back until day 5 is replayed. Real pipelines compare a delivery version before updating.

#### [day2#check-idempotent] Which load survives Sidra?

*Checkpoint*

**Question:** Sidra's delivery on day 5 corrects results first delivered on day 2. Which load leaves exactly one row per result, holding the corrected value?

- A. Append each day's file
- B. Merge each day's file on encounter, test and round
- C. Overwrite each day's partition
- D. Append, then drop rows that are identical in every column

#### [day2#lab-2-2] Load one day twice

Lab 2.2 · 25 min

Make the daily laboratory load idempotent and prove it by loading one day twice, including a day the producer delivered again with corrections.

[D2_2_idempotent_load.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D2_2_idempotent_load.ipynb)

- [ ] The append load and its duplicates (5 min)
- [ ] A table fingerprint (4 min)
- [ ] Idempotent: overwrite the day's partition (6 min)
- [ ] Corrections: merge on the business key (6 min)
- [ ] Load every day twice and compare (4 min)
- [ ] ✱ Stretch: Keep a load log so a day is skipped when its file has not changed

### Session 3: Tables with history

#### [day2#s3] Tables with history

*Session 3*

- Read an earlier version of a table by version number
- Rebuild an analysis set exactly from the recorded version
- Explain what retention and vacuuming do to time travel

#### [day2#reproduce-question] "Can you reproduce exactly what the board saw in January?"

*The board's question*

- Since then, producers corrected 2% of December discharge dates.
- Rawdah delivered late December encounters.
- Today's table gives different December figures.

- **Without history.** You rebuild from backups, if any, and hope nothing else changed.

#### [day2#table-formats] A table format adds a log of commits to files: every commit is a version

*Open table formats*

- **Delta Lake.** A JSON log beside the Parquet files. Used in the labs through delta-rs: no Java needed.
- **Apache Iceberg.** Snapshots with metadata files; time travel by snapshot id.
- **DuckLake.** The catalog in a SQL database; snapshots and time travel.

Same ideas in all three: atomic commits, versions, time travel, schema evolution.

#### [day2#history-log] Four commits, four versions of December

*Lab 2.3 · step 1*

| Version | Operation | What happened |
| --- | --- | --- |
| 0 | WRITE | October and November loaded |
| 1 | WRITE (append) | December arrives; the board's figures are built here |
| 2 | MERGE | 2% of December discharges corrected |
| 3 | WRITE (append) | Rawdah's late December encounters |

#### [day2#record-version] Record the version with the analysis, and the fingerprint of what it produced

*Lab 2.3 · step 2*

```json
// file: analysis run record
{"analysis": "december_discharges", "table": "curated/encounters",
 "version": 1, "rows": 15, "fingerprint": "2b4a6dfab81fa30c"}
```

Two fields make the figures reproducible: the version read and the fingerprint written.

#### [day2#rebuild-identical] Read version 1, rebuild, compare: identical; today: every cell moved

*Lab 2.3 · steps 3 and 4*

```python
# file: Lab 2.3
then = analysis_set(pl.read_delta(TABLE, version=1))
U.fingerprint(then) == RUN["fingerprint"]   # True
```

**15 of 15** producer and ward cells differ between version 1 and today (full size)

#### [day2#vacuum] Vacuum deletes the files old versions need

*Lab 2.3 · step 5*

- vacuum: retention 0 hours on a copy
- read v1: `FileNotFoundError`

- Delta's default retention is seven days.
- Set it to the reproducibility promise, or snapshot each release with its fingerprint.
- The board and the data owner decide the promise, not the platform alone.

#### [day2#check-history] Reproduce a release

*Checkpoint*

**Question:** A release from last March must be reproduced. The run log names the table but not the version, and the table is vacuumed weekly with seven days' retention. What is true?

- A. Read the table as of last March's timestamp
- B. It cannot be rebuilt exactly from the table; only a kept snapshot of the release would prove it
- C. Rebuild from today's table: corrections only improve it
- D. Restore the table to March and rerun

#### [day2#lab-2-3] Rebuild last month

Lab 2.3 · 25 min

Rebuild last month's analysis set from the table snapshot it was built on, prove it is identical, and measure what later corrections changed.

[D2_3_table_snapshots.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D2_3_table_snapshots.ipynb)

- [ ] Read the table's history (4 min)
- [ ] The analysis run record (4 min)
- [ ] Rebuild from the recorded version (7 min)
- [ ] Prove it identical, then diff with today (6 min)
- [ ] What vacuuming would break (4 min)
- [ ] ✱ Stretch: Restore the table to the recorded version and compare

### Session 4: Gates and lineage at scale

#### [day2#s4] Gates and lineage at scale

*Session 4*

- Run blocking rules per partition and quarantine the failures
- Emit OpenLineage run events for every job run
- Trace a defect in an output to its producer and partition

#### [day2#dip] Median creatinine fell by a quarter in September, and nobody knows why

*Yesterday's figure*

| Item | Value |
| --- | --- |
| 2025-08 | 89.8 |
| 2025-09 | 66.5 |
| 2025-10 | 90.1 |

Median creatinine, µmol/L, all producers, from yesterday's run without gates (full lake).

#### [day2#gate-per-partition] Gate each partition, so one bad delivery stops alone

*Lab 2.4 · step 1*

- The contract's ranges, per test: creatinine 20 to 1,500 µmol/L, glucose 1 to 60 mmol/L.
- A partition fails if more than 0.5% of its results fall outside.
- One lazy query gates all 36 partitions.

| Partition | Rows | Invalid |
| --- | --- | --- |
| RWD, 2025-09 | 600,012 | 100,002 (16.7%) |
| other 35 |  | 0 |

#### [day2#quarantine] Publish what passed, quarantine what failed, and say what is missing

*Lab 2.4 · step 2*

1. **35 partitions** published
2. **RWD 2025-09** quarantined until Rawdah re-sends
3. **September figure** 90.2, from 2 producers, flagged

#### [day2#openlineage] A lineage event says which run read what and wrote what

*Lab 2.4 · step 3*

```json
// file: artifacts/D2_4/today.jsonl
{"eventType": "FAIL",
 "job": {"namespace": "rimah", "name": "rimah.labs_gate"},
 "run": {"runId": "dba00c8e-...", "facets": {"gate": {"invalid": 100002, "rows": 600012}}},
 "inputs":  [{"name": "raw/labs/producer=RWD/month=2025-09"}],
 "outputs": [{"name": "quarantine/labs/producer=RWD/month=2025-09"}]}
```

#### [day2#trace-back] Walk the events backwards from the figure to the partition

*Lab 2.4 · step 4*

- start: `analysis/monthly_creatinine`
- written by: `rimah.monthly_creatinine`: 36 curated partitions
- written by: `rimah.labs_publish`: 36 raw partitions; September: 3
- medians: SDR 89.97 · UFQ 90.51 · **RWD 1.02**
- traced: Rawdah, September: creatinine in mg/dL under a µmol/L label

#### [day2#check-gates] One partition fails

*Checkpoint*

**Question:** Rawdah's September laboratory partition fails its gate. The study's monthly report is due today. What does the pipeline do?

- A. Stop the whole load until Rawdah re-sends
- B. Publish it with a warning in the log
- C. Publish the 35 partitions that passed, quarantine Rawdah's September, and flag September as two producers
- D. Divide the partition's values by 88.42 and publish

#### [day2#lab-2-4] Gates and lineage per partition

Lab 2.4 · 25 min

Run blocking rules per partition of the lake, quarantine what fails, emit lineage events, and trace a seeded defect to its producer and partition.

[D2_4_gates_lineage.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D2_4_gates_lineage.ipynb)

- [ ] Contract rules as per-partition gates (7 min)
- [ ] Quarantine and publish the rest (5 min)
- [ ] Emit OpenLineage run events (6 min)
- [ ] Trace the defect back through the events (7 min)
- [ ] ✱ Stretch: A gate on the distribution, not only on the values

#### [day2#wrap-up] Three things to keep

*Day 2 · wrap-up*

- **Read less.** Partitions, columns and lazy plans: 2.7 GB became 112 MB for the same answer.
- **Load twice, same table.** Merge on the business key; prove it with a fingerprint.
- **Versions and gates.** Record the version you read; gate per partition; emit lineage so a figure can be traced.

#### [day2#next] Day 3: Synthesise and attack

*Next*

The university wants a copy. Tomorrow you generate synthetic patients and encounters, measure whether the readmission model still works on them, and attack them to see what leaks.

## Day 3: Synthesise and attack

Synthetic patients and encounters, measured for utility and attacked for privacy

#### [day3#title] Synthesise and attack

*SDAIA Academy · Data Preparation at Scale: Contracts, Synthetic Data and Privacy*

Day 3: Synthetic patients and encounters, measured for utility and attacked for privacy

Data Science Track · 4 teaching days + capstone day · 4 sessions · 4 labs · DS-405

#### [day3#agenda] Synthesise and attack

*Today*

- **Session 1 · When synthetic data fits**: What synthetic data is for, what it cannot do, and when a de-identified extract or a query service fits better
- **Session 2 · Generating related tables**: Generators for a parent table and a child table that keep the relation: child counts and conditioning on the parent
- **Session 3 · Utility is measured against the analysis**: Fidelity scores against fitness for the analysis: train on synthetic, test on real, and the study's own estimate
- **Session 4 · Privacy is measured by attack**: Distance to the closest record against a holdout and membership inference, on each table and on linked records

#### [day3#review-day2] Yesterday in one decision

*Review of Day 2*

**Question:** Sidra corrects 15 creatinine results three days after sending them. Your daily load overwrites the delivery day's partition. What does the curated table hold afterwards?

- A. The corrected values only
- B. Both the original and the corrected results: 15 duplicate keys
- C. Only the latest day, everything else overwritten
- D. An error: the keys collide

### Session 1: When synthetic data fits

#### [day3#s1] When synthetic data fits

*Session 1*

- State what synthetic data can and cannot support
- Compare synthetic data, a de-identified extract and a query service for a request
- Record the residual risk of each option in a decision table

#### [day3#study-tables] Two related tables, split before anyone generates anything

*The data today*

| Table | Train | Holdout |
| --- | --- | --- |
| patients (one row each) | 4,151 | 1,849 |
| encounters (one row per stay) | 9,156 | 4,102 |
| readmitted within 30 days | about 15% of stays |  |

- **Why a holdout.** Generators see only the training patients. The holdout scores utility (Lab 3.3) and is the "never seen" group every attack compares with (Lab 3.4).

#### [day3#what-synthetic-is-for] A model of the data, sampled: good at patterns, bad at individuals

*Synthetic data*

- **Good for.**
  - Developing and testing code before access to real data
  - Teaching and data challenges
  - Patterns the generator was built to keep
- **Not for.**
  - Exact counts, especially small ones
  - Rare groups, outliers, a named patient
  - Relationships the generator did not model

> **And not automatically private.** Privacy is a property to measure by attack, not a property of the word.

#### [day3#three-options] Three ways to answer a request, each with its own residual risk

*The choice*

| Option | The requester gets | Residual risk |
| --- | --- | --- |
| **Synthetic file** | rows drawn from a model of the data | leaks if the generator memorises; analysis biased where it loses relations |
| **De-identified extract** | real rows, identifiers removed, minimum columns | still personal data; unique records can be found |
| **Query service** | answers to approved queries, never rows | outputs can disclose (small cells, differencing); needs people to review |

#### [day3#rare-cells] Small cells are off by more than their own size

*Lab 3.1 · step 2*

| Real count of the cell (region × diagnosis × CKD) | Cells | Mean relative error | Lost | Invented |
| --- | --- | --- | --- | --- |
| 0 | 2 |  | 0 | 2 |
| 1 to 9 | 14 | 153% | 2 | 0 |
| 10 to 49 | 45 | 31% | 0 | 0 |
| 50 and more | 48 | 10% | 0 | 0 |

Encounters per cell, real training data against the reference conditional-tree file.

#### [day3#unique-records] A third of patients are unique on five ordinary attributes

*Lab 3.1 · step 3*

| An acquaintance knows | Patients unique |
| --- | --- |
| sex, region | 0.0% |
| sex, year of birth, region | 4.2% |
| + nationality | 11.5% |
| + hospital group | 35.1% |

#### [day3#four-requests] The course's decisions, for you to challenge

*Lab 3.1 · step 4*

| Request | Option | Because |
| --- | --- | --- |
| Q1 university model development | synthetic | develop on synthetic; final fit by the consortium on real data |
| Q2 exact renal readmissions for the ministry | query service | small synthetic cells are off by 153% |
| Q3 public data challenge | synthetic | structure, not values; must pass attacks with margin |
| Q4 obstetric patients with CKD | extract | actual patients of a rare group; agreement and minimum columns |

#### [day3#check-options] Pick the option

*Checkpoint*

**Question:** The ministry asks for the number of readmissions per region and month, published on a public dashboard. Which option fits?

- A. A synthetic file the ministry counts itself
- B. A de-identified extract
- C. A query service on the real data, with small counts protected before publication
- D. The exact counts from the real data, as they are

#### [day3#lab-3-1] Four requests, three options

Lab 3.1 · 25 min

For four data requests, decide between synthetic data, a de-identified extract and a query service, with the evidence for each decision measured on the study tables.

[D3_1_choose_method.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D3_1_choose_method.ipynb)

- [ ] Read the four requests and what each needs (4 min)
- [ ] What a synthetic file gets wrong: rare cells (7 min)
- [ ] What an extract leaks: unique records (6 min)
- [ ] The decision table with residual risk (8 min)
- [ ] ✱ Stretch: Price each option in staff days and compute

### Session 2: Generating related tables

#### [day3#s2] Generating related tables

*Session 2*

- Explain why tables generated separately break the parent-child relation
- Fit a baseline generator and a conditional-tree generator to two related tables
- Check referential integrity and child counts of the synthetic tables

#### [day3#relation-lost] Generate the tables separately and the relation is gone

*Lab 3.2 · step 1*

| Encounters per patient | No heart failure | Heart failure |
| --- | --- | --- |
| Real | 2.14 | 3.06 |
| Random parent for each stay | 2.21 | 2.10 |

- **And.** 480 synthetic patients with no stay at all, where every real patient has at least one.

#### [day3#two-generators] A floor, and one that conditions each column on the ones before it

*Two generators*

- **Independent baseline.** Every column drawn from its own distribution. Perfect marginals, no relationships. The floor any generator must beat.
- **Conditional trees.** Column by column: a tree fitted on the columns before it, a value copied from a random real row of the same leaf (at least 25 rows). The CART method of synthpop.

Both run on a laptop CPU in seconds. SDV's HMASynthesizer is the stretch, in Colab.

#### [day3#tree-draw] Drawing one column

*Lab 3.2 · step 3*

1. **1 · Fit** a tree: this column from the columns before it, on real rows
2. **2 · Drop** each synthetic row into the tree: which leaf?
3. **3 · Copy** the value of a random real row in that leaf

> **Takeaway.** The leaf size is the dial: small leaves keep relations and copy people; large leaves blur both.

#### [day3#what-each-kept] The trees keep what the study needs; the baseline keeps columns

*Lab 3.2 · step 5*

|  | Stays per HF patient | Readmission, HF ÷ not | Repeat ÷ first stay | Corr. CKD, creatinine |
| --- | --- | --- | --- | --- |
| Real | 3.06 | 2.07 | 1.69 | 0.77 |
| Independent | 2.28 | 1.16 | 0.98 | 0.00 |
| Conditional trees | 2.95 | 1.91 | 1.54 | 0.77 |

No orphan encounters and every patient's stays numbered 1..n, in both files.

#### [day3#check-relation] Where the child count goes

*Checkpoint*

**Question:** A colleague fits one generator to patients and another to encounters, then assigns each synthetic encounter to a random synthetic patient. What breaks first?

- A. Who comes back: stays per patient no longer depend on the patient's conditions
- B. Referential integrity: encounters with no patient
- C. The marginal distribution of each column
- D. The overall readmission rate

#### [day3#lab-3-2] Two generators for related tables

Lab 3.2 · 25 min

Fit two generators to the patient and encounter tables, an independent baseline and conditional trees that keep the parent-child relation, and check what each kept.

[D3_2_relational_generators.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D3_2_relational_generators.ipynb)

- [ ] The relation: encounters per patient (4 min)
- [ ] Baseline: each column on its own (5 min)
- [ ] Conditional trees: parents with their child counts (7 min)
- [ ] Children conditioned on their parent (6 min)
- [ ] Integrity and relation checks (3 min)
- [ ] ✱ Stretch: Fit SDV's HMASynthesizer to the same tables in Colab

### Session 3: Utility is measured against the analysis

#### [day3#s3] Utility is measured against the analysis

*Session 3*

- Compute marginal and pairwise fidelity of a synthetic table
- Score analytical utility by training on synthetic and testing on real data
- Compare the study's key estimate on real and synthetic data

#### [day3#fidelity-vs-fitness] Fidelity scores say the baseline is nearly perfect

*Lab 3.3 · step 1*

|  | Mean marginal distance | Correlation gap |
| --- | --- | --- |
| Independent | 0.015 | 0.064 |
| Conditional trees | 0.010 | 0.013 |
| Vendor | 0.000 | 0.000 |

Kolmogorov-Smirnov for numbers, total variation distance for categories; 0 is identical.

#### [day3#tstr] Train on synthetic, test on the real holdout

*Lab 3.3 · steps 2 and 3*

| Model trained on | AUC on the real holdout | Gap to real |
| --- | --- | --- |
| Real training data (TRTR) | 0.706 | 0 |
| Independent | 0.665 | 0.041 |
| Conditional trees | 0.705 | 0.001 |
| Vendor | 0.706 | 0.000 |

#### [day3#study-estimate] The study's own number: does heart failure double the risk?

*Lab 3.3 · step 4*

| Data | Risk ratio, HF vs not | 95% interval |
| --- | --- | --- |
| Real | 2.07 | 1.84 to 2.33 |
| Independent | 1.16 | 0.96 to 1.41 |
| Conditional trees | 1.91 | 1.68 to 2.17 |

> **The baseline would publish "no clear effect".** Its interval includes 1.

#### [day3#check-utility] What proves utility

*Checkpoint*

**Question:** A generator's report shows every column's distribution within 2% of the real one. The university asks whether its readmission model will work. What do you answer?

- A. Yes: the distributions match
- B. Train on synthetic and test on the real training data
- C. Not known yet: train on synthetic, test on a real holdout, and compare the study's estimates
- D. No synthetic data can support a model

#### [day3#lab-3-3] Train on synthetic, test on real

Lab 3.3 · 25 min

Train the readmission model on each synthetic dataset, test it on real holdout data, and compare with fidelity scores and the study's own estimate.

[D3_3_synthetic_utility.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D3_3_synthetic_utility.ipynb)

- [ ] Fidelity: marginals and correlations (6 min)
- [ ] Train on real, test on real: the reference (5 min)
- [ ] Train on synthetic, test on real (7 min)
- [ ] The study's estimate on each dataset (4 min)
- [ ] The utility report (3 min)
- [ ] ✱ Stretch: Which feature's importance moved most, and why

### Session 4: Privacy is measured by attack

#### [day3#s4] Privacy is measured by attack

*Session 4*

- Compute distance-to-closest-record against a holdout baseline
- Run a membership-inference test and read its AUC
- Attack each synthetic table and the linked patient histories

#### [day3#attacks] Two attacks, both against a group the generator never saw

*Privacy by attack*

- **Distance to closest record.** For each synthetic record: is the nearest real record a member (training) or a non-member (holdout)? No copying: about 0.5.
- **Membership inference.** For each real record: score "was in training" by its distance to the nearest synthetic record. AUC 0.5 is guessing, 1.0 is certainty.

Members are a random 1,849 of the training patients, as many as the holdout.

#### [day3#twins] Exact twins prove little; the difference from the holdout does

*Lab 3.4 · step 1*

- **27%** of members have an exact twin in the trees' patient table
- **21%** of non-members, never seen by the generator, have one too

#### [day3#attack-results] Per table: the trees pass narrowly, the vendor fails outright

*Lab 3.4 · steps 2 to 5*

| Generator | Table | DCR share | Membership AUC | Passes |
| --- | --- | --- | --- | --- |
| Independent | patients / encounters | 0.49 / 0.50 | 0.52 / 0.51 | yes |
| Trees | patients / encounters | 0.52 / 0.50 | 0.55 / 0.51 | yes |
| Vendor | patients / encounters | 0.69 / 0.72 | 0.90 / 1.00 | no |

Thresholds set by the release board before the results: DCR share ≤ 0.55, AUC ≤ 0.60.

#### [day3#vendor] "Fully synthetic, privacy-safe": 90% of real stays are still there

*Lab 3.4 · step 4*

- New identifiers `V000001`…
- 1% noise on creatinine and glucose
- Everything else: the real rows

- **Measured.** 90% of real training encounters have a vendor record within 0.05 in scaled distance. Membership AUC on encounters: 1.00.

> **"Synthetic" names a process, not a property.** Ask for the method, the holdout and the attack results per table, or run them yourself.

#### [day3#check-attack] Reading an attack

*Checkpoint*

**Question:** A membership-inference test on a synthetic encounter table gives an AUC of 0.51; on the patient table, 0.88. What do you conclude?

- A. The release is safe on average
- B. Patient attributes are coarse, so the 0.88 does not matter
- C. The encounter test failed and should be re-run
- D. The patient table leaks its training patients; the release fails until it is fixed

#### [day3#lab-3-4] Attack each synthetic table

Lab 3.4 · 25 min

Run distance-to-closest-record and membership-inference tests on each synthetic table, including a vendor's file, and write the attack report.

[D3_4_attack_synthetic.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D3_4_attack_synthetic.ipynb)

- [ ] Distances to train and to holdout (6 min)
- [ ] Distance to closest record, per table (6 min)
- [ ] Membership inference and its AUC (7 min)
- [ ] The vendor file (3 min)
- [ ] The attack report (3 min)
- [ ] ✱ Stretch: Attack the linked patient histories, not single rows

#### [day3#wrap-up] Three things to keep

*Day 3 · wrap-up*

- **Choose the option.** Synthetic for patterns; extracts for actual patients under agreement; a query service for exact counts.
- **Utility against the analysis.** Train on synthetic, test on real, and compare the study's own estimate.
- **Privacy by attack.** Per table and linked, against a holdout, with thresholds set first.

#### [day3#next] Day 4: Protect and decide

*Next*

Encounter sequences, monthly statistics under one budget, a rate pooled without pooling records, and the release decision for the university.

## Day 4: Protect and decide

Longitudinal risk, a budget over twelve releases, pooling without pooling, and the decision

#### [day4#title] Protect and decide

*SDAIA Academy · Data Preparation at Scale: Contracts, Synthetic Data and Privacy*

Day 4: Longitudinal risk, a budget over twelve releases, pooling without pooling, and the decision

Data Science Track · 4 teaching days + capstone day · 4 sessions · 4 labs · DS-405

#### [day4#agenda] Protect and decide

*Today*

- **Session 1 · Disclosure risk in longitudinal records**: Encounter sequences act as quasi-identifiers: risk measured with what an adversary knows, compared with the single-table estimate
- **Session 2 · Privacy budgets over many releases**: A privacy unit, a contribution bound and a ledger that spends one budget over twelve monthly releases
- **Session 3 · Analysis without pooling records**: Federated analysis, secure aggregation and clean rooms: what each hides and what the result still reveals
- **Session 4 · The release decision**: A release decision a data protection officer can sign: method, lawful basis, classification, residual risk, conditions, approver

#### [day4#review-day3] Yesterday in one decision

*Review of Day 3*

**Question:** A new generator gives a TSTR AUC of 0.706, equal to the model trained on real data, and a membership AUC of 0.97 on encounters. What do you report?

- A. The best generator so far: release it
- B. Acceptable on average across the two measures
- C. The attack is unreliable when utility is this high
- D. It copies its training encounters: it fails, and its perfect utility is part of the evidence

### Session 1: Disclosure risk in longitudinal records

#### [day4#s1] Disclosure risk in longitudinal records

*Session 1*

- Measure uniqueness of encounter sequences as quasi-identifiers
- Compare longitudinal risk with the single-table estimate
- Reduce the risk by coarsening and truncation and measure the cost

#### [day4#single-table] On one table, 4% of patients are unique

*The usual estimate*

**4.2%** of 4,151 patients unique on sex, year of birth and region

- **Recap from DS-309.** Uniqueness and k-anonymity on a single table. Today the table has a history attached: stays, months, diagnoses.

#### [day4#what-they-know] A relative knows your stays, not your record

*The adversary*

- **Facts.** Sex and year of birth: anyone who knows you.
- **Stays.** "In hospital in March for his heart, again in July": a token of month and diagnosis group per stay.
- **The test.** How many patients match the facts and have every known token? One means found.

#### [day4#risk-by-known] Two known stays, with sex and birth year, single out 97% of the patients who have them

*Lab 4.1 · step 3*

| Known stays (month, diagnosis) | Patients with that many | Stays only | + sex, year of birth |
| --- | --- | --- | --- |
| 1 | 4,151 | 0.0% | 40.1% |
| 2 | 2,809 | 12.4% | 96.6% |
| 3 | 1,395 | 90.5% | 100% |

#### [day4#levers] Coarsening helps; truncation made it worse

*Lab 4.1 · step 4*

| Release | Adversary knows | Unique |
| --- | --- | --- |
| as is | sex, year of birth, 2 stays | 96.6% |
| coarsened: decade, quarter | sex, decade, 2 stays | 20.6% |
| coarsened | sex, decade, 3 stays | 78.0% |
| coarsened, at most 2 stays | sex, decade, 2 stays | 47.2% |

Truncation dropped 24% of the stays, the repeat stays where readmissions happen.

#### [day4#check-longitudinal] Which number to report

*Checkpoint*

**Question:** An extract of patients with all their stays shows 4% of patients unique on sex, year of birth and region. What do you tell the release board?

- A. The risk is low: 4%
- B. The 4% ignores the stays: with two known stays nearly every patient with two is unique
- C. Release only the first two stays of each patient and the risk is solved
- D. The study identifiers are pseudonyms, so uniqueness does not matter

#### [day4#lab-4-1] Sequences as quasi-identifiers

Lab 4.1 · 25 min

Measure re-identification risk when encounter sequences act as quasi-identifiers and compare it with the single-table estimate, then coarsen and measure again.

[D4_1_longitudinal_risk.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D4_1_longitudinal_risk.ipynb)

- [ ] The single-table estimate (5 min)
- [ ] Sequences an adversary could know (7 min)
- [ ] Risk by number of known encounters (5 min)
- [ ] Coarsen and truncate, then measure again (6 min)
- [ ] The risk table (2 min)
- [ ] ✱ Stretch: Which patients stay unique after coarsening, and why

### Session 2: Privacy budgets over many releases

#### [day4#s2] Privacy budgets over many releases

*Session 2*

- Bound each person's contribution to a monthly statistic
- Allocate one budget across twelve releases and keep a ledger
- Plot error against budget and show why re-releases must be charged

#### [day4#dp-recap] Noise calibrated to how much one person can change the answer

*Recap from DS-309*

- **Privacy unit**: whose presence is hidden (here: a patient).
- **Contribution bound**: the most one unit changes the statistic.
- **Laplace scale** = bound ÷ ε; expected absolute error = scale.

- **New today.** Twelve releases, not one. Every release spends budget, and the spends add up: sequential composition.

#### [day4#contribution] Count readmitted patients, not readmitted stays

*Lab 4.2 · step 1*

- **Stays.** One patient had up to **3** readmitted stays in a month: the noise would need to cover 3.
- **Patients.** Each patient moves each month's count by at most **1**: about 140 to 200 a month in 2025.

#### [day4#ledger] One budget, two allocations, a ledger that refuses

*Lab 4.2 · steps 2 and 3*

| Allocation of ε = 1 for 2025 | Releases | ε each | Expected error |
| --- | --- | --- | --- |
| A: monthly counts | 12 | 1/12 | 12 patients (about 7%) |
| B: quarterly counts | 4 | 1/4 | 4 patients (under 1%) |

```
# file: ledger
refused: everything at once needs ε=1.0000, 0.9167 left
```

#### [day4#error-budget] Error falls as one over the budget

*Lab 4.2 · step 4*

| Yearly ε | 0.1 | 0.25 | 0.5 | 1 | 2 | 4 |
| --- | --- | --- | --- | --- | --- | --- |
| Mean absolute error, monthly count (measured) | 118.9 | 48.7 | 24.4 | 11.4 | 6.1 | 3.0 |
| Expected: 12 ÷ ε | 120 | 48 | 24 | 12 | 6 | 3 |

200 repetitions of the twelve releases per budget. The lab plots it to error_budget.png.

#### [day4#averaging] Free re-releases undo the noise

*Lab 4.2 · step 5*

| Nightly copies of January, averaged | Estimate |
| --- | --- |
| 1 | 158.0 |
| 10 | 154.2 |
| 365 | 155.5 |
| true value | 154 |

- **Charged to the ledger.** Twelve nights at ε = 1/12, then refused. Or store the first noisy value and serve it again: that costs nothing.

#### [day4#check-budget] The nightly dashboard

*Checkpoint*

**Question:** The ministry's dashboard recomputes every past month each night with fresh noise at ε = 1/12. The ledger is charged only once per month. What happens?

- A. Privacy improves: the noise keeps changing
- B. Nothing: each month is still released at ε = 1/12
- C. Anyone who averages the nightly values recovers the true counts; the real spend grows every night
- D. The dashboard fails when the budget runs out

#### [day4#lab-4-2] Twelve months, one budget

Lab 4.2 · 25 min

Allocate one privacy budget across twelve monthly readmission statistics with a ledger, plot error against budget, and show why a re-release must be charged.

[D4_2_budget_ledger.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D4_2_budget_ledger.ipynb)

- [ ] The privacy unit and the contribution bound (5 min)
- [ ] The ledger that refuses to overspend (6 min)
- [ ] Twelve releases under two allocations (6 min)
- [ ] Error against budget (5 min)
- [ ] The averaging attack on free re-releases (3 min)
- [ ] ✱ Stretch: The same releases with Gaussian noise under zero-concentrated accounting

### Session 3: Analysis without pooling records

#### [day4#s3] Analysis without pooling records

*Session 3*

- Explain federated analysis, secure aggregation and clean rooms
- Compute a pooled rate with a simulated secure-aggregation protocol
- Identify what the pooled output still discloses

#### [day4#no-pooling] Analysis where the records stay

*Three ways*

- **Federated analysis.** The code travels to each site; only results come back.
- **Secure aggregation.** Sites send masked numbers; only their sum can be read.
- **Clean room.** A controlled environment where approved queries run on joined data and outputs are checked.

> **Each protects the inputs.** None protects the output by itself.

#### [day4#shares-masks] Masks that cancel in the sum

*Lab 4.3 · steps 2 and 3*

1. **1 · Agree** each pair of sites shares a random mask
2. **2 · Mask** add masks with later sites, subtract with earlier ones
3. **3 · Sum** the aggregator adds three random-looking numbers: the masks cancel

> **Result.** 2,023 readmitted of 13,258 stays: 15.26%, exact, and no site's count was ever seen.

#### [day4#dropout] A site drops out after agreeing its masks

*Lab 4.3 · step 4*

- Two masked values arrive; Rawdah's masks are left in the sum.
- The survivors reveal the masks they shared with Rawdah; the aggregator removes them: 1,369.

- **The rule that follows.** Once recovery starts, a late value from Rawdah is refused: its masks are now known, so it could be unmasked alone.

#### [day4#output-reveals] The total is exact, so subtraction works

*Lab 4.3 · step 5*

- **Two sites collude.** Total 2,023 minus Sidra's 688 and Ufuq's 681: Rawdah's 654, exactly.
- **A small subgroup.** Obstetric stays followed by readmission: total 17. The other two subtract theirs: Rawdah had 2.

> **Protect the output too:** minimum sites and people per cell, and noise on the published total (the stretch adds Laplace noise, ε = 0.5).

#### [day4#check-secagg] What the protocol protects

*Checkpoint*

**Question:** Three hospital groups compute a pooled readmission count by secure aggregation and publish it. Which statement is true?

- A. The aggregator never sees a site's count, but two sites together can compute the third's from the published total
- B. No one can learn anything about any site's count
- C. The published total is approximate because of the masks
- D. The aggregator must be trusted with every site's count

#### [day4#lab-4-3] A pooled rate without pooled records

Lab 4.3 · 25 min

Compute the cross-site readmission rate with a simulated secure-aggregation protocol, handle a site that drops out, and find what the result still discloses.

[D4_3_secure_aggregation.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D4_3_secure_aggregation.ipynb)

- [ ] Each site's counts, kept at the site (4 min)
- [ ] Additive secret shares (7 min)
- [ ] Pairwise masks and the aggregator's view (6 min)
- [ ] A site drops out (5 min)
- [ ] What the total still reveals (3 min)
- [ ] ✱ Stretch: Add noise to the total before it leaves the aggregator

### Session 4: The release decision

#### [day4#s4] The release decision

*Session 4*

- Test a data request against the sharing policy and the secondary-use rules
- Write a release decision with method, residual risk, conditions and approver
- Defend the decision against the strongest objection

#### [day4#the-request] The university's request, as it arrived

*Lab 4.4 · step 1*

| Purpose | a 30-day readmission model for a thesis and papers; "may later be offered to hospitals" |
| --- | --- |
| Data | all patient and encounter columns, record level, 2025 |
| Access | a shared drive, open to the group's students; 24 months |
| Approval | institutional approval not attached; sent by email, not on the request form |

#### [day4#national-rules] What the request is tested against

*The national frameworks*

- **Data Sharing Policy: eight principles.** Data sharing culture, single source of truth, legitimate purpose, authorized access, transparency, collective accountability, data security, ethical data use.
- **Secondary use: the applicant.** Legitimate purpose, not profit-oriented; the minimum necessary data; to the data source entity; an academic applicant through the institution with written approval; the request form.

And the PDPL: health data is sensitive; pseudonymised data remains personal data.

#### [day4#checklist] Five requirements fail before any question of method

*Lab 4.4 · step 2*

| Rule | Status |
| --- | --- |
| Academic applicant applies through the institution, with written approval | not met |
| Minimum necessary data (all columns requested; the model needs eleven features) | not met |
| Complete request form | not met |
| Authorized access, data security (a shared drive open to students) | not met |
| Legitimate purpose, transparency, collective accountability, ethical use | condition |

#### [day4#decision] Conditional approval, with every number behind it

*Lab 4.4 · steps 3 and 4*

- **Method**: the synthetic pair for development; the final model fitted by the consortium on real data from the group's code.
- **Why not an extract**: 97% unique at two known stays.
- **Utility**: AUC 0.705 against 0.706; risk ratio 1.91 inside 1.84 to 2.33.
- **Residual risk**: membership AUC 0.55 and 0.51, under 0.60.

- **Conditions and approver.** Resubmission on the form, with institutional and ethics approval; an agreement naming users, purpose and term; no onward sharing; deletion confirmed. Approver: Dr. Fadwa Al-Qassabi; adviser: Ghanem Al-Mutawakkil.

#### [day4#check-decision] The decision

*Checkpoint*

**Question:** The synthetic pair passes every attack. The university's request still lacks its academic authority's written approval. What does the board decide?

- A. Approve: the file is safe, so the approval is a formality
- B. Reject the request permanently
- C. Conditional approval: nothing moves until the request comes through the institution with written approval, on the form
- D. Send a de-identified extract instead, which needs no approval

#### [day4#lab-4-4] The decision for the university

Lab 4.4 · 25 min

Draft the decision for the university request (method, residual risk, conditions, approver) from the measured results, and test the request against the national rules for sharing and secondary use.

[D4_4_release_decision.ipynb](https://sdaiaacademy.github.io/ds-405/labs/D4_4_release_decision.ipynb)

- [ ] Read the request and the measured results (4 min)
- [ ] Test the request against the sharing principles and secondary-use rules (7 min)
- [ ] Choose the method and state the residual risk (6 min)
- [ ] Conditions and approver (5 min)
- [ ] Validate and write the record (3 min)
- [ ] ✱ Stretch: Write the strongest objection and your answer

#### [day4#wrap-up] Three things to keep

*Day 4 · wrap-up*

- **Histories identify.** Measure risk with what an adversary knows; measure every lever.
- **Budgets are accounts.** Bound each person, charge every release, cache what you publish.
- **Decide on evidence.** Rules first, then method, residual risk, conditions and a named approver.

#### [day4#next] The capstone: a release package and its defence

*Next*

Choose R-A, R-B or R-C. Contracts and pipeline, synthetic data validation, privacy method and risk, the release decision, and a repository that runs from a clone.

## Capstone: Capstone: a release package and its defence

Ten minutes each, questions included: the package, its measured results and one attack re-run live

#### [capstone#title] Capstone: a release package and its defence

*SDAIA Academy · Data Preparation at Scale: Contracts, Synthetic Data and Privacy*

Capstone: Ten minutes each, questions included: the package, its measured results and one attack re-run live

Data Science Track · 4 teaching days + capstone day · 10 min talk and demo · DS-405

#### [capstone#requests] One release package for one of three requests

*Capstone*

- **R-A · University copy.** Prof. Adnan's readmission modelling, resubmitted with approval. A synthetic pair or a code-to-data design, with its utility and attacks.
- **R-B · Public challenge.** A teaching dataset anyone can download. Must pass the attacks with margin: it is public forever.
- **R-C · Ministry dashboard.** Monthly readmission statistics for 2025 under one budget, with a ledger and small-cell rules.

Every package: contracts and pipeline, the protected or synthetic data, the utility and attack (or error) report, and the decision record.

#### [capstone#agenda] How the presentations run

*Capstone*

- **Expectations and final prep**: the rubric, a last rehearsal, then the first presentations
- **Presentations**: ten minutes each, questions and the attack re-run included
- **Review and closing**: peer feedback, the trainer's review, what next

#### [capstone#rubric] The rubric

*How presentations are scored*

| Item | Value |
| --- | --- |
| Contracts and pipeline | 25% |
| Synthetic data validation | 25% |
| Privacy method and risk | 25% |
| Release decision | 15% |
| Reproducibility | 10% |

> **Show results from at least two measured runs.** A claim without a number is a plan, not a result.

#### [capstone#format] 10 minutes for each defence, questions included

*Format*

- **1 · The request.** Which one, what it needs exactly, and the rules it was tested against.
- **2 · The package.** Method, utility and risk numbers, the decision and its conditions.
- **3 · The live attack.** The assessor names a table; you re-run one attack on it from your repository.

> **Peer feedback.** After each defence, everyone writes one strength, one question and one suggestion.

#### [capstone#running-order] Who presents when

*Running order*

| # | Presenter | Project |
| --- | --- | --- |
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |
| 4 |  |  |
| 5 |  |  |
| 6 |  |  |
| 7 |  |  |
| 8 |  |  |

#### [capstone#final-prep] Final prep · 20 minutes

*Before the first presentation*

Rehearse once, record a backup, try the demo on this screen.

#### [capstone#now-presenting] Defence, questions included

*Now presenting*

#### [capstone#review] What the presentations showed

*Trainer review*

- **Strongest patterns.** What several projects got right.
- **Common gaps.** What most projects would fix next.
- **One surprise.** Something nobody expected.

#### [capstone#what-next] Keep going

*After the course*

- **Your project stays yours:** keep it reproducible and add the next improvement you named today
- **Next in the Academy:** DS-405 has no successor in the catalog yet; DS-309 and DS-311 remain the references for single-table privacy and contracts
- **At work:** pick one release your organisation made this year and write its decision record as in Lab 4.4

#### [capstone#thanks] Thank you

*SDAIA Academy*

Data Preparation at Scale: Contracts, Synthetic Data and Privacy
