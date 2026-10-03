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

## Run instructions

The cleaning script and dependency file are being prepared. The final command will be documented here after implementation and testing.

## Expected output files

The final workflow will create cleaned tables, a cleaning-validation report, and a labeled sample of no more than 50 cleaned rows in `outputs/` and `data/sample/`.

## Submission branch

- Branch: `cleaning-emerald`
- Branch URL: to be added after the branch is pushed to GitHub
- Final commit ID: to be added after the assignment is complete
