"""Reproducible cleaning and verification for the Module 6 assignment.

Run from the repository root with:
    python code/clean_data.py

The five source CSV files in data/ are read-only inputs. All generated files
are written to outputs/ or cleaning_submission/.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"
SUBMISSION = ROOT / "cleaning_submission"

FILES = {
    "jobs": "job_exposure.csv",
    "penetration": "task_penetration.csv",
    "onet_tasks": "onet_task_statements.csv",
    "onet_occupations": "onet_occupation_data.csv",
    "bls": "bls_table_1_2_2025_35.csv",
}

BLS_CODE = "2025 National Employment Matrix code"
BLS_TITLE = "2025 National Employment Matrix title"
BLS_EMPLOYMENT = "Employment, 2025"
BLS_OUTLOOK = "Employment change, percent, 2025–35"
BLS_OPENINGS = "Occupational openings, 2025–35 annual average"
BLS_WAGE = "Median annual wage, dollars, 2025"
BLS_EDUCATION = "Typical education needed for entry"
BLS_EXPERIENCE = "Work experience in a related occupation"
BLS_TRAINING = (
    "Typical on-the-job training needed to attain competency in the occupation"
)


def normalize_soc(values: pd.Series) -> pd.Series:
    """Extract a six-digit SOC code while preserving its hyphen and leading zero."""
    return values.astype("string").str.extract(r"(\d{2}-\d{4})", expand=False)


def clean_text(values: pd.Series, *, lowercase: bool = False) -> pd.Series:
    """Trim ends and collapse whitespace without changing meaningful punctuation."""
    result = values.astype("string").str.replace(r"\s+", " ", regex=True).str.strip()
    return result.str.lower() if lowercase else result


def to_number(values: pd.Series) -> tuple[pd.Series, int]:
    """Convert display numbers; report nonblank values that could not be parsed."""
    source = values.astype("string")
    cleaned = source.str.replace(",", "", regex=False).replace({"—": pd.NA, "-": pd.NA})
    result = pd.to_numeric(cleaned, errors="coerce")
    failed = int(source.notna().sum() - result.notna().sum() - source.isin(["—", "-"]).sum())
    return result, max(failed, 0)


def load_sources() -> dict[str, pd.DataFrame]:
    missing = [filename for filename in FILES.values() if not (DATA / filename).exists()]
    if missing:
        raise FileNotFoundError(f"Missing source files in {DATA}: {missing}")
    return {
        name: pd.read_csv(DATA / filename, low_memory=False)
        for name, filename in FILES.items()
    }


def require_columns(frame: pd.DataFrame, columns: list[str], name: str) -> None:
    missing = [column for column in columns if column not in frame]
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def build_clean_data(raw: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    jobs = raw["jobs"].copy()
    penetration = raw["penetration"].copy()
    onet_tasks = raw["onet_tasks"].copy()
    onet_occupations = raw["onet_occupations"].copy()
    bls = raw["bls"].copy()

    require_columns(jobs, ["occ_code", "title", "observed_exposure"], FILES["jobs"])
    require_columns(penetration, ["task", "penetration"], FILES["penetration"])
    require_columns(
        onet_tasks, ["O*NET-SOC Code", "Task ID", "Task"], FILES["onet_tasks"]
    )
    require_columns(
        onet_occupations,
        ["O*NET-SOC Code", "Title", "Description"],
        FILES["onet_occupations"],
    )
    require_columns(
        bls,
        [
            BLS_CODE,
            BLS_TITLE,
            "Occupation type",
            BLS_EMPLOYMENT,
            BLS_OUTLOOK,
            BLS_OPENINGS,
            BLS_WAGE,
            BLS_EDUCATION,
            BLS_EXPERIENCE,
            BLS_TRAINING,
        ],
        FILES["bls"],
    )

    source_counts = {FILES[name]: len(frame) for name, frame in raw.items()}
    source_missing = {
        FILES[name]: {column: int(count) for column, count in frame.isna().sum().items() if count}
        for name, frame in raw.items()
    }
    exact_duplicates = {
        FILES[name]: int(frame.duplicated().sum()) for name, frame in raw.items()
    }

    jobs["soc_code"] = normalize_soc(jobs["occ_code"])
    jobs["title"] = clean_text(jobs["title"])
    jobs["observed_exposure"] = pd.to_numeric(jobs["observed_exposure"], errors="coerce")

    penetration["task_clean"] = clean_text(penetration["task"])
    penetration["task_key"] = clean_text(penetration["task"], lowercase=True)
    penetration["penetration"] = pd.to_numeric(penetration["penetration"], errors="coerce")
    penetration_before = len(penetration)
    penetration = penetration.drop_duplicates(["task_clean", "penetration"]).copy()
    penetration_removed = penetration_before - len(penetration)
    # Case differences do not represent different tasks for an exact-text join.
    penetration_for_join = (
        penetration.sort_values("task_clean").drop_duplicates("task_key").copy()
    )

    onet_tasks["soc_code"] = normalize_soc(onet_tasks["O*NET-SOC Code"])
    onet_tasks["task_clean"] = clean_text(onet_tasks["Task"])
    onet_tasks["task_key"] = clean_text(onet_tasks["Task"], lowercase=True)

    onet_occupations["soc_code"] = normalize_soc(onet_occupations["O*NET-SOC Code"])
    onet_occupations["title_clean"] = clean_text(onet_occupations["Title"])
    onet_occupations["description_clean"] = clean_text(onet_occupations["Description"])
    onet_occupations["base_record"] = onet_occupations["O*NET-SOC Code"].astype(
        "string"
    ).str.endswith(".00")
    descriptions = (
        onet_occupations.sort_values("base_record", ascending=False)
        .drop_duplicates("soc_code")
        [["soc_code", "description_clean"]]
        .rename(columns={"description_clean": "occupation_description"})
    )

    bls_title_changes = int((bls[BLS_TITLE].astype("string") != clean_text(bls[BLS_TITLE])).sum())
    bls[BLS_TITLE] = clean_text(bls[BLS_TITLE])
    bls["soc_code"] = normalize_soc(bls[BLS_CODE])
    bls_line_items = bls.loc[bls["Occupation type"].eq("Line item")].copy()

    numeric_map = {
        BLS_EMPLOYMENT: "employment_2025_thousands",
        BLS_OUTLOOK: "employment_change_percent_2025_35",
        BLS_OPENINGS: "annual_openings_2025_35_thousands",
        BLS_WAGE: "median_annual_wage_2025",
    }
    failed_conversions: dict[str, int] = {}
    for source, target in numeric_map.items():
        bls_line_items[target], failed_conversions[source] = to_number(bls_line_items[source])

    categorical_map = {
        BLS_EDUCATION: "typical_education",
        BLS_EXPERIENCE: "related_work_experience",
        BLS_TRAINING: "on_the_job_training",
    }
    for source, target in categorical_map.items():
        bls_line_items[target] = clean_text(bls_line_items[source]).replace("—", pd.NA)

    bls_selected = bls_line_items[
        ["soc_code", BLS_TITLE, *numeric_map.values(), *categorical_map.values()]
    ].rename(columns={BLS_TITLE: "bls_title"})

    task_matches = onet_tasks.merge(
        penetration_for_join[["task_key", "penetration"]], on="task_key", how="inner"
    )
    repeated_base_soc_tasks = int(task_matches.duplicated(["soc_code", "task_key"]).sum())
    task_matches = (
        task_matches.sort_values("penetration", ascending=False)
        .drop_duplicates(["soc_code", "task_key"])
        .copy()
    )
    task_summary = task_matches.groupby("soc_code", as_index=False).agg(
        average_task_penetration=("penetration", "mean"),
        matched_task_count=("task_key", "nunique"),
    )
    top_tasks = (
        task_matches.sort_values(["soc_code", "penetration"], ascending=[True, False])
        .assign(task_rank=lambda frame: frame.groupby("soc_code").cumcount() + 1)
        .loc[lambda frame: frame["task_rank"] <= 5,
             ["soc_code", "task_rank", "task_clean", "penetration"]]
        .rename(columns={"task_clean": "task"})
    )

    occupation = (
        jobs[["soc_code", "title", "observed_exposure"]]
        .merge(bls_selected, on="soc_code", how="inner", validate="one_to_one")
        .merge(descriptions, on="soc_code", how="left", validate="one_to_one")
        .merge(task_summary, on="soc_code", how="left", validate="one_to_one")
        .sort_values("soc_code")
        .reset_index(drop=True)
    )
    top_tasks = top_tasks.loc[top_tasks["soc_code"].isin(set(occupation["soc_code"]))].copy()

    job_soc = set(jobs["soc_code"].dropna())
    bls_soc = set(bls_line_items["soc_code"].dropna())
    unmatched_jobs = (
        jobs.loc[~jobs["soc_code"].isin(bls_soc), ["soc_code", "title"]]
        .to_dict("records")
    )
    matched_penetration_rows = int(
        raw["penetration"]["task"].pipe(clean_text, lowercase=True).isin(set(onet_tasks["task_key"])).sum()
    )

    range_checks = {
        "observed_exposure_outside_0_1": int(
            (~jobs["observed_exposure"].between(0, 1, inclusive="both")).sum()
        ),
        "penetration_outside_0_1": int(
            (~penetration["penetration"].between(0, 1, inclusive="both")).sum()
        ),
        "invalid_job_soc_codes": int(jobs["soc_code"].isna().sum()),
        "invalid_bls_line_item_soc_codes": int(bls_line_items["soc_code"].isna().sum()),
    }

    audit = {
        "source_counts": source_counts,
        "source_missing": source_missing,
        "exact_duplicates": exact_duplicates,
        "cleaning_changes": {
            "task_penetration_exact_duplicate_rows_removed": penetration_removed,
            "bls_summary_rows_excluded": int(len(bls) - len(bls_line_items)),
            "bls_titles_whitespace_standardized": bls_title_changes,
            "repeated_base_soc_task_matches_removed": repeated_base_soc_tasks,
            "failed_numeric_conversions_excluding_documented_em_dash_missing": failed_conversions,
        },
        "range_checks": range_checks,
        "merge": {
            "anthropic_occupation_rows": len(jobs),
            "bls_line_item_rows": len(bls_line_items),
            "matched_occupation_rows": len(occupation),
            "unmatched_anthropic_occupations": unmatched_jobs,
            "anthropic_task_rows_matched_to_onet": matched_penetration_rows,
            "anthropic_task_rows_total": len(raw["penetration"]),
            "top_task_rows": len(top_tasks),
        },
        "output_missing": {
            column: int(count)
            for column, count in occupation.isna().sum().items()
            if count
        },
    }
    return occupation, top_tasks, audit


def build_sample(occupation: pd.DataFrame) -> pd.DataFrame:
    """Choose 50 auditable rows: boundary, missing, unmatched-task, and spread cases."""
    picks: list[int] = []
    for column in [
        "observed_exposure",
        "employment_change_percent_2025_35",
        "median_annual_wage_2025",
    ]:
        picks.extend(occupation[column].nsmallest(5).index.tolist())
        picks.extend(occupation[column].nlargest(5).index.tolist())
    picks.extend(occupation[occupation.isna().any(axis=1)].index[:10].tolist())
    # Fill remaining places using deterministic evenly spaced rows.
    picks = list(dict.fromkeys(picks))
    for index in occupation.iloc[:: max(len(occupation) // 50, 1)].index:
        if index not in picks:
            picks.append(index)
        if len(picks) == 50:
            break
    return occupation.loc[picks[:50]].sort_values("soc_code").reset_index(drop=True)


def verify_records(
    raw: dict[str, pd.DataFrame], occupation: pd.DataFrame, top_tasks: pd.DataFrame, audit: dict
) -> list[dict]:
    """Check five identifiable source records against documented expectations."""
    bls = raw["bls"]
    onet_occ = raw["onet_occupations"].loc[
        raw["onet_occupations"]["O*NET-SOC Code"].eq("11-1011.00")
    ].iloc[0]
    bls_chief = bls.loc[bls[BLS_CODE].eq("11-1011")].iloc[0]
    bls_actor = bls.loc[bls[BLS_CODE].eq("27-2011")].iloc[0]
    onet_task = raw["onet_tasks"].loc[raw["onet_tasks"]["Task ID"].eq(8825)].iloc[0]
    task_key = clean_text(pd.Series([onet_task["Task"]]), lowercase=True).iloc[0]
    penetration_row = raw["penetration"].loc[
        clean_text(raw["penetration"]["task"], lowercase=True).eq(task_key)
    ].iloc[0]
    unmatched_job = raw["jobs"].loc[raw["jobs"]["occ_code"].eq("11-1031")].iloc[0]

    chief_output = occupation.loc[occupation["soc_code"].eq("11-1011")].iloc[0]
    actor_output = occupation.loc[occupation["soc_code"].eq("27-2011")].iloc[0]
    task_output = top_tasks.loc[
        top_tasks["soc_code"].eq("11-1011")
        & clean_text(top_tasks["task"], lowercase=True).eq(task_key)
    ].iloc[0]
    unmatched_logged = any(
        row["soc_code"] == "11-1031" for row in audit["merge"]["unmatched_anthropic_occupations"]
    )

    checks = [
        {
            "case": "O*NET occupation mapped to six-digit SOC",
            "source_file": "onet_occupation_data.csv",
            "record_id": "O*NET-SOC Code=11-1011.00",
            "original_value": f"O*NET-SOC Code={onet_occ['O*NET-SOC Code']}; Title={onet_occ['Title']}",
            "expected_result": "soc_code=11-1011; title=Chief Executives",
            "reason": "Remove only the O*NET detail suffix so the record can join on six-digit SOC.",
            "actual_result": f"soc_code={chief_output['soc_code']}; title={chief_output['title']}",
        },
        {
            "case": "BLS title whitespace",
            "source_file": "bls_table_1_2_2025_35.csv",
            "record_id": "2025 National Employment Matrix code=11-1011",
            "original_value": f"title={str(bls_chief[BLS_TITLE])!r}",
            "expected_result": f"bls_title={' '.join(str(bls_chief[BLS_TITLE]).split())}",
            "reason": "Leading spaces are table indentation, not meaningful title text.",
            "actual_result": f"bls_title={chief_output['bls_title']}",
        },
        {
            "case": "BLS unavailable wage retained as missing",
            "source_file": "bls_table_1_2_2025_35.csv",
            "record_id": "2025 National Employment Matrix code=27-2011",
            "original_value": f"title={str(bls_actor[BLS_TITLE]).strip()}; median wage={bls_actor[BLS_WAGE]}",
            "expected_result": "missing (NaN)",
            "reason": "An em dash means unavailable; it must not be converted to zero or imputed.",
            "actual_result": (
                "missing (NaN)" if pd.isna(actor_output["median_annual_wage_2025"])
                else str(actor_output["median_annual_wage_2025"])
            ),
        },
        {
            "case": "Specific O*NET task joined to task penetration",
            "source_file": "onet_task_statements.csv + task_penetration.csv",
            "record_id": "Task ID=8825",
            "original_value": (
                f"O*NET-SOC Code={onet_task['O*NET-SOC Code']}; task={onet_task['Task']}; "
                f"penetration={float(penetration_row['penetration']):.3f}"
            ),
            "expected_result": (
                f"soc_code=11-1011; task_rank=1; penetration={float(penetration_row['penetration']):.3f}"
            ),
            "reason": "Normalized exact task text should connect this task to its observed penetration and base SOC.",
            "actual_result": (
                f"soc_code={task_output['soc_code']}; task_rank={int(task_output['task_rank'])}; "
                f"penetration={float(task_output['penetration']):.3f}"
            ),
        },
        {
            "case": "Unmatched occupation",
            "source_file": "job_exposure.csv",
            "record_id": "occ_code=11-1031",
            "original_value": (
                f"title={unmatched_job['title']}; observed_exposure={float(unmatched_job['observed_exposure']):.1f}"
            ),
            "expected_result": "absent from cleaned_occupations.csv; logged unmatched",
            "reason": (
                "This analysis is limited to occupations successfully matched to BLS. "
                "Keep the record in the unmatched log rather than deleting it merely for missing values."
            ),
            "actual_result": (
                "absent from cleaned_occupations.csv; logged unmatched"
                if "11-1031" not in set(occupation["soc_code"]) and unmatched_logged
                else "unexpected result"
            ),
        },
    ]
    for check in checks:
        check["passed"] = check["actual_result"] == check["expected_result"]
    if not all(check["passed"] for check in checks):
        raise AssertionError(f"Record verification failed: {checks}")
    return checks


def write_evidence(audit: dict, checks: list[dict]) -> None:
    (OUTPUTS / "cleaning_audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    check_frame = pd.DataFrame(checks)
    check_frame.to_csv(OUTPUTS / "five_record_checks.csv", index=False)


def main() -> None:
    OUTPUTS.mkdir(exist_ok=True)
    SUBMISSION.mkdir(exist_ok=True)
    raw = load_sources()
    occupation, top_tasks, audit = build_clean_data(raw)
    checks = verify_records(raw, occupation, top_tasks, audit)
    sample = build_sample(occupation)

    occupation.to_csv(OUTPUTS / "cleaned_occupations.csv", index=False)
    top_tasks.to_csv(OUTPUTS / "cleaned_top_tasks.csv", index=False)
    sample.to_csv(SUBMISSION / "sample_cleaned_occupations.csv", index=False)
    write_evidence(audit, checks)

    print(json.dumps(audit, indent=2, ensure_ascii=False))
    print(f"\nWrote {len(occupation)} cleaned occupations and a {len(sample)}-row sample.")


if __name__ == "__main__":
    main()
