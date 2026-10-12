# Module 6 Project Data Cleaning Assignment

Project: AI Workforce Investment Planner
Student: Brahmani Mundhe
Branch: cleaning-brahmanimundhe
Branch URL: https://github.com/emeraldo26/DSO576-Project-/tree/cleaning-brahmanimundhe
Commit ID: 3f0d691dd46f17f68c991fe256079b93f51cd85b

## 14-item checklist

1. State the project vision and question
Status: Done
Evidence or explanation: The project vision is to help a workforce-development agency prioritize occupations for AI-transition training and reskilling support. The business question is: which occupations deserve review first when AI exposure, task penetration, employment size, wages, and labor-market outlook are compared? Main comparison: observed AI exposure versus 2025-35 employment change, with employment and wage context. See README.md and outputs/cleaning_report.md.

2. Define one row
Status: Done
Evidence or explanation: job_exposure is one six-digit SOC occupation; task_penetration is one normalized task; O*NET task statements are one occupation-task link; O*NET occupation data is one O*NET-SOC occupation; BLS Table 1.2 includes summary and line-item occupation rows, so only line-item occupations are retained for the analytical BLS file. Keys are documented in outputs/cleaning_evidence.json.

3. Preserve the source
Status: Done
Evidence or explanation: Original files remain unchanged in data/. The script reads them and writes cleaned outputs to outputs/cleaned/. Source versions are the downloaded CSV files present locally on 2026-10-04: Anthropic Economic Index files, O*NET occupation/task files, and BLS Table 1.2 2025-35.

4. Inspect columns and types
Status: Done
Evidence or explanation: All files are loaded as text first. Numeric fields are converted after inspection. Conversion failures were 0 for observed_exposure, 0 for penetration, and 0 for the relevant BLS numeric columns. O*NET task dates convert from MM/YYYY to YYYY-MM with 0 failures.

5. Standardize text
Status: Done
Evidence or explanation: Titles, descriptions, labels, and task text are stripped and internal whitespace is collapsed. A separate lowercase task_key is created for matching, while display text keeps meaningful punctuation and capitalization. Leading zeros and SOC punctuation are preserved as text IDs.

6. Investigate duplicates
Status: Done
Evidence or explanation: Exact duplicate rows were checked in every source. task_penetration had 7 repeated normalized task rows; all had the same penetration value, so one copy was kept. Repeated O*NET six-digit SOC codes are expected because detailed O*NET suffixes can share a six-digit SOC.

7. Handle missing data
Status: Done
Evidence or explanation: Missing values are counted before cleaning in outputs/cleaning_evidence.json. Analytical fields are not imputed. Missing text-only training/experience descriptions are labeled 'Not specified in source' so blanks do not look like a script error. Missing O*NET task type is labeled 'Missing in source'.

8. Check suspicious values
Status: Done
Evidence or explanation: Exposure and penetration were checked to be between 0 and 1. Suspicious exposure rows: 0; suspicious penetration rows: 0. BLS negative employment rows: 0; negative wage rows: 0.

9. Verify merges
Status: Done
Evidence or explanation: The occupation merge uses six-digit SOC codes and expects one Anthropic occupation to at most one BLS line item. Anthropic occupations: 756; BLS line-item occupations: 831; merged occupation rows: 755; unmatched Anthropic occupations: 1. Task matching uses normalized task text, then O*NET SOC code; matched O*NET task rows: 18680 of 18838.

10. Reconcile changes
Status: Done
Evidence or explanation: Starting rows are listed for all sources in outputs/cleaning_evidence.json. BLS summary rows removed: 281. Final merged occupation rows: 755. BLS employment represented in the merged table totals 154223.4 thousand workers.

11. Check calculations
Status: Done
Evidence or explanation: Average task penetration is calculated only over matched task records; missing task matches are left blank and not included in the denominator. Occupations with matched task data: 755. Group keys missing after SOC normalization are excluded from merges; count is shown in evidence JSON.

12. Verify individual records
Status: Done
Evidence or explanation: Five record checks are included below and in outputs/cleaning_evidence.json. Each check compares the original value, expected result, and actual cleaned result.

13. Test reproducibility
Status: Done
Evidence or explanation: From the repository root, run: python3 code/clean_project_data.py. The command recreates outputs/cleaned/*.csv, samples/cleaned_sample_50_rows.csv, outputs/cleaning_evidence.json, outputs/cleaning_report.md, and docs/module6_cleaning_assignment_brahmani_mundhe.pdf. The script was restarted and run from source files.

14. Document remaining limitations
Status: Done
Evidence or explanation: The data uses national BLS projections rather than California-specific demand. Anthropic exposure reflects observed Claude use, not all workplace AI. Exact task-text matching may miss semantically similar tasks. The output should support human review, not automatic funding decisions or claims that AI causes displacement.

## Cleaning decision log

| Rule | Reason | Check |
|---|---|---|
| Load source CSVs as text. | Protect SOC codes, punctuation, and leading zeros before conversion. | Column profiles and missing counts written to outputs/cleaning_evidence.json. |
| Normalize SOC codes to six-digit NN-NNNN. | Anthropic, O*NET, and BLS use compatible SOC roots but O*NET includes suffixes. | Five record checks confirm O*NET suffix removal and SOC merge behavior. |
| Trim text and collapse internal whitespace. | BLS titles contain indentation and task text needs stable matching. | Record check for BLS 11-1011 title and task_key generation. |
| Create lowercase task_key while preserving display task text. | Matching should ignore capitalization but not rewrite the displayed task. | Matched task counts and top task outputs recreated by script. |
| Convert numeric metric columns after cleaning display symbols. | Analysis needs numeric exposure, penetration, employment, wage, openings, and growth fields. | Failed conversion counts are zero for required numeric columns. |
| Remove BLS summary rows from analytical BLS output. | Summary rows are not individual occupations and would double count employment. | Summary rows removed count is in evidence JSON. |
| Deduplicate repeated task_penetration keys. | One normalized task appears eight times with the same penetration. | Seven extra rows removed; zero penetration conflicts found. |
| Prefer O*NET .00 description when multiple O*NET suffixes share one six-digit SOC. | The dashboard operates at six-digit SOC level. | Record check confirms 11-1011.00 is the base description for 11-1011. |
| Leave unmatched occupations and task gaps visible. | Unmatched records are evidence about coverage, not errors to hide. | Unmatched occupation count and task-match counts reported. |

## Five record checks

| Record | Original | Expected | Actual | Match |
|---|---|---|---|---|
| O*NET occupation 11-1011.00 | O*NET-SOC Code=11-1011.00 | six-digit soc_code=11-1011 | soc_code=11-1011 | True |
| O*NET occupation 11-1011.03 | detailed suffix .03 shares six-digit SOC with Chief Executives | base .00 description remains preferred for SOC 11-1011 | base preferred=True | True |
| O*NET task 8823 | Date=08/2023 and mixed-case task sentence | date_month=2023-08 and lowercase task_key for matching | date_month=2023-08; task_key starts=direct or coordinate an o | True |
| BLS occupation 11-1011 | title has leading spaces; employment=291.6; wage=213990 | trimmed title, numeric fields preserved as numbers | title=Chief executives; employment=291.6; wage=213990 | True |
| Merged occupation 15-1252 | Software Developers appears in Anthropic and BLS | merged row with exposure, BLS growth, wage, and task count | exposure=0.288; growth=10.2; tasks=17 | True |

## Codex suggestion checked

Codex suggested using normalized task text to merge task_penetration.csv with O*NET task statements. I checked that suggestion by counting matches on the full data after lowercasing and whitespace cleanup, then reviewing task examples such as O*NET task 8823. The check showed that exact text matching works for many records but is conservative, so the report keeps unmatched-task limitations visible instead of claiming full coverage.

## Data sample choice

The committed sample file samples/cleaned_sample_50_rows.csv contains up to 50 cleaned occupation rows selected from high AI exposure, low AI exposure, high projected growth, projected decline, missing task-match cases, and records with 'Not specified in source' training/experience fields. This makes the review sample more useful than simply taking the first 50 rows.

## Generated files

- outputs/cleaned/job_exposure_clean.csv
- outputs/cleaned/task_penetration_clean.csv
- outputs/cleaned/onet_task_statements_clean.csv
- outputs/cleaned/onet_occupation_data_clean.csv
- outputs/cleaned/bls_occupations_clean.csv
- outputs/cleaned/occupation_clean_merged.csv
- outputs/cleaned/top_tasks_by_occupation_clean.csv
- samples/cleaned_sample_50_rows.csv
- outputs/cleaning_evidence.json
- outputs/cleaning_report.md
- docs/module6_cleaning_assignment_brahmani_mundhe.pdf
