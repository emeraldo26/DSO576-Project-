# Project Data Cleaning Assignment

**Project:** AI Workforce Investment Planner  
**Student:** Xiru Zhang  
**Branch:** `cleaning-xiru-zhang`  
**Branch URL:** https://github.com/emeraldo26/DSO576-Project-/tree/cleaning-xiru-zhang (available after push)  
**Commit ID:** TO BE ADDED AFTER COMMIT

## 14-item checklist

### 1. State the project vision and question

**Status: Done.** The project supports a workforce-development agency in screening occupations for possible AI-transition training. The business question is: Which occupations combine higher observed AI exposure with labor-market characteristics that justify human review for reskilling support? The main comparisons are exposure, 2025 employment, projected 2025–35 employment change, annual openings, wage, and task penetration. See `cleaning_submission/README.md`.

### 2. Define one row

**Status: Done.** One row in `cleaned_occupations.csv` represents one six-digit SOC occupation, uniquely identified by `soc_code`. The independent validation found 0 duplicate `soc_code` values. One row in `cleaned_top_tasks.csv` represents a task within a six-digit SOC occupation and is uniquely identified by (`soc_code`, cleaned task text); validation found 0 duplicate composite keys. Source row definitions differ: `job_exposure.csv` has one SOC occupation per row; `task_penetration.csv` has one task observation per row; O*NET task rows use `Task ID`; O*NET occupation rows use the full O*NET-SOC code; and BLS contains summary and line-item occupation rows.

### 3. Preserve the source

**Status: Unresolved.** The preservation check is complete: the five original CSV files are loaded from `data/` but never overwritten, and their hashes match the package manifest. They were downloaded from the shared project Google Drive package on October 4, 2026. The BLS file identifies the 2025–35 projection period. However, the shared package does not document the precise Anthropic release or O*NET database version, so the source-version requirement is not fully resolved. `validate_cleaning.py` calculated SHA-256 hashes before and after two complete runs; all five hashes were unchanged. Official links and checksums are in `cleaning_submission/source_manifest.md`, and validation evidence is in `cleaning_submission/validation_report.json`.

### 4. Inspect columns and types

**Status: Done.** SOC codes and text remain strings. Exposure, penetration, employment, projected change, openings, and wage are converted to numeric values. Commas are removed before numeric conversion; BLS em dashes are treated as documented missing values. There were zero unexpected failed conversions in the four BLS measures used in the final table. Evidence: `outputs/cleaning_audit.json`, under `failed_numeric_conversions_excluding_documented_em_dash_missing`.

### 5. Standardize text

**Status: Done.** Leading/trailing whitespace is removed and internal whitespace is collapsed. This changed 1,111 BLS occupation titles, which use indentation for display. Task keys are also lowercased for matching, while readable task text keeps its original capitalization. SOC codes remain strings in `NN-NNNN` form, preserving leading zeros and punctuation. Example: the indented BLS title `Chief executives` becomes `Chief executives` without its leading spaces; O*NET code `11-1011.00` becomes join key `11-1011`.

### 6. Investigate duplicates

**Status: Done.** Exact duplicate-row counts were: job exposure 0, task penetration 6, O*NET tasks 0, O*NET occupations 0, and BLS 0. Repeated source-ID counts were separately checked: job `occ_code` 0, O*NET `Task ID` 0, full O*NET occupation code 0, and BLS matrix code 0. Six identical task-penetration rows were removed so the same task/value would not receive extra weight. O*NET sub-occupations can share a base six-digit SOC; 24 repeated (`soc_code`, normalized task) matches were removed after the task join. The base `.00` O*NET occupation description is preferred when several O*NET records map to one SOC. Evidence: `outputs/cleaning_audit.json` and `cleaning_submission/validation_report.json`.

### 7. Handle missing data

**Status: Done.** Before cleaning, semantic missing counts (null, blank, or em dash) were: O*NET `Task Type` 418; O*NET `Incumbents Responding` 587; BLS line-item wage 6; BLS related experience 716; and BLS training 321. The final 755 matched occupations contain 3 missing wages, 646 missing related-experience values, and 295 missing training values; occupation descriptions, average task penetration, and matched-task counts have 0 missing values. Counts fall partly because only matched line-item occupations enter the final table, not because values were imputed. BLS em dashes are converted to missing, and no mean, zero, or invented category is substituted. Evidence: `missing_before_cleaning` and `missing_after_cleaning` in `cleaning_submission/validation_report.json`.

### 8. Check suspicious values

**Status: Done.** All job exposure and task penetration values are within [0, 1]. Employment and annual openings are nonnegative, and all nonmissing wages are positive. All O*NET month/year values parse under the strict `%m/%Y` format. All job and BLS line-item SOC codes match the expected six-digit structure after extraction. Negative employment changes are retained because occupational decline is possible: the observed range includes −34.4% for Word Processors and Typists and 41.0% for Nurse Practitioners. Exposure ranges from 0.0 to 0.7451. These extremes are flagged as difficult cases, not automatically treated as errors. Evidence: `range_checks` in `outputs/cleaning_audit.json`, `difficult_case_examples` in `cleaning_submission/validation_report.json`, and the submitted sample.

### 9. Verify merges

**Status: Done.** The occupation join uses the six-digit SOC key and validates as one-to-one between Anthropic occupations and BLS line items. It produces 755 rows from 756 Anthropic occupations. Independent set comparison identifies one unmatched key, `11-1031 Legislators`. The analysis table is intentionally limited to occupations successfully matched to BLS, so Legislators is excluded from that table but retained in the unmatched log. This is a scope rule for the matched analysis—not a rule that rows with missing values must always be deleted. Task text is matched after lowercasing and whitespace cleanup; 17,436 of 17,998 Anthropic task rows match O*NET. Tasks are deduplicated and aggregated before the occupation join. As a multiplication check, matched BLS employment totals 154,223.4 thousand both before and after the join, and matched annual openings total 15,607.2 thousand both before and after. Evidence: `merge` in `outputs/cleaning_audit.json` and the passed total-preservation checks in `cleaning_submission/validation_report.json`.

### 10. Reconcile changes

**Status: Done.** Source counts are 756 job-exposure rows, 17,998 task-penetration rows, 18,838 O*NET task rows, 1,016 O*NET occupation rows, and 1,112 BLS rows. Cleaning removes 6 exact task duplicates. The BLS analysis excludes 281 summary rows and retains 831 line items. The final occupation table has 755 rows: 756 Anthropic occupations minus one independently identified unmatched occupation. Employment and annual-openings totals for the 755 matched BLS occupations are exactly preserved after joining (154,223.4 and 15,607.2 thousand, respectively). Wages are medians and therefore are not meaningfully summed.

### 11. Check calculations

**Status: Done.** `average_task_penetration` uses only matched, nonmissing task values; `matched_task_count` supplies its denominator for each occupation. Missing task matches do not become zero, and missing group keys cannot enter a group. Nonmissing denominators are: exposure 755, employment 755, projected change 755, annual openings 755, wage 752, and average task penetration 755. Occupation-level measures remain source values. The current assignment does not calculate a priority score because weights have not been justified. Evidence: `metric_nonmissing_denominators` in `cleaning_submission/validation_report.json`.

### 12. Verify individual records

**Status: Done.** Five identifiable source records are checked against expectations derived from the cleaning rules before their corresponding output values are read. Each check includes a source file and stable record identifier. The validator does not replace an expectation with the actual output when a check fails. All five automated checks passed. Xiru Zhang then visually compared the displayed source and cleaned values and confirmed all five decisions on October 4, 2026. Details also appear in `cleaning_submission/five_record_checks.csv` and `cleaning_submission/validation_report.json`.

| Source file | Record identifier | Original value | Expected result and reason | Actual result | Passed |
|---|---|---|---|---|---|
| `onet_occupation_data.csv` | `O*NET-SOC Code=11-1011.00` | Code `11-1011.00`; title `Chief Executives` | `soc_code=11-1011`, title retained. Remove only the O*NET detail suffix so the record can join on six-digit SOC. | `soc_code=11-1011`; title `Chief Executives` | Yes |
| `bls_table_1_2_2025_35.csv` | `2025 National Employment Matrix code=11-1011` | Title `'      Chief executives'` | `bls_title=Chief executives`. Leading spaces are table indentation, not meaningful title text. | `bls_title=Chief executives` | Yes |
| `bls_table_1_2_2025_35.csv` | `2025 National Employment Matrix code=27-2011` | Title `Actors`; median wage `—` | Wage remains missing (`NaN`). An em dash means unavailable and must not become zero or an imputed value. | `median_annual_wage_2025=NaN` | Yes |
| `onet_task_statements.csv` + `task_penetration.csv` | `Task ID=8825` | O*NET code `11-1011.00`; task “Analyze operations … policy change.”; penetration `0.831` | `soc_code=11-1011`, `task_rank=1`, penetration `0.831`. Normalized exact task text should connect the task to its observed penetration and base SOC. | `soc_code=11-1011`; `task_rank=1`; penetration `0.831` | Yes |
| `job_exposure.csv` | `occ_code=11-1031` | Title `Legislators`; exposure `0.0` | Absent from `cleaned_occupations.csv` and retained in the unmatched log. This analysis is intentionally limited to occupations successfully matched to BLS. The record is not excluded merely because it has missing values; it is outside the matched analysis table because no BLS line-item key is available. | Absent from matched output and retained in the unmatched log | Yes |

### 13. Test reproducibility

**Status: Done.** A new temporary Python 3.9 virtual environment was created on October 4, 2026. Installing only `requirements-cleaning.txt`, then running `python3 code/validate_cleaning.py`, completed with exit code 0 and status `PASS`. The validator ran the cleaning pipeline twice; hashes of `cleaned_occupations.csv`, `cleaned_top_tasks.csv`, and the 50-row sample were identical across runs, while all source-file hashes remained unchanged. It produced 755 occupations and 3,774 top-task rows. The validator exits nonzero on a failed check.

### 14. Document remaining limitations

**Status: Done.** Exact Anthropic and O*NET release versions are not recorded in the shared package. Exact-text task matching misses semantically equivalent wording. Collapsing O*NET sub-occupations to six-digit SOC can hide specialization differences. Anthropic measures observed Claude use, not all workplace AI use. BLS projections are national estimates and do not establish local need. The data cannot prove that AI caused job loss or that training will improve outcomes. Priority measures and weights remain undecided.

## Cleaning decision log

| Rule | Reason | Check/evidence |
|---|---|---|
| Keep downloaded CSV files unchanged and write results elsewhere. | Preserve an auditable source and enable reruns. | Script reads `data/`; outputs go to `outputs/` and `cleaning_submission/`. |
| Store SOC as text and extract `NN-NNNN`. | Preserve punctuation/leading zeros and connect O*NET suffix codes to BLS. | Invalid job and BLS line-item SOC counts are 0. |
| Trim and collapse whitespace; lowercase only task join keys. | Remove display formatting without damaging readable labels. | 1,111 BLS titles changed; readable task text is retained. |
| Convert numeric display values; map em dash to missing. | Enable comparison without treating unavailable values as zero. | Zero unexpected failed conversions for final BLS measures. |
| Remove six exact task-penetration duplicates. | Avoid duplicate weighting. | 17,998 source rows become 17,992 unique task/value rows. |
| Retain BLS line items and exclude 281 summaries. | Summary rows are not individual occupations and would double count. | 1,112 total BLS rows become 831 line items. |
| Prefer O*NET `.00` description for one description per base SOC. | Multiple detailed O*NET codes can map to one six-digit SOC. | Occupation merges validate as one-to-one. |
| Aggregate matched tasks before joining occupations. | Prevent task rows from multiplying employment/wage values. | Final output remains one row per SOC. |
| Limit the analysis table to occupations matched to BLS and retain an unmatched log. | The current analysis compares AI exposure with BLS labor-market measures. An unmatched source record remains valid source data but is outside that matched comparison; this is not a general missing-value deletion rule. | 755 matches; `11-1031 Legislators` is excluded from the matched table and retained in the unmatched log. |
| Do not impute missing training/descriptive data. | No defensible replacement is available. | Missing counts remain explicit in the audit. |

## How I checked a Codex suggestion

Codex suggested extracting the six-digit SOC portion from O*NET-SOC codes so they could join BLS codes. The code checks this suggestion rather than accepting it without evidence: it asserts that `11-1011.00` becomes `11-1011`, counts invalid normalized codes, compares source key sets independently, and requires the occupation merge to validate as one-to-one. The automated checks passed, invalid-code counts were zero, and 755 of 756 Anthropic occupation codes matched BLS line items. The validator identified and logged `11-1031` as unmatched. Xiru Zhang visually compared all five source and cleaned records and confirmed the decisions on October 4, 2026.

## Sample selection

The submitted 50-row sample is deterministic. It includes the five lowest and highest values for exposure, projected growth, and wage; up to ten rows containing missing values; and evenly spaced SOC records to fill the remaining slots. This emphasizes difficult and boundary cases rather than presenting only the first 50 rows.
