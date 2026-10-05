# Module 6 Data Cleaning Plan and Implementation Evidence

## Status and guardrails

The reviewed rules have now been implemented for a **national occupation-screening prototype**. Every row of all five CSVs and the relevant workbook data was inspected. The final source-to-output run passed 3,529 checks, including five saved-record checks. A fresh Python process reproduced all 41 outputs byte for byte. Original source files remain unchanged; no commit or push has been made. Sections 2–4 retain the full inspection findings and reviewed rule specification; sections 5, 7, and 8 point to actual implementation evidence.

The implementation writes to a fresh directory under `outputs/`. Lookup and analysis-view reductions are documented in a row-level ledger. IDs are loaded as text and round-trip checked. Every original column is retained alongside any parsed or corrected companion. The tracked review sample and compact evidence are copies of verified outputs.

The working tree already contained an uncommitted change to `data/README.md` before this plan was created. That file must be preserved.

## 1. Project vision, question, metric, and row grain

### Vision and user decision

The current project vision is an **AI Workforce Investment Planner** for a workforce-development agency. A program manager should be able to compare occupations using observed AI use, task exposure, workforce size, wages, and labor-market outlook, then inspect the tasks behind an occupation. The result is a shortlist for human review, not a prediction that workers will be replaced and not an automatic funding decision.

The business question for this cleaning assignment is:

> Which U.S. occupations warrant further human review for AI-transition training when observed AI use and matched task penetration are compared with national employment, outlook, wages, openings, and training requirements?

The older question in `roles/alternatives.md` names California funding. For this assignment, the user resolved that scope mismatch in favor of a **national occupation-screening prototype**. California funding conclusions still require California employment, wage, projection, program-cost, training-capacity, outcome, regional, and equity data, which are not present. No geographic reweighting is inferred from the national data.

### Main metric

The main comparison in this assignment is **observed occupation AI exposure and average matched-task penetration against national BLS labor-market context**, with task coverage shown explicitly. A priority score remains outside this assignment. Historically, the Phase 1 PDF proposed these inputs for a possible future score:

1. observed AI exposure;
2. average task penetration;
3. employment size;
4. median annual wage; and
5. projected employment change.

No priority score, weights, scaling scheme, or priority thresholds are implemented. The sketch's examples do not define cleaning rules. The output prepares validated comparisons and denominators. `task_coverage_incomplete` reports whether any task is unmatched; it is a factual coverage indicator, not a new priority threshold.

### What one row represents

| Source or proposed output | One row represents | Actual grain finding |
|---|---|---|
| `job_exposure.csv` | One six-digit SOC occupation with observed AI exposure | 756 rows and 756 unique `occ_code` values. |
| `task_penetration.csv` | Intended: one task-level penetration measurement | 17,998 rows, but only 17,991 lowercase/whitespace-normalized task keys because one normalized task appears eight times. |
| `onet_occupation_data.csv` | One full O*NET-SOC occupation record, including the two-digit suffix | 1,016 rows and 1,016 unique full codes; these collapse to 867 six-digit SOC codes. |
| `onet_task_statements.csv` | One O*NET task statement identified by a unique `Task ID` and linked to one full O*NET-SOC occupation | 18,838 rows and 18,838 unique task IDs. Task text may legitimately recur in multiple occupations. |
| `bls_table_1_2_2025_35.csv` | One unique National Employment Matrix code, either a `Summary` or `Line item` | 1,112 rows: 831 line items and 281 summaries. Both types must remain in the row-preserving table. |
| Workbook `Table 1.2` | The same 1,112 coded records, plus a title row, header row, notes, and two OOH-link columns | This is the upstream authoritative source for the derived BLS CSV. |
| Proposed occupation master | One `job_exposure` occupation, left joined to BLS and O*NET with match-status fields | Expected 756 rows; 755 have BLS line-item data and one, `11-1031`, does not. |
| Proposed BLS-complete analysis view | One occupation with exposure and a matched BLS line item | Expected 755 rows, derived from the 756-row master with a documented filter. |
| Proposed occupation-task view | One unique six-digit SOC plus normalized-task link with penetration | Current rules produce 17,760 links for the 755 BLS-complete occupations. |

## 2. Actual source inspection results

### 2.1 File integrity, dimensions, and types

All five CSV SHA-256 values match the checksums currently recorded in `data/README.md`. The workbook checksum is recorded here for reproducibility because it is not listed there.

| File | Rows × columns | SHA-256 result | Default inferred types | Types to use in the cleaning workflow |
|---|---:|---|---|---|
| `job_exposure.csv` | 756 × 3 | Match | `occ_code`, `title`: string; `observed_exposure`: float | Code and title text; exposure nullable decimal |
| `task_penetration.csv` | 17,998 × 2 | Match | `task`: string; `penetration`: float | Task text; penetration nullable decimal |
| `onet_occupation_data.csv` | 1,016 × 3 | Match | All string | All text; derived six-digit SOC kept in an additional field |
| `onet_task_statements.csv` | 18,838 × 8 | Match | `Task ID`: integer; `Incumbents Responding`: float; other fields string | IDs text; respondents nullable integer; date parsed as monthly period; other fields text/category |
| `bls_table_1_2_2025_35.csv` | 1,112 × 15 | Match | Employment, distribution, change, and openings fields infer as float; self-employment, wage, and categories infer as string | Code text; nine measure fields nullable numeric; categories text; raw marker fields retained |
| `bls_occupation_tables_2025_35.xlsx` | 12 worksheets; `Table 1.2` has 1,112 coded rows | `a7d060f0576f7d4f5b829b9a0bb4a6c11a12766d159ebb0e07aab5bd2e7583c5` | Native Excel numbers/text; no formulas in any sheet | Read `Table 1.2` with text-preserving NA settings and explicit numeric conversion |

The audit read every CSV field as a raw UTF-8 string first. No malformed-width records were found. This avoids losing leading zeros before type validation.

### 2.2 Missing counts and conversion results by column

Definitions used below:

- `blank` means an exact empty string;
- `em dash` means the source marker `—`;
- whitespace-only and common word markers such as `NA`, `N/A`, `null`, `NaN`, or `missing` were checked separately and were zero in all five CSVs;
- conversion failures exclude approved source markers. An approved marker becomes nullable; it never becomes zero.

#### `job_exposure.csv`

| Column | Blank | Em dash | Numeric/date failures | Actual range or note |
|---|---:|---:|---:|---|
| `occ_code` | 0 | 0 | N/A | All 756 match `NN-NNNN`; unique. |
| `title` | 0 | 0 | N/A | 756 unique; no trim/case collision. |
| `observed_exposure` | 0 | 0 | 0 | 0.0000–0.7451; 411 exact zeros and 345 positive values. |

#### `task_penetration.csv`

| Column | Blank | Em dash | Numeric/date failures | Actual range or note |
|---|---:|---:|---:|---|
| `task` | 0 | 0 | N/A | 17,992 exact strings and 17,991 conservative normalized keys. |
| `penetration` | 0 | 0 | 0 | 0.0000–1.0000; 16,644 zeros, 1,354 positive values, and 204 values equal to 1. |

#### `onet_occupation_data.csv`

| Column | Blank | Em dash | Numeric/date failures | Actual range or note |
|---|---:|---:|---:|---|
| `O*NET-SOC Code` | 0 | 0 | N/A | All 1,016 match `NN-NNNN.NN`; unique. |
| `Title` | 0 | 0 | N/A | 1,016 unique. |
| `Description` | 0 | 0 | N/A | 1,016 unique. |

#### `onet_task_statements.csv`

| Column | Blank | Em dash | Numeric/date failures | Actual range or note |
|---|---:|---:|---:|---|
| `O*NET-SOC Code` | 0 | 0 | N/A | 923 unique full codes; all valid format. |
| `Title` | 0 | 0 | N/A | 923 titles; each code has one title. |
| `Task ID` | 0 | 0 | 0 digit-format failures | 18,838 unique digit strings, length 1–5. It remains an ID, not a quantity. |
| `Task` | 0 | 0 | N/A | 17,579 exact task strings; recurrence across occupations is expected. |
| `Task Type` | 418 | 0 | N/A | The 418 blanks are all `Domain Source = Analyst`; they are structural, not random. |
| `Incumbents Responding` | 587 | 0 | 0 among 18,251 populated values | 15–233. All 587 blanks are Analyst or Analyst-Transition records. |
| `Date` | 0 | 0 | 0 of 18,838 using strict `%m/%Y` | 06/2006–08/2026 across 22 month values. |
| `Domain Source` | 0 | 0 | N/A | Four consistent categories. |

#### `bls_table_1_2_2025_35.csv`

| Column | Blank | Em dash | Numeric failures | Actual range or note |
|---|---:|---:|---:|---|
| `2025 National Employment Matrix title` | 0 | 0 | N/A | 1,111 titles have intentional leading spaces that encode hierarchy. |
| `2025 National Employment Matrix code` | 0 | 0 | N/A | 1,112 unique valid text codes; `00-0000` has a leading zero. |
| `Occupation type` | 0 | 0 | N/A | 831 `Line item`, 281 `Summary`. |
| `Employment, 2025` | 0 | 0 | 0 | 0.2–170,280.8 thousand. |
| `Employment, 2035` | 0 | 0 | 0 | 0.2–176,198.5 thousand. |
| `Employment distribution, percent, 2025` | 0 | 0 | 0 | 0.0–100.0 percent. |
| `Employment distribution, percent, 2035` | 0 | 0 | 0 | 0.0–100.0 percent. |
| `Employment change, numeric, 2025–35` | 0 | 0 | 0 | -752.1–5,917.6 thousand. |
| `Employment change, percent, 2025–35` | 0 | 0 | 0 | -34.4–41.0 percent. |
| `Percent self-employed, 2025` | 0 | 220 | 0 among 892 populated values | 0.0–94.6 percent; 197 line items and 23 summaries are unavailable. |
| `Occupational openings, 2025–35 annual average` | 0 | 0 | 0 | 0.0–17,461.8 thousand. |
| `Median annual wage, dollars, 2025` | 0 | 9 | 0 among 1,103 populated values | $30,890–$559,030; six line items and three summaries are unavailable. |
| `Typical education needed for entry` | 0 | 281 | N/A | Every line item is populated; all 281 summaries use `—`. |
| `Work experience in a related occupation` | 716 | 281 | N/A | All 716 blanks are line items; the workbook contains the literal category `None` in those cells. All summaries use `—`. |
| `Typical on-the-job training needed to attain competency in the occupation` | 321 | 281 | N/A | All 321 blanks are line items; the workbook contains the literal category `None` in those cells. All summaries use `—`. |

### 2.3 BLS workbook-to-CSV audit

The workbook contains 12 visible sheets: `Index`, `Table 1.1`–`Table 1.6`, `Table 1.8`–`Table 1.12`. There are no formulas. `Table 1.2` has a title row, one header row, 1,112 coded data rows, a note block, 17 columns, and units of thousands for employment and openings. The derived CSV keeps the first 15 columns and drops the two OOH-link columns. `Table 1.10` independently repeats the 1,112 codes and the shared employment, change, percent-change, and openings measures with zero value mismatches, so it can serve as a workbook-level audit without becoming another analytical input.

The 1,112 CSV records match the workbook's coded rows in order, key, title, and all numeric values. There is one material extraction error:

- 716 workbook cells containing the valid category string `None` in work experience became blank in the CSV.
- 321 workbook cells containing the valid category string `None` in on-the-job training became blank in the CSV.
- These are 1,037 text differences. No other semantic differences were found in the retained 15 columns.

The likely cause is a default NA parser treating the string `None` as missing. The future extraction must use `keep_default_na=False` and must prove that `None`, blank, `—`, and numeric zero remain distinct. The workbook will be treated as the raw authority for these two columns; the current CSV will remain unchanged as evidence of the extraction issue.

### 2.4 Exact duplicates and repeated keys

Exact full-row duplicates and repeated business keys are different checks and will remain separate in all reports.

| Dataset | Exact full-row duplicates | Candidate-key result |
|---|---|---|
| BLS CSV | 0 groups; 0 rows | BLS code unique; 0 repeated groups. |
| Job exposure | 0 groups; 0 rows | `occ_code` unique; 0 repeated groups. |
| O*NET occupation | 0 groups; 0 rows | Full O*NET-SOC code unique; 0 repeated groups. |
| O*NET task statements | 0 groups; 0 rows | `Task ID`, `(full code, Task ID)`, and `(full code, Task)` are each unique. |
| Task penetration | 2 exact groups, 8 rows involved, 6 beyond-first copies | Two exact task strings repeat four times each. After lowercase/whitespace normalization, they form one 8-row group with 7 beyond-first records. All eight values are 0.7263. |

Expected repeated relationship keys are not erroneous duplicates:

- O*NET occupation full codes collapse to 867 six-digit SOC values. Seventy-six SOC groups contain 225 records, or 149 records beyond one per six-digit SOC. The largest group, `15-1299`, has 10 full codes. Every group has exactly one `.00` base record.
- Exact O*NET task text repeats across occupations in 397 groups containing 1,656 rows. Under lowercase/whitespace normalization, 398 groups contain 1,658 rows. This is an expected many-to-many relationship.
- `(full O*NET-SOC Code, normalized task)` is unique. After full codes collapse to six-digit SOC, `(soc_code, normalized task)` has 24 two-row duplicate groups. These 24 extra links may be consolidated only in a derived aggregation table.

### 2.5 Category and text consistency

- No case/trim variants were found in the low-cardinality category columns.
- `Task Type`: 14,071 `Core`, 4,349 `Supplemental`, 418 blank Analyst records.
- `Domain Source`: 13,097 `Incumbent`, 5,154 `Occupational Expert`, 418 `Analyst`, and 169 `Analyst - Transition`.
- BLS title indentation is intentional: depths are 0 spaces for 1 row, 2 for 22, 4 for 95, 6 for 476, and 8 for 518. Raw titles must remain unchanged. A stripped display title is allowed only as a separate field.
- Stripping BLS title indentation produces three title collisions across different codes/types: `Cashiers`, `Fishing and hunting workers`, and `Tour and travel guides`. Titles therefore cannot be keys.
- Conservative task normalization finds one `Web`/`web` case variant, the eight-row duplicate group described above.
- Removing punctuation would collapse 31 additional task groups and is unsafe. Three punctuation-only pairs have conflicting values:
  - `Advise students on academic and vocational curricula and on career issues.` = 0.7735, versus the comma variant = 0.8157;
  - `Compile, administer, and grade examinations or assign this work to others.` = 0.9669, versus the comma variant = 0.9134;
  - `Maintain customer records using automated systems.` = 0.7239, versus the comma variant = 1.0.

The proposed task key therefore lowercases, collapses whitespace, and trims only. It will not remove punctuation, stem words, or perform semantic/fuzzy matching in this cleaning assignment.

### 2.6 Suspicious values to flag, not automatically change

| Finding | Actual result | Treatment proposed |
|---|---|---|
| Exposure zeros | 411/756 = 54.37% | Preserve as real zero; do not convert to missing. |
| Penetration zeros | 16,644/17,998 = 92.48% | Preserve as real zero; do not impute or discard. |
| Penetration equals 1 | 204 rows | Flag for review only; values pass the documented 0–1 domain. |
| Old O*NET task dates | Range 06/2006–08/2026; 4,804 rows predate 2020 | Retain. Add a task-vintage field/flag; do not infer that old means invalid. |
| Negative BLS change | 223 line items have negative numeric change and 232 have negative percent change | Legitimate projections; preserve. |
| Zero BLS distribution/openings | 509 line items show 0.0 for 2025 distribution, 506 for 2035, and 3 show 0.0 openings | Preserve. These are published/rounded zeros, not missing. |
| High self-employment | Maximum 94.6% for `41-9091` | Passes domain; retain and flag as an extreme. |
| High wage | Maximum $559,030 for `29-1243` | Passes domain; retain and flag as an extreme. |
| High exposure | Maximum 0.7451 for `15-1251` | Passes domain; retain and flag as an extreme. |
| Missing BLS wage | Six detailed occupations have `—` | Retain row and marker; cleaned numeric value is null, never zero. |
| BLS `None` categories lost in CSV | 716 work-experience and 321 training values | Re-extract from workbook after approval; never infer from blank alone. |

### 2.7 Possible merge keys, relationships, and actual coverage

| Relationship | Key and cardinality | Actual result |
|---|---|---|
| Job exposure → BLS detailed occupations | Six-digit SOC; one-to-one among unique codes | 755/756 job occupations match (99.87%). `11-1031 Legislators` is the only job-only code. BLS has 76 additional line-item codes. |
| Job exposure → O*NET occupation | Six-digit SOC; one job to one or more full O*NET codes | 756/756 match. The `.00` record provides a deterministic base description while suffix records remain preserved. |
| O*NET task → O*NET occupation | Full O*NET-SOC code; many tasks to one occupation | All 18,838 task rows and all 923 task-bearing codes match; zero title mismatches. Ninety-three occupation full codes have no task rows. |
| Penetration task → O*NET task | Lowercase + collapsed whitespace + trim; one penetration key may match multiple occupation-task rows | 17,429 unique task keys intersect. 17,436/17,998 penetration rows match (96.88%); 562 unique penetration keys do not. 18,680/18,838 O*NET task rows match (99.16%); 149 unique O*NET keys, 158 rows, do not. |
| O*NET full-code task links → six-digit SOC task links | Derived `(soc_code, task_normalized)` | 18,838 raw rows become 18,814 unique SOC-task links because 24 links recur after suffix collapse. Of these, 18,656 have penetration data. |
| BLS-complete occupation subset → matched task links | Six-digit SOC | 17,760 matched links for 755 occupations. All 755 have at least one match. |

Title checks support, but do not replace, code joins: all 756 job titles match the chosen O*NET `.00` title after conservative normalization, and all 755 job/BLS overlapping titles match after removing BLS indentation and normalizing case.

## 3. Reviewed cleaning rules by column

Every rule below creates a new field or output. Raw columns remain unchanged. These reviewed rules are implemented in `code/clean_module6.py`; canonical parsed/category fields are companions rather than replacements for the raw columns.

### 3.1 `job_exposure.csv`

| Column | Proposed rule | Why it fits the question | Exceptions/risks | Verification |
|---|---|---|---|---|
| `occ_code` | Read as text; retain raw; validate `^\d{2}-\d{4}$`; copy to canonical `soc_code` without numeric conversion. | It is the occupation join key. | No current invalid values; future leading-zero codes must survive. | 756 populated, 756 unique, 0 format failures; round-trip exact string comparison. |
| `title` | Preserve as supplied; use only for display and title cross-checks, never as a join key. | Occupation names help users interpret the ranking. | Case/punctuation can differ across sources even when codes match. | 0 blanks; verify normalized titles for matched codes and log disagreements. |
| `observed_exposure` | Parse to nullable decimal; retain 0–1 units; assert `0 <= value <= 1`; keep raw text beside parsed value in audit output. | Primary AI-use component. | Zero is valid. Do not silently display it as a percent without labeling a separate presentation field. | 756 conversions, 0 failures, 0 out of range, min 0, max 0.7451, 411 zeros. |

### 3.2 `task_penetration.csv`

| Column | Proposed rule | Why it fits the question | Exceptions/risks | Verification |
|---|---|---|---|---|
| `task` | Preserve raw; add `task_normalized` using lowercase, whitespace collapse, and trim only. Add duplicate-group and source-row-count fields. Keep all 17,998 rows in the row-preserving table. | Connects AI penetration to occupation tasks and supports top-task evidence. | Punctuation removal creates false equivalences with conflicting values. | 17,991 normalized keys; one repeated normalized key with eight rows; regression-test the three conflicting punctuation pairs. |
| `penetration` | Parse to nullable decimal; retain 0–1 units; assert range. A derived lookup may consolidate a repeated normalized key only when every nonmissing value is identical; otherwise stop and send the group to review. | Used in occupation task averages and top-five tasks. | Zero is valid. Duplicate handling changes totals and denominators. | 17,998 conversions, 0 failures/out-of-range; duplicate group has one distinct value, 0.7263. Reconcile raw sum 1,201.2546 to normalized-lookup sum 1,196.1705. |

### 3.3 `onet_occupation_data.csv`

| Column | Proposed rule | Why it fits the question | Exceptions/risks | Verification |
|---|---|---|---|---|
| `O*NET-SOC Code` | Read as text; retain full code; validate `^\d{2}-\d{4}\.\d{2}$`; derive, do not replace with, the six-digit `soc_code`. Add `is_base_record` for suffix `.00`. | Full codes preserve O*NET detail; six-digit codes enable BLS/Anthropic joins. | Collapsing suffixes is many-to-one, not deduplication. | 1,016 unique valid full codes; 867 derived SOCs; 76 multi-record groups; every group has exactly one `.00`. |
| `Title` | Preserve; use the `.00` record's title only in a documented six-digit display bridge. | Provides readable occupation labels and a join-quality check. | Detailed suffix titles are not interchangeable with the base title. | 0 blank; `.00` title matches all 756 job titles after normalization. |
| `Description` | Preserve; use the `.00` description in the derived occupation view. | Supports the requested occupation drill-down, not the score itself. | Do not concatenate detailed descriptions or silently select a non-base suffix. | 0 blank; one selected base description for each of 867 six-digit SOCs. |

### 3.4 `onet_task_statements.csv`

| Column | Proposed rule | Why it fits the question | Exceptions/risks | Verification |
|---|---|---|---|---|
| `O*NET-SOC Code` | Preserve full text code; validate format; derive six-digit SOC separately. | Connects each task to an occupation. | Multiple full codes may collapse to one SOC. | 0 invalid; reconcile 923 full codes to 798 six-digit task-bearing SOCs. |
| `Title` | Preserve and validate against `onet_occupation_data.csv` on full code. | Human-readable audit field. | Not a key. | All 923 codes match exactly; 0 title conflicts. |
| `Task ID` | Read and write as text; validate digits; never use as a numeric measure. | Stable task-record identifier for audit and difficult-record tests. | No leading zeros appear now, but future releases may contain them. | 18,838 populated/unique; 0 format failures; exact string round-trip. |
| `Task` | Preserve raw; create the same conservative `task_normalized` key as the penetration file. Do not deduplicate globally. In a derived six-digit SOC-task bridge only, consolidate the 24 repeated pairs and retain contributing Task IDs/full codes. | Enables task matching without erasing legitimate task reuse across occupations. | Global task-text uniqueness is false; punctuation normalization is unsafe. | Raw row count remains 18,838; derived bridge has 18,814 links; audit exactly 24 consolidated extras. |
| `Task Type` | Preserve `Core`/`Supplemental`; map blank to nullable with `missing_reason = analyst_not_classified`, not to either category. | May support later task interpretation. | All 418 blanks are Analyst records and appear structural. | Cross-tab Task Type by Domain Source; counts remain 14,071/4,349/418. |
| `Incumbents Responding` | Parse populated values to nullable integer; keep blank null with `missing_reason = analyst_source_not_applicable`. | Useful for task evidence quality, but not a current score input. | Blank must not become zero. | 18,251 valid integers 15–233; 587 structural blanks; 0 failures. |
| `Date` | Strictly parse `%m/%Y`; retain original string and create a month field such as `YYYY-MM-01`; add vintage flags without dropping old rows. | Documents when task evidence was last associated with the record. | This is source vintage, not an outcome time series. | 18,838 valid dates, 0 failures, range 06/2006–08/2026; row counts by year reconcile. |
| `Domain Source` | Preserve four published categories; no standardization beyond validation. | Explains structural missingness and evidence provenance. | `Analyst - Transition` is distinct from `Analyst`. | Exact four-category counts and cross-tab checks. |

### 3.5 BLS Table 1.2

| Column | Proposed rule | Why it fits the question | Exceptions/risks | Verification |
|---|---|---|---|---|
| `2025 National Employment Matrix title` | Preserve raw indentation; add a stripped display title; never use title as a key. | Displays occupation and preserves hierarchy. | Three stripped-title collisions prove title is not unique. | Raw values round-trip; indentation-depth counts and collision list remain unchanged. |
| `2025 National Employment Matrix code` | Read/write text; validate `^\d{2}-\d{4}$`; retain summary codes and leading zeros. | Main occupation join key and hierarchy identifier. | `00-0000` and codes ending `-0000` are valid summaries, not missing detail. | 1,112 populated/unique/valid; exact check for `00-0000`. |
| `Occupation type` | Preserve `Summary`/`Line item`; use only `Line item` in a separate analytical view. | Prevents hierarchical double counting while retaining all source evidence. | Summary rows are excluded from a view, never deleted from the clean table. Never infer type from the code: seven valid line items end in `0` (`13-1020`, `13-2020`, `29-2010`, `31-1120`, `39-7010`, `47-4090`, `51-2090`). | 831 + 281 = 1,112; exclusion audit lists every summary code and reason. |
| `Employment, 2025` | Parse decimal; retain thousands; name output `employment_2025_thousands`. | Workforce-size input. | Do not multiply to persons unless a separately named, documented derived field is approved. | 1,112 conversions, 0 failures; range and BLS-total reconciliation. |
| `Employment, 2035` | Parse decimal; retain thousands; name explicitly. | Supports projection checks and context. | Published precision is rounded. | 1,112 conversions; range and total reconciliation. |
| `Employment distribution, percent, 2025` | Parse decimal percent; preserve published value. | Optional context/control, not currently a score input. | Hundreds of valid line items round to 0.0; line-item percentages should not be expected to sum to 100. | 0 failures; compare each row to employment/total within published rounding tolerance. |
| `Employment distribution, percent, 2035` | Same rule as 2025 distribution. | Optional projected context/control. | Same rounding issue. | 0 failures; row-level rounding check. |
| `Employment change, numeric, 2025–35` | Parse decimal; retain thousands and published sign. | Labor-market change in worker-count terms. | The displayed 2025/2035 values are rounded, so subtraction can differ by 0.1 thousand. | 0 failures; all differences from displayed subtraction within 0.1 thousand; do not overwrite. |
| `Employment change, percent, 2025–35` | Parse and preserve the BLS-published percentage. Do not recompute it from displayed rounded fields. | Proposed score input and chart axis. | Hidden source precision causes material differences for small occupations. | 0 failures; regression-test `51-2061` at -6.1% even though displayed employment is 0.2 → 0.2. |
| `Percent self-employed, 2025` | Treat `—` as unavailable/null with raw marker retained; parse all other values as percent. | Context for workforce structure; not a current score input. | `—` is not zero. | 892 values, 220 markers, 0 failures; 0–94.6 domain check. |
| `Occupational openings, 2025–35 annual average` | Parse decimal; retain thousands and published zero. | Measures continuing demand and appears in drill-down. | Openings include growth and replacement; they are not the same as employment change. | 1,112 conversions; 0 failures; total and 3 zero line-item checks. |
| `Median annual wage, dollars, 2025` | Treat `—` as unavailable/null; parse other values as dollars; retain unit. | Economic context and a proposed score component pending approval. | Six line items have no wage; null must not become zero. | 1,103 values, 9 markers, 0 failures; range check and missing-code audit. |
| `Typical education needed for entry` | Preserve published categories; keep summary-row `—` as not applicable. | Training-access context. | Do not impose an ordinal score during cleaning. | Nine raw categories/markers; all 831 line items populated. |
| `Work experience in a related occupation` | Re-extract from workbook with `keep_default_na=False`; restore literal `None` only where the workbook says `None`; keep summary `—` distinct. | Training-feasibility context requires distinguishing no experience from missing data. | Never infer `None` from a CSV blank without the workbook key/value match. | All 1,112 code-aligned workbook/CSV rows checked; expected 716 `None`, 115 other line-item categories, and 281 summary `—`; 0 unexplained blanks. |
| `Typical on-the-job training needed to attain competency in the occupation` | Same workbook-authoritative restoration rule; retain `None` as a valid category. | Directly supports training/reskilling context. | `None`, blank, and `—` are different states. | Expected 321 `None`, 510 other line-item categories, 281 summary `—`; 0 unexplained blanks. |

## 4. Reconciliation, calculations, and denominators

### 4.1 Row-count reconciliation

The future pipeline will stop if any equality below fails unexpectedly.

| Stage | Reconciliation |
|---|---|
| Raw inputs | 756 jobs; 17,998 penetration rows; 1,016 O*NET occupations; 18,838 O*NET tasks; 1,112 BLS rows. |
| BLS row types | 831 line items + 281 summaries = 1,112. The clean BLS table remains 1,112 rows. |
| Job/BLS join | 755 matched + 1 job-only = 756 job-master rows; 755 matched + 76 BLS-only = 831 line items. |
| O*NET occupation bridge | 1,016 full-code rows → 867 six-digit groups; 149 detailed-suffix extras are preserved in the full table and logged in the bridge. |
| Penetration lookup | 17,998 raw rows → 17,991 normalized keys; exactly 7 beyond-first normalized records belong to one reviewed group. |
| O*NET task bridge | 18,838 raw task rows → 18,814 unique six-digit SOC-task links; exactly 24 suffix-collapse extras are logged. |
| Task matching | 18,814 unique links → 18,656 with penetration; the difference is 158 unmatched links. |
| BLS-complete occupation tasks | 17,760 matched links across 755 occupations. |
| Proposed top-five view | 3,774 rows: 754 occupations contribute five tasks and `39-5093` contributes four. Ties will use a documented deterministic secondary sort, not source order. |

No unmatched or summary record disappears silently. A row-preserving master and a row-level `join_audit`/`view_exclusion` file will show its status and reason.

### 4.2 BLS totals and units

Employment, numeric change, and openings are in **thousands**; wages are in **dollars**; BLS percentages are percentage values such as `3.5`, not decimal fractions such as `0.035`. Exposure and penetration are 0–1 fractions. The workflow will not combine or re-express these units without explicit field names and a logged calculation.

| Measure (thousands where applicable) | BLS total row | Sum of 831 line items | Difference, line sum minus total |
|---|---:|---:|---:|
| Employment 2025 | 170,280.8 | 170,267.2 | -13.6 |
| Employment 2035 | 176,198.5 | 176,184.5 | -14.0 |
| Employment change 2025–35 | 5,917.6 | 5,917.9 | +0.3 |
| Annual openings | 17,461.8 | 17,460.7 | -1.1 |

These differences are consistent with the workbook note that subcategories may not add because of rounding and excluded occupational data. They will be reported, not forced to zero. Summary and line-item rows will never be summed together because that would double count the hierarchy.

As a negative control, summing employment across all 1,112 hierarchical rows produces 756,448.7 thousand for 2025, which is obviously double counted and must never be used as a workforce denominator.

Line-item distribution percentages sum to 94.0% for 2025 and 94.8% for 2035 because 509 and 506 detailed values respectively round to 0.0. The row-level published percentages agree with employment divided by the total within the expected one-decimal rounding tolerance; the column sum is not a valid control total.

### 4.3 Calculation checks

- `Employment, 2035 - Employment, 2025` versus published numeric change: 285 rows differ by 0.1 thousand because the displayed source fields are independently rounded. The maximum absolute difference is 0.1. Preserve the published change.
- Recalculating percent change from displayed rounded employment/change is unsafe: 269 rows differ by more than 0.10 percentage point and the maximum difference is 6.1 points. Preserve the BLS-published percent.
- Workbook `Table 1.10` has zero mismatches with `Table 1.2` for all shared measures across all 1,112 codes. Its separations and openings components also reconcile within 0.1 thousand at published precision. This is an independent control, not a reason to duplicate those columns in the main analysis.
- Annual openings are a 2025–35 **annual average**, while numeric employment change is a **ten-year total change**. They cannot be added or compared as if they share a period. Any later openings decomposition must use the Table 1.10 definition and the correct `/10` time conversion.
- The BLS wage footnote covers nonfarm wage-and-salary workers and excludes self-employed workers and some other groups. Its population is not identical to total employment. Occupation medians cannot be summed or simply averaged to reproduce the all-occupation median.
- Exposure: raw `n=756`, sum `58.1944`, mean `0.07697672`. The BLS-complete subset has `n=755`, the same sum because unmatched Legislators has exposure zero, and mean `0.07707868`. Any reported mean must state its population.
- Employment-weighted exposure over the 755 BLS-matched occupations has an employment denominator of `154,223.4` thousand and a weighted mean of `0.12865751`. It must not be presented as the unweighted occupation mean.
- Penetration: raw `n=17,998`, sum `1,201.2546`, mean `0.06674378`; normalized-key lookup `n=17,991`, sum `1,196.1705`, mean `0.06648716`. Duplicate policy therefore changes the denominator and must be named.

### 4.4 Average task penetration denominator

The proposed occupation-level calculation is:

`sum(penetration for unique matched (soc_code, task_normalized) links) / count(unique matched links)`

It will be named `average_matched_task_penetration`, not simply `average_task_penetration`. It will be accompanied by:

- `total_unique_onet_tasks`;
- `matched_unique_tasks`;
- `task_match_rate = matched_unique_tasks / total_unique_onet_tasks`; and
- an explicit low-coverage flag.

Unmatched tasks will remain null and will not be imputed as zero because zero is a real penetration measurement. Among the 755 BLS-complete occupations, 648 have 100% task-key coverage and 107 have partial coverage. The minimum is `23-2011 Paralegals and Legal Assistants`: 7 of 12 tasks, or 58.33%.

The priority-score denominator and weighting cannot be checked until the user approves the score formula. When defined, the workflow will show every component's population, scale, direction, missing policy, weight, and contribution, and will reconcile the final score back to those components.

## 5. Five difficult-record verification cases

The expected results below were encoded in `code/module6_record_expectations.json` before running the pipeline. The five checks now read saved CSV outputs, not merely in-memory objects. All five match. Full original, expected, actual, reason and match-status evidence is in [five_record_checks.csv](docs/module6_evidence/five_record_checks.csv). The table retains the original inspection context; the following actual-output results complete it.

| Case | Original source value(s) | Expected result after approved cleaning | Actual now from inspection | Post-run assertion |
|---|---|---|---|---|
| 1. Leading-zero ID: BLS `00-0000` | Code `00-0000`, type `Summary`, employment 2025 `170280.8` thousand | Code remains exact text; row remains in the 1,112-row clean table; it is excluded only from the 831-row line-item view with a logged reason | Exact code and values present; pass at source stage | `repr(code) == '00-0000'`; one clean row; one summary-view exclusion; no numeric coercion |
| 2. Lost valid category: BLS `11-1011` | Workbook OJT value is literal `None`; current CSV value is blank | Clean OJT category is text `None`, raw workbook provenance retained, missing flag false | Workbook/CSV mismatch confirmed; current CSV blank is not trustworthy | `ojt == 'None'`; `ojt_is_missing == False`; workbook code/value join is one-to-one |
| 3. Hidden precision: BLS `51-2061` | Employment 0.2 → 0.2, numeric change 0.0, published change -6.1%, openings 0.0, self-employed `—` | Preserve the two real zeros and published -6.1%; only self-employment becomes nullable with raw marker `—` | All five source values confirmed | No recomputation overwrites -6.1; zero/null/marker states match expected exactly |
| 4. Unmatched occupation: job `11-1031` | `Legislators`, exposure 0.0; no BLS Table 1.2 row | Keep it in the 756-row occupation master with `bls_match_status = job_only` and null BLS fields; include it in the exclusion audit for the optional 755-row BLS-complete view | One and only one job-only code confirmed | Master count 756; one unmatched code exactly `11-1031`; BLS-complete count 755; no source row deletion |
| 5. Denominator risk: SOC `23-2011` | 12 unique O*NET tasks, 7 matched penetration values, 5 unmatched; exposure 0.2927 | Use denominator 7 for `average_matched_task_penetration`, report coverage 7/12 = 58.33%, and do not turn five unmatched tasks into zeros | Matched-only mean = 0.1338571429; zero-imputed mean would be 0.0780833333 and is rejected | Actual clean mean equals matched-only result; task counts equal 7 + 5 = 12; low-coverage flag set |

Additional automated regression checks will cover the eight-row press-release duplicate group, the three conflicting punctuation pairs, O*NET Analyst Task ID `15267` with structural blanks, and the BLS stripped-title collisions.

Actual saved-output results: case 1 retains text `00-0000`, `Summary`, employment `170280.8`, and `is_line_item=False`; case 2 yields `ojt="None"`, an empty missing-reason field, original CSV blank, and workbook `"None"`; case 3 retains 0.2 → 0.2, change 0, published -6.1%, openings 0, and null self-employment with `source_unavailable`; case 4 retains `11-1031`, exposure 0, `job_only`, and null BLS employment; case 5 yields 12 total tasks, 7 matched, 5 unmatched, coverage 0.583333333333, mean 0.133857142857, and incomplete coverage true. Each case has `match_status=PASS`.

## 6. Which datasets are necessary

| Dataset/source | Decision | Reason |
|---|---|---|
| `job_exposure.csv` | Necessary | Supplies the occupation-level AI exposure used in the main comparison and proposed score. |
| BLS workbook `Table 1.2` | Necessary as raw authority | Supplies national employment, outlook, openings, wage, education, experience, and training and is needed to recover valid `None` categories. |
| `bls_table_1_2_2025_35.csv` | Necessary only as the current derived input/audit comparison; not an independent source | It is convenient for the existing script but contains 1,037 category extraction errors. It should be reproducibly rebuilt from the workbook or replaced by a verified clean extract. |
| `task_penetration.csv` | Necessary if task exposure or top tasks remain in scope | Supplies task-level AI penetration. It has no occupation code and cannot work alone. |
| `onet_task_statements.csv` | Necessary together with task penetration | Provides the occupation-task bridge and task metadata. |
| `onet_occupation_data.csv` | Necessary for the requested description drill-down and base-record validation; optional for a score-only table | Supplies descriptions and validates full O*NET codes, but does not add a proposed numeric score component. |
| Other BLS workbook sheets | Not necessary as cleaning inputs for the current scope | Several are summaries or rankings derived from the same projections and would create duplication. They may be used as independent spot-checks. `Table 1.10` and `Table 1.12` would require a separately approved expansion of the question. |
| OpenAI Signals | Not necessary/currently unavailable in the repository | The documented activity-period grain lacks a confirmed occupation crosswalk and is not part of the five CSVs. |
| Separate California labor/program data | Necessary only if the business question remains California-specific | The present national BLS data cannot support a California funding recommendation. |

## 7. Implemented workflow, outputs, and evidence

### 7.1 Reproducible source-to-output pipeline

`code/clean_module6.py` runs the reviewed rules in order: source hash/header/width
checks; all-row profiling; row-preserving typed companions; workbook category
re-extraction; reviewed lookup/bridge reductions; cardinality-validated joins;
task metrics with denominators; reconciliation; saved-output record checks;
sample generation; and final source-hash verification.

Dependencies are pinned in `requirements-cleaning.txt`. The tested interpreter
is CPython 3.11.4. The pipeline refuses an existing output directory, unexpected
source hash, failed conversion, conflicting normalized task values, invalid key,
unexpected merge cardinality, or unexplained count/total difference. It records
`FAILED.json` and exits nonzero on an error.

`code/module6_record_expectations.json` records the five expected outcomes before
execution. `code/verify_module6.py` launches a new Python process, compares every
output file, checks the submitted sample, and verifies that an altered temporary
source copy is rejected. Run commands and all 41 expected outputs are listed in
[code/README.md](code/README.md).

### 7.2 Actual final output

The final output directory is `outputs/module6/`. All six original hashes are
unchanged. All five clean source tables preserve their original rows and raw
columns. The canonical BLS companions restore 716 literal `None` experience
values and 321 literal `None` OJT values.

| Output | Actual rows | Meaning |
|---|---:|---|
| `job_exposure_clean.csv` | 756 | All original occupation exposure records |
| `task_penetration_clean.csv` | 17,998 | All original task measurements, including duplicate evidence |
| `onet_occupation_clean.csv` | 1,016 | All full O*NET-SOC records |
| `onet_task_statements_clean.csv` | 18,838 | All task records and IDs |
| `bls_table_1_2_clean.csv` | 1,112 | All BLS summary and line-item records, with workbook-derived companions |
| `task_penetration_lookup.csv` | 17,991 | Unique conservative task keys, identical-value consolidation only |
| `onet_occupation_soc_bridge.csv` | 867 | One unique .00 description per six-digit SOC |
| `onet_soc_task_bridge.csv` | 18,814 | Unique SOC/task links, retaining contributing IDs |
| `occupation_master.csv` | 756 | Every job occupation, including unmatched Legislators |
| `occupation_analysis_bls_complete.csv` | 755 | Explicit optional BLS-complete subset |
| `occupation_tasks.csv` | 17,760 | Matched task links for those 755 occupations |
| `top_tasks_by_occupation.csv` | 3,774 | Deterministically selected top-five task display |
| `examples/module6_cleaned_sample.csv` | 50 | Forty-eight master records and two labeled BLS controls |

Every reduction is accounted for in `before_after_row_counts.csv` and the
row-level `view_reductions.csv`. In particular, the 18,814-link bridge reduces
to 18,656 measured links (158 unknown), then to 17,760 eligible occupation links
(896 outside the BLS-complete job set), then to 3,774 displayed links (13,986
outside each occupation's top five). These reductions never remove source rows.

### 7.3 Decision log and review copies

[cleaning_decision_log.csv](docs/module6_evidence/cleaning_decision_log.csv)
contains 16 implemented decisions, each with a rule, reason, check, exceptions,
authorization, expected recoveries/reductions and code hash. Actual reductions
and category-cell recoveries are independently recorded by the run.

Compact evidence is copied into `docs/module6_evidence/` so it is eligible for
Git tracking. Full row-level audits stay under ignored `outputs/` and can be
recreated. The only submitted cleaned-data sample has 50 rows; its selection is
explained in [examples/README.md](examples/README.md).

The exact filename `requirements.txt` is ignored, so the pinned dependency file
uses `requirements-cleaning.txt`. No change to `.gitignore` was necessary.
`.gitattributes` preserves LF bytes for the sample/evidence. The existing
`data/README.md` edit is preserved. New deliverables are uncommitted and pending
staging on `cleantaotianchen123`; no commit or push occurred.

### 7.4 Actual verification and failed development check

The final run passed **3,529 checks; 0 failed**. The five saved-record checks all
passed. A fresh-process run recreated **41 of 41 files byte for byte**, and the
submitted sample matched. A deliberate one-value change in disposable copied
input was rejected by the source hash guard, as expected.

The first development run failed the sample-count check (49 instead of 50):
`31-1120` was assumed to be in the job master, but it is BLS-only. The sample
was corrected to include it explicitly as a BLS control. This was a sample
construction defect, not a source correction. The failed run remains in
`outputs/module6-run1/`; it is not the final result.

## 8. Exact Module 6 checklist and evidence

The following items use the assignment headings from
`Module_6_Homework.pdf`, pages 2–3, supplied by the user, in their original order.
They replace the earlier provisional interpretation; that interpretation is not
presented as the official checklist.

Status reflects completed work, not merely a plan. No item is marked Not
applicable because all fourteen apply. Item 3 remains Unresolved only for
upstream release/download metadata; source preservation itself is verified.
Documenting limitations (item 14) is Done even though the listed limitations
remain.

| # | Assignment item | Status | Concrete evidence or explanation |
|---:|---|---|---|
| 1 | State the project vision and question | Done | Section 1 defines the national screening question and exposure/task-versus-BLS comparison. `code/README.md` and `outputs/module6/cleaning_report.md` use that scope. No score/weights/thresholds are invented. |
| 2 | Define one row | Done | Section 1 gives each source/output grain. [repeated_key_summary.csv](docs/module6_evidence/repeated_key_summary.csv) verifies full-code, Task ID, SOC and task-key cardinalities; the occupation master has 756 unique SOC rows. |
| 3 | Preserve the source | Unresolved | Preservation is Done: [source_manifest.csv](docs/module6_evidence/source_manifest.csv) records identical before/after SHA-256 for all six files; code never writes into `data/`, and `data/README.md` is preserved. Sources, load settings and local snapshot hashes are in `code/README.md`. Exact Anthropic/O*NET vendor release IDs and original download dates were not supplied, and BLS download provenance is unverified. These metadata cannot be inferred from filesystem dates; obtain the original download records to complete this item. |
| 4 | Inspect columns and types | Done | `outputs/module6/source_schema.csv` and `clean_schema.csv` cover every column. [conversion_checks.csv](docs/module6_evidence/conversion_checks.csv) reports zero unexpected numeric/date failures. IDs remain text; Date parses strictly as month/year; source markers are counted separately. |
| 5 | Standardize text | Done | `outputs/module6/text_changes.csv` gives every original/derived text pair. Task matching only lowercases, collapses whitespace and trims. BLS stripped titles are separate fields. Three conflicting punctuation pairs remain distinct; saved ID round trips and case 1 preserve `00-0000`. |
| 6 | Investigate duplicates | Done | [exact_duplicate_summary.csv](docs/module6_evidence/exact_duplicate_summary.csv) separates 2 exact groups / 8 involved rows / 6 extra copies from [repeated_key_summary.csv](docs/module6_evidence/repeated_key_summary.csv). Full sources retain all rows; the normalized lookup consolidates 7 extras, the SOC/task bridge 24, and the description bridge 149, with lineage and row-level reasons. |
| 7 | Handle missing data | Done | [before_after_missing.csv](docs/module6_evidence/before_after_missing.csv) covers every source column and its canonical companion. Workbook recovery restores 716 + 321 literal None values; 418 task-type and 587 respondent structural blanks remain null with reasons. Numeric unavailable markers become nullable companions, never zeros. |
| 8 | Check suspicious values | Done | `outputs/module6/suspicious_values.csv`, `task_vintage_counts.csv` and `validation_checks.csv` record retained zeros, extrema, negative projections, unavailable values and source vintage. Strict date conversion has 0 failures. BLS published -6.1% is preserved for `51-2061`; unusual valid values are retained. |
| 9 | Verify merges | Done | [merge_summary.csv](docs/module6_evidence/merge_summary.csv) and full `merge_key_audit.csv` show both sides: 755 job/BLS matches, 1 job-only, 76 BLS-only; 17,429 shared normalized task keys, 562 penetration-only and 149 O*NET-only. Code uses explicit one-to-one/many-to-one validation and no unexpected fanout. Master retains 756 rows. |
| 10 | Reconcile changes | Done | [before_after_row_counts.csv](docs/module6_evidence/before_after_row_counts.csv) reconciles all sources/views; `outputs/module6/view_reductions.csv` explains each excluded/consolidated row. [total_reconciliation.csv](docs/module6_evidence/total_reconciliation.csv) checks published totals, 831 detailed occupations, 755 matches and 76 BLS-only occupations. |
| 11 | Check calculations | Done | [metric_denominators.csv](docs/module6_evidence/metric_denominators.csv) names each metric population and denominator; `task_denominators.csv` gives all SOC counts/coverage. Independent Decimal calculations verify every master occupation's task mean. Missing group keys fail; missing penetration is excluded from the mean denominator, measured zero is included. Rounding residuals and units are documented in section 4 and `published_calculation_checks.csv`. |
| 12 | Verify individual records | Done | Five expectations were authored in `code/module6_record_expectations.json` before the run. [five_record_checks.csv](docs/module6_evidence/five_record_checks.csv) records original, expected, actual, reason and match status from saved outputs; **5 PASS**. Section 5 explains the cases. |
| 13 | Test reproducibility | Done | `code/verify_module6.py` restarted execution in a fresh subprocess using pinned dependencies and original inputs. [reproducibility.json](docs/module6_evidence/reproducibility.json) reports **41 identical files**, identical submitted 50-row sample, and correct rejection of deliberate source drift. Commands are in `code/README.md`. |
| 14 | Document remaining limitations | Done | Section 9, `code/README.md`, and `outputs/module6/cleaning_report.md` explicitly document national/California mismatch, Claude coverage, release metadata, SOC-version uncertainty, unmatched tasks, task vintage, wage population, rounding and submission work. Each limitation states its effect or missing evidence. |

## 9. Remaining limitations and review handoff

- **Geography:** the implemented scope is national. California funding conclusions
  require California data and training/program evidence.
- **Measure meaning:** observed Claude use does not establish displacement or
  causality. A priority score, its weights and its thresholds are outside scope.
- **Provenance:** exact local content is fixed by hash, but vendor release IDs,
  download dates, licensing confirmation and external BLS download authenticity
  still need source records. No such metadata is invented.
- **Task coverage:** unmatched tasks remain unknown. Paralegals has 7/12 coverage;
  the matched-task mean can differ from an all-task mean. No fuzzy match or
  imputation is justified here.
- **Classification and vintage:** six-digit code/title agreement is evidence of
  match feasibility, not proof of identical classification versions. O*NET
  record dates span 2006–2026 and suffix detail remains in the full clean table.
- **BLS arithmetic/populations:** published rounding and excluded occupational
  data explain nonzero control differences. Wages have a different population
  from employment; occupation medians cannot be averaged into a national median.
- **Submission:** the current branch is `cleantaotianchen123`. Code, dependency
  file, README, compact evidence and 50-row sample are ready for review in
  Git-eligible paths. No commit or push occurred. The assignment's Gradescope
  PDF and notebook are now completed; see `code/README.md` and the submission
  receipts for fresh-kernel and page-review results. Actual submitted commit
  ID remains pending; no commit or push is authorized yet.

The reviewed cleaning rules have been executed. No additional permission is
needed to inspect these results. The remaining source metadata gaps and final
publishing steps are explicitly separate from the completed pipeline and artifacts.
