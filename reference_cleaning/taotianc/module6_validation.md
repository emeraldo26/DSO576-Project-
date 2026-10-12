# Module 6 validation summary

Scope: **national occupation-screening prototype**. Compare observed AI exposure
and matched task penetration with BLS employment, outlook and training context.
California funding conclusions need California data. No priority score, weights
or thresholds were created.

## Actual results

| Check/result | Actual |
|---|---:|
| Final full-source validations | 3,529 PASS, 0 FAIL |
| Saved-output individual-record checks | 5 PASS, 0 FAIL |
| Original data files with identical before/after SHA-256 | 6 of 6 |
| Clean source row counts | 756; 17,998; 1,016; 18,838; 1,112 |
| BLS literal None categories recovered in canonical companions | 716 experience + 321 OJT = 1,037 |
| Occupation master | 756; Legislators retained as job_only |
| Optional BLS-complete view | 755 |
| Matched occupation-task links for that view | 17,760 |
| Top-five displayed task links | 3,774 |
| Submitted sample | 50 rows |
| Fresh-process output comparison | 41 of 41 files byte-identical |
| Deliberately changed copied input | Correctly rejected before cleaning |

Full output: `outputs/module6/`. Compact evidence is in
[module6_evidence](module6_evidence/); detailed row ledgers are generated locally.
[Run instructions](../code/README.md) list all output filenames and commands.
[plan.md section 8](../plan.md#8-exact-module-6-checklist-and-evidence) maps the
actual evidence to the fourteen assignment items. Source release/download
metadata is the one partially unresolved checklist item; preservation passed.

## Five checks written before execution

The expected values in `code/module6_record_expectations.json` were recorded
before running the pipeline. The checker reloads saved outputs as text.

| Record | Original | Expected | Actual | Match |
|---|---|---|---|---|
| BLS 00-0000 | Leading-zero text ID; Summary; employment 170280.8 | Preserve ID, summary and control total | Exact ID; Summary; 170280.8; is_line_item=False | PASS |
| BLS 11-1011 | OJT CSV blank; workbook literal None | Canonical None, no missing flag; retain both originals | None; missing reason empty; CSV blank and workbook None retained | PASS |
| BLS 51-2061 | Employment .2→.2; change 0; published -6.1%; openings 0; self-employment em dash | Retain -6.1 and zeros; only unavailable self-employment null | .2→.2; 0; -6.1; 0; null with source_unavailable | PASS |
| Job 11-1031 | Legislators; exposure 0; no BLS match | Retain master row with job_only and null BLS values | Exposure 0; job_only; null BLS employment | PASS |
| Job 23-2011 | Twelve O*NET tasks, seven measured, five unmatched | Denominator 7, coverage 7/12, mean .133857142857 | Counts 12/7/5; coverage .583333333333; mean .133857142857 | PASS |

The machine-readable [five-record file](module6_evidence/five_record_checks.csv)
includes complete original, expected and actual values plus the reason. No
unmatched task is imputed to zero.

## How the Codex suggestion was verified

The proposed recovery of BLS `None` was checked against all 1,112 code-aligned
workbook rows. The prior CSV differs in exactly 716 work-experience cells and
321 OJT cells; each is a blank corresponding to a literal workbook `None`.
All other retained text fields match, and all numeric fields match within
floating serialization precision. Table 1.10 independently matches shared
measures for all 1,112 codes. Recovery copies only verified workbook cells into
new canonical fields. It does not reinterpret unrelated blanks.

The alternative of stripping punctuation from task keys was rejected on concrete
evidence: `Maintain customer records using automated systems.` has penetration
0.7239 while its comma variant has 1.0. Both remain separate; three such conflicting
pairs have explicit regression checks.

## Failures and resolutions

The initial development run stopped with `sample maximum 50 records: actual=49;
expected=50`. `31-1120` was incorrectly included in a master-table sample selection
even though its code is BLS-only. The corrected sample labels it as a BLS control
and now includes 48 master rows plus two controls. The failed run is retained in
`outputs/module6-run1/`; the final result is `outputs/module6/`.

There are **no unresolved failures in the final run**. The later negative test
intentionally changed one exposure value in temporary copied inputs; a nonzero
exit and source-hash error were the expected successful outcome of that test.

## Preservation and limits

The six source hashes are unchanged. The pre-existing uncommitted
`data/README.md` edit is also byte-identical to its starting hash:
`2a19f633cd2a81a895dbafcd37c5227c03c4924300500a2bc442925fc74b4681`.

Original release/download metadata, state-specific evidence, task-match gaps,
SOC version equivalence, vintage differences, BLS rounding and wage-population
limits remain documented in plan section 9. No score or causal conclusion is
supported by cleaning alone. The subsequent submission-artifact step produced a
six-page Gradescope PDF and a notebook executed from a fresh kernel. See
`code/README.md`, `notebook_execution.json` and `independent_bls_none_check.json`
in the evidence folder. Cleaning commit: `1f85f180ceb04b71e7bd921f706859c04317acbd`.
The later metadata update records this ID without changing cleaning rules or source
data. No Gradescope upload is performed.
