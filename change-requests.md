# Team change requests

## Claims

| Author | Feature | Number | Distinct scope or new evidence |
| --- | --- | --- | --- |
| Taotianchen Wan | SOC major-group horizontal bar chart | Number of declining detailed occupations in each filtered SOC major group | Role 3: independently count distinct SOCs with negative numeric projected employment changes; compare all 22 groups and filtered totals with the backend; test negative, zero, positive, and missing growth; inspect the supplied Phase 3 chart source. Other teammates' features are outside scope. |

## Requests

### AUDIT-TW-03 Verify the supplied Phase 3 SOC chart in the running app

- **Author:** Taotianchen Wan
- **Status:** Open — backend checks passed; live UI verification pending.
- **Version checked:** Uploaded `app.py`, `analysis/backend.py`, `analysis/cleaning.py`, and `data/cleaned/occupation_clean_merged.csv`. File SHA-256 values are recorded in `my-audit.md` and `evidence/audit-results.json`. Their current Git commit was not supplied or independently verified.
- **Historical context:** The earlier record described a missing dashboard at commit `4a6a5b486bd08c179d14a72c9e5a1b8c7dd567b1`. That historical claim was not rechecked in this review. The subsequently supplied `app.py` contains the Phase 3 dashboard and SOC chart, so the missing-interface conclusion does not apply to the supplied file.
- **Intended behavior:** Under BUILD_SPEC.md, Compare occupations / U1, a horizontal chart must count declining occupations by SOC major group within the current filtered population. Bars must be ordered by count descending, labeled as occupation counts, and placed beside or after the bubble chart and before the ranking table. No-match filters must produce no bars.
- **Reproducible checks:** From the audit package root, run `python -m pip install -r audit-requirements.txt`, then `python checks/audit_soc_declines.py`. Inspect the SOC chart block in `app.py`, beginning with `groups_frame = backend.group_summary(filtered)`.
- **Expected result:** Group counts match independent counts of distinct SOCs with negative numeric projected employment change. The running chart uses those filtered counts and the required presentation.
- **Actual backend result:** All 36 real-data cases, one synthetic case, and two invalid-bound checks passed. The supplied table contains 755 unique occupations and 22 groups. There are 216 declining occupations overall, including SOC 51 = 66 and SOC 43 = 40. SOC 43 with exposure >=20% gives 17. Inputs remained unchanged.
- **Actual source result:** The supplied chart calls `group_summary(filtered)`, sorts declining counts descending with SOC ascending for ties, configures horizontal bars and the y-axis category order, and labels counts as occupations rather than displaced workers. It plots only positive-count groups and displays a message when none exist. The chart block follows the bubble chart and precedes the ranking table.
- **Evidence:** `checks/audit_soc_declines.py`, `evidence/audit-results.json`, `evidence/group-counts.csv`, the supplied `app.py`, and `analysis/backend.py` functions `filter_occupations`, `group_summary`, and `summary_metrics`. Individual conclusions and limitations are in `my-audit.md`.
- **Conclusion and remaining uncertainty:** No count defect was found in the supplied backend, and the chart configuration matches the inspected requirements. Browser rendering and interaction remain untested. The raw BLS source and original project test suite were not supplied and were not checked in this review.
- **Requested action:** Record the actual Phase 3 commit and run the UI checks below. This is a verification follow-up, not a confirmed counting bug. Change application code only if a reproducible mismatch is found.
- **Verification check and expected result:** With the supplied data, default bars sum to 216; SOC 51 gives 66; SOC 43 gives 40; SOC 43 with minimum exposure 20% gives 17. A no-match search produces no bars, and Growing-only produces no declining bars. Confirm descending visual order, occupation-count labels, correct placement, filter updates, and agreement between bar totals and the declining-occupation card.
- **Implementation commit and verification result:** Not yet recorded. No application implementation was changed in this review. Keep this request open until live UI verification is recorded.
- Supporting scripts, audit-requirements.txt, and evidence files referenced above are in my individual audit package and are not included in this PR.
