import pandas as pd
from pathlib import Path

data_dir = Path("data")

files = [
    "job_exposure.csv",
    "task_penetration.csv",
    "onet_task_statements.csv",
    "onet_occupation_data.csv",
    "bls_table_1_2_2025_35.csv"
]

for filename in files:
    df = pd.read_csv(data_dir / filename, low_memory=False)

    print(f"\n{'=' * 50}")
    print(f"DATASET: {filename}")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\nColumn names:")
    print(df.columns.tolist())

    print("\nMissing values:")
    print(df.isna().sum().to_string())

    print("\nDuplicate rows:")
    print(df.duplicated().sum())


penetration = pd.read_csv("data/task_penetration.csv")

penetration["task_normalized"] = (
    penetration["task"]
    .astype("string")
    .str.lower()
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

duplicates = penetration[
    penetration.duplicated("task_normalized", keep=False)
]

print("\nDUPLICATE TASK ANALYSIS")
print("Rows with repeated normalized task:", len(duplicates))
print("Unique repeated task descriptions:", duplicates["task_normalized"].nunique())

conflicts = (
    duplicates.groupby("task_normalized")["penetration"]
    .nunique()
)

print("Tasks with conflicting penetration values:", (conflicts > 1).sum())

print("\nSample repeated tasks:")
print(
    duplicates[["task", "penetration"]]
    .head(20)
    .to_string(index=False)
)

# Verify duplicate removal

penetration_unique = penetration.drop_duplicates(
    subset="task_normalized"
)

print("\nDEDUPLICATION VERIFICATION")
print("Original rows:", len(penetration))
print("Cleaned rows:", len(penetration_unique))
print("Rows removed:", len(penetration) - len(penetration_unique))

print(
    "Remaining duplicate task descriptions:",
    penetration_unique.duplicated("task_normalized").sum()
)

print(
    "Original unique task descriptions:",
    penetration["task_normalized"].nunique()
)

print(
    "Cleaned unique task descriptions:",
    penetration_unique["task_normalized"].nunique()
)

# Investigate missing values

onet = pd.read_csv("data/onet_task_statements.csv")
bls = pd.read_csv("data/bls_table_1_2_2025_35.csv")

print("\nO*NET MISSING VALUE ANALYSIS")

for col in ["Task Type", "Incumbents Responding"]:
    print(f"\nColumn: {col}")
    print("Missing:", onet[col].isna().sum())
    print("Non-missing examples:")
    print(onet[col].dropna().value_counts().head(5))

print("\nBLS MISSING VALUE ANALYSIS")

for col in [
    "Work experience in a related occupation",
    "Typical on-the-job training needed to attain competency in the occupation"
]:
    print(f"\nColumn: {col}")
    print("Missing:", bls[col].isna().sum())
    print("Non-missing examples:")
    print(bls[col].dropna().value_counts().head(5))

    print("\nMissing values by occupation type:")
    print(
        bls.groupby("Occupation type")[col]
        .apply(lambda x: x.isna().sum())
    )

# Examine BLS missing values and dash placeholders

bls = pd.read_csv("data/bls_table_1_2_2025_35.csv")

columns = [
    "Work experience in a related occupation",
    "Typical on-the-job training needed to attain competency in the occupation"
]

for col in columns:
    print(f"\nCOLUMN: {col}")

    print("Missing values:", bls[col].isna().sum())
    print("Dash values:", (bls[col] == "—").sum())

    print("\nExamples of rows with missing values:")

    print(
        bls.loc[
            bls[col].isna(),
            [
                "2025 National Employment Matrix title",
                "Occupation type",
                col
            ]
        ]
        .head(5)
        .to_string(index=False)
    )

    print("\nExamples of rows with dash values:")

    print(
        bls.loc[
            bls[col] == "—",
            [
                "2025 National Employment Matrix title",
                "Occupation type",
                col
            ]
        ]
        .head(5)
        .to_string(index=False)
    )

# Investigate unmatched SOC codes

jobs = pd.read_csv("data/job_exposure.csv")
bls = pd.read_csv("data/bls_table_1_2_2025_35.csv")

bls_line = bls[bls["Occupation type"] == "Line item"].copy()

bls_codes = set(
    bls_line["2025 National Employment Matrix code"]
    .astype(str)
    .str.extract(r"(\d{2}-\d{4})", expand=False)
    .dropna()
)

jobs["soc_code"] = (
    jobs["occ_code"]
    .astype(str)
    .str.extract(r"(\d{2}-\d{4})", expand=False)
)

unmatched = jobs[~jobs["soc_code"].isin(bls_codes)]

print("\nUNMATCHED OCCUPATION ANALYSIS")
print("Anthropic occupations:", len(jobs))
print("Unmatched occupations:", len(unmatched))
print(unmatched[["occ_code", "title", "observed_exposure"]].to_string(index=False))

print("\nDATA TYPE INSPECTION")

for filename in files:
    df = pd.read_csv(data_dir / filename, low_memory=False)

    print(f"\nDATASET: {filename}")
    print(df.dtypes.to_string())

# Investigate BLS numeric conversions

bls = pd.read_csv("data/bls_table_1_2_2025_35.csv")

columns = [
    "Percent self-employed, 2025",
    "Median annual wage, dollars, 2025"
]

print("\nBLS NUMERIC CONVERSION ANALYSIS")

for col in columns:
    print(f"\nColumn: {col}")

    original = bls[col].astype("string").str.strip()

    cleaned = original.str.replace(",", "", regex=False)

    numeric = pd.to_numeric(cleaned, errors="coerce")

    failed = original.notna() & numeric.isna()

    print("Original dtype:", bls[col].dtype)
    print("Converted dtype:", numeric.dtype)
    print("Failed conversions:", failed.sum())

    print("\nValues that failed conversion:")
    print(original[failed].value_counts().head(10))

print("\nTEXT STANDARDIZATION VERIFICATION")

# Check task descriptions
print("\nTASK TEXT")

print("Original example:")
print(penetration["task"].iloc[0])

print("\nNormalized example:")
print(penetration["task_normalized"].iloc[0])

print("\nUnique normalized tasks:")
print(penetration["task_normalized"].nunique())

# Check SOC codes
onet_occ = pd.read_csv("data/onet_occupation_data.csv")

onet_occ["soc_normalized"] = (
    onet_occ["O*NET-SOC Code"]
    .astype("string")
    .str.extract(r"(\d{2}-\d{4})", expand=False)
)

print("\nSOC CODE STANDARDIZATION")

print(
    onet_occ[
        ["O*NET-SOC Code", "soc_normalized"]
    ].head(5).to_string(index=False)
)

print(
    "\nSOC codes that failed normalization:",
    onet_occ["soc_normalized"].isna().sum()
)

print("\nREPEATED IDENTIFIER ANALYSIS")

# Anthropic occupation identifiers
jobs = pd.read_csv("data/job_exposure.csv")

print(
    "Repeated Anthropic occupation codes:",
    jobs.duplicated("occ_code").sum()
)

# O*NET occupation identifiers
onet_occ = pd.read_csv("data/onet_occupation_data.csv")

print(
    "Repeated original O*NET-SOC codes:",
    onet_occ.duplicated("O*NET-SOC Code").sum()
)

print(
    "Repeated normalized six-digit SOC codes:",
    onet_occ.duplicated("soc_normalized").sum()
    if "soc_normalized" in onet_occ.columns
    else "Not calculated"
)

# O*NET task identifiers
onet_tasks = pd.read_csv("data/onet_task_statements.csv")

print(
    "Repeated O*NET Task IDs:",
    onet_tasks.duplicated("Task ID").sum()
)

# BLS occupation identifiers
bls = pd.read_csv("data/bls_table_1_2_2025_35.csv")
bls_line = bls[bls["Occupation type"] == "Line item"]

print(
    "Repeated BLS line-item occupation codes:",
    bls_line.duplicated(
        "2025 National Employment Matrix code"
    ).sum()
)

# Check repeated normalized SOC codes

onet_occ = pd.read_csv("data/onet_occupation_data.csv")

onet_occ["soc_normalized"] = (
    onet_occ["O*NET-SOC Code"]
    .astype("string")
    .str.extract(r"(\d{2}-\d{4})", expand=False)
)

print("\nNORMALIZED SOC DUPLICATE CHECK")

print(
    "Original O*NET occupations:",
    len(onet_occ)
)

print(
    "Unique original O*NET-SOC codes:",
    onet_occ["O*NET-SOC Code"].nunique()
)

print(
    "Unique normalized six-digit SOC codes:",
    onet_occ["soc_normalized"].nunique()
)

print(
    "Repeated normalized SOC codes:",
    onet_occ.duplicated("soc_normalized").sum()
)

print("\nMISSING VALUE VERIFICATION")

# Load original datasets
onet = pd.read_csv("data/onet_task_statements.csv")
bls = pd.read_csv("data/bls_table_1_2_2025_35.csv")

# Create separate copies for cleaning
onet_clean = onet.copy()
bls_clean = bls.copy()

# Preserve missing values in descriptive columns
onet_columns = [
    "Task Type",
    "Incumbents Responding"
]

bls_columns = [
    "Work experience in a related occupation",
    "Typical on-the-job training needed to attain competency in the occupation"
]

for col in onet_columns:
    print(f"\nO*NET: {col}")
    print("Before:", onet[col].isna().sum())
    print("After:", onet_clean[col].isna().sum())

for col in bls_columns:
    print(f"\nBLS: {col}")
    print("Before:", bls[col].isna().sum())
    print("After:", bls_clean[col].isna().sum())

print("\nSUSPICIOUS VALUE ANALYSIS")

jobs = pd.read_csv("data/job_exposure.csv")
tasks = pd.read_csv("data/task_penetration.csv")
onet = pd.read_csv("data/onet_task_statements.csv")
bls = pd.read_csv("data/bls_table_1_2_2025_35.csv")

# Check AI exposure and penetration ranges
for df, col in [
    (jobs, "observed_exposure"),
    (tasks, "penetration")
]:
    print(f"\n{col}")
    print("Minimum:", df[col].min())
    print("Maximum:", df[col].max())
    print("Outside 0–1:", ((df[col] < 0) | (df[col] > 1)).sum())

# Check negative employment values
for col in [
    "Employment, 2025",
    "Employment, 2035",
    "Occupational openings, 2025–35 annual average"
]:
    print(f"\n{col}")
    print("Negative values:", (bls[col] < 0).sum())

# Check O*NET dates
dates = pd.to_datetime(onet["Date"], errors="coerce")

print("\nO*NET Date")
print("Invalid dates:", dates.isna().sum())
print("Earliest date:", dates.min())
print("Latest date:", dates.max())

print("\nMERGE VALIDATION")

jobs = pd.read_csv("data/job_exposure.csv")
bls = pd.read_csv("data/bls_table_1_2_2025_35.csv")

# Standardize occupation codes
jobs["soc"] = (
    jobs["occ_code"]
    .astype("string")
    .str.extract(r"(\d{2}-\d{4})", expand=False)
)

bls["soc"] = (
    bls["2025 National Employment Matrix code"]
    .astype("string")
    .str.extract(r"(\d{2}-\d{4})", expand=False)
)

# Keep detailed occupation rows
bls = bls[bls["Occupation type"] == "Line item"].copy()

# Merge with indicator to identify unmatched records
merged = jobs.merge(
    bls,
    on="soc",
    how="left",
    indicator=True,
    validate="one_to_one"
)

print("Anthropic occupations:", len(jobs))
print("BLS line-item occupations:", len(bls))
print("Merged rows:", len(merged))

print("\nMerge match status:")
print(merged["_merge"].value_counts())

print("\nDuplicate SOC codes after merge:")
print(merged.duplicated("soc").sum())

print("\nUnmatched occupations:")
print(
    merged.loc[
        merged["_merge"] == "left_only",
        ["soc", "title", "observed_exposure"]
    ].to_string(index=False)
)

print("\nRECONCILIATION CHECK")

jobs = pd.read_csv("data/job_exposure.csv")
bls = pd.read_csv("data/bls_table_1_2_2025_35.csv")

jobs["soc"] = (
    jobs["occ_code"]
    .astype("string")
    .str.extract(r"(\d{2}-\d{4})", expand=False)
)

bls["soc"] = (
    bls["2025 National Employment Matrix code"]
    .astype("string")
    .str.extract(r"(\d{2}-\d{4})", expand=False)
)

bls = bls[bls["Occupation type"] == "Line item"].copy()

merged = jobs.merge(
    bls,
    on="soc",
    how="inner",
    validate="one_to_one"
)

print("Original Anthropic rows:", len(jobs))
print("Matched rows:", len(merged))
print("Excluded rows:", len(jobs) - len(merged))

original_total = jobs["observed_exposure"].sum()
matched_total = merged["observed_exposure"].sum()

print("\nOriginal exposure sum:", round(original_total, 4))
print("Matched exposure sum:", round(matched_total, 4))
print("Difference:", round(original_total - matched_total, 4))

print("\nExpected matched rows:", 755)
print("Actual matched rows:", len(merged))

print(
    "Row count check passed:",
    len(merged) == 755
)

print(
    "Exposure sum check passed:",
    abs(original_total - matched_total) < 0.000001
)

print("\nCALCULATION VALIDATION")

tasks = pd.read_csv("data/task_penetration.csv")

# Normalize task descriptions
tasks["task_normalized"] = (
    tasks["task"]
    .astype("string")
    .str.lower()
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

# Remove duplicate normalized tasks
tasks_clean = tasks.drop_duplicates(
    subset="task_normalized"
)

print("Original task records:", len(tasks))
print("Cleaned task records:", len(tasks_clean))

print(
    "Missing penetration values:",
    tasks_clean["penetration"].isna().sum()
)

print(
    "Missing normalized task descriptions:",
    tasks_clean["task_normalized"].isna().sum()
)

print(
    "Duplicate normalized tasks remaining:",
    tasks_clean.duplicated("task_normalized").sum()
)

print(
    "Average penetration:",
    round(tasks_clean["penetration"].mean(), 4)
)

print("\nOCCUPATION CALCULATION INSPECTION")

occupations = pd.read_csv(
    "outputs/occupation_exploration.csv"
)

print("\nColumns:")
print(occupations.columns.tolist())

print("\nFirst 5 rows:")
print(occupations.head(5).to_string(index=False))

print("\nMissing values by column:")
print(occupations.isna().sum().to_string())

print("\nDuplicate occupation codes:")
for col in occupations.columns:
    if "soc" in col.lower():
        print(col, occupations.duplicated(col).sum())


print("\nTASK OUTPUT INSPECTION")

task_output = pd.read_csv(
    "outputs/top_tasks_by_occupation.csv"
)

print("\nColumns:")
print(task_output.columns.tolist())

print("\nFirst 5 rows:")
print(task_output.head(5).to_string(index=False))

print("\nTotal rows:", len(task_output))

print("\nMissing values by column:")
print(task_output.isna().sum().to_string())

print("\nCHIEF EXECUTIVES CALCULATION CHECK")

# Load source datasets
onet = pd.read_csv("data/onet_task_statements.csv")
penetration = pd.read_csv("data/task_penetration.csv")
occupations = pd.read_csv("outputs/occupation_exploration.csv")

# Normalize task descriptions
for df, col in [(onet, "Task"), (penetration, "task")]:
    df["task_normalized"] = (
        df[col]
        .astype("string")
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

# Remove duplicate task-penetration records
penetration = penetration.drop_duplicates(
    subset="task_normalized"
)

# Normalize O*NET occupation codes
onet["soc_code"] = (
    onet["O*NET-SOC Code"]
    .astype("string")
    .str.extract(r"(\d{2}-\d{4})", expand=False)
)

# Select Chief Executives' tasks
chief_tasks = onet[onet["soc_code"] == "11-1011"]

# Match tasks to penetration scores
matched = chief_tasks.merge(
    penetration[["task_normalized", "penetration"]],
    on="task_normalized",
    how="inner",
    validate="many_to_one"
)

# Calculate average using all matched task records
calculated_average = matched["penetration"].mean()
calculated_count = len(matched)

# Retrieve values from the team's output
reported = occupations.loc[
    occupations["soc_code"] == "11-1011"
].iloc[0]

print("Calculated matched task count:", calculated_count)
print("Reported matched task count:", reported["matched_task_count"])

print("Calculated average:", round(calculated_average, 6))
print("Reported average:", round(reported["average_task_penetration"], 6))

print(
    "Count matches:",
    calculated_count == reported["matched_task_count"]
)

print(
    "Average matches:",
    abs(
        calculated_average - reported["average_task_penetration"]
    ) < 0.000001
)

print("\nFULL OCCUPATION CALCULATION VALIDATION")

# Recalculate averages across ALL occupations
all_matched = onet.merge(
    penetration[["task_normalized", "penetration"]],
    on="task_normalized",
    how="inner",
    validate="many_to_one"
)

recalculated = (
    all_matched.groupby("soc_code")
    .agg(
        calculated_average=("penetration", "mean"),
        calculated_count=("penetration", "count")
    )
    .reset_index()
)

# Compare against the team's occupation output
comparison = occupations.merge(
    recalculated,
    on="soc_code",
    how="left",
    validate="one_to_one"
)

# Compare values
comparison["count_matches"] = (
    comparison["matched_task_count"]
    == comparison["calculated_count"]
)

comparison["average_matches"] = (
    (
        comparison["average_task_penetration"]
        - comparison["calculated_average"]
    ).abs() < 0.000001
)

print("Occupations checked:", len(comparison))

print(
    "Occupations with recalculated tasks:",
    comparison["calculated_count"].notna().sum()
)

print(
    "Task count mismatches:",
    (~comparison["count_matches"]).sum()
)

print(
    "Average mismatches:",
    (~comparison["average_matches"]).sum()
)

print("\nExample mismatches:")
print(
    comparison.loc[
        ~comparison["count_matches"]
        | ~comparison["average_matches"],
        [
            "soc_code",
            "matched_task_count",
            "calculated_count",
            "average_task_penetration",
            "calculated_average"
        ]
    ].head(10).to_string(index=False)
)

print("\nMISMATCHED OCCUPATION INVESTIGATION")

problem_codes = [
    "15-1299",
    "19-3039",
    "19-4051",
    "27-3043",
    "29-1129"
]

for soc in problem_codes:
    subset = onet[onet["soc_code"] == soc]

    print(f"\nSOC: {soc}")

    print("Original O*NET-SOC codes:")
    print(
        subset["O*NET-SOC Code"]
        .value_counts()
        .to_string()
    )

    print("Total O*NET task records:", len(subset))

    print(
        "Unique normalized task descriptions:",
        subset["task_normalized"].nunique()
    )

print("\nFINAL OCCUPATION CALCULATION VERIFICATION")

# Remove repeated task descriptions within each occupation
all_matched_unique = all_matched.drop_duplicates(
    subset=["soc_code", "task_normalized"]
)

# Recalculate occupation-level statistics
recalculated_unique = (
    all_matched_unique.groupby("soc_code")
    .agg(
        calculated_average=("penetration", "mean"),
        calculated_count=("penetration", "count")
    )
    .reset_index()
)

# Compare against the team's output
final_comparison = occupations.merge(
    recalculated_unique,
    on="soc_code",
    how="left",
    validate="one_to_one"
)

count_matches = (
    final_comparison["matched_task_count"]
    == final_comparison["calculated_count"]
)

average_matches = (
    (
        final_comparison["average_task_penetration"]
        - final_comparison["calculated_average"]
    ).abs() < 0.000001
)

print("Occupations checked:", len(final_comparison))

print("Task count mismatches:", (~count_matches).sum())
print("Average mismatches:", (~average_matches).sum())

print(
    "All calculations verified:",
    count_matches.all() and average_matches.all()
)

print("\nRECORD-LEVEL VERIFICATION CANDIDATES")

# 1. Original vs normalized task description
task_example = pd.read_csv("data/task_penetration.csv").iloc[0]

print("\nCHECK 1: TASK NORMALIZATION")
print("Original:", task_example["task"])
print(
    "Expected:",
    " ".join(task_example["task"].lower().split())
)

# 2. Original vs normalized SOC code
onet_example = pd.read_csv(
    "data/onet_occupation_data.csv"
).iloc[0]

print("\nCHECK 2: SOC NORMALIZATION")
print("Original:", onet_example["O*NET-SOC Code"])
print(
    "Expected:",
    onet_example["O*NET-SOC Code"][:7]
)

# 3. Duplicate task removal
print("\nCHECK 3: DUPLICATE TASK REMOVAL")
print("Original task records:", 17998)
print("Expected cleaned task records:", 17991)
print("Actual cleaned task records:", len(tasks_clean))

# 4. Unmatched occupation
print("\nCHECK 4: UNMATCHED OCCUPATION")
print("Original SOC:", "11-1031")
print("Expected matched dataset inclusion:", False)
print(
    "Actual matched dataset inclusion:",
    "11-1031" in occupations["soc_code"].values
)

# 5. Occupation-level calculation
chief = occupations.loc[
    occupations["soc_code"] == "11-1011"
].iloc[0]

print("\nCHECK 5: CHIEF EXECUTIVES")
print("Original occupation:", "11-1011")
print("Expected matched task count:", 49)
print("Actual matched task count:", chief["matched_task_count"])
print("Expected average penetration:", 0.032945)
print(
    "Actual average penetration:",
    round(chief["average_task_penetration"], 6)
)

print("\nFINAL RECORD-LEVEL VERIFICATION")

# CHECK 1: Task normalization
raw_tasks = pd.read_csv("data/task_penetration.csv")

original_task = raw_tasks.loc[0, "task"]
expected_task = " ".join(original_task.lower().split())
actual_task = tasks_clean.loc[
    tasks_clean["task"] == original_task,
    "task_normalized"
].iloc[0]

print("\nCHECK 1: TASK NORMALIZATION")
print("Original:", original_task)
print("Expected:", expected_task)
print("Actual:", actual_task)
print("Passed:", expected_task == actual_task)


# CHECK 2: SOC normalization
raw_onet = pd.read_csv("data/onet_occupation_data.csv")

original_soc = raw_onet.loc[0, "O*NET-SOC Code"]
expected_soc = "11-1011"

actual_soc = (
    pd.Series([original_soc])
    .str.extract(r"(\d{2}-\d{4})", expand=False)
    .iloc[0]
)

print("\nCHECK 2: SOC NORMALIZATION")
print("Original:", original_soc)
print("Expected:", expected_soc)
print("Actual:", actual_soc)
print("Passed:", expected_soc == actual_soc)


# CHECK 3: A specific repeated task
raw_tasks["task_normalized"] = (
    raw_tasks["task"]
    .astype("string")
    .str.lower()
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

repeated = raw_tasks.loc[
    raw_tasks.duplicated("task_normalized", keep=False)
]

example_task = repeated["task_normalized"].iloc[0]

original_count = (
    raw_tasks["task_normalized"] == example_task
).sum()

actual_count = (
    tasks_clean["task_normalized"] == example_task
).sum()

print("\nCHECK 3: DUPLICATE TASK")
print("Original task:", example_task)
print("Original occurrences:", original_count)
print("Expected occurrences:", 1)
print("Actual occurrences:", actual_count)
print("Passed:", actual_count == 1)


# CHECK 4: Legislators excluded from matched output
print("\nCHECK 4: UNMATCHED OCCUPATION")
print("Original SOC:", "11-1031")
print("Expected inclusion:", False)

actual_inclusion = (
    occupations["soc_code"] == "11-1031"
).any()

print("Actual inclusion:", actual_inclusion)
print("Passed:", actual_inclusion == False)


# CHECK 5: Chief Executives calculation
chief = occupations.loc[
    occupations["soc_code"] == "11-1011"
].iloc[0]

print("\nCHECK 5: CHIEF EXECUTIVES")
print("Original SOC:", "11-1011")
print("Expected task count:", 49)
print("Actual task count:", chief["matched_task_count"])
print("Expected average:", 0.032945)
print(
    "Actual average:",
    round(chief["average_task_penetration"], 6)
)

print(
    "Passed:",
    chief["matched_task_count"] == 49
    and abs(
        chief["average_task_penetration"] - 0.032945
    ) < 0.000001
)