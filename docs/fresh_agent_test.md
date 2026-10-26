# Phase 2 fresh-agent test

This record covers the score-based `integration-phase2` snapshot at commit
`8d463d80bbe60b22800a7ca7c52fe5274ca3cf21` before this handoff fix. It is an
acceptance record, not a claim that the score has been approved by the team.

## What was checked

- The repository explains the occupation/task grains, six-digit SOC joins,
  workbook category recovery, and the public backend functions in
  `analysis/backend.py`.
- With the six raw inputs present locally, `analysis.run_phase2` rebuilt 755
  matched occupations, a 756-row master, and 17,760 task pairs. The regenerated
  clean CSVs, ledger, and audit were byte-identical to the committed outputs.
- With only Git-tracked files in a temporary clone, the backend can use the
  committed clean tables, but the raw-source pipeline stops at the first missing
  input. The missing inputs are the five CSVs and the BLS XLSX listed in
  `data/README.md`.
- The original source-dependent test module ran 19/19 tests with the local raw
  inputs. A clean clone cannot run those reconstruction checks until the six
  inputs are supplied. Backend-only checks are separated in `analysis/tests/test_backend.py`
  and do not require raw inputs.

## Score review

The code and `BUILD_SPEC.md` agree on fixed 95th-percentile references and
weights of 40% observed exposure, 30% projected contraction, 20% employment
size, and 10% average task penetration. Growth/no-change receives zero on the
contraction component; missing required score inputs remain unavailable rather
than becoming zero. The score is a 0–100 screening rank for further review
under these stated choices. It is not a job-loss probability, a causal AI
effect, or validated training need. The weights, reference snapshot, and use of
the correlated exposure/task measures remain choices for team review; this file
does not say the team has approved them.

## Data access result and remaining items

The Drive preview was readable and identified `AI_transition_project_datasets.zip`;
a read-only archive check found all six expected files and matching hashes. This
does not prove every fresh agent has permission to download it. The archive does
not identify Anthropic or O*NET release dates/versions. Those provenance fields
remain unavailable and should be confirmed if the course requires them.

The official BLS page and workbook URL are documented in `data/README.md`, along
with the exact Table 1.2-to-CSV extraction steps. No permissions were changed,
and no raw data was committed.

## Local instruction conflict

The untracked local `AGENTS.md` describes Chang's individual Module 6 workflow,
requires stopping after a draft plan, and says to wait for Chang's approval before
implementing cleaning transformations. That conflicts with this user-authorized
integration handoff, which requests documentation/test fixes and submission. It
also requires an individual PDF outside this Phase 2 handoff. `AGENTS.md` and
`plan.md` remain local, unmodified, and uncommitted. The recommended resolution
is to keep those instructions scoped to Chang's individual cleaning branch and
use `BUILD_SPEC.md` plus the explicit integration task for this branch.
