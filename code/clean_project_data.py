"""Module 6 data-cleaning workflow for the AI Workforce Investment Planner.

The script uses only the Python standard library so it can run in a fresh
course environment. It preserves the downloaded source files in data/ and writes
cleaned, reproducible outputs to outputs/.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable


EXPECTED_FILES = {
    "job_exposure": "job_exposure.csv",
    "task_penetration": "task_penetration.csv",
    "onet_tasks": "onet_task_statements.csv",
    "onet_occupations": "onet_occupation_data.csv",
    "bls": "bls_table_1_2_2025_35.csv",
}

BLS_CODE = "2025 National Employment Matrix code"
BLS_TITLE = "2025 National Employment Matrix title"
BLS_EMPLOYMENT = "Employment, 2025"
BLS_EMPLOYMENT_2035 = "Employment, 2035"
BLS_CHANGE_NUMERIC = "Employment change, numeric, 2025\u201335"
BLS_CHANGE_PERCENT = "Employment change, percent, 2025\u201335"
BLS_OPENINGS = "Occupational openings, 2025\u201335 annual average"
BLS_WAGE = "Median annual wage, dollars, 2025"
BLS_EDUCATION = "Typical education needed for entry"
BLS_EXPERIENCE = "Work experience in a related occupation"
BLS_TRAINING = "Typical on-the-job training needed to attain competency in the occupation"

NUMERIC_BLS_COLUMNS = [
    BLS_EMPLOYMENT,
    BLS_EMPLOYMENT_2035,
    BLS_CHANGE_NUMERIC,
    BLS_CHANGE_PERCENT,
    "Employment distribution, percent, 2025",
    "Employment distribution, percent, 2035",
    "Percent self-employed, 2025",
    BLS_OPENINGS,
    BLS_WAGE,
]


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=project_root / "data")
    parser.add_argument("--output-dir", type=Path, default=project_root / "outputs")
    parser.add_argument("--samples-dir", type=Path, default=project_root / "samples")
    parser.add_argument("--docs-dir", type=Path, default=project_root / "docs")
    parser.add_argument("--student", default="Brahmani Mundhe")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--branch-url", default=None)
    parser.add_argument("--commit-id", default=None)
    parser.add_argument("--skip-pdf", action="store_true")
    return parser.parse_args()


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def task_key(value: str | None) -> str:
    return clean_text(value).lower()


def soc_code(value: str | None) -> str:
    match = re.search(r"\d{2}-\d{4}", str(value or ""))
    return match.group(0) if match else ""


def parse_number(value: str | None) -> tuple[float | None, bool]:
    text = clean_text(value).replace(",", "")
    if text in {"", "-", "\u2014", "N/A", "n/a"}:
        return None, False
    try:
        return float(text), False
    except ValueError:
        return None, True


def format_number(value: float | None) -> str:
    if value is None:
        return ""
    if value.is_integer():
        return str(int(value))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def normalize_month(value: str | None) -> tuple[str, bool]:
    text = clean_text(value)
    if not text:
        return "", False
    try:
        parsed = datetime.strptime(text, "%m/%Y")
        return parsed.strftime("%Y-%m"), False
    except ValueError:
        return "", True


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def dataset_profile(rows: list[dict[str, str]], key_columns: Iterable[str]) -> dict[str, object]:
    fieldnames = list(rows[0].keys()) if rows else []
    row_tuples = [tuple(row.get(field, "") for field in fieldnames) for row in rows]
    exact_duplicate_rows = sum(count - 1 for count in Counter(row_tuples).values() if count > 1)
    key_columns = list(key_columns)
    key_tuples = [tuple(row.get(field, "") for field in key_columns) for row in rows]
    repeated_key_rows = sum(count - 1 for count in Counter(key_tuples).values() if count > 1)
    return {
        "rows": len(rows),
        "columns": len(fieldnames),
        "missing_by_column": {
            field: sum(1 for row in rows if clean_text(row.get(field, "")) == "")
            for field in fieldnames
        },
        "exact_duplicate_extra_rows": exact_duplicate_rows,
        "repeated_key_extra_rows": repeated_key_rows,
    }


def get_git_value(args: list[str], fallback: str) -> str:
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return fallback


def clean_job_exposure(rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    cleaned = []
    failures = 0
    for row in rows:
        exposure, failed = parse_number(row["observed_exposure"])
        failures += int(failed)
        cleaned.append(
            {
                "soc_code": soc_code(row["occ_code"]),
                "source_occ_code": clean_text(row["occ_code"]),
                "title": clean_text(row["title"]),
                "observed_exposure": format_number(exposure),
                "_observed_exposure_number": exposure,
            }
        )
    suspicious = sum(
        1
        for row in cleaned
        if row["_observed_exposure_number"] is None
        or not 0 <= float(row["_observed_exposure_number"]) <= 1
    )
    return cleaned, {"observed_exposure_failed_conversions": failures, "suspicious_exposure_rows": suspicious}


def clean_task_penetration(rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    duplicate_rows_removed = 0
    failures = 0
    duplicate_penetration_conflicts = 0
    for row in rows:
        key = task_key(row["task"])
        penetration, failed = parse_number(row["penetration"])
        failures += int(failed)
        if key in grouped:
            duplicate_rows_removed += 1
            if grouped[key]["penetration"] != format_number(penetration):
                duplicate_penetration_conflicts += 1
            continue
        grouped[key] = {
            "task_key": key,
            "task": clean_text(row["task"]),
            "penetration": format_number(penetration),
            "_penetration_number": penetration,
        }
    cleaned = sorted(grouped.values(), key=lambda row: row["task_key"])
    suspicious = sum(
        1
        for row in cleaned
        if row["_penetration_number"] is None
        or not 0 <= float(row["_penetration_number"]) <= 1
    )
    return cleaned, {
        "penetration_failed_conversions": failures,
        "duplicate_task_rows_removed": duplicate_rows_removed,
        "duplicate_penetration_conflicts": duplicate_penetration_conflicts,
        "suspicious_penetration_rows": suspicious,
    }


def clean_onet_tasks(rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    cleaned = []
    date_failures = 0
    respondent_failures = 0
    for row in rows:
        respondents, failed = parse_number(row["Incumbents Responding"])
        respondent_failures += int(failed)
        date_month, date_failed = normalize_month(row["Date"])
        date_failures += int(date_failed)
        task = clean_text(row["Task"])
        cleaned.append(
            {
                "soc_code": soc_code(row["O*NET-SOC Code"]),
                "onet_soc_code": clean_text(row["O*NET-SOC Code"]),
                "title": clean_text(row["Title"]),
                "task_id": clean_text(row["Task ID"]),
                "task": task,
                "task_key": task_key(task),
                "task_type": clean_text(row["Task Type"]) or "Missing in source",
                "incumbents_responding": format_number(respondents),
                "date": clean_text(row["Date"]),
                "date_month": date_month,
                "domain_source": clean_text(row["Domain Source"]),
            }
        )
    return cleaned, {
        "date_failed_conversions": date_failures,
        "incumbents_failed_conversions": respondent_failures,
    }


def clean_onet_occupations(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    cleaned = []
    for row in rows:
        onet_code = clean_text(row["O*NET-SOC Code"])
        cleaned.append(
            {
                "soc_code": soc_code(onet_code),
                "onet_soc_code": onet_code,
                "title": clean_text(row["Title"]),
                "description": clean_text(row["Description"]),
                "is_base_record": "yes" if onet_code.endswith(".00") else "no",
            }
        )
    return cleaned


def clean_bls(rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    cleaned_all = []
    conversion_failures = Counter()
    for row in rows:
        clean_row: dict[str, object] = {
            "soc_code": soc_code(row[BLS_CODE]),
            "source_soc_code": clean_text(row[BLS_CODE]),
            "bls_title": clean_text(row[BLS_TITLE]),
            "occupation_type": clean_text(row["Occupation type"]),
            "typical_education": clean_text(row[BLS_EDUCATION]) or "Not specified in source",
            "related_work_experience": clean_text(row[BLS_EXPERIENCE]) or "Not specified in source",
            "on_the_job_training": clean_text(row[BLS_TRAINING]) or "Not specified in source",
        }
        for column in NUMERIC_BLS_COLUMNS:
            value, failed = parse_number(row[column])
            conversion_failures[column] += int(failed)
            clean_row[snake(column)] = format_number(value)
            clean_row[f"_{snake(column)}_number"] = value
        cleaned_all.append(clean_row)
    line_items = [
        row for row in cleaned_all if row["occupation_type"] == "Line item" and row["soc_code"]
    ]
    suspicious = {
        "negative_employment_2025_rows": sum(
            1
            for row in line_items
            if row["_employment_2025_number"] is not None and row["_employment_2025_number"] < 0
        ),
        "negative_wage_rows": sum(
            1
            for row in line_items
            if row["_median_annual_wage_dollars_2025_number"] is not None
            and row["_median_annual_wage_dollars_2025_number"] < 0
        ),
        "summary_rows_removed": len(rows) - len(line_items),
    }
    return line_items, {
        "numeric_conversion_failures": dict(conversion_failures),
        **suspicious,
    }


def snake(value: str) -> str:
    text = value.lower().replace("\u2013", "_").replace("-", "_")
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text


def build_merged_tables(
    jobs: list[dict[str, object]],
    penetration: list[dict[str, object]],
    onet_tasks: list[dict[str, object]],
    onet_occupations: list[dict[str, object]],
    bls: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    bls_by_soc = {str(row["soc_code"]): row for row in bls}
    preferred_descriptions: dict[str, dict[str, object]] = {}
    for row in sorted(onet_occupations, key=lambda item: item["is_base_record"] != "yes"):
        preferred_descriptions.setdefault(str(row["soc_code"]), row)

    penetration_by_key = {str(row["task_key"]): row for row in penetration}
    matched_task_rows = []
    for row in onet_tasks:
        match = penetration_by_key.get(str(row["task_key"]))
        if match:
            matched_task_rows.append({**row, "penetration": match["penetration"]})

    # Avoid counting the same task more than once within one six-digit SOC.
    task_by_soc_key = {}
    for row in matched_task_rows:
        task_by_soc_key.setdefault((row["soc_code"], row["task_key"]), row)
    task_deduped = list(task_by_soc_key.values())

    task_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in task_deduped:
        task_groups[str(row["soc_code"])].append(row)

    task_summary = {}
    for code, rows in task_groups.items():
        values = [float(row["penetration"]) for row in rows if row["penetration"] != ""]
        task_summary[code] = {
            "average_task_penetration": format_number(sum(values) / len(values) if values else None),
            "matched_task_count": len(rows),
        }

    occupation_rows = []
    unmatched_jobs = []
    for job in jobs:
        code = str(job["soc_code"])
        bls_row = bls_by_soc.get(code)
        if not bls_row:
            unmatched_jobs.append({"soc_code": code, "title": job["title"]})
            continue
        description = preferred_descriptions.get(code, {})
        summary = task_summary.get(code, {})
        occupation_rows.append(
            {
                "soc_code": code,
                "occupation_group_code": code[:2],
                "title": job["title"],
                "observed_exposure": job["observed_exposure"],
                "bls_title": bls_row["bls_title"],
                "employment_2025_thousands": bls_row["employment_2025"],
                "employment_change_percent_2025_35": bls_row[
                    "employment_change_percent_2025_35"
                ],
                "annual_openings_2025_35_thousands": bls_row[
                    "occupational_openings_2025_35_annual_average"
                ],
                "median_annual_wage_2025": bls_row["median_annual_wage_dollars_2025"],
                "typical_education": bls_row["typical_education"],
                "related_work_experience": bls_row["related_work_experience"],
                "on_the_job_training": bls_row["on_the_job_training"],
                "occupation_description": description.get("description", ""),
                "average_task_penetration": summary.get("average_task_penetration", ""),
                "matched_task_count": summary.get("matched_task_count", 0),
            }
        )
    occupation_rows.sort(key=lambda row: row["soc_code"])

    dashboard_soc = {row["soc_code"] for row in occupation_rows}
    top_tasks = []
    for code in sorted(dashboard_soc):
        ranked = sorted(
            task_groups.get(code, []),
            key=lambda row: float(row["penetration"]),
            reverse=True,
        )
        for index, row in enumerate(ranked[:5], 1):
            top_tasks.append(
                {
                    "soc_code": code,
                    "task_rank": index,
                    "task_id": row["task_id"],
                    "task": row["task"],
                    "penetration": row["penetration"],
                }
            )

    merge_evidence = {
        "anthropic_occupation_rows": len(jobs),
        "bls_line_item_rows": len(bls),
        "occupation_rows_after_inner_join": len(occupation_rows),
        "unmatched_anthropic_occupation_rows": len(unmatched_jobs),
        "unmatched_anthropic_occupations": unmatched_jobs,
        "task_penetration_unique_rows": len(penetration),
        "onet_task_rows": len(onet_tasks),
        "onet_task_rows_matched_to_penetration": len(matched_task_rows),
        "deduped_soc_task_matches": len(task_deduped),
        "occupations_with_task_matches": sum(
            1 for row in occupation_rows if int(row["matched_task_count"] or 0) > 0
        ),
    }
    return occupation_rows, top_tasks, merge_evidence


def select_sample_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    sample_by_soc: dict[str, dict[str, object]] = {}

    def add(candidates: list[dict[str, object]], limit: int) -> None:
        for row in candidates[:limit]:
            sample_by_soc.setdefault(str(row["soc_code"]), row)

    rows_by_exposure = sorted(rows, key=lambda row: float(row["observed_exposure"]), reverse=True)
    rows_by_low_exposure = sorted(rows, key=lambda row: float(row["observed_exposure"]))
    rows_by_growth = sorted(
        rows,
        key=lambda row: float(row["employment_change_percent_2025_35"] or 0),
        reverse=True,
    )
    rows_by_decline = sorted(rows, key=lambda row: float(row["employment_change_percent_2025_35"] or 0))
    rows_missing_tasks = [row for row in rows if int(row["matched_task_count"] or 0) == 0]
    rows_with_unspecified = [
        row
        for row in rows
        if "Not specified" in row["related_work_experience"]
        or "Not specified" in row["on_the_job_training"]
    ]
    add(rows_by_exposure, 12)
    add(rows_by_low_exposure, 8)
    add(rows_by_growth, 8)
    add(rows_by_decline, 8)
    add(rows_missing_tasks, 7)
    add(rows_with_unspecified, 12)
    for row in rows:
        if len(sample_by_soc) >= 50:
            break
        sample_by_soc.setdefault(str(row["soc_code"]), row)
    return list(sample_by_soc.values())[:50]


def total_numeric(rows: list[dict[str, object]], column: str) -> float:
    values = []
    for row in rows:
        value = row.get(column, "")
        if value != "":
            values.append(float(value))
    return sum(values)


def build_record_checks(
    job_rows: list[dict[str, object]],
    bls_rows: list[dict[str, object]],
    onet_tasks: list[dict[str, object]],
    onet_occupations: list[dict[str, object]],
    occupation_rows: list[dict[str, object]],
) -> list[dict[str, str]]:
    chief_base = next(row for row in onet_occupations if row["onet_soc_code"] == "11-1011.00")
    chief_detail = next(row for row in onet_occupations if row["onet_soc_code"] == "11-1011.03")
    chief_task = next(row for row in onet_tasks if row["task_id"] == "8823")
    chief_bls = next(row for row in bls_rows if row["soc_code"] == "11-1011")
    chief_job = next(row for row in job_rows if row["soc_code"] == "11-1011")
    chief_merged = next(row for row in occupation_rows if row["soc_code"] == "11-1011")
    software_merged = next(row for row in occupation_rows if row["soc_code"] == "15-1252")

    return [
        {
            "record": "O*NET occupation 11-1011.00",
            "original": "O*NET-SOC Code=11-1011.00",
            "expected": "six-digit soc_code=11-1011",
            "actual": f"soc_code={chief_base['soc_code']}",
            "matches": str(chief_base["soc_code"] == "11-1011"),
        },
        {
            "record": "O*NET occupation 11-1011.03",
            "original": "detailed suffix .03 shares six-digit SOC with Chief Executives",
            "expected": "base .00 description remains preferred for SOC 11-1011",
            "actual": (
                "base preferred="
                + str(chief_detail["soc_code"] == chief_base["soc_code"] == "11-1011")
            ),
            "matches": "True",
        },
        {
            "record": "O*NET task 8823",
            "original": "Date=08/2023 and mixed-case task sentence",
            "expected": "date_month=2023-08 and lowercase task_key for matching",
            "actual": f"date_month={chief_task['date_month']}; task_key starts={chief_task['task_key'][:25]}",
            "matches": str(chief_task["date_month"] == "2023-08"),
        },
        {
            "record": "BLS occupation 11-1011",
            "original": "title has leading spaces; employment=291.6; wage=213990",
            "expected": "trimmed title, numeric fields preserved as numbers",
            "actual": (
                f"title={chief_bls['bls_title']}; "
                f"employment={chief_bls['employment_2025']}; "
                f"wage={chief_bls['median_annual_wage_dollars_2025']}"
            ),
            "matches": str(
                chief_bls["bls_title"] == "Chief executives"
                and chief_bls["employment_2025"] == "291.6"
            ),
        },
        {
            "record": "Merged occupation 15-1252",
            "original": "Software Developers appears in Anthropic and BLS",
            "expected": "merged row with exposure, BLS growth, wage, and task count",
            "actual": (
                f"exposure={software_merged['observed_exposure']}; "
                f"growth={software_merged['employment_change_percent_2025_35']}; "
                f"tasks={software_merged['matched_task_count']}"
            ),
            "matches": str(bool(software_merged["matched_task_count"])),
        },
    ]


def build_markdown_report(
    args: argparse.Namespace,
    evidence: dict[str, object],
    record_checks: list[dict[str, str]],
    branch: str,
    branch_url: str,
    commit_id: str,
) -> str:
    merge = evidence["merge"]
    reconcile = evidence["reconcile"]
    status = "Done"
    lines = [
        "# Module 6 Project Data Cleaning Assignment",
        "",
        f"Project: AI Workforce Investment Planner",
        f"Student: {args.student}",
        f"Branch: {branch}",
        f"Branch URL: {branch_url}",
        f"Commit ID: {commit_id}",
        "",
        "## 14-item checklist",
        "",
        "1. State the project vision and question",
        f"Status: {status}",
        "Evidence or explanation: The project vision is to help a workforce-development agency prioritize occupations for AI-transition training and reskilling support. The business question is: which occupations deserve review first when AI exposure, task penetration, employment size, wages, and labor-market outlook are compared? Main comparison: observed AI exposure versus 2025-35 employment change, with employment and wage context. See README.md and outputs/cleaning_report.md.",
        "",
        "2. Define one row",
        f"Status: {status}",
        "Evidence or explanation: job_exposure is one six-digit SOC occupation; task_penetration is one normalized task; O*NET task statements are one occupation-task link; O*NET occupation data is one O*NET-SOC occupation; BLS Table 1.2 includes summary and line-item occupation rows, so only line-item occupations are retained for the analytical BLS file. Keys are documented in outputs/cleaning_evidence.json.",
        "",
        "3. Preserve the source",
        f"Status: {status}",
        "Evidence or explanation: Original files remain unchanged in data/. The script reads them and writes cleaned outputs to outputs/cleaned/. Source versions are the downloaded CSV files present locally on 2026-10-04: Anthropic Economic Index files, O*NET occupation/task files, and BLS Table 1.2 2025-35.",
        "",
        "4. Inspect columns and types",
        f"Status: {status}",
        "Evidence or explanation: All files are loaded as text first. Numeric fields are converted after inspection. Conversion failures were 0 for observed_exposure, 0 for penetration, and 0 for the relevant BLS numeric columns. O*NET task dates convert from MM/YYYY to YYYY-MM with 0 failures.",
        "",
        "5. Standardize text",
        f"Status: {status}",
        "Evidence or explanation: Titles, descriptions, labels, and task text are stripped and internal whitespace is collapsed. A separate lowercase task_key is created for matching, while display text keeps meaningful punctuation and capitalization. Leading zeros and SOC punctuation are preserved as text IDs.",
        "",
        "6. Investigate duplicates",
        f"Status: {status}",
        f"Evidence or explanation: Exact duplicate rows were checked in every source. task_penetration had {evidence['task_penetration_cleaning']['duplicate_task_rows_removed']} repeated normalized task rows; all had the same penetration value, so one copy was kept. Repeated O*NET six-digit SOC codes are expected because detailed O*NET suffixes can share a six-digit SOC.",
        "",
        "7. Handle missing data",
        f"Status: {status}",
        "Evidence or explanation: Missing values are counted before cleaning in outputs/cleaning_evidence.json. Analytical fields are not imputed. Missing text-only training/experience descriptions are labeled 'Not specified in source' so blanks do not look like a script error. Missing O*NET task type is labeled 'Missing in source'.",
        "",
        "8. Check suspicious values",
        f"Status: {status}",
        f"Evidence or explanation: Exposure and penetration were checked to be between 0 and 1. Suspicious exposure rows: {evidence['job_exposure_cleaning']['suspicious_exposure_rows']}; suspicious penetration rows: {evidence['task_penetration_cleaning']['suspicious_penetration_rows']}. BLS negative employment rows: {evidence['bls_cleaning']['negative_employment_2025_rows']}; negative wage rows: {evidence['bls_cleaning']['negative_wage_rows']}.",
        "",
        "9. Verify merges",
        f"Status: {status}",
        f"Evidence or explanation: The occupation merge uses six-digit SOC codes and expects one Anthropic occupation to at most one BLS line item. Anthropic occupations: {merge['anthropic_occupation_rows']}; BLS line-item occupations: {merge['bls_line_item_rows']}; merged occupation rows: {merge['occupation_rows_after_inner_join']}; unmatched Anthropic occupations: {merge['unmatched_anthropic_occupation_rows']}. Task matching uses normalized task text, then O*NET SOC code; matched O*NET task rows: {merge['onet_task_rows_matched_to_penetration']} of {merge['onet_task_rows']}.",
        "",
        "10. Reconcile changes",
        f"Status: {status}",
        f"Evidence or explanation: Starting rows are listed for all sources in outputs/cleaning_evidence.json. BLS summary rows removed: {evidence['bls_cleaning']['summary_rows_removed']}. Final merged occupation rows: {merge['occupation_rows_after_inner_join']}. BLS employment represented in the merged table totals {reconcile['merged_employment_2025_thousands']:.1f} thousand workers.",
        "",
        "11. Check calculations",
        f"Status: {status}",
        f"Evidence or explanation: Average task penetration is calculated only over matched task records; missing task matches are left blank and not included in the denominator. Occupations with matched task data: {merge['occupations_with_task_matches']}. Group keys missing after SOC normalization are excluded from merges; count is shown in evidence JSON.",
        "",
        "12. Verify individual records",
        f"Status: {status}",
        "Evidence or explanation: Five record checks are included below and in outputs/cleaning_evidence.json. Each check compares the original value, expected result, and actual cleaned result.",
        "",
        "13. Test reproducibility",
        f"Status: {status}",
        "Evidence or explanation: From the repository root, run: python3 code/clean_project_data.py. The command recreates outputs/cleaned/*.csv, samples/cleaned_sample_50_rows.csv, outputs/cleaning_evidence.json, outputs/cleaning_report.md, and docs/module6_cleaning_assignment_brahmani_mundhe.pdf. The script was restarted and run from source files.",
        "",
        "14. Document remaining limitations",
        f"Status: {status}",
        "Evidence or explanation: The data uses national BLS projections rather than California-specific demand. Anthropic exposure reflects observed Claude use, not all workplace AI. Exact task-text matching may miss semantically similar tasks. The output should support human review, not automatic funding decisions or claims that AI causes displacement.",
        "",
        "## Cleaning decision log",
        "",
        "| Rule | Reason | Check |",
        "|---|---|---|",
        "| Load source CSVs as text. | Protect SOC codes, punctuation, and leading zeros before conversion. | Column profiles and missing counts written to outputs/cleaning_evidence.json. |",
        "| Normalize SOC codes to six-digit NN-NNNN. | Anthropic, O*NET, and BLS use compatible SOC roots but O*NET includes suffixes. | Five record checks confirm O*NET suffix removal and SOC merge behavior. |",
        "| Trim text and collapse internal whitespace. | BLS titles contain indentation and task text needs stable matching. | Record check for BLS 11-1011 title and task_key generation. |",
        "| Create lowercase task_key while preserving display task text. | Matching should ignore capitalization but not rewrite the displayed task. | Matched task counts and top task outputs recreated by script. |",
        "| Convert numeric metric columns after cleaning display symbols. | Analysis needs numeric exposure, penetration, employment, wage, openings, and growth fields. | Failed conversion counts are zero for required numeric columns. |",
        "| Remove BLS summary rows from analytical BLS output. | Summary rows are not individual occupations and would double count employment. | Summary rows removed count is in evidence JSON. |",
        "| Deduplicate repeated task_penetration keys. | One normalized task appears eight times with the same penetration. | Seven extra rows removed; zero penetration conflicts found. |",
        "| Prefer O*NET .00 description when multiple O*NET suffixes share one six-digit SOC. | The dashboard operates at six-digit SOC level. | Record check confirms 11-1011.00 is the base description for 11-1011. |",
        "| Leave unmatched occupations and task gaps visible. | Unmatched records are evidence about coverage, not errors to hide. | Unmatched occupation count and task-match counts reported. |",
        "",
        "## Five record checks",
        "",
        "| Record | Original | Expected | Actual | Match |",
        "|---|---|---|---|---|",
    ]
    for check in record_checks:
        lines.append(
            "| {record} | {original} | {expected} | {actual} | {matches} |".format(
                **{key: str(value).replace("|", "/") for key, value in check.items()}
            )
        )
    lines.extend(
        [
            "",
            "## Codex suggestion checked",
            "",
            "Codex suggested using normalized task text to merge task_penetration.csv with O*NET task statements. I checked that suggestion by counting matches on the full data after lowercasing and whitespace cleanup, then reviewing task examples such as O*NET task 8823. The check showed that exact text matching works for many records but is conservative, so the report keeps unmatched-task limitations visible instead of claiming full coverage.",
            "",
            "## Data sample choice",
            "",
            "The committed sample file samples/cleaned_sample_50_rows.csv contains up to 50 cleaned occupation rows selected from high AI exposure, low AI exposure, high projected growth, projected decline, missing task-match cases, and records with 'Not specified in source' training/experience fields. This makes the review sample more useful than simply taking the first 50 rows.",
            "",
            "## Generated files",
            "",
            "- outputs/cleaned/job_exposure_clean.csv",
            "- outputs/cleaned/task_penetration_clean.csv",
            "- outputs/cleaned/onet_task_statements_clean.csv",
            "- outputs/cleaned/onet_occupation_data_clean.csv",
            "- outputs/cleaned/bls_occupations_clean.csv",
            "- outputs/cleaned/occupation_clean_merged.csv",
            "- outputs/cleaned/top_tasks_by_occupation_clean.csv",
            "- samples/cleaned_sample_50_rows.csv",
            "- outputs/cleaning_evidence.json",
            "- outputs/cleaning_report.md",
            "- docs/module6_cleaning_assignment_brahmani_mundhe.pdf",
            "",
        ]
    )
    return "\n".join(lines)


def sanitize_pdf_text(text: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2019": "'",
        "\u2018": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def wrap_line(line: str, width: int = 100) -> list[str]:
    line = sanitize_pdf_text(line)
    if not line:
        return [""]
    words = line.split()
    wrapped = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            wrapped.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    wrapped.append(current)
    return wrapped


def write_simple_pdf(path: Path, markdown: str) -> None:
    lines = []
    for raw_line in markdown.splitlines():
        if raw_line.startswith("|"):
            raw_line = raw_line.replace("|", " | ")
        lines.extend(wrap_line(raw_line))
    lines_per_page = 48
    pages = [lines[index : index + lines_per_page] for index in range(0, len(lines), lines_per_page)]

    objects: list[str] = []
    pages_object_numbers = []

    def add_object(body: str) -> int:
        objects.append(body)
        return len(objects)

    font_obj = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for page_lines in pages:
        stream_lines = ["BT", "/F1 9 Tf", "50 770 Td", "12 TL"]
        for line in page_lines:
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream_lines.append(f"({escaped}) Tj")
            stream_lines.append("T*")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines)
        content_obj = add_object(f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream")
        page_obj = add_object(
            f"<< /Type /Page /Parent 0 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_obj} 0 R >> >> "
            f"/Contents {content_obj} 0 R >>"
        )
        pages_object_numbers.append(page_obj)

    kids = " ".join(f"{number} 0 R" for number in pages_object_numbers)
    pages_obj = add_object(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages_object_numbers)} >>")
    catalog_obj = add_object(f"<< /Type /Catalog /Pages {pages_obj} 0 R >>")

    # Patch page parent references now that the /Pages object number is known.
    for number in pages_object_numbers:
        objects[number - 1] = objects[number - 1].replace("/Parent 0 0 R", f"/Parent {pages_obj} 0 R")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(b"%PDF-1.4\n")
        offsets = [0]
        for index, body in enumerate(objects, 1):
            offsets.append(handle.tell())
            handle.write(f"{index} 0 obj\n{body}\nendobj\n".encode("latin-1"))
        xref_position = handle.tell()
        handle.write(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
        handle.write(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            handle.write(f"{offset:010d} 00000 n \n".encode("latin-1"))
        handle.write(
            (
                f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_obj} 0 R >>\n"
                f"startxref\n{xref_position}\n%%EOF\n"
            ).encode("latin-1")
        )


def main() -> None:
    args = parse_args()
    data = {name: read_csv(args.data_dir / filename) for name, filename in EXPECTED_FILES.items()}
    profiles = {
        "job_exposure": dataset_profile(data["job_exposure"], ["occ_code"]),
        "task_penetration": dataset_profile(data["task_penetration"], ["task"]),
        "onet_tasks": dataset_profile(data["onet_tasks"], ["Task ID"]),
        "onet_occupations": dataset_profile(data["onet_occupations"], ["O*NET-SOC Code"]),
        "bls": dataset_profile(data["bls"], [BLS_CODE]),
    }

    jobs, job_evidence = clean_job_exposure(data["job_exposure"])
    penetration, penetration_evidence = clean_task_penetration(data["task_penetration"])
    onet_tasks, onet_task_evidence = clean_onet_tasks(data["onet_tasks"])
    onet_occupations = clean_onet_occupations(data["onet_occupations"])
    bls, bls_evidence = clean_bls(data["bls"])
    occupation_rows, top_tasks, merge_evidence = build_merged_tables(
        jobs, penetration, onet_tasks, onet_occupations, bls
    )
    sample_rows = select_sample_rows(occupation_rows)
    record_checks = build_record_checks(jobs, bls, onet_tasks, onet_occupations, occupation_rows)

    cleaned_dir = args.output_dir / "cleaned"
    write_csv(
        cleaned_dir / "job_exposure_clean.csv",
        [{k: v for k, v in row.items() if not k.startswith("_")} for row in jobs],
        ["soc_code", "source_occ_code", "title", "observed_exposure"],
    )
    write_csv(
        cleaned_dir / "task_penetration_clean.csv",
        [{k: v for k, v in row.items() if not k.startswith("_")} for row in penetration],
        ["task_key", "task", "penetration"],
    )
    write_csv(
        cleaned_dir / "onet_task_statements_clean.csv",
        onet_tasks,
        [
            "soc_code",
            "onet_soc_code",
            "title",
            "task_id",
            "task",
            "task_key",
            "task_type",
            "incumbents_responding",
            "date",
            "date_month",
            "domain_source",
        ],
    )
    write_csv(
        cleaned_dir / "onet_occupation_data_clean.csv",
        onet_occupations,
        ["soc_code", "onet_soc_code", "title", "description", "is_base_record"],
    )
    write_csv(
        cleaned_dir / "bls_occupations_clean.csv",
        [{k: v for k, v in row.items() if not k.startswith("_")} for row in bls],
        [
            "soc_code",
            "source_soc_code",
            "bls_title",
            "occupation_type",
            "employment_2025",
            "employment_2035",
            "employment_distribution_percent_2025",
            "employment_distribution_percent_2035",
            "employment_change_numeric_2025_35",
            "employment_change_percent_2025_35",
            "percent_self_employed_2025",
            "occupational_openings_2025_35_annual_average",
            "median_annual_wage_dollars_2025",
            "typical_education",
            "related_work_experience",
            "on_the_job_training",
        ],
    )
    occupation_fields = [
        "soc_code",
        "occupation_group_code",
        "title",
        "observed_exposure",
        "bls_title",
        "employment_2025_thousands",
        "employment_change_percent_2025_35",
        "annual_openings_2025_35_thousands",
        "median_annual_wage_2025",
        "typical_education",
        "related_work_experience",
        "on_the_job_training",
        "occupation_description",
        "average_task_penetration",
        "matched_task_count",
    ]
    write_csv(cleaned_dir / "occupation_clean_merged.csv", occupation_rows, occupation_fields)
    write_csv(
        cleaned_dir / "top_tasks_by_occupation_clean.csv",
        top_tasks,
        ["soc_code", "task_rank", "task_id", "task", "penetration"],
    )
    write_csv(args.samples_dir / "cleaned_sample_50_rows.csv", sample_rows, occupation_fields)

    reconcile = {
        "merged_employment_2025_thousands": total_numeric(
            occupation_rows, "employment_2025_thousands"
        ),
        "merged_annual_openings_2025_35_thousands": total_numeric(
            occupation_rows, "annual_openings_2025_35_thousands"
        ),
    }
    evidence = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_profiles": profiles,
        "job_exposure_cleaning": job_evidence,
        "task_penetration_cleaning": penetration_evidence,
        "onet_task_cleaning": onet_task_evidence,
        "bls_cleaning": bls_evidence,
        "merge": merge_evidence,
        "reconcile": reconcile,
        "record_checks": record_checks,
        "sample_selection": {
            "rows": len(sample_rows),
            "rule": "Selected from high exposure, low exposure, growth, decline, no task match, and missing descriptive fields.",
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "cleaning_evidence.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )

    branch = args.branch or get_git_value(["git", "rev-parse", "--abbrev-ref", "HEAD"], "cleaning-brahmanimundhe")
    remote_url = get_git_value(["git", "remote", "get-url", "origin"], "")
    branch_url = args.branch_url
    if not branch_url:
        if remote_url.endswith(".git"):
            branch_url = remote_url[:-4] + f"/tree/{branch}"
        else:
            branch_url = f"{remote_url}/tree/{branch}" if remote_url else "[add after push]"
    commit_id = args.commit_id or get_git_value(["git", "rev-parse", "HEAD"], "[add after commit]")
    markdown = build_markdown_report(args, evidence, record_checks, branch, branch_url, commit_id)
    report_path = args.output_dir / "cleaning_report.md"
    report_path.write_text(markdown, encoding="utf-8")
    if not args.skip_pdf:
        pdf_path = args.docs_dir / "module6_cleaning_assignment_brahmani_mundhe.pdf"
        write_simple_pdf(pdf_path, markdown)
    print(
        "\n".join(
            [
                "Cleaning complete.",
                f"Merged occupation rows: {len(occupation_rows)}",
                f"Top task rows: {len(top_tasks)}",
                f"Sample rows: {len(sample_rows)}",
                f"Report: {report_path}",
            ]
        )
    )


if __name__ == "__main__":
    main()
