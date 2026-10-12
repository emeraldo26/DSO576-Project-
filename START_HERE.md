# Your Phase 2 project files

The data comparison and Python backend are prepared. All five supplied cleaning pipelines were reproduced. The official BLS workbook matches Taotian's original fingerprint, and its category recovery is independently verified. Keep this package separate from your existing Module 6 folder while reviewing it.

## What to open first

| Item | Simple explanation |
|---|---|
| `BUILD_SPEC.md` | The detailed instructions for building the Phase 3 dashboard |
| `data/cleaned/occupation_clean_merged.csv` | The 755 occupations used for dashboard comparisons |
| `data/cleaned/occupation_master.csv` | All 756 exposure occupations, preserving unmatched Legislators |
| `data/cleaned/occupation_task_matches.csv` | The tasks used for the occupation calculations |
| `data/cleaned/bls_category_recovery.csv` | Proof for each corrected training/experience category |
| `analysis/` | Reusable Python cleaning and dashboard calculations |
| `docs/team_reconciliation.md` | How the five individual cleaning approaches were compared and resolved |
| `docs/fresh_agent_test.md` | The assignment's separate fresh-agent-test record |
| `APPLY_PHASE2.patch` | Included in this downloaded package to apply the changes to your existing Git repository |

## Check the files in VS Code

1. Unzip the package and open its `AI_Workforce_Phase2` folder in VS Code.
2. Open Terminal -> New Terminal in that folder.
3. Run these commands:

```bash
python3 -m pip install -r requirements.txt
python3 -m analysis.run_phase2
python3 -m unittest discover -s tests -v
```

Expected: 755 analysis occupations, 756 master occupations, 17,760 matched dashboard task rows, and 17 passing backend checks. The extra BLS workbook is already included locally. Raw inputs stay excluded from Git; cleaned tables are tracked. These commands prepare and check Phase 2; the dashboard interface belongs to Phase 3.

The fresh-agent build trial is recorded in `docs/fresh_agent_test.md`, with its evidence files. It found unclear interaction instructions that were then fixed in the specification. A live dashboard run remains Phase 3 work because Streamlit and Plotly were unavailable in the checking environment.

## Add this work to your GitHub project

The uploaded archive has no Git history. Your existing VS Code project is the actual Git repository. Use the patch there, preferably with your local Codex agent so it can preserve local work and handle the current branch correctly.

Open your ORIGINAL project in VS Code and give Codex the instruction below. Replace the bracketed path with the actual location of the unzipped package:

> Apply the Phase 2 changes from [path to AI_Workforce_Phase2]/APPLY_PHASE2.patch to our DSO576-Project- repository. Read any repository instructions. Preserve existing work. Create an isolated branch/worktree named phase2-brahmanimundhe from current origin/main. Run git apply --check before applying; resolve any actual differences with current main without discarding unrelated changes. Copy the six raw inputs from the package's data folder into the worktree's local data folder for reproducibility, keeping them ignored by Git. Install requirements, run python3 -m analysis.run_phase2 and python3 -m unittest discover -s tests -v. Review the resulting diff, commit the intended Phase 2 files, push the branch, and create a pull request targeting main. Report the real branch, commit, and PR link. Do not include raw input files in the commit.

Review the pull request with your team and merge the agreed implementation into `main`, as the assignment requires. Record the actual merge commit. This package does not claim that the GitHub merge or a Canvas/Gradescope upload has already happened.

The proposed MVP uses visible filters, metric sorting, and a shortlist because the submissions provide no justified composite score. Discuss that scope revision with the team when reviewing the PR. The dashboard interface is Phase 3. Exact Anthropic/O*NET release metadata remains unspecified and is labeled as such. If another member has separate cleaning work, add it to the reconciliation evidence.

Follow your actual Canvas/Gradescope instructions for what to upload and where. The supplied project PDF lists the deliverables but does not state a submission format or deadline.
