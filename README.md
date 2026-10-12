# AI Workforce Investment Planner

## Project overview

The **AI Workforce Investment Planner** explores how observed AI use, occupation-level tasks, and labor-market data can support workforce decisions. The project is designed to help a workforce-development agency identify occupations that may deserve priority for AI-transition training and reskilling support.

The analysis combines:

- Anthropic Economic Index data on occupation exposure and task penetration;
- O*NET occupation and task information; and
- BLS employment, wage, training, and employment-projection data.

The repository preserves the **Phase 1 data-exploration pipeline** and adds the **Phase 2 canonical implementation** in `analysis/`. All five supplied individual cleaning pipelines were reproduced. The BLS workbook matches the recorded source exactly, and its category recovery is independently verified. The implementation preserves a 756-row master, prepares the 755-row BLS-matched analysis view and task table, and provides reusable dashboard functions. This package has not yet been merged into `main`. Start with `START_HERE.md`, review `BUILD_SPEC.md`, and see `docs/fresh_agent_test.md` for the separate test record.

The proposed MVP uses explicit filters and user-selected metric sorting. Phase 1 supplied no justified priority-score weights, so this draft does not invent a composite score. The team must review this proposed scope change.


### Version-control note

Raw CSV/XLSX files directly under `data/` remain local inputs excluded from Git. The agreed occupation/task tables under `data/cleaned/` should be tracked on `main` after team reconciliation. Regenerate them with `python -m analysis.run_phase2`. The dependency file is also tracked.

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
- A composite priority score is outside the proposed draft scope; metric sorting is implemented. The dashboard interface belongs to Phase 3.
- Future work should review match quality, validate the target decision-maker, add relevant regional or training-access data, justify scoring weights, and test the results with stakeholders.
