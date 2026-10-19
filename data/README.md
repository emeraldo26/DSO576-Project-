# Raw inputs and provenance

Raw downloaded datasets are local inputs and are intentionally excluded from Git.
Run the commands below from the repository root. All six files must be placed
directly in `data/` with these exact names:

| File | Grain and source evidence |
|---|---|
| `job_exposure.csv` | One Anthropic Economic Index occupation row (`occ_code`, title, observed exposure); release/observation period is not supplied. |
| `task_penetration.csv` | Anthropic Economic Index task penetration; release/observation period is not supplied. |
| `onet_task_statements.csv` | O*NET task statements bundled for this analysis; exact O*NET release is not supplied. |
| `onet_occupation_data.csv` | O*NET occupation descriptions; exact O*NET release is not supplied. |
| `bls_table_1_2_2025_35.csv` | BLS Employment Projections Table 1.2, 2025–35; 1,112 rows and 15 columns. |
| `bls_occupation_tables_2025_35.xlsx` | BLS all-occupation workbook containing Table 1.2 and Table 1.10. |

The supplied Drive link is:
`https://drive.google.com/file/d/1FYnToysUpMV1YG3GvhsTGd5vdG4GkiWj/view?usp=sharing`.
Its preview identifies `AI_transition_project_datasets.zip`. A read-only check of
that archive found all six files above, with the hashes listed in the audit below.
The archive's access is account/permission dependent; confirm access with the
course owner if a fresh clone cannot download it. No raw data is uploaded here.

The independently verifiable official BLS source page is
https://www.bls.gov/emp/tables/occupational-projections-and-characteristics.htm,
which links the all-occupation XLSX (`occupation.xlsx`). The current workbook
was saved under the canonical name above. The exact workbook hash is recorded
in `data/cleaned/data_audit.json`; the BLS page may later serve a newer release.

## Download and generate the BLS CSV

1. Download the workbook linked from the BLS page above.
2. Save/rename it to `data/bls_occupation_tables_2025_35.xlsx`.
3. Read worksheet `Table 1.2` with row 2 as the header and the first 15 columns.
4. Keep rows whose `2025 National Employment Matrix code` is nonblank and write
   those 15 columns as UTF-8 CSV to `data/bls_table_1_2_2025_35.csv` with
   `index=False`. This reproduces the committed CSV byte-for-byte for the
   supplied workbook; the pipeline then verifies both files and Table 1.10.

For example:

```python
import pandas as pd

frame = pd.read_excel(
    "data/bls_occupation_tables_2025_35.xlsx",
    sheet_name="Table 1.2", header=1, usecols=range(15),
    dtype={"2025 National Employment Matrix code": "string"},
)
frame = frame.loc[frame["2025 National Employment Matrix code"].notna()]
frame.to_csv("data/bls_table_1_2_2025_35.csv", index=False)
```

Verify every input with SHA-256 (macOS/Linux):

```bash
shasum -a 256 data/*.{csv,xlsx}
```

Expected hashes for the supplied snapshot are in `data/cleaned/data_audit.json`.
The Anthropic and O*NET release identifiers and observation period are not
present in the supplied files, so they remain explicitly unavailable.

Phase 2 proposed clean files are under `data/cleaned/`. These are allowed by
the ignore rules and should be tracked on `main` after team reconciliation:

- `occupation_clean_merged.csv`: one row per matched six-digit occupation
- `occupation_master.csv`: all exposure occupations with BLS match status; preserves Legislators
- `occupation_task_matches.csv`: one row per scored occupation/task pair
- `data_audit.json`: row counts, exclusions, missing values, and source fingerprints
- `bls_category_recovery.csv`: workbook cells supporting each category recovery

Generate them with `python -m analysis.run_phase2`. The audit records row counts,
hashes, workbook recovery, and the comparison of the supplied pipelines.
