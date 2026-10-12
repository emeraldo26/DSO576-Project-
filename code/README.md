# Phase 1 data exploration

This folder contains the exploration code for the **AI Workforce Investment
Planner**. The code checks whether the proposed Anthropic, O*NET, and BLS data
can support the dashboard sketch.

It performs four Phase 1 checks:

1. Confirms the expected files and columns are present.
2. Standardizes occupation codes to the six-digit SOC format.
3. Measures occupation-level and task-level match rates.
4. Creates an occupation-level table and a top-five-tasks table for later use.

**The code does not calculate a priority score yet.** 
The team still needs to choose and justify how the measures should be weighted.

## Files needed locally

Download data resource from google drive: 
https://drive.google.com/file/d/1FYnToysUpMV1YG3GvhsTGd5vdG4GkiWj/view?usp=sharing 

Place these downloaded files in a local `data/` folder:

- `job_exposure.csv`
- `task_penetration.csv`
- `onet_task_statements.csv`
- `onet_occupation_data.csv`
- `bls_table_1_2_2025_35.csv`

The `data/` folder is excluded by `.gitignore`, so the downloaded datasets will
not be committed to GitHub.


## Run the exploration

From the repository root:

```bash
python code/explore_data.py
```

The script writes its generated tables and text report to `outputs/`. That
folder is also excluded from Git because the results can be reproduced by
running the script.
