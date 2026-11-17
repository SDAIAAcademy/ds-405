---
course: "Data Preparation at Scale: Contracts, Synthetic Data and Privacy"
code: "DS-405"
version: "2027.1.0"
deck: "day3"
day: 3
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ds-405/slides/day3.html"
---

# Data Preparation at Scale: Contracts, Synthetic Data and Privacy

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
