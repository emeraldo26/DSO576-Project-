# Fresh coding-agent build test and resolved questions

Date: October 12, 2026 (UTC). Tool: a separate Codex coding subagent, `fresh_agent_test`, started without the prior project conversation. It received the repository path and instructions to follow `BUILD_SPEC.md`, begin the Phase 3 MVP, and record questions and assumptions. It worked only in an isolated copy. The supplied archive had no Git metadata, so no repository commit is invented; input and final fingerprints are retained in `docs/fresh_agent_evidence/`.

## Outcome

The agent began both dashboard tabs using the existing backend: filtering, cards, comparison chart definition, metric sorting, group summary, occupation details, top tasks, session shortlist, removal, and CSV export. It did not need to invent source joins, dates, missing-value imputations, metric formulas, composite-score weights, or risk thresholds.

The initial build identified three important interaction/ranking questions and one future-data question. The source specification was updated, and the isolated trial was checked against the clarified contracts. No significant product, data, metric, or interaction guesses remained for the documented MVP.

Streamlit and Plotly were unavailable. The trial app compiled, but actual UI rendering, widget callbacks, reruns, and browser interactions were not tested. This is Phase 3 build evidence, not a finished dashboard. The Phase 2 package's working implementation is in `analysis/`.

## Questions, guesses, and corrections

| Question raised | Initial interpretation | Final instruction and recheck |
|---|---|---|
| Does Reset clear sorting, details, or the shortlist? | Reset only filters; retain other state. | Explicitly preserve sorting, saved SOCs, and a still-visible detail selection. State/helper checks passed. |
| What appears when a minimum exceeds its maximum? | Suppress comparisons while allowing access to saved rows. | Show the input error; suppress cards/chart/table/groups/details; keep Shortlist accessible and its outside-filter count unavailable. Pure and static conditional-rendering checks passed. |
| Is shortlist rank global, filtered, or within saved rows? | Existing backend ranks the saved subset. | Explicitly rank 1..N within saved rows under the selected metric/direction, with SOC tie-breaking and missing values last. Backend/export checks passed. |
| What if regenerated data removes a saved SOC? | Initially pause shortlist table/export and offer Clear. | Remove only unavailable identifiers, name them in a notice, keep valid saved rows/export, and clear an absent detail SOC. Trial changed; targeted checks passed. |
| Has every teammate approved replacing the composite score? | Follow the proposed specification without claiming a vote. | Team review remains part of integration. No score weights or approval are invented. |

Minor choices were recorded: independent enable switches for each bound, selector order matching the sorted table, display formatting, and specific shades/bubble size. Bound and selector behaviors are now explicit. Visual choices do not change calculations or ranking.

The agent also found stale handoff text: 15 checks instead of 17, pending workbook status despite completed verification, and a legacy `reported_result_not_reverified` label. The guide was corrected; the evidence field is now `reproduced_result`, and the audit was regenerated. The full report preserves these discoveries as history.

## Checks actually performed

- All 17 existing source/backend unit tests passed in the fresh copy.
- All six raw-source fingerprints matched the audit.
- The pipeline regenerated the four canonical CSVs byte-identically: analysis occupations, master occupations, task matches, and category-recovery ledger.
- The initial trial passed 22 helper/backend/export assertions and Python syntax compilation.
- The clarified-contract recheck passed 22 checks: 19 pure helper/backend assertions, 2 static AST checks, and 1 syntax-compilation check. These did not execute real UI widgets or chart rendering.
- Attempted startup reported the unavailable Streamlit dependency. Both UI libraries were independently confirmed unavailable; none was installed.

Runtime: Python 3.12.14, pandas 2.2.3, openpyxl 3.1.5. No publishing, external messages, or source-repository changes were performed by the fresh agent.

## Evidence and remaining work

`docs/fresh_agent_evidence/` contains the full agent report, initial/final fingerprints, initial/recheck results, regeneration/startup logs, and exact trial source and recheck script as `.py.txt` evidence. Those text files are for inspection and are not used by the Phase 2 pipeline. Original trial paths are historical provenance.

Final specification SHA-256: `67400d397e87271d96bb1ec85ddc4cbfa03a8d6eb3f4f322f31cc7862e8ab5ce`.

Trial app SHA-256: `46a76f6d571600d086ee42624f2a943351f81762304509c6cbb6e1e1a169e52f`.

The team still needs to review and merge the agreed implementation into `main`, record the actual merge commit, and follow course submission instructions. Selecting/testing UI dependency versions and running the actual dashboard remain Phase 3 work.
