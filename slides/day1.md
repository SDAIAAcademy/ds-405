---
course: "Data Preparation at Scale: Contracts, Synthetic Data and Privacy"
code: "DS-405"
version: "2027.1.0"
deck: "day1"
day: 1
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ds-405/slides/day1.html"
---

# Data Preparation at Scale: Contracts, Synthetic Data and Privacy

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
