"""Clean the project source tables and write reproducible validation evidence.

Raw files under data/raw/ are never overwritten. The script creates cleaned
tables under outputs/ and a small review sample under data/sample/.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "outputs"
SAMPLE_DIR = ROOT / "data" / "sample"


def normalize_text(series: pd.Series) -> pd.Series:
    """Trim surrounding whitespace and collapse repeated whitespace."""
    return series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)


def add_soc_key(frame: pd.DataFrame, source_column: str, key_name: str) -> tuple[pd.DataFrame, int]:
    """Add a six-digit SOC key while preserving the source identifier."""
    result = frame.copy()
    result[source_column] = normalize_text(result[source_column])
    result[key_name] = result[source_column].str.extract(r"^(\d{2}-\d{4})", expand=False)
    invalid = int(result[key_name].isna().sum())
    return result, invalid


def convert_numeric(
    frame: pd.DataFrame,
    column: str,
    conversion_report: list[dict],
) -> None:
    """Convert formatted numeric text and record failed conversions."""
    original = frame[column]
    cleaned = (
        original.astype("string")
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip()
        .replace({"": pd.NA, "--": pd.NA, "—": pd.NA, "N/A": pd.NA})
    )
    converted = pd.to_numeric(cleaned, errors="coerce")
    failed = int((cleaned.notna() & converted.isna()).sum())
    conversion_report.append(
        {
            "column": column,
            "nonmissing_before": int(cleaned.notna().sum()),
            "nonmissing_after": int(converted.notna().sum()),
            "failed_conversions": failed,
        }
    )
    frame[column] = converted


def table_report(name: str, before: pd.DataFrame, after: pd.DataFrame) -> dict:
    return {
        "table": name,
        "rows_before": len(before),
        "rows_after": len(after),
        "row_change": len(after) - len(before),
        "columns_after": len(after.columns),
        "exact_duplicates_before": int(before.duplicated().sum()),
        "exact_duplicates_after": int(after.duplicated().sum()),
    }


def missing_report(name: str, frame: pd.DataFrame) -> list[dict]:
    return [
        {
            "table": name,
            "column": column,
            "missing_count": int(frame[column].isna().sum()),
            "missing_percent": round(float(frame[column].isna().mean() * 100), 3),
        }
        for column in frame.columns
        if frame[column].isna().any()
    ]


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    SAMPLE_DIR.mkdir(exist_ok=True)

    conversion_report: list[dict] = []
    table_reports: list[dict] = []
    missing_reports: list[dict] = []
    duplicate_reports: list[dict] = []
    merge_reports: list[dict] = []
    key_reports: list[dict] = []
    metric_rows: list[dict] = []

    # Occupation-level exposure data.
    exposure_raw = pd.read_csv(RAW_DIR / "job_exposure.csv")
    exposure = exposure_raw.copy()
    exposure["title"] = normalize_text(exposure["title"])
    exposure, invalid = add_soc_key(exposure, "occ_code", "soc6")
    key_reports.append({"table": "job_exposure", "key": "soc6", "invalid_count": invalid})
    exposure.to_csv(OUTPUT_DIR / "job_exposure_clean.csv", index=False)
    table_reports.append(table_report("job_exposure", exposure_raw, exposure))
    missing_reports.extend(missing_report("job_exposure", exposure))

    # Task-level penetration data.
    penetration_raw = pd.read_csv(RAW_DIR / "task_penetration.csv")
    penetration = penetration_raw.copy()
    penetration["task_original"] = penetration["task"]
    penetration["task"] = normalize_text(penetration["task"])
    penetration["task_normalized"] = penetration["task"].str.casefold()
    convert_numeric(penetration, "penetration", conversion_report)
    normalized_duplicates = int(penetration.duplicated(["task_normalized", "penetration"]).sum())
    conflicting_groups = (
        penetration.groupby("task_normalized", dropna=False)["penetration"].nunique(dropna=False) > 1
    )
    conflicting_task_count = int(conflicting_groups.sum())
    penetration = penetration.drop_duplicates(["task_normalized", "penetration"], keep="first")
    duplicate_reports.append(
        {
            "table": "task_penetration",
            "duplicate_type": "normalized_task_and_penetration",
            "count": normalized_duplicates,
            "conflicting_task_groups": conflicting_task_count,
        }
    )
    penetration.to_csv(OUTPUT_DIR / "task_penetration_clean.csv", index=False)
    table_reports.append(table_report("task_penetration", penetration_raw, penetration))
    missing_reports.extend(missing_report("task_penetration", penetration))

    # O*NET occupation data: retain the full code and add the six-digit key.
    onet_occ_raw = pd.read_csv(RAW_DIR / "onet_occupation_data.csv")
    onet_occ = onet_occ_raw.copy()
    onet_occ["Title"] = normalize_text(onet_occ["Title"])
    onet_occ, invalid = add_soc_key(onet_occ, "O*NET-SOC Code", "soc6")
    key_reports.append({"table": "onet_occupation_data", "key": "O*NET-SOC Code", "invalid_count": invalid})
    onet_occ.to_csv(OUTPUT_DIR / "onet_occupation_clean.csv", index=False)
    table_reports.append(table_report("onet_occupation_data", onet_occ_raw, onet_occ))
    missing_reports.extend(missing_report("onet_occupation_data", onet_occ))

    # O*NET task statements: Task ID is the record key; occupation codes repeat.
    tasks_raw = pd.read_csv(RAW_DIR / "onet_task_statements.csv")
    tasks = tasks_raw.copy()
    tasks["Title"] = normalize_text(tasks["Title"])
    tasks["Task"] = normalize_text(tasks["Task"])
    tasks["task_normalized"] = tasks["Task"].str.casefold()
    tasks, invalid = add_soc_key(tasks, "O*NET-SOC Code", "soc6")
    key_reports.append({"table": "onet_task_statements", "key": "Task ID", "invalid_count": int(tasks["Task ID"].isna().sum())})
    convert_numeric(tasks, "Incumbents Responding", conversion_report)
    tasks.to_csv(OUTPUT_DIR / "onet_task_statements_clean.csv", index=False)
    table_reports.append(table_report("onet_task_statements", tasks_raw, tasks))
    missing_reports.extend(missing_report("onet_task_statements", tasks))

    # BLS CSV extract: preserve summary rows, but use line items for occupation joins.
    bls_raw = pd.read_csv(RAW_DIR / "bls_table_1_2_2025_35.csv")
    bls = bls_raw.copy()
    title_column = "2025 National Employment Matrix title"
    code_column = "2025 National Employment Matrix code"
    bls[title_column] = normalize_text(bls[title_column])
    bls, invalid = add_soc_key(bls, code_column, "soc6")
    key_reports.append({"table": "bls_table_1_2", "key": code_column, "invalid_count": invalid})
    bls_numeric_columns = [
        "Employment, 2025",
        "Employment, 2035",
        "Employment distribution, percent, 2025",
        "Employment distribution, percent, 2035",
        "Employment change, numeric, 2025–35",
        "Employment change, percent, 2025–35",
        "Occupational openings, 2025–35 annual average",
        "Median annual wage, dollars, 2025",
    ]
    for column in bls_numeric_columns:
        convert_numeric(bls, column, conversion_report)
    bls.to_csv(OUTPUT_DIR / "bls_table_1_2_clean.csv", index=False)
    table_reports.append(table_report("bls_table_1_2", bls_raw, bls))
    missing_reports.extend(missing_report("bls_table_1_2", bls))

    bls_line = bls[bls["Occupation type"].eq("Line item")].copy()
    exposure_merge = exposure.merge(
        bls_line,
        on="soc6",
        how="left",
        indicator=True,
        validate="one_to_one",
        suffixes=("_exposure", "_bls"),
    )
    merge_counts = exposure_merge["_merge"].value_counts().to_dict()
    merge_reports.append(
        {
            "merge": "job_exposure to BLS line items",
            "left_rows": len(exposure),
            "right_rows": len(bls_line),
            "output_rows": len(exposure_merge),
            "matched": int(merge_counts.get("both", 0)),
            "left_only": int(merge_counts.get("left_only", 0)),
            "right_only": int(merge_counts.get("right_only", 0)),
        }
    )
    exposure_merge.loc[exposure_merge["_merge"].eq("left_only")].drop(columns="_merge").to_csv(
        OUTPUT_DIR / "unmatched_exposure_records.csv", index=False
    )
    exposure_merge.drop(columns="_merge").to_csv(OUTPUT_DIR / "occupation_clean.csv", index=False)
    SAMPLE_DIR.mkdir(exist_ok=True)
    exposure_merge.drop(columns="_merge").head(50).to_csv(SAMPLE_DIR / "occupation_clean_sample.csv", index=False)

    def add_metric(table: str, metric: str, series: pd.Series, statistic: str, unit: str, missing_rule: str) -> None:
        valid = series.dropna()
        if statistic == "sum":
            value = valid.sum()
        elif statistic == "mean":
            value = valid.mean()
        else:
            raise ValueError(f"Unsupported statistic: {statistic}")
        metric_rows.append(
            {
                "table": table,
                "metric": metric,
                "statistic": statistic,
                "unit": unit,
                "rows_total": len(series),
                "nonmissing_count": len(valid),
                "missing_count": int(series.isna().sum()),
                "denominator": len(valid),
                "value": value,
                "missing_value_rule": missing_rule,
            }
        )

    matched_occupations = exposure_merge.loc[exposure_merge["_merge"].eq("both")]
    add_metric(
        "job_exposure", "mean observed exposure", exposure["observed_exposure"], "mean",
        "exposure proportion", "Exclude missing exposure values; none are missing.",
    )
    add_metric(
        "task_penetration", "mean task penetration", penetration["penetration"], "mean",
        "penetration proportion", "Exclude missing penetration values; none are missing.",
    )
    add_metric(
        "matched occupation merge", "total employment 2025", matched_occupations["Employment, 2025"], "sum",
        "thousands of workers", "Use matched occupations with nonmissing BLS employment; unmatched occupations are reported separately.",
    )
    add_metric(
        "matched occupation merge", "total employment 2035", matched_occupations["Employment, 2035"], "sum",
        "thousands of workers", "Use matched occupations with nonmissing BLS employment; unmatched occupations are reported separately.",
    )
    add_metric(
        "matched occupation merge", "mean employment change percent", matched_occupations["Employment change, percent, 2025–35"], "mean",
        "percent", "Exclude missing projected-change values and report the denominator.",
    )
    add_metric(
        "matched occupation merge", "mean median annual wage", matched_occupations["Median annual wage, dollars, 2025"], "mean",
        "dollars", "Do not treat missing wages as zero; average only nonmissing wages.",
    )
    pd.DataFrame(metric_rows).to_csv(OUTPUT_DIR / "metric_validation.csv", index=False)

    # Five reproducible record checks for the assignment evidence.
    record_checks: list[dict] = []

    unmatched_row = exposure.loc[exposure["soc6"].eq("11-1031")].iloc[0]
    unmatched_actual = int(exposure_merge.loc[exposure_merge["soc6"].eq("11-1031"), "_merge"].eq("both").sum())
    record_checks.append(
        {
            "check_id": "R1",
            "case": "unmatched occupation",
            "original": f'{unmatched_row["occ_code"]} | {unmatched_row["title"]}',
            "expected": "No BLS line-item match; preserve and flag the exposure record",
            "actual": f"BLS matches = {unmatched_actual}",
            "matches_expected": unmatched_actual == 0,
        }
    )

    duplicate_task = penetration_raw.loc[penetration_raw.duplicated(keep=False), "task"].iloc[0]
    duplicate_key = normalize_text(pd.Series([duplicate_task])).str.casefold().iloc[0]
    retained_count = int((penetration["task_normalized"].eq(duplicate_key)).sum())
    record_checks.append(
        {
            "check_id": "R2",
            "case": "duplicate task penetration",
            "original": duplicate_task,
            "expected": "One row retained for the normalized task and penetration value",
            "actual": f"Retained rows = {retained_count}",
            "matches_expected": retained_count == 1,
        }
    )

    wage_row = bls_raw.loc[bls_raw["2025 National Employment Matrix code"].eq("27-2011")].iloc[0]
    wage_cleaned = bls.loc[bls["2025 National Employment Matrix code"].eq("27-2011"), "Median annual wage, dollars, 2025"].iloc[0]
    record_checks.append(
        {
            "check_id": "R3",
            "case": "missing BLS wage",
            "original": f'{wage_row["2025 National Employment Matrix code"]} | {wage_row["Median annual wage, dollars, 2025"]}',
            "expected": "Formatted missing marker becomes missing, not zero",
            "actual": "Missing" if pd.isna(wage_cleaned) else str(wage_cleaned),
            "matches_expected": bool(pd.isna(wage_cleaned)),
        }
    )

    missing_task_row = tasks_raw.loc[tasks_raw["Task Type"].isna()].iloc[0]
    cleaned_task_type = tasks.loc[tasks["Task ID"].eq(missing_task_row["Task ID"]), "Task Type"].iloc[0]
    record_checks.append(
        {
            "check_id": "R4",
            "case": "missing task type",
            "original": f'{missing_task_row["Task ID"]} | {missing_task_row["Task Type"]}',
            "expected": "Missing task type remains missing; do not infer a category",
            "actual": "Missing" if pd.isna(cleaned_task_type) else str(cleaned_task_type),
            "matches_expected": bool(pd.isna(cleaned_task_type)),
        }
    )

    normal_soc = "11-1011"
    normal_match = exposure_merge.loc[exposure_merge["soc6"].eq(normal_soc)]
    normal_wage = normal_match["Median annual wage, dollars, 2025"].iloc[0]
    record_checks.append(
        {
            "check_id": "R5",
            "case": "successful occupation merge",
            "original": "11-1011 | Chief Executives | exposure 0.0333",
            "expected": "One BLS line-item match with a numeric wage",
            "actual": f"Matches = {int(normal_match['_merge'].eq('both').sum())}; wage = {normal_wage}",
            "matches_expected": bool(normal_match["_merge"].eq("both").sum() == 1 and pd.notna(normal_wage)),
        }
    )
    pd.DataFrame(record_checks).to_csv(OUTPUT_DIR / "record_checks.csv", index=False)

    pd.DataFrame(table_reports).to_csv(OUTPUT_DIR / "cleaning_row_counts.csv", index=False)
    pd.DataFrame(missing_reports).to_csv(OUTPUT_DIR / "cleaning_missing_values.csv", index=False)
    pd.DataFrame(duplicate_reports).to_csv(OUTPUT_DIR / "cleaning_duplicates.csv", index=False)
    pd.DataFrame(conversion_report).to_csv(OUTPUT_DIR / "cleaning_conversions.csv", index=False)
    pd.DataFrame(merge_reports).to_csv(OUTPUT_DIR / "cleaning_merges.csv", index=False)
    pd.DataFrame(key_reports).to_csv(OUTPUT_DIR / "cleaning_keys.csv", index=False)

    print("Cleaning complete. Raw files were not modified.")
    print(pd.DataFrame(table_reports).to_string(index=False))
    print("\nMerge evidence:")
    print(pd.DataFrame(merge_reports).to_string(index=False))


if __name__ == "__main__":
    main()
