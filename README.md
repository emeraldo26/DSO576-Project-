# AI Workforce Investment Planner

## Project overview

The **AI Workforce Investment Planner** explores how observed AI use, occupation-level tasks, and labor-market data can support workforce decisions. The project is designed to help a workforce-development agency identify occupations that may deserve priority for AI-transition training and reskilling support.

The analysis combines:

- Anthropic Economic Index data on occupation exposure and task penetration;
- O*NET occupation and task information; and
- BLS employment, wage, training, and employment-projection data.

This integration branch contains Phase 1 exploration, Brahmani's individual Module 6 cleaning workflow, and the reviewed Phase 2 occupation/task data and analysis backend. The dashboard interface is planned for Phase 3; see [BUILD_SPEC.md](BUILD_SPEC.md).


### Version-control note

The five raw CSV files and the BLS workbook directly under `data/` are local inputs ignored by Git. The reviewed Phase 2 files under `data/cleaned/` are tracked for the proposed dashboard data contract. See [data/README.md](data/README.md) for source and workbook requirements.

## Reproduce and check Phase 2

With the six raw files listed in `data/README.md` present locally, install `requirements.txt` and run:

```bash
python3 -m pip install -r requirements.txt
python3 -m analysis.run_phase2
python3 -m unittest discover -s analysis/tests -v
```

The backend-only checks use only the tracked clean tables and can run in a
fresh clone even before raw inputs are downloaded:

```bash
python3 -m unittest analysis.tests.test_backend -v
```

`analysis.tests.test_phase2` is the source-reconstruction suite. It runs when all six
raw inputs are present and reports a clear skip listing missing files otherwise.

The Phase 2 path writes 755 matched occupations, a 756-row master retaining the unmatched Legislators record, 17,760 scored occupation/task pairs, a BLS category-recovery ledger, and an audit JSON. The fixed-reference review score is calculated by `analysis/backend.py` when loading the clean occupations: 40% observed AI exposure, 30% projected employment contraction, 20% employment size, and 10% average task penetration. It is a screening rank, not a causal estimate or job-loss probability. The raw measures and score components remain available for review. The source fingerprints and row reconciliation are in `data/cleaned/data_audit.json`.

Brahmani's individual cleaning script is retained separately at `code/clean_project_data.py`; its reviewed 50-row sample is `data/samples/cleaned_sample_50_rows.csv`. Run `python3 code/clean_project_data.py --skip-pdf` to recreate her full outputs under ignored `outputs/`. The integration uses exact decimal arithmetic for its four-place task-mean output so the sample regenerates identically. Her output schema differs from the Phase 2 backend contract, so use `analysis.run_phase2` for `data/cleaned/`. The two paths preserve their distinct cleaning decisions and provenance.

## Data and analysis flow

The main occupation-level join uses six-digit SOC codes. The task-level join uses normalized task text, then connects matched tasks to O*NET-SOC occupation codes. The pipeline also keeps employment, projected change, annual openings, wages, education, related experience, and on-the-job training fields from BLS.

## Project documentation map

- Start with [`docs/project-start.md`](docs/project-start.md) for the project context, candidate visions, and unresolved questions.
- Review [`docs/Phase1- Deliverables.pdf`](docs/Phase1-%20Deliverables.pdf) for the Phase 1 project sketch.
- See [`roles/members.md`](roles/members.md) for team ownership.
- See [`code/README.md`](code/README.md) for the Phase 1 script description.
- See [`data/README.md`](data/README.md) for the raw-data policy.
- See [`docs/team_reconciliation.md`](docs/team_reconciliation.md) for the Phase 2 comparison of the five cleaning submissions.

## Current limitations and next steps

- AI exposure is an observation of usage and should not be interpreted as proof of job replacement.
- The current task match is based on normalized exact task text, so semantically similar but differently worded tasks may remain unmatched.
- National BLS projections do not by themselves describe California or other local labor markets.
- The fixed-reference priority score is a transparent review choice and should be assessed by the team before using it for decisions. The dashboard interface is not yet implemented.
- Future work should review match quality, add relevant regional or training-access data, and test the screening choices with stakeholders.
