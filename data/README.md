# Data

**Raw downloaded datasets should not be committed to this repository.**

Current planned sources are from:
- Anthropic Economic Index
- O*NET
- BLS OEWS
- BLS Employment Projections

**Download data resource from google drive:**
https://drive.google.com/file/d/1FYnToysUpMV1YG3GvhsTGd5vdG4GkiWj/view?usp=sharing 

Place these downloaded files in a local `data/` folder:

- `job_exposure.csv`
- `task_penetration.csv`
- `onet_task_statements.csv`
- `onet_occupation_data.csv`
- `bls_table_1_2_2025_35.csv`
- `bls_occupation_tables_2025_35.xlsx` (the official workbook may download as `occupation.xlsx`)

Official BLS workbook: https://www.bls.gov/emp/ind-occ-matrix/occupation.xlsx
The pipeline verifies all codes and shared values against the CSV before
recovering literal `None` categories. It rejects incompatible source versions.

The raw CSV/XLSX files directly inside `data/` are excluded by `.gitignore`,
so the downloaded sources will not be committed to GitHub.

Phase 2 proposed clean files are under `data/cleaned/`. These are allowed by
the ignore rules and should be tracked on `main` after team reconciliation:

- `occupation_clean_merged.csv`: one row per matched six-digit occupation
- `occupation_master.csv`: all exposure occupations with BLS match status; preserves Legislators
- `occupation_task_matches.csv`: one row per scored occupation/task pair
- `data_audit.json`: row counts, exclusions, missing values, and source fingerprints
- `bls_category_recovery.csv`: workbook cells supporting each category recovery

Generate them with `python -m analysis.run_phase2`. The audit records the actual
comparison of all five supplied pipelines and independently verified workbook
recovery. The package still needs to be merged into the team's main branch.
