# Module 6 — Cleaning Decision Log

## Decision 1: Duplicate Task Descriptions

Dataset: task_penetration.csv

Issue:
Duplicate task descriptions were identified.

Evidence:
- Original records: 17,998
- Exact duplicate rows: 6
- Repeated normalized task records: 8
- Conflicting penetration values: 0

Decision:
Retain one record per normalized task description.

Business Justification:
Prevents duplicate task matches without discarding
conflicting penetration measurements.

Verification:
Verification:
- Original records: 17,998
- Cleaned records: 17,991
- Records removed: 7
- Remaining duplicate normalized tasks: 0
- Unique task descriptions preserved: 17,991

Result:
Deduplication was successful. All unique normalized
task descriptions were retained, and no conflicting
penetration values were discarded.

## Decision 2: Missing Values

Datasets:
- onet_task_statements.csv
- bls_table_1_2_2025_35.csv

Issue:
Several descriptive and occupational requirement
columns contain missing values.

Evidence:
- O*NET Task Type: 418 missing values
- O*NET Incumbents Responding: 587 missing values
- BLS Related Work Experience: 716 missing values
- BLS On-the-Job Training: 321 missing values

Decision:
Preserve missing values rather than imputing
unsupported information.

Business Justification:
These columns are not required for the current
AI exposure and task penetration calculations.
Replacing missing values with assumed categories
or numerical values could misrepresent occupational
characteristics.

Verification:
Verification:
- Confirmed 716 missing values in BLS related work experience.
- Confirmed 321 missing values in BLS on-the-job training.
- Identified 281 dash placeholders in each BLS column.
- Sample inspection showed missing values in line-item
  occupations and dash placeholders in summary occupations.
- Missing values were preserved rather than imputed.

Result:
Missing values were retained to avoid introducing unsupported
occupational characteristics. Summary-level BLS records were
excluded from the occupation-level analysis.

Limitation:
Missing occupational requirement information may limit
future dashboard filtering and comparisons.

## Decision 3: Unmatched Occupation

Datasets:
- job_exposure.csv
- bls_table_1_2_2025_35.csv

Issue:
One Anthropic occupation could not be matched to a
BLS line-item occupation using its SOC code.

Evidence:
- Anthropic occupations: 756
- Successfully matched: 755 (99.9%)
- Unmatched: Legislators (SOC 11-1031)
- Observed AI exposure for Legislators: 0.0

Decision:
Exclude the unmatched occupation from the integrated
occupation-level dataset while retaining it in the
original source data.

Business Justification:
The dashboard requires both AI exposure and BLS
employment information. Including an unmatched
occupation would result in incomplete employment
metrics.

Verification:
- Confirmed exactly one unmatched SOC code.
- Confirmed the unmatched occupation is Legislators.
- Confirmed the final integrated dataset contains
  755 occupation records.

Limitation:
The dashboard excludes Legislators and therefore
does not provide complete coverage of all Anthropic
occupations.