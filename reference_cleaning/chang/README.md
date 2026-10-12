# Chang Zhou's data cleaning

Branch: `cleaning-chang`<br>
Branch URL: https://github.com/emeraldo26/DSO576-Project-/tree/cleaning-chang<br>
Submitted commit ID: a60695e11a17c5d607ab4239c2c8d9429ba0d444

This is the individual data-cleaning implementation of the accepted [plan](../../plan.md). It prepares occupation and occupation-task data for later analysis. It does not calculate a priority score or build the dashboard. The source release versions and download dates are unknown; the script records and checks SHA-256 hashes instead.

## Run from raw sources

Use Python 3.11 or newer. From the repository root:

```bash
python -m pip install -r code/cleaning_chang/requirements.txt
python code/cleaning_chang/clean_data.py \
  --data-dir data \
  --output-dir outputs/cleaning_chang/my_fresh_run \
  --sample-file code/cleaning_chang/my_fresh_sample.csv
```

The five raw CSVs must be placed under `data/` as described in [data/README.md](../../data/README.md). The script checks their hashes and exact column sets before cleaning. It refuses to overwrite any existing output or sample file; choose unused paths for each run. Full outputs go under Git-ignored `outputs/`. The committed sample contains no more than 50 occupation rows. `clean_data.ipynb` is an inspectable, read-only notebook that runs the same functions in memory and displays the stage profiles, reconciliation, conversions, and record checks. Run it from the repository root or this folder.

## Outputs and interpretation

The script writes `occupation.csv` (one row per exposure SOC), `occupation_tasks.csv` (one row per six-digit SOC and normalized matched task), and `top_five_tasks.csv` (up to five matched tasks per SOC). `matched_task_count` is the nonmissing denominator of `average_task_penetration`. Employment and annual openings are in thousands; annual openings are thousands per year. Wages are annual dollars; projected change percentages are percentage points. The occupation output keeps `11-1031` Legislators with missing BLS fields.

Five `source_grain_*.csv` files preserve every input row and original source field, along with derived keys/typed fields and match status. `bls_line_items.csv` and `bls_summaries.csv` separate the two BLS grains. `penetration_lookup.csv` collapses only agreeing task-key duplicates for matching. `unmatched_keys.csv` lists distinct failed keys, while `unmatched_*_rows.csv` preserves complete unmatched source rows. The 76 BLS line items absent from exposure are retained in their unmatched-row file and source-grain output. `record_checks.csv` shows source file, row/key, original, expected, actual, and pass/fail for five checks. `validation_report.json` contains stage-by-stage row counts, missing values, duplicates, numeric ranges, category counts, BLS totals, and marker conversions.

The sample selection is deterministic: Chief Executives and Legislators first; then up to 12 SOCs with missing wage or task-average context; then the first SOC in each occupation group, with repeats removed and a 50-row limit. It illustrates normal, unmatched, missing-context, and group coverage cases. It is not a statistical sample or a substitute for the full output. Full source and generated tables remain outside Git.

## Validation and limits

The script asserts unique join keys, one `.00` O*NET description per six-digit SOC, agreeing penetration values for duplicate task keys, preserved raw text, expected missing-marker conversions, no unexpected join multiplication, BLS matched-plus-unmatched total reconciliation, and all five record checks. It stops on changed raw hashes or a new conflict. Negative projected employment change is flagged and retained. Normalized exact text does not match semantically similar wording. AI exposure is observed use, not a causal estimate of job loss.

The existing `code/explore_data.py` and other team files are untouched. This README and its notebook document Chang's cleaning pipeline only. The individual PDF and GitHub push are intentionally pending review.
