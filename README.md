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

## Module 6 data-cleaning submission

Student: Brahmani Mundhe  
Branch: `cleaning-brahmanimundhe`  
Branch URL: `https://github.com/emeraldo26/DSO576-Project-/tree/cleaning-brahmanimundhe`  
Commit ID: run `git rev-parse HEAD` after the final local commit; the exact
submitted commit is also recorded in the generated Gradescope PDF.

Run the cleaning assignment from the repository root:

```bash
python3 code/clean_project_data.py
```

The original CSV files remain unchanged in `data/`. The script writes full
cleaned outputs to `outputs/`, writes the review sample to
`samples/cleaned_sample_50_rows.csv`, and recreates the PDF report at
`docs/module6_cleaning_assignment_brahmani_mundhe.pdf`.

## Current limitations and next steps

- AI exposure is an observation of usage and should not be interpreted as proof of job replacement.
- The current task match is based on normalized exact task text, so semantically similar but differently worded tasks may remain unmatched.
- National BLS projections do not by themselves describe California or other local labor markets.
- A priority score, weighting method, and final dashboard have not yet been implemented.
- Future work should review match quality, validate the target decision-maker, add relevant regional or training-access data, justify scoring weights, and test the results with stakeholders.
