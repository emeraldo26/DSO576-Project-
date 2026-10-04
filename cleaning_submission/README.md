# Module 6 data-cleaning submission — Xiru Zhang

## Project and question

The **AI Workforce Investment Planner** supports a workforce-development agency in screening occupations for possible AI-transition training. The business question is: **Which occupations combine higher observed AI exposure with labor-market characteristics that justify further human review for reskilling support?** The main comparisons are observed AI exposure, employment, projected employment change, annual openings, wage, and matched task penetration. This is a screening tool, not evidence that AI caused job loss.

## GitHub submission identifiers

- Branch: `cleaning-xiru-zhang`
- Branch URL: `https://github.com/emeraldo26/DSO576-Project-/tree/cleaning-xiru-zhang` (will work after the branch is pushed)
- Verified code commit ID: `69643db70a0239091bf87fc74bf4c7e29e8a13e4`

This ID identifies the code, sample, report, and validation evidence that passed the documented checks. A later documentation commit adds the ID and exported PDF without changing the verified cleaning logic.

## Data sources and versions

The source package was downloaded from the project Google Drive link on **October 4, 2026**. It contains:

- Anthropic Economic Index: `job_exposure.csv` and `task_penetration.csv`;
- O*NET: `onet_task_statements.csv` and `onet_occupation_data.csv`;
- BLS Employment Projections 2025–35, Table 1.2: `bls_table_1_2_2025_35.csv`.

The package does not state an Anthropic release number or O*NET database version. That metadata remains a limitation and should be confirmed with the person who prepared the shared package. The original CSV files remain unchanged in `data/` and are ignored by Git. Official source links and verified package checksums are recorded in `cleaning_submission/source_manifest.md`.

## Reproduce the results

Use Python 3.9 or newer from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-cleaning.txt
python3 code/clean_data.py
python3 code/validate_cleaning.py
```

Expected generated files:

- `outputs/cleaned_occupations.csv` — 755 occupation rows;
- `outputs/cleaned_top_tasks.csv` — 3,774 occupation-task rows;
- `outputs/cleaning_audit.json` — counts, missingness, range checks, and merge evidence;
- `outputs/five_record_checks.csv` — original, expected, and actual results for five records;
- `cleaning_submission/validation_report.json` — submitted copy of independent validation, source/output hashes, totals, denominators, and reproducibility evidence;
- `cleaning_submission/sample_cleaned_occupations.csv` — 50 shareable cleaned rows.

The full outputs are reproducible and intentionally ignored by Git. The 50-row sample is committed with the submission. It deliberately includes low/high exposure, growth, and wage cases; rows with missing output values; and evenly spaced occupation codes, rather than taking only the first 50 rows.

## Submitted files

- `code/clean_data.py`: cleaning, joins, checks, and output generation.
- `code/validate_cleaning.py`: independent validation that runs the pipeline twice and fails on discrepancies.
- `requirements-cleaning.txt`: pinned dependency.
- `cleaning_submission/cleaning_report.md`: checklist, decision log, verification, and limitations.
- `cleaning_submission/sample_cleaned_occupations.csv`: 50-row sample.
- `cleaning_submission/five_record_checks.csv`: machine-readable five-record evidence.
- `cleaning_submission/validation_report.json`: machine-readable full validation evidence.
- `cleaning_submission/source_manifest.md`: official links, download date, version limitation, and source checksums.
