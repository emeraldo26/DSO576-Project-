"""Pure reusable analysis functions for the planned dashboard."""
from __future__ import annotations

from pathlib import Path
from collections.abc import Iterable
import pandas as pd
from .cleaning import require_columns, unique_keys

OUTLOOKS = {"Growing", "Stable", "Declining", "Unknown"}
SORT_METRICS = {
    "observed_exposure", "average_task_penetration", "employment_2025",
    "employment_change_percent_2025_35", "median_annual_wage_2025",
}


def load_clean_data(clean_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and validate the two canonical tables once in the UI's data layer."""
    clean_dir = Path(clean_dir)
    occupations = pd.read_csv(
        clean_dir / "occupation_clean_merged.csv",
        dtype={"soc_code": "string", "occupation_group_code": "string"},
        keep_default_na=False, na_values=[""],
    )
    tasks = pd.read_csv(
        clean_dir / "occupation_task_matches.csv", dtype={"soc_code": "string"},
        keep_default_na=False, na_values=[""],
    )
    require_columns(occupations, [
        "soc_code", "title", "occupation_group_code", "occupation_group_name",
        "observed_exposure", "average_task_penetration", "employment_2025",
        "employment_change_percent_2025_35", "median_annual_wage_2025", "labor_market_outlook",
    ], "clean occupations")
    require_columns(tasks, ["soc_code", "task", "task_normalized", "penetration"], "clean tasks")
    unique_keys(occupations, ["soc_code"], "clean occupations")
    unique_keys(tasks, ["soc_code", "task_normalized"], "clean tasks")
    if not tasks["soc_code"].isin(occupations["soc_code"]).all():
        raise ValueError("Clean tasks reference an occupation outside the clean occupation table")
    return occupations, tasks


def filter_occupations(
    occupations: pd.DataFrame, *, groups: Iterable[str] | None = None,
    outlooks: Iterable[str] | None = None, employment_min: float | None = None,
    employment_max: float | None = None, exposure_min: float | None = None,
    exposure_max: float | None = None, query: str = "",
) -> pd.DataFrame:
    """Apply filters together. Exposure bounds are 0–1; employment is persons.

    None means no restriction. An empty group/outlook iterable selects no rows.
    A range excludes rows missing its numeric value. Inputs remain unchanged.
    """
    for low, high, name in [
        (employment_min, employment_max, "employment"),
        (exposure_min, exposure_max, "exposure"),
    ]:
        if low is not None and high is not None and low > high:
            raise ValueError(f"{name}: minimum exceeds maximum")
        if any(v is not None and (not pd.notna(v) or v < 0 or v == float("inf")) for v in (low, high)):
            raise ValueError(f"{name}: bounds must be finite and nonnegative")
    if any(v is not None and v > 1 for v in (exposure_min, exposure_max)):
        raise ValueError("Exposure bounds must be fractions between 0 and 1")
    result = occupations.copy()
    if groups is not None:
        result = result.loc[result["occupation_group_code"].isin(list(groups))]
    if outlooks is not None:
        selected = set(outlooks)
        if selected - OUTLOOKS:
            raise ValueError(f"Unknown outlook categories: {selected - OUTLOOKS}")
        result = result.loc[result["labor_market_outlook"].isin(selected)]
    for column, low, high in [
        ("employment_2025", employment_min, employment_max),
        ("observed_exposure", exposure_min, exposure_max),
    ]:
        if low is not None:
            result = result.loc[result[column].ge(low)]
        if high is not None:
            result = result.loc[result[column].le(high)]
    if query.strip():
        query = query.strip()
        mask = result["title"].str.contains(query, case=False, regex=False, na=False)
        mask |= result["soc_code"].str.contains(query, case=False, regex=False, na=False)
        result = result.loc[mask]
    return result.reset_index(drop=True)


def _number_or_none(value):
    return None if pd.isna(value) else float(value)


def summary_metrics(occupations: pd.DataFrame) -> dict:
    """Aggregate the already-filtered occupation table, without double counting.

    Mean exposure treats every observed occupation equally. It is not a share
    of workers using AI. Employment describes only included occupations.
    """
    exposure = occupations["observed_exposure"]
    return {
        "occupation_count": int(len(occupations)),
        "employment_2025": _number_or_none(occupations["employment_2025"].sum(min_count=1)),
        "employment_value_count": int(occupations["employment_2025"].notna().sum()),
        "mean_observed_exposure": _number_or_none(exposure.mean()),
        "exposure_value_count": int(exposure.notna().sum()),
        "declining_occupation_count": int(occupations["labor_market_outlook"].eq("Declining").sum()),
        "unknown_outlook_count": int(occupations["labor_market_outlook"].eq("Unknown").sum()),
    }


def group_summary(occupations: pd.DataFrame) -> pd.DataFrame:
    """Return counts, included employment, and mean exposure by SOC major group."""
    frame = occupations.copy()
    frame["declining"] = frame["labor_market_outlook"].eq("Declining").astype(int)
    return frame.groupby(
        ["occupation_group_code", "occupation_group_name"], as_index=False, dropna=False
    ).agg(
        occupation_count=("soc_code", "size"),
        employment_2025=("employment_2025", lambda v: v.sum(min_count=1)),
        mean_observed_exposure=("observed_exposure", "mean"),
        declining_occupation_count=("declining", "sum"),
    ).sort_values("occupation_group_code", kind="stable").reset_index(drop=True)


def comparison_data(occupations: pd.DataFrame) -> pd.DataFrame:
    """Return scatterplot values. Wage availability does not gate chart inclusion."""
    columns = ["soc_code", "title", "occupation_group_name", "observed_exposure",
               "employment_change_percent_2025_35", "employment_2025",
               "labor_market_outlook", "median_annual_wage_2025"]
    frame = occupations[columns].dropna(subset=[
        "observed_exposure", "employment_change_percent_2025_35", "employment_2025",
    ]).copy()
    frame = frame.loc[frame["employment_2025"].gt(0)]
    frame["observed_exposure_percent"] = frame["observed_exposure"] * 100
    return frame.reset_index(drop=True)


def rank_occupations(
    occupations: pd.DataFrame, metric: str = "observed_exposure", *, ascending: bool = False,
) -> pd.DataFrame:
    """Sort by the user's chosen measure, then SOC code; missing values come last."""
    if metric not in SORT_METRICS:
        raise ValueError(f"Unsupported sort metric: {metric}")
    frame = occupations.sort_values(
        [metric, "soc_code"], ascending=[ascending, True], na_position="last", kind="stable"
    ).reset_index(drop=True).drop(columns="display_rank", errors="ignore").copy()
    frame.insert(0, "display_rank", range(1, len(frame) + 1))
    return frame


def top_tasks(tasks: pd.DataFrame, soc_code: str, limit: int = 5) -> pd.DataFrame:
    """Choose the highest penetration tasks, including genuine zero values."""
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("Task limit must be a positive integer")
    frame = tasks.loc[tasks["soc_code"].eq(soc_code)].sort_values(
        ["penetration", "task_normalized"], ascending=[False, True], kind="stable"
    ).head(limit).reset_index(drop=True).copy()
    frame.insert(0, "task_rank", range(1, len(frame) + 1))
    return frame


def occupation_details(occupations: pd.DataFrame, tasks: pd.DataFrame, soc_code: str) -> dict:
    """Return an occupation record plus up to five tasks as a reusable dataframe."""
    rows = occupations.loc[occupations["soc_code"].eq(soc_code)]
    if len(rows) != 1:
        raise KeyError(f"Expected one occupation for {soc_code}; found {len(rows)}")
    record = {}
    for key, value in rows.iloc[0].to_dict().items():
        if pd.isna(value):
            record[key] = None
        else:
            record[key] = value.item() if hasattr(value, "item") else value
    return {"occupation": record, "top_tasks": top_tasks(tasks, soc_code)}


def shortlist_data(
    occupations: pd.DataFrame, soc_codes: Iterable[str], metric: str = "observed_exposure", *,
    ascending: bool = False,
) -> pd.DataFrame:
    """Select saved SOC identifiers from the full dataset, including hidden rows."""
    codes = set(soc_codes)
    unknown = codes - set(occupations["soc_code"])
    if unknown:
        raise KeyError(f"Unknown shortlist occupation codes: {sorted(unknown)}")
    return rank_occupations(
        occupations.loc[occupations["soc_code"].isin(codes)], metric, ascending=ascending,
    )
