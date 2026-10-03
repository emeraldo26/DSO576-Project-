# AI Workforce Investment Planner — Data Cleaning

## Project question

Which occupations may deserve priority for AI-transition training and reskilling support based on observed AI exposure, task penetration, employment, wages, and projected employment change?

## Data sources and versions

The raw files are stored locally under `data/raw/` and are preserved unchanged.

| File | Source/version |
|---|---|
| `job_exposure.csv` | Anthropic Economic Index; downloaded September 2026 |
| `task_penetration.csv` | Anthropic Economic Index; downloaded September 2026 |
| `onet_occupation_data.csv` | O*NET Resource Center occupation data; downloaded September 2026 |
| `onet_task_statements.csv` | O*NET task statements bundled for this project; downloaded September 2026 |
| `bls_table_1_2_2025_35.csv` | U.S. Bureau of Labor Statistics, 2025–35 National Employment Matrix Table 1.2 |
| `bls_occupation_tables_2025_35.xlsx` | U.S. Bureau of Labor Statistics, 2025–35 occupation tables |

Source pages and file checksums are documented in `data/raw/README.md`.

## Planned cleaning rules

These rules are written before the cleaning transformations are applied:

1. Keep the raw source files unchanged and write cleaned data to `outputs/`.
2. Preserve occupation and task identifiers as strings so leading zeros are not lost.
3. Strip unnecessary leading/trailing whitespace from text fields without changing meaningful text.
4. Convert percentage, wage, employment, openings, and penetration fields to numeric values and record failed conversions.
5. Count exact duplicate rows and repeated identifiers separately before deciding whether any records can be removed.
6. Report missing values before and after cleaning; do not fill values without a documented reason.
7. Validate merge keys and report unmatched records and row-count changes.
8. Keep unusual but valid observations and flag values that require review rather than silently deleting them.

## Initial inspection evidence

The inspection script is `code/inspect_raw_data.py`. It reads every CSV and every worksheet in the raw Excel workbook without changing them and writes ignored evidence files to `outputs/`.

- `job_exposure.csv`: 756 rows; `occ_code` is unique.
- `task_penetration.csv`: 17,998 rows; six exact duplicate rows were found, and task text includes case differences that need a matching key.
- `onet_occupation_data.csv`: 1,016 rows; `O*NET-SOC Code` is unique.
- `onet_task_statements.csv`: 18,838 rows; `Task ID` is unique, while occupation codes repeat because this is a task-level table. Missing values occur in `Task Type` and `Incumbents Responding`.
- `bls_table_1_2_2025_35.csv`: 1,112 rows; 831 line-item rows and 281 summary rows. Several employment and wage fields require numeric conversion because they contain formatted text.
- The BLS workbook contains multiple tables; the project-level BLS extract is preserved as the CSV above and will be used for the occupation-level analysis.

## Cleaning decision log — initial rules

| Rule | Reason | Check/evidence |
|---|---|---|
| Preserve every raw file and write transformed files separately. | The assignment requires the source to remain unchanged and the results to be reproducible. | Compare raw file checksums and confirm no script writes under `data/raw/`. |
| Keep SOC and O*NET-SOC identifiers as strings; derive a documented six-digit SOC join key without overwriting the original. | Numeric conversion can remove leading zeros, and O*NET includes `.00` extension codes. | Report identifier lengths, invalid formats, and unmatched keys before and after each merge. |
| Strip surrounding whitespace and collapse repeated internal whitespace in text fields; preserve the original text columns. | Whitespace can prevent valid task/title matches, but original wording must remain auditable. | Compare original and normalized values and count changed records. |
| Create a case-insensitive normalized task key for matching. | `task_penetration.csv` contains case variants of otherwise matching task text. | Count normalized-key duplicates and identify conflicting penetration values. |
| Deduplicate task-penetration rows only when the normalized task and penetration value agree; flag conflicts for review. | Exact repeated observations do not add information, but conflicting values should not be silently averaged. | Report duplicate groups, conflict count, and rows retained. |
| Convert BLS formatted numeric fields to numeric values and record failed conversions. | Wages and percentage fields include text formatting that prevents reliable calculations. | Compare non-null counts before and after conversion and list failed values. |
| Keep BLS summary and line-item rows in the cleaned source, but use line-item rows for occupation-level joins unless the analysis explicitly needs summaries. | Summary rows are valid aggregates but can double-count occupations in a merge. | Report row counts by `Occupation type` and verify that joins use the intended subset. |
| Keep missing `Task Type`, `Incumbents Responding`, and BLS training/experience values as missing unless a documented project rule supports an alternative. | Missingness may represent unavailable information, not zero. | Report missing counts before and after cleaning and explain metric-specific denominators. |

## Run instructions

The raw files must be available under `data/raw/`. Install the dependencies and run the scripts from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 code/inspect_raw_data.py
python3 code/clean_data.py
```

The inspection script records the starting state. The cleaning script applies the documented rules without overwriting `data/raw/`.

## Expected output files

The workflow creates cleaned tables and validation evidence in the ignored `outputs/` directory, including:

- `occupation_clean.csv`
- `job_exposure_clean.csv`
- `task_penetration_clean.csv`
- `onet_occupation_clean.csv`
- `onet_task_statements_clean.csv`
- `bls_table_1_2_clean.csv`
- `cleaning_row_counts.csv`
- `cleaning_missing_values.csv`
- `cleaning_duplicates.csv`
- `cleaning_conversions.csv`
- `cleaning_merges.csv`
- `cleaning_keys.csv`
- `unmatched_exposure_records.csv`
- `record_checks.csv`

The labeled submission sample is written to `data/sample/occupation_clean_sample.csv` and contains no more than 50 cleaned rows.

`record_checks.csv` contains five checks covering an unmatched occupation, a duplicate task, a missing wage, a missing task type, and a successful occupation merge. Each check records the original value, expected result, actual result, and whether the result matched the expectation.

The first run found 17,998 raw task-penetration rows and retained 17,991 after removing duplicate normalized task/penetration pairs. It converted all nonmissing numeric values without failed conversions. The occupation merge matched 755 of 756 AI-exposure records to BLS line-item records. The unmatched record is `11-1031 — Legislators`: it is present in the exposure data but absent from the BLS line-item extract, so it is preserved and flagged in `unmatched_exposure_records.csv` rather than dropped.

## Submission branch

- Branch: `cleaning-emerald`
- Branch URL: to be added after the branch is pushed to GitHub
- Final commit ID: to be added after the assignment is complete
