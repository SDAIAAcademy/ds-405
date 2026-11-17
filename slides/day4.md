---
course: "Data Preparation at Scale: Contracts, Synthetic Data and Privacy"
code: "DS-405"
version: "2027.1.0"
deck: "day4"
day: 4
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ds-405/slides/day4.html"
---

# Data Preparation at Scale: Contracts, Synthetic Data and Privacy

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
