# Fresh coding-agent build trial

Current outcome: the updated specification resolves the significant implementation questions. The clarified-contract recheck passed 22 checks; no important MVP implementation guesses remain. Live UI validation remains unavailable.

Date: October 12, 2026 (UTC). Tool/session: separate Codex coding subagent, given the repository path and instructions to follow BUILD_SPEC.md, without prior project conversation. Repository supplied as an archive-derived filesystem copy; no repository-specific .git metadata or commit identifier was present. Exact input fingerprints are in fresh_agent_input_snapshot.json.

The agent copied the repository to /workspace/scratch/c082ec3e1eb5/fresh_agent_trial and changed only that isolated copy. It began a local Phase 3 MVP at app.py. It did not modify the source repository, install dependencies, initialize a browser, publish, contact anyone, or delegate.

## Result and limits

The specification was sufficient to begin the MVP without inventing data joins, imputation, dates, metric formulas, score weights, or risk thresholds. The trial implements both tabs, cache keys containing both CSV paths and modification times, filters, summary cards, a Plotly bubble-chart definition, metric-sorted table, group summary, occupation selector/details, top tasks, shortlist session state, removal, and UTF-8 CSV export through the existing backend.

Streamlit and Plotly are unavailable in this runtime. Therefore the UI, chart rendering, widget state across reruns, callbacks in an actual Streamlit session, and browser interactions were not run or visually verified. The app is a build trial, not a tested or deployable final dashboard. No UI dependency version was silently selected; choosing and testing versions remains Phase 3 work.

## Initial questions and provisional interpretations

| ID | Exact question | Interpretation used in trial | Importance / status |
|---|---|---|---|
| Q1 / A2 | Does Reset filters also clear occupation detail, sorting, or saved selections? | Reset only filter controls; preserve sort metric/direction, saved SOCs, and the current detail SOC if still visible. A later valid filtering pass clears detail if excluded. | Important interaction contract; explicit specification wording requested. |
| Q2 / A3 | What should comparison and Shortlist show while numeric minimum exceeds maximum? | Show an input error and suppress comparison cards/chart/table/details. Keep Shortlist accessible; outside-current-filter count is unavailable until filters are valid. Do not show stale results or pretend there are zero valid matches. | Important interaction contract; explicit specification wording requested. |
| Q3 / A4 | Is selected-sort rank in export global, filtered, or within the saved shortlist? | Existing shortlist_data recomputes ranks 1..N within the saved subset under selected metric/direction. Trial labels this population explicitly. | Important metric interpretation; backend supports it, but prose needs explicit population. |
| Q4 | What happens if a regenerated clean dataset omits a previously saved SOC? | Do not silently discard identifiers. Trial reports the backend error, pauses shortlist table/export, and provides Clear shortlist. | Future-data edge case; not a blocker for the supplied static snapshot. Precise migration/removal policy remains unspecified. |
| Q5 | Has the team adopted the proposed metric-sort MVP in place of the Phase 1 priority score? | Follow BUILD_SPEC.md's proposed scope for this authorized trial; do not infer a separate all-member vote or invent a score. | Team integration status, not an implementation ambiguity. |

These were provisional during the initial trial. The parent clarified Q1–Q4 in the updated BUILD_SPEC.md. The recheck below supersedes the initial Q4 error-and-clear policy. Q5 remains an explicitly documented team-integration task rather than an implementation guess.

## Minor implementation choices

- A1: Give employment and exposure bounds independent enable switches; disabled bounds pass None. Employment controls use persons and accept typed exact values. Exposure controls display 0–100 percent and pass fractions. No bounds are swapped.
- A5: List occupations in the detail selector in the current table's selected metric order, showing title plus SOC. Start with no selection.
- A6: Use literal Not reported for missing displayed fields, an em dash for unavailable aggregate summaries, and None required for verified literal None categories. CSV exports retain the underlying clean values and provenance fields.
- Visual choices: the required outlook colors use hexadecimal shades; the largest bubble is 45 pixels in Plotly with area sizing. These choices do not alter data or prioritization.
- Session persistence is Streamlit session_state plus CSV export as specified; no disk or account persistence is invented.

## Actual checks performed

- python -m unittest discover -s tests -v: all 17 existing backend/source checks passed in 1.431 seconds.
- Six raw-file SHA-256 fingerprints matched the audit, including the BLS workbook fingerprint a7d060f0576f7d4f5b829b9a0bb4a6c11a12766d159ebb0e07aab5bd2e7583c5.
- python -m analysis.run_phase2 --output-dir rebuild_check: exit 0. Occupation analysis, task matches, occupation master, and category-recovery CSVs regenerated byte-identically to the supplied canonical tables. Pipeline output is retained in pipeline_check.log.
- app.py parses via ast and compiles with python -m py_compile app.py: exit 0.
- 22 direct assertions passed for pure trial helpers and backend/export calls. They cover correct loading, formatting of zero/fractions/growth/missing/None, default programmers rank, idempotent add, reset interpretation, hidden saved occupations, all five metrics in both directions, all clean export fields plus consecutive saved-subset ranks, removal/clear, and empty-result formatting. Evidence is in trial_validation.json. These assertions do not test real Streamlit interactions.
- Attempted python app.py: exit 1 with the expected explicit message UI dependency unavailable: streamlit. Both Streamlit and Plotly availability were independently checked as false; runtime_check.log records the result.
- Runtime: Python 3.12.14, pandas 2.2.3, openpyxl 3.1.5. No dependencies were installed.

## Material inconsistencies found in the input snapshot

- START_HERE.md described Taotian's workbook as unavailable and the workbook verification/five-pipeline reproduction as still pending, while BUILD_SPEC.md, team_reconciliation.md, the workbook, and actual checks established verification and all five reproductions. It also reported 15 checks rather than 17.
- docs/fresh_agent_test.md also said 15 backend checks; 17 exist and passed. It correctly stated that backend checks alone were not the fresh-agent build trial.
- data_audit.json contains a legacy nested field named reported_result_not_reverified even though the same Taotian evidence marks reproduced, workbook_verified, and all 3,529 checks passing. Rename or remove that legacy field to avoid inconsistent evidence status.
- No numerical or join disagreement was found in the canonical analysis inputs. The clean-data snapshot matched the specified 755 analysis occupations, 756 master occupations, 17,760 task pairs, 154,223,400 included employment, three missing wages, and verified None categories.

The parent reported that source START_HERE.md was updated during this test to resolve its stale status/counts. This isolated report retains the discovery as evidence of what the fresh agent initially saw; the trial input copy itself was not refreshed during the initial test.

## Clarified-contract recheck — October 12, 2026

Read the updated source BUILD_SPEC.md and copied it into the existing isolated trial. Source and copied specification hashes were verified identical. All code/evidence changes remained inside the isolated trial; no source repository changes, installations, browser use, publishing, communications, or additional agents occurred.

The updated specification explicitly resolves the important questions:

| Question | Final contract | Trial recheck |
|---|---|---|
| Q1 Reset scope | Reset filter controls only; preserve metric/direction, saved shortlist, and still-visible detail. | Pure state/helper checks passed. |
| Q2 Invalid bounds | Suppress every comparison view including groups/details; retain Shortlist and mark outside-filter count unavailable; preserve detail identifier until valid filtering resumes. | Pure checks distinguish invalid from valid empty results; static AST checks verified conditional rendering and Shortlist wiring. |
| Q3 Rank population | Recalculate rank within the saved subset, with SOC tie-breaking and missing values last. | Backend/export checks passed for subset ranks, hidden saved rows, ties, and missing values. |
| Q4 Regenerated identifiers | Remove only unavailable saved SOCs; show a notice listing those SOCs; preserve valid saved rows/export; clear an absent detail SOC. | Trial changed to reconcile session identifiers before rendering. Pure checks passed for selective removal, returned notice identifiers, detail clearing, valid export, repeated reconciliation, and the all-removed case. |

The independently enabled range controls and detail dropdown order are also now explicit. No important product/data/metric/interaction guesses remain for the documented MVP. The proposed scope's team review, merge, submission, and selection/testing of UI dependency versions remain disclosed project tasks; no completion or team vote is inferred.

Recheck command: python recheck_validation.py. Exactly **22 checks passed**: 19 pure helper/backend assertions, 2 static AST assertions, and 1 successful Python syntax-compilation check. These are additional clarified-contract checks; the initial 22 checks remain preserved separately in trial_validation.json. The original 17 source/backend unit tests were not rerun during this targeted recheck because backend/data inputs were unchanged.

**No live UI runtime was tested.** Streamlit and Plotly remain unavailable. Pure functions and static code inspection cannot verify actual widgets, callback timing, Streamlit reruns, chart rendering, or browser behavior. The trial remains unverified Phase 3 build evidence.

Final fingerprints:

- Source BUILD_SPEC.md SHA-256: 67400d397e87271d96bb1ec85ddc4cbfa03a8d6eb3f4f322f31cc7862e8ab5ce
- Trial app.py SHA-256: 46a76f6d571600d086ee42624f2a943351f81762304509c6cbb6e1e1a169e52f

The parent corrected START_HERE.md. The source team_comparison_evidence.json and regenerated data_audit.json were inspected read-only and now use reproduced_result in place of the misleading legacy field. The initial inconsistencies above are retained as historical discoveries, not outstanding contradictions.

Recheck evidence is in recheck_validation.json; its runnable pure/static check script is recheck_validation.py. updated_spec_snapshot.json records the final source-specification/app fingerprints and confirms the source/trial specifications match. The original trial_validation.json and input snapshot remain unchanged.

## Files produced in the isolated trial

- app.py — begun Phase 3 MVP.
- docs/fresh_agent_test.md — this fresh-agent record.
- fresh_agent_input_snapshot.json — specification/backend/input fingerprints.
- trial_validation.json — 22 direct-check results and environment limitations.
- pipeline_check.log — canonical regeneration output.
- runtime_check.log — compilation and unavailable-UI startup evidence.
- rebuild_check/ — independently regenerated clean outputs, used only for comparison.

- recheck_validation.py / recheck_validation.json — runnable clarified-contract checks and results.
- updated_spec_snapshot.json — final source specification and trial-app fingerprints.
