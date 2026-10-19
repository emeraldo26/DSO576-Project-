# AI Workforce Investment Planner

## Project overview

The **AI Workforce Investment Planner** explores how observed AI use, occupation-level tasks, and labor-market data can support workforce decisions. The project is designed to help a workforce-development agency identify occupations that may deserve priority for AI-transition training and reskilling support.

The analysis combines:

- Anthropic Economic Index data on occupation exposure and task penetration;
- O*NET occupation and task information; and
- BLS employment, wage, training, and employment-projection data.

The current implementation is a **Phase 1 data-exploration pipeline**. It validates the proposed joins and produces analysis-ready tables. It does not yet calculate a final priority score because the team has not selected or justified the score weights.


### Version-control note

The CSV files under `data/` is local working artifacts. They are intentionally excluded from Git by `.gitignore` because the source datasets are downloaded separately and the outputs can be reproduced by running the analysis script. 

## Data and analysis flow

The main occupation-level join uses six-digit SOC codes. The task-level join uses normalized task text, then connects matched tasks to O*NET-SOC occupation codes. The pipeline also keeps employment, projected change, annual openings, wages, education, related experience, and on-the-job training fields from BLS.

## Project documentation map

- Start with [`docs/project-start.md`](docs/project-start.md) for the project context, candidate visions, and unresolved questions.
- Review [`docs/Phase1- Deliverables.pdf`](docs/Phase1-%20Deliverables.pdf) for the Phase 1 project sketch.
- See [`roles/members.md`](roles/members.md) for team ownership.
- See [`code/README.md`](code/README.md) for the Phase 1 script description.
- See [`data/README.md`](data/README.md) for the raw-data policy.

## Current limitations and next steps

- AI exposure is an observation of usage and should not be interpreted as proof of job replacement.
- The current task match is based on normalized exact task text, so semantically similar but differently worded tasks may remain unmatched.
- National BLS projections do not by themselves describe California or other local labor markets.
- A priority score, weighting method, and final dashboard have not yet been implemented.
- Future work should review match quality, validate the target decision-maker, add relevant regional or training-access data, justify scoring weights, and test the results with stakeholders.

---

## Module 6 — Individual Data Cleaning (Kaho)

### Branch
`kaho-module6-cleaning`

### Repository
https://github.com/emeraldo26/DSO576-Project-

### Data sources
This analysis uses five CSV datasets:

1. `job_exposure.csv` — Anthropic occupation-level AI exposure
2. `task_penetration.csv` — Anthropic task-level AI penetration
3. `onet_task_statements.csv` — O*NET task statements
4. `onet_occupation_data.csv` — O*NET occupation descriptions
5. `bls_table_1_2_2025_35.csv` — BLS employment projections

The CSV files were obtained from the team's shared Google Drive
on October 19, 2026.

Original upstream dataset versions have not yet been verified.
Raw datasets are preserved locally and excluded from Git.

### Cleaning and validation
The cleaning process includes:

- Standardizing task descriptions and SOC occupation codes.
- Investigating exact duplicates and repeated identifiers.
- Preserving missing values where imputation is unjustified.
- Validating numeric ranges and dates.
- Checking occupation-level joins and unmatched records.
- Reconciling row counts and AI exposure totals.
- Independently verifying average task penetration calculations.

### Environment
Python 3 with pandas.

### How to reproduce

1. Clone the repository and switch to the
   `kaho-module6-cleaning` branch.
2. Install dependencies using pip install -r requirements.txt.3. Place the five source CSV files in `data/`.
4. Run:

   ```bash
   python code/explore_data.py
   python code/inspect_cleaning.py
   ```

### Expected outputs

The exploration pipeline produces:

- `outputs/occupation_exploration.csv`
- `outputs/top_tasks_by_occupation.csv`
- `outputs/exploration_report.txt`

Expected validation results include:

- 755 matched occupations.
- 17,991 unique normalized task descriptions.
- 0 duplicate occupation codes in the matched output.
- 0 mismatches in occupation-level task counts.
- 0 mismatches in occupation-level average penetration.
- 5 successful record-level verification checks.

### Synthetic Data Sample

The file `samples/module6_synthetic_sample.csv` contains
10 fictional records illustrating the cleaning rules and
edge cases investigated during Module 6.

The sample is synthetic because permission to redistribute
the original source records has not been confirmed.

It includes examples of:
- SOC code normalization
- Task text normalization
- Duplicate task handling
- Unmatched occupations
- Missing numeric values
- Valid zero values
- Out-of-range numeric values

The out-of-range penetration value (1.2) is an intentionally
invalid synthetic test case. No such value was identified
in the original task penetration dataset.

The synthetic sample is illustrative and is not used by
the current exploration or verification scripts.

To inspect actual cleaning results, obtain the five original
CSV files from the team's shared Google Drive, place them
in the `data/` directory, and run:

    python code/explore_data.py
    python code/inspect_cleaning.py

The verification script reports missing values, duplicates,
join results, reconciliation checks, and five record-level
verification results.

### Individual documentation

- `docs/module6_checklist.md`
- `docs/module6_cleaning_log.md`
- `code/inspect_cleaning.py`

### Limitations

- Original source versions have not yet been independently verified.
- Exact text matching may miss semantically equivalent tasks.
- One Anthropic occupation (Legislators, SOC 11-1031)
  is excluded from the matched analytical dataset.
- The project has not yet finalized its workforce investment
  priority score or weighting methodology.

### Commit ID

To be added after the final commit.