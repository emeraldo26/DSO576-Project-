# DSO 576 Module 6: national occupation-screening prototype

Compare observed occupation AI exposure and matched task penetration with
national BLS employment, projected change, wages, openings and training context.
California funding conclusions require California data. No priority score,
weights or priority thresholds are calculated.

Current branch: `cleantaotianchen123`.
Branch URL: https://github.com/emeraldo26/DSO576-Project-/tree/cleantaotianchen123
Submitted commit ID: **pending review; no assignment commit or push has been made**.
The existing HEAD is not a submitted cleaning commit. Replace the pending field
with the actual submitted commit ID after the user approves committing/pushing.

## Sources and snapshot versions

Place these originals in `data/`. The pipeline validates their SHA-256 hashes
against the reviewed snapshot and never writes to that directory. The hashes in
[the source manifest](../docs/module6_evidence/source_manifest.csv) identify the
exact local versions. URLs below are the repository's documented provenance;
this work did not download replacement datasets.

| File | Source | Version information available |
|---|---|---|
| `job_exposure.csv` | [Anthropic Economic Index](https://huggingface.co/datasets/Anthropic/EconomicIndex) | Exact local hash; release ID/download date not supplied |
| `task_penetration.csv` | Anthropic Economic Index | Exact local hash; release ID/download date not supplied |
| `onet_task_statements.csv` | Bundled O*NET; [O*NET](https://www.onetcenter.org/database.html) | Exact hash; record vintages 06/2006–08/2026; database release not supplied |
| `onet_occupation_data.csv` | O*NET occupation data | Exact local hash; database release not supplied |
| `bls_occupation_tables_2025_35.xlsx` | [BLS projections](https://www.bls.gov/emp/tables/occupational-projections-and-characteristics.htm) | Labeled 2025–35 projections / 2025 characteristics; exact hash; download date unverified |
| `bls_table_1_2_2025_35.csv` | Workbook Table 1.2, A:O, coded rows 3–1114 | Hash-pinned existing extract; two category columns lost literal None |

Original vendor release/download metadata remains unresolved. Filesystem dates
are not used as download dates. A new source version requires reviewing the
profile, expected counts and hashes rather than bypassing checks.

## Run from the repository root

Tested with CPython **3.11.4**. Direct and transitive packages are pinned in
[requirements-cleaning.txt](../requirements-cleaning.txt). With Python and pip:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-cleaning.txt
.venv\Scripts\python.exe code/clean_module6.py --output-dir outputs/module6
.venv\Scripts\python.exe code/verify_module6.py --baseline outputs/module6
```

Equivalent commands using `uv` and the installed CPython 3.11.4 runtime:

```powershell
uv run --no-project --python 3.11.4 --with-requirements requirements-cleaning.txt python code/clean_module6.py --output-dir outputs/module6
uv run --no-project --python 3.11.4 --with-requirements requirements-cleaning.txt python code/verify_module6.py --baseline outputs/module6
```

Output directories and verification report paths must be fresh. For a rerun,
preserve existing evidence and choose another name:

```powershell
uv run --no-project --python 3.11.4 --with-requirements requirements-cleaning.txt python code/clean_module6.py --output-dir outputs/module6-rerun
uv run --no-project --python 3.11.4 --with-requirements requirements-cleaning.txt python code/verify_module6.py --baseline outputs/module6-rerun --report outputs/module6-rerun-verification.json
```

The verifier starts a new Python process from the originals, compares all 41
emitted files byte for byte, and checks the submitted sample. It also changes
one exposure value in disposable input copies and verifies hash rejection.
Actual sources remain unchanged. Python/package versions appear in the manifest.

## Code and expected outputs

- `clean_module6.py`: source validation, cleaning, merges, metrics, audits, sample.
- `module6_record_expectations.json`: five expectations recorded before execution.
- `verify_module6.py`: fresh-process reproducibility and source-drift test.
- `explore_data.py`: historical Phase 1 code, unchanged. Its inner join and default
  NA parsing are superseded by the Module 6 pipeline.

| Output group | Files and purpose |
|---|---|
| Row-preserving clean tables | `job_exposure_clean.csv` (756), `task_penetration_clean.csv` (17,998), `onet_occupation_clean.csv` (1,016), `onet_task_statements_clean.csv` (18,838), `bls_table_1_2_clean.csv` (1,112) |
| Lookups/bridges | `task_penetration_lookup.csv`, `onet_occupation_soc_bridge.csv`, `onet_soc_task_bridge.csv`, `task_links_all.csv` |
| Analytical views | `occupation_master.csv` (756), `occupation_analysis_bls_complete.csv` (755), `occupation_tasks.csv` (17,760), `top_tasks_by_occupation.csv` (3,774) |
| Schema/missing profiles | `source_schema.csv`, `clean_schema.csv`, `source_missing.csv`, `source_categories.csv`, `before_after_missing.csv`, `conversion_checks.csv`, `task_vintage_counts.csv` |
| Duplicates/text/ranges | `exact_duplicate_summary.csv`, `exact_duplicate_rows.csv`, `repeated_key_summary.csv`, `text_changes.csv`, `suspicious_values.csv` |
| Reconciliation/merges | `before_after_row_counts.csv`, `view_reductions.csv`, `merge_key_audit.csv`, `merge_summary.csv`, `bls_category_recovery.csv`, `total_reconciliation.csv`, `published_calculation_checks.csv`, `metric_denominators.csv`, `task_denominators.csv` |
| Verification/documentation | `source_manifest.csv`, `run_manifest.json`, `validation_checks.csv`, `five_record_checks.csv`, `cleaning_decision_log.csv`, `cleaning_report.md`, `cleaned_sample.csv` |

All 41 files are written under the selected output directory. Canonical fields
are added alongside original columns: BLS `Work experience in a related
occupation` remains the original CSV string, while `work_experience` holds the
workbook-derived category. `*_csv_raw`, `*_workbook_raw`, and
`*_missing_reason` preserve provenance.

Literal `None` is a valid category. Empty canonical CSV fields mean null. Read
outputs with `dtype='string', keep_default_na=False` first, then use the schema
for numeric conversion. CSV cannot enforce types; avoid automatically
type-inferring spreadsheet round trips.

Employment/change/openings remain thousands; wages remain dollars. BLS percent
values such as 3.5 remain distinct from 0–1 AI measurements. Published BLS
percentages are preserved. Task averages use unique matched tasks, with matched,
total and unmatched counts plus coverage. Incomplete coverage means at least
one unmatched task; it is not a priority threshold. Missing group keys fail.

## Actual validation and sample

The final run passed **3,529 checks**, with **zero failures**; five saved-record
checks passed. A fresh process reproduced all **41 files** exactly and the
submitted **50-row sample** matched. Deliberate source drift was rejected.

See [validation summary](../docs/module6_validation.md),
[evidence files](../docs/module6_evidence/), and the exact 14-item checklist in
[plan.md section 8](../plan.md#8-exact-module-6-checklist-and-evidence).

The first development run stopped because its intended sample had 49 rows:
`31-1120` exists only in BLS, not in the job master. The corrected sample includes
it explicitly as a BLS control. The failed development directory,
`outputs/module6-run1/`, is retained locally and is not the final result.

[Sample selection](../examples/README.md) explains its 48 occupation-master rows
and two BLS controls. The sample is deterministic and deliberately includes
difficult cases; it is not representative for national statistics.

## Gradescope PDF and reproducible notebook

The six-page [individual PDF](../output/pdf/module6_individual_submission.pdf)
contains the exact checklist, all 16 cleaning decisions, reductions/totals,
five original/expected/actual record checks and the independent BLS category
check. The individual cover identifies **Taotianchen Wan** and retains the branch
URL. Assignment commit ID remains **pending**.

[module6_cleaning.ipynb](module6_cleaning.ipynb) runs the original-source pipeline,
shows validation tables and independently checks workbook cells without importing
the cleaning module. It then runs the 41-file reproducibility and deliberate
source-drift tests. Its five code cells completed in a fresh Python 3.11.4 kernel
with no error outputs. [Execution receipt](../docs/module6_evidence/notebook_execution.json)
pins the executed notebook hash. The workbook check verified 716 experience and
321 training literal `None` cells against CSV blanks and saved canonical values.
This verifies local source agreement, not external BLS provenance.

From the repository root, using a Python environment installed with
`pip install -r requirements-submission.txt`, run:

```powershell
python code/execute_module6_notebook.py
python code/build_module6_submission.py
```

Or use the tested runtime without activating an environment:

```powershell
uv run --no-project --python 3.11.4 --with-requirements requirements-submission.txt python code/execute_module6_notebook.py
uv run --no-project --python 3.11.4 --with-requirements requirements-submission.txt python code/build_module6_submission.py
```

The executor starts a fresh kernel using its own interpreter, saves the executed
notebook and execution receipt, and stops on errors. Each notebook run uses a
fresh `outputs/module6-notebook-*` directory. It refreshes the compact independent
category-check receipt; sources and existing pipeline runs remain unchanged.
The PDF builder reads saved evidence, verifies the notebook hash, rebuilds the
PDF and renders every page under ignored `outputs/module6-pdf-qa/`. Review those
page images after any PDF change; a successful render alone is not visual QA.
The final six pages were individually inspected for legibility and table layout.

The first PDF draft split case 3 onto an extra page. Table padding was adjusted
without shrinking the font; the final PDF has six pages with intact case tables.
An initial runtime lookup could not find Node; the skill's marker then ran
successfully with a temporary `uv` Node runtime. Neither affected source data.

## Git and submission status

`.gitignore` excludes raw `data/*.csv`, `data/*.xlsx`, and `outputs/`. It also
ignores the exact name `requirements.txt`; `requirements-cleaning.txt` is
unignored. Code, plan, dependencies, compact evidence and sample use Git-eligible
paths. No ignore rule was relaxed, and the pre-existing `data/README.md` edit
was preserved. New files are pending staging/commit.

The PDF uses `output/pdf/` (singular), not ignored `outputs/`; the notebook is not
the ignored `code/mock.ipynb`. Both dependency filenames are Git-eligible.
See [final file inventory and Git snapshot](../docs/module6_submission_files.md).
Git-eligible means not ignored, not already committed. No staging, commit, push
or Gradescope submission has occurred. The branch URL above may not expose new
artifacts until an assignment commit is approved and pushed.

The older generated `cleaning_report.md` records the pipeline-stage handoff;
its statement that PDF/notebook work remained is historical. This README and
the submission receipts record their subsequent completion. Original source
release/download metadata still remains unresolved.
