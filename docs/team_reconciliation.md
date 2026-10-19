# Cleaning reconciliation - canonical implementation

Review date: October 11, 2026. The five shared CSVs have the same SHA-256 fingerprints as the checked manifests in Chang's, Xiru's, and Taotian's submissions. All five CSV fingerprints remained unchanged during this review. Exact source releases remain unspecified.

The supplied work covers Brahmani Mundhe, Chang Zhou, Taotianchen Wan, Xiru Zhang, and Emerald Ouyang. No cleaning submission for Kaho Sakemi was supplied, so none is assumed. The selected canonical rules below are implemented and checked. All five supplied pipelines were reproduced. Workbook-category recovery is independently verified. The fresh-agent test is recorded separately, and this package has not been merged into main.

## What was actually checked

| Submission | Reproduction in this review | Occupation treatment | Evidence retained |
|---|---|---|---|
| Brahmani | Script ran successfully on the five common CSVs; six of seven cleaned CSVs reproduced byte-identically | 755 matched occupations | Original script/report/evidence and numeric comparison |
| Chang | Full script ran successfully; its five record checks passed | 756-row master, including unmatched Legislators | Original script/README and reproduced validation JSON |
| Xiru | Cleaning script ran successfully with source/output paths directed to isolated review folders | 755 matched occupations | Original script/report/manifest and reproduced audit |
| Emerald | Cleaning script ran successfully with source/output paths directed to isolated review folders | 756-row left-joined exposure master; task sources cleaned separately | Original script/README and reproduced merge summary |
| Taotian | Full pipeline reproduced with the verified original workbook: 3,529 checks passed, 0 failed | 756-row master and 755-row BLS-complete view | Original script, expectations, manifests, supplied evidence, and reproduced results |

Unmodified reference scripts and relevant records are under reference_cleaning/. Machine-readable results and uploaded-archive fingerprints are in docs/team_comparison_evidence.json. Recorded branch commit references come from the submissions; the ZIP archives themselves do not contain Git histories.

## Differences and proposed resolution

| Topic | Difference found | Selected canonical rule and reason |
|---|---|---|
| Master versus analysis scope | Chang and Emerald keep Legislators; Brahmani and Xiru exclude it from BLS-dependent analysis. Taotian reports both views. | Preserve all 756 exposure occupations in occupation_master.csv; use the 755 BLS matches in occupation_clean_merged.csv. Preserve coverage evidence while keeping the Phase 1 comparison scope explicit. |
| Occupation measures | Exposure, employment, projected change, openings, and wages match across all five reproduced pipelines for the common 755 SOCs. | Keep original measured values and validate one-to-one joins. |
| Task duplicates | Some submissions preserve raw rows and consolidate only a lookup; others save a deduplicated source copy. | Raw inputs remain untouched. The analytical lookup has 17,991 distinct normalized tasks, removing seven redundant equal-score rows, including six exact duplicates. Conflicting scores raise an error. |
| Task-link counts | 18,656 distinct scored SOC/task pairs cover all source O*NET occupations; the dashboard scope contains 17,760 of them. | Record both populations. Store only the 17,760 dashboard pairs in its task table. These counts measure different scopes and do not indicate a failed join. |
| Task-average precision | Brahmani stores four-decimal means. Chang and Xiru retain full calculation precision. | Store full precision; round only in the UI. The arithmetic uses the same distinct measured tasks and includes true zero values. |
| Reproduction rounding tie | One uploaded Brahmani cell (41-4012) is 0.4797; rerunning the supplied script produces 0.4796. The full mean is 0.47965. | Avoid storing a four-decimal rounded derived mean. This is a rounding-boundary difference, not a substantive change in the source observations. |
| Highest tasks | Top-five score lists agree in the common 755-occupation scope across the three reproduced pipelines that produce them. Tied task texts can differ because tie-breaking differs. Chang also writes top tasks outside this scope. | Sort penetration descending, then normalized task text ascending. This gives repeatable selection without claiming a distinction between tied scores. |
| Missing wage | The common analysis view contains three missing wages. | Keep occupations; display missing wage as unavailable rather than zero. |
| Experience/training blanks | Brahmani labels blanks Not specified in source; Chang/Xiru/Emerald preserve missingness. Taotian reports recovering literal None categories from a separate workbook. | Workbook comparison verified all 1,112 codes and shared fields. Recover only the 716 experience and 321 training CSV blanks backed by literal workbook None; preserve original CSV/workbook values and a cell ledger. Within the analysis view, 646 experience and 295 training categories are recovered. No other blank is filled. |
| Units and percentages | Source employment/openings are thousands. Projected change is already expressed in percent units. | Keep source-unit fields and add fields multiplied by 1,000 for person-count display. Never multiply projected growth by 100 again. |
| Valid decline and low counts | Negative projected change and zero openings appear legitimately. Some combined detailed SOC codes end in zero. | Retain detailed rows selected by Occupation type = Line item; preserve published growth, genuine zeros, and valid six-digit codes. Do not reject codes simply because they end in zero. |
| Priority score | The inspected individual cleaning submissions supply no agreed score or weights. | A separately proposed, transparent 40/30/20/10 review-priority formula is in `BUILD_SPEC.md` and `analysis/backend.py`; it is not a job-loss probability. Team review is pending before integration. |

## Checked totals and boundaries

- Master: 756 exposure occupations. Analysis: 755. The unmatched SOC is 11-1031, Legislators.
- All BLS detailed rows: 831. Summary rows: 281; they never enter occupation-level employment totals.
- Included employment: 154,223.4 thousand, or 154,223,400 persons. Included annual openings: 15,607.2 thousand per year.
- Distinct source penetration keys: 17,991; keys matching O*NET text: 17,429. Matched original O*NET task rows: 18,680 of 18,838. Distinct scored SOC/task pairs across all O*NET SOCs: 18,656; in dashboard scope: 17,760.
- Source gaps and zero penetration remain distinct. No occupation/task metric is imputed from unmatched text.

## Workbook verification completed

The workbook uploaded as occupation.xlsx is byte-identical to the source recorded by Taotian: SHA-256 a7d060f0576f7d4f5b829b9a0bb4a6c11a12766d159ebb0e07aab5bd2e7583c5. It is stored under data/bls_occupation_tables_2025_35.xlsx. The official download link is https://www.bls.gov/emp/ind-occ-matrix/occupation.xlsx.

The independent canonical verifier checked all 1,112 codes, all nine numeric fields, and every other text field. The only allowed differences were 716 experience and 321 training CSV blanks corresponding to literal workbook None. Shared numeric measures also agree with Table 1.10. The 1,037 recovered cells and workbook addresses are recorded in data/cleaned/bls_category_recovery.csv. All raw files remain unchanged.

Taotian's full original pipeline now passes 3,529 checks, and its seven common occupation measures agree with the canonical analysis table. Original and reproduced records are under reference_cleaning/taotianc/. The project's separate 17 backend checks also pass.

## Remaining integration

Review the chosen scope and canonical decisions with the team when merging. No claim of a separate all-member vote is made. If another member has a separate cleaning submission, include it in the comparison. Exact Anthropic/O*NET release metadata remains unspecified and is explicitly labeled in the specification. The merge into main and the final Canvas/Gradescope upload have not been performed.
