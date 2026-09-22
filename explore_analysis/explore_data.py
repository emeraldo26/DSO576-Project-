"""Phase 1 data exploration for the AI Workforce Investment Planner (in GPT-assisted).

This script checks whether the Anthropic, O*NET, and BLS datasets can be
connected at the occupation and task levels. It also creates two analysis-ready
tables that could support the proposed dashboard.

It intentionally does not calculate a priority score because the team has not
yet selected or justified weights for the five measures in the project vision.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


EXPECTED_FILES = {
    "job_exposure": "job_exposure.csv",
    "task_penetration": "task_penetration.csv",
    "onet_tasks": "onet_task_statements.csv",
    "onet_occupations": "onet_occupation_data.csv",
    "bls": "bls_table_1_2_2025_35.csv",
}


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=project_root / "data",
        help="Folder containing the five CSV files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=project_root / "outputs",
        help="Folder for generated exploration results.",
    )
    return parser.parse_args()


def require_columns(df: pd.DataFrame, columns: list[str], dataset: str) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"{dataset} is missing required columns: {missing}")


def normalize_soc(values: pd.Series) -> pd.Series:
    """Convert SOC and O*NET-SOC values to a six-digit NN-NNNN code."""
    return values.astype("string").str.extract(r"(\d{2}-\d{4})", expand=False)


def normalize_task(values: pd.Series) -> pd.Series:
    """Standardize task text for a conservative exact-text match."""
    return (
        values.astype("string")
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def to_number(values: pd.Series) -> pd.Series:
    """Convert BLS display values to numbers; symbols such as — become missing."""
    cleaned = values.astype("string").str.replace(",", "", regex=False)
    return pd.to_numeric(cleaned, errors="coerce")


def pct(numerator: int, denominator: int) -> float:
    return 100 * numerator / denominator if denominator else 0.0


def load_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    missing = [name for name in EXPECTED_FILES.values() if not (data_dir / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing files in {data_dir}: {missing}. "
            "Downloaded datasets belong in data/ and should not be committed to Git."
        )

    return {
        key: pd.read_csv(data_dir / filename, low_memory=False)
        for key, filename in EXPECTED_FILES.items()
    }


def explore(data: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    jobs = data["job_exposure"].copy()
    penetration = data["task_penetration"].copy()
    onet_tasks = data["onet_tasks"].copy()
    onet_occupations = data["onet_occupations"].copy()
    bls = data["bls"].copy()

    require_columns(jobs, ["occ_code", "title", "observed_exposure"], "job_exposure.csv")
    require_columns(penetration, ["task", "penetration"], "task_penetration.csv")
    require_columns(
        onet_tasks,
        ["O*NET-SOC Code", "Title", "Task"],
        "onet_task_statements.csv",
    )
    require_columns(
        onet_occupations,
        ["O*NET-SOC Code", "Title", "Description"],
        "onet_occupation_data.csv",
    )

    bls_code = "2025 National Employment Matrix code"
    bls_title = "2025 National Employment Matrix title"
    employment = "Employment, 2025"
    outlook = "Employment change, percent, 2025–35"
    openings = "Occupational openings, 2025–35 annual average"
    wage = "Median annual wage, dollars, 2025"
    education = "Typical education needed for entry"
    related_experience = "Work experience in a related occupation"
    training = "Typical on-the-job training needed to attain competency in the occupation"
    require_columns(
        bls,
        [
            bls_code,
            bls_title,
            "Occupation type",
            employment,
            outlook,
            openings,
            wage,
            education,
            related_experience,
            training,
        ],
        "bls_table_1_2_2025_35.csv",
    )

    jobs["soc_code"] = normalize_soc(jobs["occ_code"])
    onet_tasks["soc_code"] = normalize_soc(onet_tasks["O*NET-SOC Code"])
    onet_occupations["soc_code"] = normalize_soc(onet_occupations["O*NET-SOC Code"])
    bls["soc_code"] = normalize_soc(bls[bls_code])

    # Summary rows describe broad groups rather than individual occupations.
    bls_line_items = bls.loc[bls["Occupation type"].eq("Line item")].copy()
    bls_line_items = bls_line_items.loc[bls_line_items["soc_code"].notna()].copy()

    # Prefer the base .00 O*NET record when detailed sub-occupations share a SOC.
    onet_occupations["base_record"] = (
        onet_occupations["O*NET-SOC Code"].astype("string").str.endswith(".00")
    )
    descriptions = (
        onet_occupations.sort_values("base_record", ascending=False)
        .drop_duplicates("soc_code")
        [["soc_code", "Description"]]
        .rename(columns={"Description": "occupation_description"})
    )

    penetration["task_normalized"] = normalize_task(penetration["task"])
    onet_tasks["task_normalized"] = normalize_task(onet_tasks["Task"])
    penetration_unique = penetration.drop_duplicates("task_normalized")

    task_matches = onet_tasks.merge(
        penetration_unique[["task_normalized", "penetration"]],
        on="task_normalized",
        how="inner",
    )
    # A six-digit SOC can include multiple O*NET sub-occupations. Avoid showing
    # the same task twice within one occupation.
    task_matches = (
        task_matches.sort_values("penetration", ascending=False)
        .drop_duplicates(["soc_code", "task_normalized"])
    )

    task_summary = (
        task_matches.groupby("soc_code", as_index=False)
        .agg(
            average_task_penetration=("penetration", "mean"),
            matched_task_count=("task_normalized", "nunique"),
        )
    )
    top_tasks = (
        task_matches.sort_values(["soc_code", "penetration"], ascending=[True, False])
        .assign(task_rank=lambda frame: frame.groupby("soc_code").cumcount() + 1)
        .loc[lambda frame: frame["task_rank"] <= 5]
        [["soc_code", "task_rank", "Task", "penetration"]]
        .rename(columns={"Task": "task"})
    )

    bls_selected = bls_line_items[
        [
            "soc_code",
            bls_title,
            employment,
            outlook,
            openings,
            wage,
            education,
            related_experience,
            training,
        ]
    ].copy()
    bls_selected = bls_selected.rename(
        columns={
            bls_title: "bls_title",
            employment: "employment_2025_thousands",
            outlook: "employment_change_percent_2025_35",
            openings: "annual_openings_2025_35_thousands",
            wage: "median_annual_wage_2025",
            education: "typical_education",
            related_experience: "related_work_experience",
            training: "on_the_job_training",
        }
    )
    numeric_columns = [
        "employment_2025_thousands",
        "employment_change_percent_2025_35",
        "annual_openings_2025_35_thousands",
        "median_annual_wage_2025",
    ]
    for column in numeric_columns:
        bls_selected[column] = to_number(bls_selected[column])

    occupation_table = (
        jobs[["soc_code", "title", "observed_exposure"]]
        .merge(bls_selected, on="soc_code", how="inner", validate="one_to_one")
        .merge(descriptions, on="soc_code", how="left", validate="one_to_one")
        .merge(task_summary, on="soc_code", how="left", validate="one_to_one")
        .sort_values("soc_code")
    )
    occupation_table.insert(
        1,
        "occupation_group_code",
        occupation_table["soc_code"].str.slice(0, 2),
    )
    dashboard_soc = set(occupation_table["soc_code"])
    top_tasks = top_tasks.loc[top_tasks["soc_code"].isin(dashboard_soc)].copy()

    job_soc = set(jobs["soc_code"].dropna())
    bls_soc = set(bls_line_items["soc_code"].dropna())
    unmatched_jobs = jobs.loc[~jobs["soc_code"].isin(bls_soc), ["soc_code", "title"]]
    penetration_task_keys = set(penetration_unique["task_normalized"].dropna())
    onet_task_keys = set(onet_tasks["task_normalized"].dropna())
    matched_penetration_rows = int(penetration["task_normalized"].isin(onet_task_keys).sum())
    matched_onet_rows = int(onet_tasks["task_normalized"].isin(penetration_task_keys).sum())

    report_lines = [
        "AI Workforce Investment Planner — Phase 1 exploration",
        "",
        "Dataset rows",
        f"- job_exposure.csv: {len(jobs):,}",
        f"- task_penetration.csv: {len(penetration):,}",
        f"- onet_task_statements.csv: {len(onet_tasks):,}",
        f"- onet_occupation_data.csv: {len(onet_occupations):,}",
        f"- BLS Table 1.2: {len(bls):,} total rows; {len(bls_line_items):,} line-item occupations",
        "",
        "Occupation-level SOC match",
        f"- Anthropic occupations: {len(job_soc):,}",
        f"- Matched to BLS line items: {len(job_soc & bls_soc):,} ({pct(len(job_soc & bls_soc), len(job_soc)):.1f}%)",
        f"- Unmatched Anthropic occupations: {len(job_soc - bls_soc):,}",
    ]
    if not unmatched_jobs.empty:
        report_lines.extend(
            f"  - {row.soc_code}: {row.title}" for row in unmatched_jobs.itertuples()
        )
    report_lines.extend(
        [
            "",
            "Task-text match after lowercasing and whitespace cleanup",
            f"- Anthropic task rows matched to O*NET: {matched_penetration_rows:,} of {len(penetration):,} ({pct(matched_penetration_rows, len(penetration)):.1f}%)",
            f"- O*NET task rows matched to Anthropic: {matched_onet_rows:,} of {len(onet_tasks):,} ({pct(matched_onet_rows, len(onet_tasks)):.1f}%)",
            f"- Dashboard occupations with matched task data: {occupation_table['average_task_penetration'].notna().sum():,}",
            "",
            "Generated tables",
            f"- occupation_exploration.csv: {len(occupation_table):,} occupations",
            f"- top_tasks_by_occupation.csv: {len(top_tasks):,} occupation-task rows",
            "",
            "Note: no priority score was calculated because the team has not yet justified its weights.",
        ]
    )

    return occupation_table, top_tasks, "\n".join(report_lines) + "\n"


def main() -> None:
    args = parse_args()
    data = load_data(args.data_dir)
    occupation_table, top_tasks, report = explore(data)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    occupation_table.to_csv(args.output_dir / "occupation_exploration.csv", index=False)
    top_tasks.to_csv(args.output_dir / "top_tasks_by_occupation.csv", index=False)
    (args.output_dir / "exploration_report.txt").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
