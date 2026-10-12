# AI Workforce Investment Planner - Phase 2 build specification

**Status:** Canonical implementation prepared from the main archive and five individual cleaning submissions. All five pipelines were reproduced. The BLS workbook is byte-identical to Taotian's recorded source; category recovery is independently verified. Resolved differences and evidence are in `docs/team_reconciliation.md`. The fresh-agent check is recorded separately; the package has not been merged into `main`.

## Vision and scope

A program manager at a workforce-development agency needs a shortlist of occupations to review for AI-transition training and reskilling support. This national screening tool puts observed AI exposure, task penetration, employment, wages, and projected employment change together, making comparisons easier than consulting separate source tables.

The output supports occupation review. Observed Claude use does not prove job displacement or training need. BLS projections do not show that AI caused employment changes. The data lacks regional demand, individual skills, training costs, and evidence of program outcomes.

**Proposed revision from Phase 1:** replace the unexplained composite priority score and priority-color bands with visible measures, user-selected sorting, and a saved shortlist. This keeps the comparison and occupation drill-down from the original vision. No score weights or risk thresholds are invented. The team must review this revision during reconciliation.

## Core use cases

| Use case | User selects/inputs | Dashboard shows | User decides |
|---|---|---|---|
| U1: compare a workforce segment | SOC group, employment range, exposure range, and outlook | Filtered summary cards, comparison chart, occupation table, and group summary | Which occupations deserve review |
| U2: inspect one occupation | An occupation in the filtered selector | Description, source measures, training context, task-match coverage, and up to five tasks | Whether its task patterns warrant further investigation |
| U3: assemble a shortlist | Add/remove a selected occupation | Saved occupation list and CSV download | Which occupations to bring to program review |

## Data contract

The Phase 3 app reads `data/cleaned/occupation_clean_merged.csv` and `data/cleaned/occupation_task_matches.csv`. The separate `occupation_master.csv` preserves all 756 exposure occupations, including Legislators marked `unmatched`; it is an archival coverage view, not an input to the default dashboard totals. The app does not join raw data at interaction time. Source fingerprints, counts, exclusions, and comparison status are in `data/cleaned/data_audit.json`.

| Table/fields | Meaning, source, and preparation |
|---|---|
| Occupations: `soc_code`, `title` | One row per six-digit SOC shared by Anthropic `occ_code` and BLS detailed line items. Title comes from Anthropic. Strip surrounding text whitespace. |
| `occupation_group_code`, `occupation_group_name` | First two SOC digits and the matching BLS major-group summary title. Summary rows supply labels only. |
| `observed_exposure` | Supplied Anthropic `observed_exposure`, stored as a fraction from 0 to 1. |
| `average_task_penetration` | Arithmetic mean of supplied penetration over distinct normalized matched tasks in a SOC. Include actual zeros. Unmatched tasks do not become zero. |
| `matched_task_count`, `total_task_count`, `task_match_rate` | Counts of scored matches and all distinct O*NET task texts at six-digit SOC level. Rate = matches / total, unavailable when total is zero. Tasks from O*NET sub-occupations are combined once per distinct task text. |
| `employment_2025_thousands`, `employment_2025` | BLS `Employment, 2025`; second field is the first multiplied by 1,000. These remain estimates at the source's precision. |
| `employment_change_percent_2025_35` | BLS `Employment change, percent, 2025–35`. Already in percent units: 3.2 displays as 3.2%, not 320%. |
| `labor_market_outlook` | Growing if projected change > 0, Stable if = 0, Declining if < 0, Unknown if missing. These labels describe projected growth only. |
| `median_annual_wage_2025` | BLS median annual wage in USD. Missing wages remain blank, never zero. |
| `annual_openings_2025_35_thousands`, `annual_openings_2025_35` | BLS annual average openings for 2025–35. Second field multiplies thousands by 1,000. |
| `typical_education`, `related_work_experience`, `on_the_job_training` | BLS categories. Work experience/training values use code-aligned workbook verification to recover only CSV blanks corresponding to literal `None`. Explicit `None` is a real category. Unverified blanks remain unavailable; no value is inferred by analogy. Companion `_csv_raw`, `_workbook_raw`, and `_source` fields preserve provenance. |
| `occupation_description`, `description_source_onet_code` | Prefer O*NET `.00` occupation description. If absent, select the lowest O*NET code within the SOC deterministically and retain the selected source code. |
| Tasks: `soc_code`, `task`, `task_normalized`, `penetration` | One row per scored SOC/task-text pair. Match by lowercasing, collapsing whitespace, and trimming. Penetration remains a 0–1 fraction. |

Use `analysis/cleaning.py` to regenerate the proposal. Remove exact duplicates. Collapse equal-score normalized task duplicates; conflicting scores raise an error for review. Preserve punctuation in task keys. Reject invalid SOC keys and conflicting occupation duplicates. Keep only BLS `Line item` rows in occupation totals, including legitimate detailed codes ending in zero. Join occupation sources one-to-one; preserve unmatched exposure occupations in the master, then select the BLS-matched analysis view. Connect task scores many-to-one by normalized text, then deduplicate each SOC/task pair. Keep full calculation precision; round only for display. Missing wages or training do not exclude an otherwise matched occupation.

The inspected snapshot has a 756-row master, 755 analysis occupations, and 17,760 distinct scored dashboard occupation/task pairs. The unmatched exposure occupation is `11-1031` (Legislators). Seven normalized task duplicates are removed, including six exact duplicates. Three retained occupations have missing wages. Workbook verification recovers 716 experience and 321 training categories across all BLS rows; 646 and 295 respectively belong to the analysis view. The ledger is `data/cleaned/bls_category_recovery.csv`. Across all O*NET SOCs there are 18,656 distinct scored task pairs; the two task counts describe different populations. The supplied files do not identify the Anthropic release or observation period; show that as unavailable rather than inventing a date.

## Dashboard layout and behavior

Build a local Streamlit app at `app.py` using Plotly for the chart. Start on **Compare occupations**, with a second tab named **Shortlist**. All views use the same filtered dataframe, except the saved shortlist.

**Compare occupations / U1**

- Sidebar: SOC major-group multiselect, outlook multiselect, inclusive employment minimum/maximum, inclusive exposure minimum/maximum, literal case-insensitive title/SOC search, and Reset filters.
- Defaults: all groups and outlooks, no employment bounds, no exposure bounds, empty search. A cleared group/outlook multiselect means all in the UI; pass `None` to the backend. Each lower/upper bound is independently enabled and initially disabled, so one-sided bounds are supported. Employment inputs use persons; exposure controls display 0–100% and pass fractions to the backend.
- Reset filters resets group/outlook/range/search controls to their defaults. Preserve the selected sort metric/direction, saved shortlist, and detail selection if its SOC remains visible after reset.
- Invalid minimum/maximum combinations show the input error and suppress comparison cards, chart, table, group summary, and details until corrected. Do not swap bounds, show stale comparison results, or treat invalid inputs as zero valid matches. Keep the Shortlist accessible; its outside-current-filters count displays as unavailable until the filters are valid.
- Four cards: occupation count; included 2025 employment; mean occupation exposure; number of declining occupations. The mean is unweighted across nonmissing occupation values, not a percentage of workers using AI. Label employment as belonging to included occupations.
- Bubble chart: x = projected employment change (%), y = observed exposure (%), bubble area proportional to employment. Add a vertical line at x = 0. Use outlook colors Growing = teal, Stable = gray, Declining = orange, Unknown = light gray. Tooltip: title, SOC, exposure, change, employment, wage. Exclude only rows missing chart inputs or having nonpositive employment; show the number omitted.
- Occupation table: title, SOC, exposure, task mean, employment, wage, projected change, and task-match rate. Default sort is exposure descending. A control allows exposure, task mean, employment, wage, or projected change, with ascending/descending direction. Ties use SOC ascending; missing values come last. Format exposure/task/coverage as percentages with two decimals, growth with one decimal, employment/openings as comma-separated persons, and wages as whole USD. Label the rank as order under the selected metric, without implying reskilling need.
- Collapsible group summary: SOC group, occupation count, employment sum, mean occupation exposure, and declining count. Use the current filters. Do not average occupational median wages into a purported workforce wage.

**Occupation details / U2**

Below the chart/table, an occupation selector lists filtered titles as `Title (SOC)` in the table's selected sort order. Start with no occupation selected. Use the selector for drill-down; plot clicking is not required. Show the selected occupation's description, original measures, education, experience, training, annual openings, and matched/total task counts. Show up to five tasks sorted by penetration descending, then normalized task text ascending. If fewer tasks exist, show the available tasks. For a missing field display `Not reported`; show actual zero as zero. For BLS experience/training category `None`, display `None required` and clarify that it describes typical entry requirements, not AI-training need. If valid filters remove the selected occupation, clear the selection and ask the user to select another. Invalid filters temporarily suppress details without changing the saved detail identifier.

**Shortlist / U3**

An Add to shortlist button saves the selected SOC once. The Shortlist tab shows saved occupations, removal controls, Clear shortlist, and a UTF-8 CSV download with the clean occupation fields and selected-sort rank. Recalculate ranks from 1 within the saved occupation subset under the current selected metric/direction, using SOC ascending for ties and missing values last; these are not ranks in the full or filtered comparison population. Save SOC identifiers in session state. Filters do not discard saved occupations; show a count of saved occupations outside current valid filters. Export all saved occupations. The shortlist lasts for the browser session, with export as the persistence mechanism.

When regenerated clean data omits a saved SOC, remove only those unavailable identifiers from session state and display a notice listing the removed SOCs. Keep every still-valid saved SOC and allow table/export to continue. Clear a detail selection whose SOC no longer exists. Never discard saved identifiers silently or substitute occupations.

For no filter results, show `No occupations match these filters`, an empty table, and a Reset option. Count cards show zero; unavailable numeric summaries show a dash. Do not restore the full dataset implicitly. Empty shortlist export stays disabled.

## Backend and technical design

| Component | Job and contract |
|---|---|
| `analysis/cleaning.py` | Validate raw CSVs and return `CleanResult(occupations, tasks, audit, master)` without printing or writing. |
| `analysis/run_phase2.py` | CLI orchestration: load and verify the five CSVs and BLS workbook, run cleaning, write analysis/task/master tables, category-recovery ledger, and audit JSON. |
| `analysis/backend.py` | Load clean tables; return filtered dataframes, metric dictionaries, group/chart tables, sorted rows, occupation details, and shortlist rows. Functions do not mutate inputs. |
| `app.py` in Phase 3 | Own layout, formatting, controls, and session state. Call existing backend functions rather than duplicating calculations. |

CSV files and pandas fit the inspected data volume. Keep both clean tables in memory. Cache clean-data loading in the app using both file paths and modification times as cache inputs so regeneration invalidates stale data. Filter and summarize the cached dataframe locally; never download sources for each control change. No database, remote API, credentials, or worker-level data is needed for this MVP. Phase 3 deployment must include the agreed clean tables, dependency file, and explicit relative paths, and add tested Streamlit/Plotly dependencies. Raw inputs remain ignored by Git; agreed clean outputs must be tracked on `main`.

## Build order and acceptance checks

1. Review the documented canonical decisions and run the pipeline/backend checks. Verify table keys, workbook recovery, and source fingerprints.
2. Build the cached clean-data loader, controls, and summary cards.
3. Build the plot, metric-sorted table, and group summary from the same filtered data.
4. Add occupation details, shortlist session state, and CSV export.
5. Run acceptance checks with a fresh coding agent. Record questions/guesses in `docs/fresh_agent_test.md` and resolve them before submitting.

For this supplied snapshot:

- Exactly 755 unique SOCs in the analysis view; Legislators remains in the 756-row master with missing BLS metrics and `bls_match_status = unmatched`. Task keys are unique within each SOC and reference analysis occupations.
- Included employment sums to 154,223,400 persons. Chief Executives (`11-1011`) displays 291,600 employment, not 291.6 persons.
- Default sort starts with Computer Programmers (`15-1251`), with 74.51% exposure and -7.3% projected change.
- Chief Executives' highest task penetration is 83.10%. Task means include matched zero values.
- Missing wages remain unavailable for three retained occupations. They still appear in the chart when its required fields are present.
- Chief Executives shows `None required` for typical on-the-job training. Its source CSV blank and verified workbook `None` remain recorded separately.
- Exact numeric filter boundaries are inclusive. A search with no matches stays empty across all compare views.
- Adding the same SOC twice creates one shortlist row. Filters can hide an occupation without erasing its saved selection.
- Shortlist ordering/export respects the selected metric and direction. Resorting an already-ranked dataframe updates its displayed ranks without an error.
- Reset preserves sorting, the shortlist, and a still-visible detail selection. Invalid bounds suppress only the comparison views and mark the shortlist's outside-filter count unavailable.
- If a regenerated dataset removes a saved SOC, a notice identifies the removed SOC, the remaining saved rows stay available, and any invalid detail selection clears.
- Backend checks run with `python -m unittest discover -s tests -v`. The separate fresh-agent build trial and resolved questions are recorded in `docs/fresh_agent_test.md`; a live Streamlit/Plotly UI run remains Phase 3 validation.
