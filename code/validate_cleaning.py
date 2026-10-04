"""Independent validation for the Module 6 cleaning assignment.

This script snapshots source-file hashes, runs the cleaning pipeline twice,
and validates the generated files against rules derived from the source data.
It does not alter expected values based on whether a check passes.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"
SUBMISSION = ROOT / "cleaning_submission"

SOURCE_FILES = [
    "job_exposure.csv",
    "task_penetration.csv",
    "onet_task_statements.csv",
    "onet_occupation_data.csv",
    "bls_table_1_2_2025_35.csv",
]

BLS_CODE = "2025 National Employment Matrix code"
BLS_TITLE = "2025 National Employment Matrix title"
BLS_EMPLOYMENT = "Employment, 2025"
BLS_OUTLOOK = "Employment change, percent, 2025–35"
BLS_OPENINGS = "Occupational openings, 2025–35 annual average"
BLS_WAGE = "Median annual wage, dollars, 2025"
BLS_EXPERIENCE = "Work experience in a related occupation"
BLS_TRAINING = (
    "Typical on-the-job training needed to attain competency in the occupation"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def hashes(paths: list[Path]) -> dict[str, str]:
    return {path.name: sha256(path) for path in paths}


def semantic_missing(series: pd.Series) -> int:
    text = series.astype("string").str.strip()
    return int(series.isna().sum() + text.isin(["", "—", "-"]).sum())


def normalized_soc(series: pd.Series) -> pd.Series:
    return series.astype("string").str.extract(r"(\d{2}-\d{4})", expand=False)


def normalized_task(series: pd.Series) -> pd.Series:
    return series.astype("string").str.lower().str.replace(r"\s+", " ", regex=True).str.strip()


def add_check(checks: list[dict], name: str, expected, actual, evidence: str) -> None:
    if isinstance(expected, float) or isinstance(actual, float):
        passed = math.isclose(float(expected), float(actual), rel_tol=1e-12, abs_tol=1e-9)
    else:
        passed = expected == actual
    checks.append(
        {
            "check": name,
            "expected": expected,
            "actual": actual,
            "passed": bool(passed),
            "evidence": evidence,
        }
    )


def main() -> None:
    source_paths = [DATA / name for name in SOURCE_FILES]
    missing = [str(path) for path in source_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing source files: {missing}")

    source_hashes_before = hashes(source_paths)
    command = [sys.executable, str(ROOT / "code" / "clean_data.py")]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)

    generated_paths = [
        OUTPUTS / "cleaned_occupations.csv",
        OUTPUTS / "cleaned_top_tasks.csv",
        SUBMISSION / "sample_cleaned_occupations.csv",
    ]
    first_output_hashes = hashes(generated_paths)
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    second_output_hashes = hashes(generated_paths)
    source_hashes_after = hashes(source_paths)

    jobs = pd.read_csv(DATA / "job_exposure.csv", low_memory=False)
    penetration = pd.read_csv(DATA / "task_penetration.csv", low_memory=False)
    onet_tasks = pd.read_csv(DATA / "onet_task_statements.csv", low_memory=False)
    onet_occupations = pd.read_csv(DATA / "onet_occupation_data.csv", low_memory=False)
    bls = pd.read_csv(DATA / "bls_table_1_2_2025_35.csv", low_memory=False)
    occupation = pd.read_csv(OUTPUTS / "cleaned_occupations.csv", low_memory=False)
    top_tasks = pd.read_csv(OUTPUTS / "cleaned_top_tasks.csv", low_memory=False)
    sample = pd.read_csv(SUBMISSION / "sample_cleaned_occupations.csv", low_memory=False)

    bls_line = bls.loc[bls["Occupation type"].eq("Line item")].copy()
    bls_line["soc_code"] = normalized_soc(bls_line[BLS_CODE])
    job_soc = set(normalized_soc(jobs["occ_code"]).dropna())
    bls_soc = set(bls_line["soc_code"].dropna())
    matched_soc = job_soc & bls_soc

    checks: list[dict] = []
    add_check(checks, "source files unchanged after two runs", source_hashes_before, source_hashes_after,
              "SHA-256 hashes taken before and after both pipeline runs")
    add_check(checks, "two runs produce identical submitted outputs", first_output_hashes,
              second_output_hashes, "SHA-256 hashes of both full outputs and the 50-row sample")
    add_check(checks, "cleaned occupation row count", len(matched_soc), len(occupation),
              "Expected count is the intersection of source SOC keys")
    add_check(checks, "cleaned occupation key duplicates", 0,
              int(occupation["soc_code"].duplicated().sum()), "One row must represent one SOC")
    add_check(checks, "top-task composite-key duplicates", 0,
              int(top_tasks.duplicated(["soc_code", "task"]).sum()),
              "One row must represent one normalized task within an SOC")
    add_check(checks, "submitted sample maximum rows", True, len(sample) <= 50,
              "Assignment permits up to 50 cleaned rows")
    add_check(checks, "submitted sample row count", 50, len(sample),
              "The documented deterministic selection should fill all 50 permitted rows")
    add_check(checks, "submitted sample duplicate SOC keys", 0,
              int(sample["soc_code"].duplicated().sum()),
              "The sample should contain 50 different occupations")
    add_check(checks, "submitted sample keys come from full output", True,
              set(sample["soc_code"]).issubset(set(occupation["soc_code"])),
              "Every sample SOC must be traceable to the full cleaned output")
    for column in [
        "observed_exposure",
        "employment_change_percent_2025_35",
        "median_annual_wage_2025",
    ]:
        boundary_soc = set(occupation.nsmallest(5, column)["soc_code"]) | set(
            occupation.nlargest(5, column)["soc_code"]
        )
        add_check(checks, f"sample includes five low/high {column} cases", True,
                  boundary_soc.issubset(set(sample["soc_code"])),
                  "Confirms the documented difficult-case selection rule")

    expected_unmatched = sorted(job_soc - bls_soc)
    actual_unmatched = sorted(job_soc - set(occupation["soc_code"]))
    add_check(checks, "unmatched Anthropic SOC keys", expected_unmatched, actual_unmatched,
              "Calculated independently from source SOC sets")

    matched_bls = bls_line.loc[bls_line["soc_code"].isin(matched_soc)]
    expected_employment = float(matched_bls[BLS_EMPLOYMENT].sum())
    expected_openings = float(matched_bls[BLS_OPENINGS].sum())
    add_check(checks, "matched employment total preserved", expected_employment,
              float(occupation["employment_2025_thousands"].sum()),
              "A task join must not multiply occupation employment")
    add_check(checks, "matched annual-openings total preserved", expected_openings,
              float(occupation["annual_openings_2025_35_thousands"].sum()),
              "A task join must not multiply occupation openings")

    add_check(checks, "observed exposure within [0,1]", 0,
              int((~occupation["observed_exposure"].between(0, 1)).sum()),
              "Values outside the documented proportion range")
    add_check(checks, "task penetration within [0,1]", 0,
              int((~top_tasks["penetration"].between(0, 1)).sum()),
              "Values outside the documented proportion range")
    add_check(checks, "nonnegative employment", 0,
              int((occupation["employment_2025_thousands"] < 0).sum()),
              "Negative employment is impossible")
    add_check(checks, "nonnegative annual openings", 0,
              int((occupation["annual_openings_2025_35_thousands"] < 0).sum()),
              "Negative annual openings are impossible")
    add_check(checks, "positive nonmissing wages", 0,
              int((occupation["median_annual_wage_2025"].dropna() <= 0).sum()),
              "Nonpositive annual wage is suspicious")

    parsed_dates = pd.to_datetime(onet_tasks["Date"], format="%m/%Y", errors="coerce")
    add_check(checks, "invalid O*NET month/year dates", 0,
              int(parsed_dates.isna().sum() - onet_tasks["Date"].isna().sum()),
              "Strict parsing with format MM/YYYY")

    repeated_ids = {
        "job_exposure occ_code": int(jobs["occ_code"].duplicated().sum()),
        "O*NET Task ID": int(onet_tasks["Task ID"].duplicated().sum()),
        "O*NET occupation code": int(onet_occupations["O*NET-SOC Code"].duplicated().sum()),
        "BLS matrix code": int(bls[BLS_CODE].duplicated().sum()),
    }
    exact_duplicates = {
        "job_exposure.csv": int(jobs.duplicated().sum()),
        "task_penetration.csv": int(penetration.duplicated().sum()),
        "onet_task_statements.csv": int(onet_tasks.duplicated().sum()),
        "onet_occupation_data.csv": int(onet_occupations.duplicated().sum()),
        "bls_table_1_2_2025_35.csv": int(bls.duplicated().sum()),
    }

    missing_before = {
        "O*NET Task Type": semantic_missing(onet_tasks["Task Type"]),
        "O*NET Incumbents Responding": semantic_missing(onet_tasks["Incumbents Responding"]),
        "BLS median wage (line items)": semantic_missing(bls_line[BLS_WAGE]),
        "BLS related experience (line items)": semantic_missing(bls_line[BLS_EXPERIENCE]),
        "BLS training (line items)": semantic_missing(bls_line[BLS_TRAINING]),
    }
    missing_after = {
        "median_annual_wage_2025": int(occupation["median_annual_wage_2025"].isna().sum()),
        "related_work_experience": int(occupation["related_work_experience"].isna().sum()),
        "on_the_job_training": int(occupation["on_the_job_training"].isna().sum()),
        "occupation_description": int(occupation["occupation_description"].isna().sum()),
        "average_task_penetration": int(occupation["average_task_penetration"].isna().sum()),
        "matched_task_count": int(occupation["matched_task_count"].isna().sum()),
    }
    metric_denominators = {
        column: int(occupation[column].notna().sum())
        for column in [
            "observed_exposure",
            "employment_2025_thousands",
            "employment_change_percent_2025_35",
            "annual_openings_2025_35_thousands",
            "median_annual_wage_2025",
            "average_task_penetration",
        ]
    }

    difficult_cases = {
        "minimum_exposure": occupation.loc[occupation["observed_exposure"].idxmin(),
                                             ["soc_code", "title", "observed_exposure"]].to_dict(),
        "maximum_exposure": occupation.loc[occupation["observed_exposure"].idxmax(),
                                             ["soc_code", "title", "observed_exposure"]].to_dict(),
        "minimum_growth": occupation.loc[occupation["employment_change_percent_2025_35"].idxmin(),
                                           ["soc_code", "title", "employment_change_percent_2025_35"]].to_dict(),
        "maximum_growth": occupation.loc[occupation["employment_change_percent_2025_35"].idxmax(),
                                           ["soc_code", "title", "employment_change_percent_2025_35"]].to_dict(),
    }

    # These expectations are derived from five identifiable source records plus
    # documented rules before reading each corresponding output value.
    onet_occ = onet_occupations.loc[
        onet_occupations["O*NET-SOC Code"].eq("11-1011.00")
    ].iloc[0]
    bls_chief = bls.loc[bls[BLS_CODE].eq("11-1011")].iloc[0]
    bls_actor = bls.loc[bls[BLS_CODE].eq("27-2011")].iloc[0]
    onet_task = onet_tasks.loc[onet_tasks["Task ID"].eq(8825)].iloc[0]
    task_penetration_source = penetration.loc[
        normalized_task(penetration["task"]).eq(normalized_task(pd.Series([onet_task["Task"]])).iloc[0])
    ].iloc[0]
    unmatched_job = jobs.loc[jobs["occ_code"].eq("11-1031")].iloc[0]

    chief_output = occupation.loc[occupation["soc_code"].eq("11-1011")].iloc[0]
    actor_output = occupation.loc[occupation["soc_code"].eq("27-2011")].iloc[0]
    task_output = top_tasks.loc[
        top_tasks["task"].eq(" ".join(str(onet_task["Task"]).split()))
        & top_tasks["soc_code"].eq("11-1011")
    ].iloc[0]

    onet_occ_expected = "soc_code=11-1011; title=Chief Executives"
    onet_occ_actual = f"soc_code={chief_output['soc_code']}; title={chief_output['title']}"
    chief_title_expected = " ".join(str(bls_chief[BLS_TITLE]).split())
    chief_title_actual = str(chief_output["bls_title"])
    actor_wage_expected = "missing (NaN)"
    actor_wage_actual = "missing (NaN)" if pd.isna(actor_output["median_annual_wage_2025"]) else str(
        actor_output["median_annual_wage_2025"]
    )
    task_expected = (
        f"soc_code=11-1011; task_rank=1; penetration={float(task_penetration_source['penetration']):.3f}"
    )
    task_actual = (
        f"soc_code={task_output['soc_code']}; task_rank={int(task_output['task_rank'])}; "
        f"penetration={float(task_output['penetration']):.3f}"
    )
    unmatched_expected = "absent from cleaned_occupations.csv; logged unmatched"
    unmatched_actual = (
        "absent from cleaned_occupations.csv; logged unmatched"
        if str(unmatched_job["occ_code"]) not in set(occupation["soc_code"])
        and str(unmatched_job["occ_code"]) in expected_unmatched
        else "unexpected result"
    )
    record_checks = [
        {
            "case": "O*NET occupation mapped to six-digit SOC",
            "source_file": "onet_occupation_data.csv",
            "record_id": "O*NET-SOC Code=11-1011.00",
            "original_value": "O*NET-SOC Code=11-1011.00; Title=Chief Executives",
            "expected_result": onet_occ_expected,
            "reason": "Remove only the O*NET detail suffix so the record can join on six-digit SOC.",
            "actual_result": onet_occ_actual,
        },
        {
            "case": "BLS title whitespace",
            "source_file": "bls_table_1_2_2025_35.csv",
            "record_id": "2025 National Employment Matrix code=11-1011",
            "original_value": f"title={str(bls_chief[BLS_TITLE])!r}",
            "expected_result": f"bls_title={chief_title_expected}",
            "reason": "Leading spaces are table indentation, not meaningful title text.",
            "actual_result": f"bls_title={chief_title_actual}",
        },
        {
            "case": "BLS unavailable wage retained as missing",
            "source_file": "bls_table_1_2_2025_35.csv",
            "record_id": "2025 National Employment Matrix code=27-2011",
            "original_value": f"title={str(bls_actor[BLS_TITLE]).strip()}; median wage={bls_actor[BLS_WAGE]}",
            "expected_result": actor_wage_expected,
            "reason": "An em dash means unavailable; it must not be converted to zero or imputed.",
            "actual_result": actor_wage_actual,
        },
        {
            "case": "Specific O*NET task joined to task penetration",
            "source_file": "onet_task_statements.csv + task_penetration.csv",
            "record_id": "Task ID=8825",
            "original_value": (
                f"O*NET-SOC Code={onet_task['O*NET-SOC Code']}; "
                f"task={onet_task['Task']}; penetration={float(task_penetration_source['penetration']):.3f}"
            ),
            "expected_result": task_expected,
            "reason": "Normalized exact task text should connect this task to its observed penetration and base SOC.",
            "actual_result": task_actual,
        },
        {
            "case": "Unmatched occupation",
            "source_file": "job_exposure.csv",
            "record_id": "occ_code=11-1031",
            "original_value": (
                f"title={unmatched_job['title']}; observed_exposure={float(unmatched_job['observed_exposure']):.1f}"
            ),
            "expected_result": unmatched_expected,
            "reason": (
                "This analysis is limited to occupations successfully matched to BLS. "
                "Keep the record in the unmatched log rather than deleting it merely for missing values."
            ),
            "actual_result": unmatched_actual,
        },
    ]
    for record in record_checks:
        record["passed"] = record["expected_result"] == record["actual_result"]
    add_check(checks, "all five record checks match fixed expectations", True,
              all(record["passed"] for record in record_checks),
              "See record_checks in this validation report")

    type_checks = {
        "soc_code_is_text": occupation["soc_code"].dtype == object,
        "observed_exposure_is_numeric": pd.api.types.is_numeric_dtype(occupation["observed_exposure"]),
        "employment_is_numeric": pd.api.types.is_numeric_dtype(occupation["employment_2025_thousands"]),
        "growth_is_numeric": pd.api.types.is_numeric_dtype(occupation["employment_change_percent_2025_35"]),
        "openings_is_numeric": pd.api.types.is_numeric_dtype(occupation["annual_openings_2025_35_thousands"]),
        "wage_is_numeric": pd.api.types.is_numeric_dtype(occupation["median_annual_wage_2025"]),
    }
    add_check(checks, "cleaned output types", True, all(type_checks.values()),
              "SOC is text; analytic measures are numeric")

    failures = [check for check in checks if not check["passed"]]
    evidence = {
        "status": "PASS" if not failures else "FAIL",
        "python": sys.version,
        "command": " ".join(command),
        "source_sha256": source_hashes_after,
        "output_sha256": second_output_hashes,
        "checks": checks,
        "exact_duplicate_rows": exact_duplicates,
        "repeated_ids": repeated_ids,
        "missing_before_cleaning": missing_before,
        "missing_after_cleaning": missing_after,
        "metric_nonmissing_denominators": metric_denominators,
        "difficult_case_examples": difficult_cases,
        "record_checks": record_checks,
        "type_checks": type_checks,
    }
    OUTPUTS.mkdir(exist_ok=True)
    rendered_evidence = json.dumps(evidence, indent=2, ensure_ascii=False)
    (OUTPUTS / "validation_report.json").write_text(rendered_evidence, encoding="utf-8")
    (SUBMISSION / "validation_report.json").write_text(rendered_evidence, encoding="utf-8")
    record_frame = pd.DataFrame(record_checks)
    record_frame.to_csv(OUTPUTS / "five_record_checks.csv", index=False)
    record_frame.to_csv(SUBMISSION / "five_record_checks.csv", index=False)

    print(json.dumps(evidence, indent=2, ensure_ascii=False))
    if failures:
        raise AssertionError(f"{len(failures)} validation check(s) failed")


if __name__ == "__main__":
    main()
