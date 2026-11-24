---
course: "Data Preparation at Scale: Contracts, Synthetic Data and Privacy"
code: "DS-405"
version: "2027.2.0"
deck: "day2"
day: 2
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ds-405/slides/day2.html"
---

# Data Preparation at Scale: Contracts, Synthetic Data and Privacy

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
- Choose log-based change data capture or a full reload for a source, from how often it is copied, how much changes and whether rows are deleted

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

Same fingerprint, same rows: the proof that a re-run day gives identical output.

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

#### [day2#reload-or-capture] Ufuq's dispensing table, copied every 15 minutes: three ways to copy it

*A source refreshed often*

| One day, 96 copies | Rows read | Deletes seen | Needs |
| --- | --- | --- | --- |
| Full reload each time | 46,272,005 | all | Nothing but read access |
| Query on an updated-at column | 6,171 | 0 of 129 | A column every writer keeps current |
| Log-based change data capture | 6,436 events | 129 of 129 | Read access to the database's change log |

One simulated day of a 480,000-line table: 4,416 inserts, 1,891 updates, 129 deletes.

**Contrast:** Rawdah's ward reference table, 1,840 rows copied weekly with about 12 changes, is simply reloaded.

#### [day2#change-log] Apply events in log order, merged on the key, and remember the last one applied

*Reading the change log*

- seq 66: insert line 480047 (copy 3)
- seq 78: update line 480047 (copy 3)
- seq 212: delete line 480047 (copy 8)

| After copy 8 | Line 480047 in the copy |
| --- | --- |
| Full reload | gone: correct |
| Updated-at query | still there, as of seq 78: wrong |
| Change log | gone: correct |

Applied with the merge of Lab 2.2: insert, update or delete by key, skipping any event at or below the sequence already applied, so a replay changes nothing.

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
- Diagnose data that was written but is not found, and register it through the table or its catalog

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

#### [day2#written-not-found] A file in the table's folder is not a file in the table

*Written, but not found*

| Sidra's curated pharmacy table | January |
| --- | --- |
| Parquet files in `month=2026-01/` | 1 |
| January files in the table's log | 0 |
| Rows read through the table | 0 |
| Rows read by a glob over the folder | 9,387 |

- job: copied January's file into the folder: "success"
- study: January: no rows
- commit: the same rows appended through the writer: version 3
- study: January: 9,387 rows

#### [day2#register-partitions] Compare what the metadata lists with what the folder holds

*Diagnose, then register*

| What you find | Register it by |
| --- | --- |
| Files copied in, or a job that stopped before its commit (a table format such as Delta) | Writing the rows through the table's writer, so a commit lists them |
| A new folder the catalog has no partition for (a Hive-style catalog) | `ALTER TABLE … ADD PARTITION`, or `MSCK REPAIR TABLE` for every new folder |
| `month=2026-1` beside `month=2026-01` | Fixing the writer's format: a filter on 2026-01 finds none of its rows |

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

Version read, fingerprint written: the figures are reproducible.

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
