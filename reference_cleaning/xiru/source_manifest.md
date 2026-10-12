# Source manifest

The shared Google Drive package was downloaded on October 4, 2026. Its bundled
README names these official source pages:

- Anthropic Economic Index: https://huggingface.co/datasets/Anthropic/EconomicIndex
- O*NET Resource Center: https://www.onetcenter.org/database.html
- BLS Table 1.2: https://www.bls.gov/emp/tables/occupational-projections-and-characteristics.htm

The package identifies the BLS projection period as 2025–35 but does not state
the Anthropic release number or O*NET database version. Those two version fields
remain unresolved.

## Package SHA-256 checksums

| File | SHA-256 |
|---|---|
| `bls_table_1_2_2025_35.csv` | `460af8e1eaf961732bc29b56cc92b25c4d6ef85c587b8b566f834beaebededa2` |
| `job_exposure.csv` | `4f0a3adf5feeb2ec5f5d02ab18cc5e851a2a4b8470bde84c0c9335017be12d68` |
| `onet_occupation_data.csv` | `a09eae1d6609686e44e05b7290993a1c8b523d8ca224bc0eedc194c855c3ee02` |
| `onet_task_statements.csv` | `4568e14d8db6f05551ad37e056e909b13ebae4a26bcb5ff915bb5f281d582c57` |
| `task_penetration.csv` | `85bee872db1d55d3e9a7f4e89da5ae4a5d59aa8ec875d728fbf4b7d820984616` |

`code/validate_cleaning.py` independently recalculates these hashes before and
after running the cleaning pipeline twice. The October 4 validation matched all
five package checksums and found no source-file changes.
