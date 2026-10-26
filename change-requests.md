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
- Status: open
- App version or commit checked: 7485591666afe70acf5c0c7f9eeed6d6e5e16e74, unchanged local app; Streamlit 1.66.1 and Plotly 6.9.0.
- Feature or number and its intended behavior or definition: Bubble-chart population after Reset filters. BUILD_SPEC.md specifies Reset filters and defaults with exposure bounds disabled. A reset should keep all occupations included until another filter is deliberately applied.
- Inputs and steps to reproduce: Start a fresh session. Enable Use minimum exposure, set Minimum AI exposure (%) to 50, and press Enter. Observe 11 chart points. Click Reset filters. Observe 755 points, but the checkbox remains checked and the input remains 50.00. Change Sort by to Median annual wage. Observe the chart returns to 11 points.
- Expected result: Reset disables the exposure bound, synchronizes the visible controls with the full population, and subsequent sorting keeps 755 chart points.
- Actual result: Reset briefly produces 755 points while showing the old active bound; the next sort restores the 11-point filtered population.
- Evidence: check_reset_browser.py; browser-evidence/reset-results.json; browser-evidence/05-reset-followup.png. Reproduced in a separate fresh Chrome session after first appearing during the main browser audit. app.py reset_filters(), lines 62–66, removes widget keys; main() creates the bound widgets at lines 158–163 and applies their returned values at lines 179–180.
- Likely cause, if established, and remaining uncertainty: Removing keys does not persistently reset the currently mounted widgets in the tested Streamlit version. A code-level root cause and behavior on the team's deployed dependency versions remain to be verified.
- Requested change: Reset widget values explicitly to their defaults using the supported Streamlit callback pattern, keeping the displayed control states and backend filter inputs synchronized. Coordinate with the filter owner; no teammate code has been changed.
- Verification check and expected result: Repeat the steps in a fresh session. After reset the bound is unchecked; sorting still leaves 755 chart points. Also check the other bounds, multiselects, and search retain their default state after a later interaction.
- Implementation commit and verification result, if resolved: Not resolved; no implementation change was made.

### B5-01 Correct projected-decline units in occupation details

- Author: Brahmani Mundhe
- Status: open
- App version or commit checked: Backend/data commit `4a6a5b4`, together with the separately shared `app.py`.
- Feature or number and its intended behavior or definition: Part 5 — occupation details and task list. The projected-decline value should use the unit stated in its row label.
- Inputs and steps to reproduce: Launch the app, scroll to Occupation details, select Paralegals and Legal Assistants (23-2011), and inspect the projected-change and projected-decline rows.
- Expected result: Projected change displays `-0.3%`. The row labeled “Projected decline (percentage points)” displays `0.3 pp`.
- Actual result: The projected-decline row displays `0.3%`, despite its percentage-points label.
- Evidence (including file, function, and relevant lines if code was checked): Confirmed in my live app screenshots. In the audited `app.py`, `details()` at line 103 passes this value to `growth()`, which appends `%` at lines 45–46. Source review was AI-assisted. Separate checks passed: Paralegals’ average task penetration is `(0.9370 / 7) × 100 = 13.39%`, and task coverage is `(7 / 12) × 100 = 58.33%`; both match the live display.
- Likely cause, if established, and remaining uncertainty: The percentage formatter is reused for a field labeled in percentage points. This is a presentation inconsistency; the underlying numeric magnitude is unchanged. Raw-source accuracy was not independently re-established.
- Requested change: Use a percentage-point formatter for this row, preserving `Not reported` for missing values. Keep the separate projected-change row in percent.
- Verification check and expected result: Paralegals displays decline `0.3 pp`; Chief Executives displays decline `0.0 pp`. Their projected-change values remain `-0.3%` and `3.2%`, respectively.
- Implementation commit and verification result, if resolved: Not resolved; no fix has been implemented or verified.
