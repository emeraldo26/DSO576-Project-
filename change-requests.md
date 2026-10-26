# Team change requests

Copy this template into the top folder of your team's app repository if `change-requests.md` is missing. If it already exists, add to it; do not replace your teammates' work. Keep your individual evidence and conclusions in `my-audit.md`.

## Claims

Add your name and what you will audit. Choose a different scope from your teammates, or explain the new evidence you will contribute.

| Author | Feature | Number | Distinct scope or new evidence |
| --- | --- | --- | --- |
| Xiru | Filters and summary cards | Occupation count; total employment | Check that filters select the intended occupations and that summary counts and employment totals match the filtered data. |
| Emerald | Bubble chart | Axis values; bubble sizes; AI exposure percentages | Check that plotted values, bubble sizes, and percentage formatting match the underlying data and intended chart definitions. |
| Maksim | SOC group bar chart | Declining-occupation count per SOC group | Independently count declining occupations by SOC group and compare the results with the bar chart. |
| Chang Zhou | Priority score and ranking table | Priority scores; displayed ranks | Independently recalculate priority scores using the build-spec formula and check sorting, rank assignment, and consistency between scores and displayed ranks. |
| Brahmani | Occupation details and task list | Occupation-level measures; task values and ordering | Compare the selected occupation’s displayed measures and tasks with the source data, and check that tasks follow the intended ordering. |
| Kaho | Shortlist and CSV export | Shortlist count; duplicate count; exported ranks | Test adding and removing occupations, check deduplication, and compare exported CSV rows and ranks with the intended shortlist output. |

## Requests

Copy this block for each actionable finding and choose a unique ID. Reference that ID in your individual audit. A check that finds no defect belongs in your audit; do not invent a bug to fill a request.

### AUDIT-XX Short description

- Author:
- Status: open
- App version or commit checked:
- Feature or number and its intended behavior or definition:
- Inputs and steps to reproduce:
- Expected result:
- Actual result:
- Evidence (including file, function, and relevant lines if code was checked):
- Likely cause, if established, and remaining uncertainty:
- Requested change:
- Verification check and expected result:
- Implementation commit and verification result, if resolved:

Record findings without undoing a teammate's work. Mark a request resolved only after verifying the change.
