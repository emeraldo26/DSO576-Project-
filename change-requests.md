# Team change requests

Copy this template into the top folder of your team's app repository if `change-requests.md` is missing. If it already exists, add to it; do not replace your teammates' work. Keep your individual evidence and conclusions in `my-audit.md`.

## Claims

Add your name and what you will audit. Choose a different scope from your teammates, or explain the new evidence you will contribute.

| Author | Feature | Number | Distinct scope or new evidence |
| --- | --- | --- | --- |
| Xiru | Filters and summary cards | Occupation count; total employment | Check that filters select the intended occupations and that summary counts and employment totals match the filtered data. |
| Emerald | Bubble chart: axes, bubble area, tooltips, omissions, and explanatory caption | Observed AI exposure percentage; axis values and employment size encoding | Compare BUILD_SPEC.md with app.py and analysis/backend.py at commit 7485591666afe70acf5c0c7f9eeed6d6e5e16e74. AI-assisted numerical and local browser checks passed for chart scaling and area encoding. B2-01 records a reproduced reset discrepancy affecting chart population, adding rendered-chart evidence to the filter audit. |
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

### B2-01 Persistently clear exposure bounds when resetting chart filters

- Author: Emerald
- Status: resolved
- App version or commit checked: 7485591666afe70acf5c0c7f9eeed6d6e5e16e74, unchanged local app; Streamlit 1.66.1 and Plotly 6.9.0.
- Feature or number and its intended behavior or definition: Bubble-chart population after Reset filters. BUILD_SPEC.md specifies Reset filters and defaults with exposure bounds disabled. A reset should keep all occupations included until another filter is deliberately applied.
- Inputs and steps to reproduce: Start a fresh session. Enable Use minimum exposure, set Minimum AI exposure (%) to 50, and press Enter. Observe 11 chart points. Click Reset filters. Observe 755 points, but the checkbox remains checked and the input remains 50.00. Change Sort by to Median annual wage. Observe the chart returns to 11 points.
- Expected result: Reset disables the exposure bound, synchronizes the visible controls with the full population, and subsequent sorting keeps 755 chart points.
- Actual result: Reset briefly produces 755 points while showing the old active bound; the next sort restores the 11-point filtered population.
- Evidence: audits/emerald/check_reset_browser.py; audits/emerald/browser-evidence/reset-results.json; audits/emerald/browser-evidence/05-reset-followup.png. Reproduced in a separate fresh Chrome session after first appearing during the main browser audit. app.py reset_filters(), lines 62–66, removes widget keys; main() creates the bound widgets at lines 158–163 and applies their returned values at lines 179–180.
- Likely cause, if established, and remaining uncertainty: Removing keys does not persistently reset the currently mounted widgets in the tested Streamlit version. A code-level root cause and behavior on the team's deployed dependency versions remain to be verified.
- Requested change: Reset widget values explicitly to their defaults using the supported Streamlit callback pattern, keeping the displayed control states and backend filter inputs synchronized. Coordinate with the filter owner; no teammate code has been changed.
- Verification check and expected result: Repeat the steps in a fresh session. After reset the bound is unchecked; sorting still leaves 755 chart points. Also check the other bounds, multiselects, and search retain their default state after a later interaction.
- Implementation commit and verification result, if resolved: Resolved in the Phase 3 MVP revision: `reset_filters()` now writes explicit defaults to every filter key in an `on_click` callback. Verified by `analysis/tests/test_app.py::test_reset_persists_after_next_interaction` (11 → reset → 755, checkbox unchecked, still 755 after changing sort).

### B5-01 Correct projected-decline units in occupation details

- Author: Brahmani Mundhe
- Status: resolved
- App version or commit checked: Backend/data commit `4a6a5b4`, together with the separately shared `app.py`.
- Feature or number and its intended behavior or definition: Part 5 — occupation details and task list. The projected-decline value should use the unit stated in its row label.
- Inputs and steps to reproduce: Launch the app, scroll to Occupation details, select Paralegals and Legal Assistants (23-2011), and inspect the projected-change and projected-decline rows.
- Expected result: Projected change displays `-0.3%`. The row labeled “Projected decline (percentage points)” displays `0.3 pp`.
- Actual result: The projected-decline row displays `0.3%`, despite its percentage-points label.
- Evidence (including file, function, and relevant lines if code was checked): Confirmed in my live app screenshots. In the audited `app.py`, `details()` at line 103 passes this value to `growth()`, which appends `%` at lines 45–46. Source review was AI-assisted. Separate checks passed: Paralegals’ average task penetration is `(0.9370 / 7) × 100 = 13.39%`, and task coverage is `(7 / 12) × 100 = 58.33%`; both match the live display.
- Likely cause, if established, and remaining uncertainty: The percentage formatter is reused for a field labeled in percentage points. This is a presentation inconsistency; the underlying numeric magnitude is unchanged. Raw-source accuracy was not independently re-established.
- Requested change: Use a percentage-point formatter for this row, preserving `Not reported` for missing values. Keep the separate projected-change row in percent.
- Verification check and expected result: Paralegals displays decline `0.3 pp`; Chief Executives displays decline `0.0 pp`. Their projected-change values remain `-0.3%` and `3.2%`, respectively.
- Implementation commit and verification result, if resolved: Resolved: new `points()` formatter; Paralegals shows `0.3 pp`. Verified by `test_decline_in_percentage_points`.

### C4-01 Label the ranking-table wage as median

- Author: Chang Zhou
- Status: resolved
- App version or commit checked: `a1776b5` (the app code is unchanged from its introduction in `c4621e9`).
- Feature or number and its intended behavior or definition: Part 4 ranking table. The wage column should name the measure it displays.
- Inputs and steps to reproduce: Open Compare occupations and read the wage column heading; add an occupation to Shortlist and read the same heading there; inspect `display_table()` in `app.py`.
- Expected result: The heading says “Median annual wage” because the table displays `median_annual_wage_2025`, formatted as dollars.
- Actual result: The heading says “Annual wage”. The source column and value formatter already use the median wage field.
- Evidence (including file, function, and relevant lines if code was checked): `app.py` `display_table()`, lines 70–83: line 72 selects `median_annual_wage_2025`, line 79 formats it, and line 82 labels it “Annual wage”. `BUILD_SPEC.md` identifies the wage as a median. This is a code review; a live UI check remains to be done.
- Likely cause, if established, and remaining uncertainty: The display label is abbreviated; no numeric-value defect is established.
- Requested change: Change only this ranking-table heading to “Median annual wage”.
- Verification check and expected result: Confirm the new heading in both Compare occupations and Shortlist. Compare several SOC wage values before and after; the values and ordering should remain the same.
- Implementation commit and verification result, if resolved: Resolved: ranking-table and shortlist heading now read “Median annual wage”; values unchanged.

### C4-02 Explain score components and provisional interpretation concisely

- Author: Chang Zhou
- Status: resolved
- App version or commit checked: `a1776b5` (the app code is unchanged from its introduction in `c4621e9`).
- Feature or number and its intended behavior or definition: Part 4 “How the review score works” expander should let a reader interpret the 0–100 score using the formula in `BUILD_SPEC.md`, without changing the backend calculation.
- Inputs and steps to reproduce: Expand “How the review score works” below the ranking table and compare its text with `BUILD_SPEC.md` and `analysis/backend.py`.
- Expected result: A brief explanation says exposure and matched-task mean are divided by fixed reference values and capped at 1; only negative projected employment change contributes to decline; employment uses `log1p(employment_2025 / 1000) / log1p(921220 / 1000)`, capped at 1. The four components receive 40/30/20/10 weights and the sum is multiplied by 100. A missing required input leaves the score unavailable. The weights are a provisional team screening choice, and the score is neither a job-loss probability nor an AI-caused job-loss estimate.
- Actual result: The expander gives the weights, fixed-reference behavior, missing-input rule, and wage exclusion, but not the component transformations or provisional interpretation.
- Evidence (including file, function, and relevant lines if code was checked): `app.py` lines 248–251; `analysis/backend.py` `SCORE_REFERENCES` and `score_occupations()`, lines 16–63; `BUILD_SPEC.md` score definitions around lines 48–57. This is a code review; no score-calculation defect is claimed.
- Likely cause, if established, and remaining uncertainty: The app summarizes the formula more briefly than the build specification. The visual length of a proposed expanded explanation has not yet been checked in a live browser.
- Requested change: Add a compact component explanation and provisional-use sentence inside the existing expander. Use the exact backend reference values if numbers are shown, especially `0.3194842391304347` for task penetration. Keep the expander collapsed by default and avoid a large table unless the rendered layout remains readable. Do not change `score_occupations()`.
- Verification check and expected result: Compare every displayed transformation and reference value with the backend and spec; confirm the expander is readable at normal width and scores remain unchanged.
- Implementation commit and verification result, if resolved: Resolved: “How the review score works” expander lists each transformation with the exact backend reference values, the 40/30/20/10 weights, the missing-input rule, and the provisional-use sentence. Section ③ also shows component contributions visually. `score_occupations()` unchanged.

### C4-03 Clarify sort choices and rank rules

- Author: Chang Zhou
- Status: resolved
- App version or commit checked: `a1776b5` (the app code is unchanged from its introduction in `c4621e9`).
- Feature or number and its intended behavior or definition: Part 4 sort controls and displayed ranks should be understandable without reading the source code.
- Inputs and steps to reproduce: Inspect the six “Sort by” labels and change Direction between descending and ascending; compare the ranking table with the sorting contract in `BUILD_SPEC.md`.
- Expected result: Brief help text defines the six measures: 0–100 review priority score, observed AI exposure percentage, mean penetration across matched tasks, 2025 employment in persons, 2025 median annual wage in dollars, and BLS projected employment change percentage from 2025 to 2035. It also states that Direction controls high-to-low or low-to-high order, exact ties (including zeros) use SOC code ascending, missing values sort last, and ranks count rows from 1 in the current view.
- Actual result: The interface lists the six short labels and a direction selector, but does not state their units, tie rule, missing-value rule, or how ranks are assigned.
- Evidence (including file, function, and relevant lines if code was checked): `app.py` `SORT_OPTIONS`, lines 17–24; sort controls, lines 167–169; table call, lines 245–247. `analysis/backend.py` `rank_occupations()`, lines 189–199, already implements the stated tie, missing-value, and rank rules. This is a code review; a live UI check remains to be done.
- Likely cause, if established, and remaining uncertainty: The interface relies on short control labels while the fuller sorting contract stays in the build specification. No backend sorting defect is claimed.
- Requested change: Add compact sort help near the control or in a collapsed explanation near the table; avoid a long always-visible paragraph. Keep `rank_occupations()` unchanged.
- Verification check and expected result: Confirm all six descriptions match the selected columns and units. Check default score descending, reverse direction, an exact zero tie ordered by SOC ascending, missing values last, and row-by-row ranks beginning at 1.
- Implementation commit and verification result, if resolved: Resolved: the Sort by control has a help tooltip and a “How sorting and ranks work” expander defining all six measures, direction, tie and missing-value rules, and rank counting. `rank_occupations()` unchanged.
