# Module 6 — Data Cleaning Checklist

Project: AI Workforce Investment Planner
Student: Kaho Sakemi

## 1. State the Project Vision and Question
Status: Done

Evidence:
Project Vision: Develop an AI Workforce Investment Planner
that helps businesses identify occupations where AI
investments may create opportunities for workforce
development and productivity improvements.

Business Question: Which occupations should businesses
prioritize for AI workforce investment based on observed
AI exposure, task penetration, and employment outlook?

Main Metrics:
- Observed AI exposure by occupation
- Average AI task penetration
- Projected employment growth (2025–2035)

Reference: code/explore_data.py


## 2. Define One Row
Status: Done

Evidence:
The final occupation-level dataset contains one row per
six-digit SOC occupation code.

Unique identifier: soc_code

The task-level dataset contains one row per matched
occupation-task combination.

Unique identifier: soc_code + task_normalized

Final dataset sizes:
- occupation_exploration.csv: 755 rows
- top_tasks_by_occupation.csv: 3,774 rows

Reference: code/explore_data.py

## 3. Preserve the Source
Status: Done

Source:
Team's shared Google Drive folder.

Files:
- job_exposure.csv
- task_penetration.csv
- onet_task_statements.csv
- onet_occupation_data.csv
- bls_table_1_2_2025_35.csv

Download date: October 19, 2026
Source version: Not independently verified.

Preservation:
Original CSV files are retained unchanged in data/.
Transformations are performed in separate DataFrames.
Raw data files are excluded from GitHub.

Loading:
pd.read_csv("data/filename.csv")

Reference:
- data/README.md
- code/explore_data.py

## 4. Inspect Columns and Types
Status: Done

Evidence:
Inspected data types across all five source datasets
using pandas dtypes.

Most columns were already assigned appropriate types,
including numeric AI exposure and task penetration values.

SOC occupation codes were retained as strings to preserve
their identifier formatting.

Two BLS columns required numeric conversion:
- Percent self-employed, 2025: 220 conversion failures
- Median annual wage, dollars, 2025: 9 conversion failures

All 229 failed conversions were caused by em dash (—)
placeholders rather than malformed numeric values.

Cleaning Rule:
Remove thousands separators from numeric strings and
convert values using pd.to_numeric(errors="coerce").

Treat em dash placeholders as missing values (NaN),
not zero, to avoid introducing misleading numerical values.

Reference:
- code/inspect_cleaning.py
- code/explore_data.py

## 5. Standardize Text
Status: Done

Evidence:
Task descriptions were standardized by converting text
to lowercase, replacing repeated whitespace with single
spaces, and removing leading/trailing whitespace.

Example:
Original:
"Accept and check containers of mail from large volume
mailers, couriers, and contractors."

Normalized:
"accept and check containers of mail from large volume
mailers, couriers, and contractors."

The task-penetration dataset contains 17,991 unique
normalized task descriptions.

O*NET occupation codes were standardized to six-digit
SOC codes for cross-dataset matching.

Examples:
11-1011.00 -> 11-1011
11-1011.03 -> 11-1011
11-1021.00 -> 11-1021

All 1,016 O*NET occupation codes were successfully
normalized, with zero failed conversions.

Original O*NET-SOC codes were preserved to retain
detailed occupational distinctions.

Reference:
- code/inspect_cleaning.py
- code/explore_data.py

NORMALIZED SOC DUPLICATE CHECK
Original O*NET occupations: 1016
Unique original O*NET-SOC codes: 1016
Unique normalized six-digit SOC codes: 867
Repeated normalized SOC codes: 149

## 7. Handle Missing Data
Status: Done

Evidence:
Missing values were inspected across all five
source datasets.

Four columns contained missing values:

Column                         Before   After
O*NET Task Type                  418      418
O*NET Incumbents Responding      587      587
BLS Related Work Experience      716      716
BLS On-the-Job Training          321      321

Cleaning Rule:
Preserve missing values in these descriptive and
occupational requirement columns rather than
replacing them with assumed values.

Business Justification:
These columns are not required for the current
AI exposure and task penetration calculations.
Imputing values could introduce unsupported
occupational characteristics.

Verification:
Missing-value counts were compared before and
after copying the original datasets. All four
counts remained unchanged.

Limitation:
This check verifies missing-value preservation
in source copies, not the final merged dataset.

Reference:
- code/inspect_cleaning.py

## 8. Check Suspicious Values
Status: Done

Evidence:
Checked numeric ranges, negative values, and date validity
across the source datasets.

AI Exposure:
- Minimum: 0.0
- Maximum: 0.7451
- Values outside 0–1: 0

Task Penetration:
- Minimum: 0.0
- Maximum: 1.0
- Values outside 0–1: 0

Employment and Job Openings:
- Negative 2025 employment values: 0
- Negative 2035 employment values: 0
- Negative annual occupational openings: 0

O*NET Task Dates:
- Invalid dates: 0
- Earliest date: June 1, 2006
- Latest date: August 1, 2026

Cleaning Decision:
No values were removed or modified based on these
validation checks because no violations were detected.

Date parsing produced a pandas format-inference warning,
but all dates were successfully converted.

Limitation:
These checks cover selected numerical and date validity
rules, not every possible data-quality issue.

Reference:
- code/inspect_cleaning.py

## 9. Validate Merges
Status: Done

Evidence:
Validated the merge between Anthropic AI exposure data
and BLS employment projections using standardized
six-digit SOC occupation codes.

Source Records:
- Anthropic occupations: 756
- BLS line-item occupations: 831

LEFT JOIN Validation:
- Total merged rows: 756
- Successfully matched occupations: 755
- Unmatched Anthropic occupations: 1
- Duplicate SOC codes after merge: 0

Unmatched Record:
- SOC: 11-1031
- Occupation: Legislators
- Observed AI exposure: 0.0

Cleaning Decision:
Preserve all original records.

Use an inner join for the final matched occupation-level
dataset, resulting in 755 occupations.

The unmatched Legislators record is excluded from the
matched analytical dataset because no corresponding
BLS line-item record was found.

Verification:
A left join with indicator=True and
validate="one_to_one" confirmed the match counts.

No duplicate occupation records were introduced.

Reference:
- code/inspect_cleaning.py
- code/explore_data.py

## 10. Reconcile Row Counts and Totals
Status: Done

Evidence:
Reconciled record counts and observed AI exposure
totals before and after merging Anthropic occupation
data with BLS employment projections.

Row Count Reconciliation:
- Original Anthropic occupations: 756
- Matched occupations: 755
- Excluded occupations: 1
- Expected matched occupations: 755
- Actual matched occupations: 755

Exposure Reconciliation:
- Original exposure sum: 58.1944
- Matched exposure sum: 58.1944
- Difference: 0.0

Verification:
Both automated reconciliation checks returned True.

Explanation:
The only excluded occupation was Legislators
(SOC 11-1031), with an observed exposure of 0.0.

Therefore, excluding this record did not change
the total exposure sum.

No unexpected record multiplication or exposure
changes were detected.

Limitation:
The exposure sum is used as a data integrity check,
not as a business KPI.

Reference:
- code/inspect_cleaning.py

## 11. Verify Calculations
Status: Done

Evidence:
Independently recalculated average task penetration
and matched task counts for all 755 occupations.

Initial Validation:
- Occupations checked: 755
- Task count mismatches: 5
- Average penetration mismatches: 4

Investigation:
The five mismatched occupations contained repeated
normalized task descriptions within the same six-digit
SOC classification.

Example:
SOC 19-3039 contained 32 task records but only
20 unique normalized task descriptions.

Cleaning Rule:
Remove duplicate normalized task descriptions within
each occupation before calculating average penetration.

Final Validation:
- Occupations checked: 755
- Task count mismatches: 0
- Average penetration mismatches: 0
- All calculations verified: True

Calculation:
Average task penetration =
Sum of penetration scores for unique matched tasks /
Number of unique matched tasks

Verification:
Reconstructed the calculation independently from
the original O*NET and task penetration datasets.

The recalculated averages and task counts matched
the team's output for all 755 occupations.

Reference:
- code/inspect_cleaning.py
- code/explore_data.py

## 12. Verify Five Individual Records
Status: Done

Evidence:
Five record-level checks were performed using original
source records, expected cleaning outcomes, and actual
results.

CHECK 1: Task Normalization
Original:
"Accept and check containers of mail from large volume
mailers, couriers, and contractors."

Expected:
"accept and check containers of mail from large volume
mailers, couriers, and contractors."

Actual:
"accept and check containers of mail from large volume
mailers, couriers, and contractors."

Result: PASS

CHECK 2: SOC Code Normalization
Original: 11-1011.00
Expected: 11-1011
Actual: 11-1011
Result: PASS

CHECK 3: Duplicate Task Removal
Original:
8 occurrences of the normalized task beginning
"write interesting and effective press releases..."

Expected: 1 occurrence
Actual: 1 occurrence
Result: PASS

CHECK 4: Unmatched Occupation
Original: Legislators (SOC 11-1031)
Expected: Excluded from matched analytical dataset
Actual: Excluded
Result: PASS

CHECK 5: Occupation-Level Calculation
Original: Chief Executives (SOC 11-1011)

Expected matched task count: 49
Actual matched task count: 49

Expected average task penetration: 0.032945
Actual average task penetration: 0.032945

Result: PASS

Verification Summary:
All five record-level checks passed.

Reference:
- code/inspect_cleaning.py
- outputs/occupation_exploration.csv

## 13. Test reproducibility
Status: Unresolved
Evidence:

## 14. Document remaining limitations
Status: Unresolved
Evidence: