"""Prepare canonical occupation/task tables with verified BLS category provenance."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import pandas as pd
from openpyxl import load_workbook

FILES = {
    "jobs": "job_exposure.csv",
    "penetration": "task_penetration.csv",
    "onet_tasks": "onet_task_statements.csv",
    "onet_occupations": "onet_occupation_data.csv",
    "bls": "bls_table_1_2_2025_35.csv",
}
BLS_COLUMNS = {
    "2025 National Employment Matrix title": "bls_title",
    "Employment, 2025": "employment_2025_thousands",
    "Employment change, percent, 2025–35": "employment_change_percent_2025_35",
    "Occupational openings, 2025–35 annual average": "annual_openings_2025_35_thousands",
    "Median annual wage, dollars, 2025": "median_annual_wage_2025",
    "Typical education needed for entry": "typical_education",
    "Work experience in a related occupation": "related_work_experience",
    "Typical on-the-job training needed to attain competency in the occupation": "on_the_job_training",
}
BLS_CODE = "2025 National Employment Matrix code"
NUMERIC_BLS = [
    "employment_2025_thousands", "employment_change_percent_2025_35",
    "annual_openings_2025_35_thousands", "median_annual_wage_2025",
]
WORKBOOK_FILE = "bls_occupation_tables_2025_35.xlsx"
CATEGORY_FIELDS = {
    "Work experience in a related occupation": "related_work_experience",
    "Typical on-the-job training needed to attain competency in the occupation": "on_the_job_training",
}
WORKBOOK_NUMERIC_FIELDS = [
    "Employment, 2025", "Employment, 2035",
    "Employment distribution, percent, 2025", "Employment distribution, percent, 2035",
    "Employment change, numeric, 2025–35", "Employment change, percent, 2025–35",
    "Percent self-employed, 2025", "Occupational openings, 2025–35 annual average",
    "Median annual wage, dollars, 2025",
]


@dataclass
class CleanResult:
    occupations: pd.DataFrame
    tasks: pd.DataFrame
    audit: dict
    master: pd.DataFrame


def require_columns(frame: pd.DataFrame, columns: list[str], name: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{name}: missing columns {missing}")


def normalize_soc(values: pd.Series) -> pd.Series:
    """Accept SOC or O*NET-SOC identifiers, preserving the six-digit code."""
    return values.astype("string").str.strip().str.extract(
        r"^(\d{2}-\d{4})(?:\.\d{2})?$", expand=False
    )


def normalize_task(values: pd.Series) -> pd.Series:
    return values.astype("string").str.lower().str.replace(
        r"\s+", " ", regex=True
    ).str.strip().replace("", pd.NA)


def numeric(values: pd.Series, name: str) -> pd.Series:
    text = values.astype("string").str.strip().str.replace(",", "", regex=False)
    text = text.replace({"": pd.NA, "—": pd.NA, "–": pd.NA, "-": pd.NA})
    result = pd.to_numeric(text, errors="coerce").astype("float64")
    invalid = text.notna() & result.isna()
    if invalid.any():
        raise ValueError(f"{name}: unexpected numeric values {text[invalid].unique().tolist()}")
    if result.isin([float("inf"), float("-inf")]).any():
        raise ValueError(f"{name}: infinite values")
    return result


def unique_keys(frame: pd.DataFrame, keys: list[str], name: str) -> None:
    if frame[keys].isna().any().any():
        raise ValueError(f"{name}: missing or invalid key")
    if frame.duplicated(keys).any():
        raise ValueError(f"{name}: duplicate key after normalization: {keys}")


def verify_bls_workbook(csv_frame: pd.DataFrame, path: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Recover only CSV blanks backed by an explicit workbook None category.

    Require identical codes, every shared numeric value, and all other text.
    Return prepared BLS data, a cell-level recovery ledger, and verification.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}. Download the BLS workbook; see data/README.md.")
    book = load_workbook(path, read_only=True, data_only=False)
    try:
        rows = list(book["Table 1.2"].iter_rows())
        headers = [cell.value for cell in rows[1][:15]]
        if headers != csv_frame.columns.tolist():
            raise ValueError("BLS workbook/CSV headers differ; review the source versions")
        coded = [row for row in rows[2:] if isinstance(row[1].value, str) and row[1].value]
        if any(cell.data_type == "f" for row in coded for cell in row[:15]):
            raise ValueError("Unexpected formula in workbook source data")
        values = [[cell.value for cell in row[:15]] for row in coded]
        excel = pd.DataFrame(values, columns=headers).astype("string").fillna("")
        csv_data = csv_frame.astype("string").fillna("").copy()
        unique_keys(excel, [BLS_CODE], "BLS workbook")
        unique_keys(csv_data, [BLS_CODE], "BLS CSV")
        if set(excel[BLS_CODE]) != set(csv_data[BLS_CODE]):
            raise ValueError("BLS workbook/CSV occupation sets differ")
        excel = excel.set_index(BLS_CODE).reindex(csv_data[BLS_CODE]).reset_index()
        row_by_code = {row[1].value: row[0].row for row in coded}
        numeric_checks = {}
        for field in WORKBOOK_NUMERIC_FIELDS:
            left, right = numeric(csv_data[field], field), numeric(excel[field], field)
            equal = (left.isna() & right.isna()) | (left - right).abs().le(1e-8)
            if not equal.all():
                raise ValueError(f"BLS workbook/CSV numeric mismatch: {field}")
            numeric_checks[field] = 0
        recovered, counts = [], {}
        for field in headers:
            if field in WORKBOOK_NUMERIC_FIELDS:
                continue
            differences = csv_data[field].ne(excel[field])
            permitted = csv_data[field].eq("") & excel[field].eq("None") if field in CATEGORY_FIELDS else pd.Series(False, index=csv_data.index)
            if (differences & ~permitted).any():
                raise ValueError(f"Unexpected BLS workbook/CSV text difference: {field}")
            if field in CATEGORY_FIELDS:
                target = CATEGORY_FIELDS[field]
                csv_data[target + "_csv_raw"] = csv_data[field]
                csv_data[target + "_workbook_raw"] = excel[field]
                csv_data[target + "_source"] = "csv"
                mask = differences & permitted
                for i in csv_data.index[mask]:
                    code = csv_data.loc[i, BLS_CODE]
                    recovered.append({
                        "soc_code": code, "field": target, "csv_original": "",
                        "workbook_original": "None", "clean_value": "None",
                        "workbook_cell": f'{"NO"[list(CATEGORY_FIELDS).index(field)]}{row_by_code[code]}',
                    })
                csv_data.loc[mask, field] = "None"
                csv_data.loc[mask, target + "_source"] = "workbook_verified"
                counts[target] = int(mask.sum())
        # Cross-check the workbook's independent separations/openings table.
        other_rows = list(book["Table 1.10"].values)
        other = pd.DataFrame(
            [r for r in other_rows[2:] if isinstance(r[1], str) and r[1]],
            columns=other_rows[1],
        ).astype("string").fillna("")
        unique_keys(other, [BLS_CODE], "BLS Table 1.10")
        if set(other[BLS_CODE]) != set(excel[BLS_CODE]):
            raise ValueError("BLS Table 1.10 occupation sets differ")
        other = other.set_index(BLS_CODE).reindex(excel[BLS_CODE]).reset_index()
        for field in [WORKBOOK_NUMERIC_FIELDS[i] for i in [0, 1, 4, 5, 7]]:
            left, right = numeric(excel[field], field), numeric(other[field], field)
            if not ((left.isna() & right.isna()) | (left - right).abs().le(1e-8)).all():
                raise ValueError(f"BLS Table 1.10 cross-check failed: {field}")
        verification = {
            "status": "verified", "coded_rows": len(excel),
            "numeric_mismatches": numeric_checks, "unexpected_text_mismatches": 0,
            "recovered_categories": counts, "table_1_10_shared_measure_mismatches": 0,
        }
        ledger = pd.DataFrame(recovered, columns=[
            "soc_code", "field", "csv_original", "workbook_original", "clean_value", "workbook_cell",
        ])
        return csv_data, ledger, verification
    finally:
        book.close()


def load_sources(data_dir: Path) -> tuple[dict[str, pd.DataFrame], dict, pd.DataFrame]:
    sources, metadata = {}, {}
    for key, filename in FILES.items():
        path = Path(data_dir) / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing {path}. See data/README.md.")
        sources[key] = pd.read_csv(path, dtype="string", keep_default_na=False, low_memory=False)
        metadata[filename] = {
            "rows": len(sources[key]), "columns": list(sources[key].columns),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size_bytes": path.stat().st_size,
        }
    workbook = Path(data_dir) / WORKBOOK_FILE
    sources["bls"], ledger, verification = verify_bls_workbook(sources["bls"], workbook)
    metadata[WORKBOOK_FILE] = {
        "sha256": hashlib.sha256(workbook.read_bytes()).hexdigest(),
        "size_bytes": workbook.stat().st_size, "verification": verification,
        "source_url": "https://www.bls.gov/emp/ind-occ-matrix/occupation.xlsx",
    }
    return sources, metadata, ledger


def clean_sources(sources: dict[str, pd.DataFrame]) -> CleanResult:
    """Return clean tables and observed diagnostics, without writing files."""
    jobs = sources["jobs"].copy()
    penetration = sources["penetration"].copy()
    ot = sources["onet_tasks"].copy()
    descriptions = sources["onet_occupations"].copy()
    bls = sources["bls"].copy()
    require_columns(jobs, ["occ_code", "title", "observed_exposure"], "jobs")
    require_columns(penetration, ["task", "penetration"], "penetration")
    require_columns(ot, ["O*NET-SOC Code", "Task", "Task ID"], "onet_tasks")
    require_columns(descriptions, ["O*NET-SOC Code", "Description"], "onet_occupations")
    require_columns(bls, [BLS_CODE, "Occupation type", *BLS_COLUMNS], "bls")
    raw_counts = {key: len(frame) for key, frame in sources.items()}

    jobs = jobs.drop_duplicates().copy()
    jobs["soc_code"] = normalize_soc(jobs["occ_code"])
    unique_keys(jobs, ["soc_code"], "jobs")
    jobs["title"] = jobs["title"].astype("string").str.strip()
    jobs["observed_exposure"] = numeric(jobs["observed_exposure"], "observed_exposure")
    penetration["penetration"] = numeric(penetration["penetration"], "penetration")
    for frame, column in [(jobs, "observed_exposure"), (penetration, "penetration")]:
        if ((frame[column] < 0) | (frame[column] > 1)).any():
            raise ValueError(f"{column}: values must be fractions between 0 and 1")

    penetration["task_normalized"] = normalize_task(penetration["task"])
    if penetration["task_normalized"].isna().any():
        raise ValueError("penetration: blank task text")
    if penetration.groupby("task_normalized")["penetration"].nunique(dropna=False).gt(1).any():
        raise ValueError("Conflicting penetration values for the same normalized task")
    exact_task_duplicates = int(sources["penetration"].duplicated().sum())
    penetration = penetration.sort_values("task", kind="stable").drop_duplicates("task_normalized")

    ot["soc_code"] = normalize_soc(ot["O*NET-SOC Code"])
    ot["task_normalized"] = normalize_task(ot["Task"])
    if ot[["soc_code", "task_normalized"]].isna().any().any():
        raise ValueError("onet_tasks: invalid occupation code or blank task text")
    total_tasks = ot.groupby("soc_code")["task_normalized"].nunique().rename("total_task_count")
    task_rows = ot.merge(
        penetration[["task_normalized", "penetration"]], on="task_normalized",
        how="inner", validate="many_to_one",
    )
    task_rows = task_rows.sort_values(
        ["soc_code", "task_normalized", "O*NET-SOC Code", "Task ID"], kind="stable"
    ).drop_duplicates(["soc_code", "task_normalized"])
    # Blank penetration is unavailable, while a supplied zero remains a valid match.
    scored_tasks = task_rows.loc[task_rows["penetration"].notna()].copy()
    summary = scored_tasks.groupby("soc_code").agg(
        average_task_penetration=("penetration", "mean"),
        matched_task_count=("task_normalized", "nunique"),
    )

    descriptions["soc_code"] = normalize_soc(descriptions["O*NET-SOC Code"])
    if descriptions["soc_code"].isna().any():
        raise ValueError("onet_occupations: invalid occupation code")
    descriptions["base_record"] = descriptions["O*NET-SOC Code"].str.endswith(".00")
    descriptions = descriptions.sort_values(
        ["soc_code", "base_record", "O*NET-SOC Code"], ascending=[True, False, True], kind="stable"
    ).drop_duplicates("soc_code")
    descriptions = descriptions[["soc_code", "Description", "O*NET-SOC Code"]].rename(columns={
        "Description": "occupation_description", "O*NET-SOC Code": "description_source_onet_code",
    })

    group_rows = bls.loc[
        bls["Occupation type"].str.strip().eq("Summary")
        & bls[BLS_CODE].str.strip().str.fullmatch(r"\d{2}-0000")
    ].copy()
    group_names = dict(zip(
        group_rows[BLS_CODE].str.strip().str[:2],
        group_rows["2025 National Employment Matrix title"].str.strip(),
    ))
    detailed = bls.loc[bls["Occupation type"].str.strip().eq("Line item")].drop_duplicates().copy()
    detailed["soc_code"] = normalize_soc(detailed[BLS_CODE])
    unique_keys(detailed, ["soc_code"], "BLS line items")
    provenance = [field + suffix for field in CATEGORY_FIELDS.values()
                  for suffix in ["_csv_raw", "_workbook_raw", "_source"]
                  if field + suffix in detailed]
    detailed = detailed[["soc_code", *BLS_COLUMNS, *provenance]].rename(columns=BLS_COLUMNS)
    for column in NUMERIC_BLS:
        detailed[column] = numeric(detailed[column], column)
        if column != "employment_change_percent_2025_35" and detailed[column].lt(0).any():
            raise ValueError(f"{column}: negative value")
    for column in ["bls_title", "typical_education", "related_work_experience", "on_the_job_training"]:
        detailed[column] = detailed[column].astype("string").str.strip().replace({"": pd.NA, "—": pd.NA})

    occupation_table = jobs[["soc_code", "title", "observed_exposure"]].merge(
        detailed, on="soc_code", how="left", validate="one_to_one", indicator="_bls_join"
    ).merge(descriptions, on="soc_code", how="left", validate="one_to_one").merge(
        total_tasks, on="soc_code", how="left", validate="one_to_one"
    ).merge(summary, on="soc_code", how="left", validate="one_to_one")
    for column in ["matched_task_count", "total_task_count"]:
        occupation_table[column] = occupation_table[column].fillna(0).astype("int64")
    occupation_table["task_match_rate"] = occupation_table["matched_task_count"] / occupation_table[
        "total_task_count"
    ].replace(0, float("nan"))
    occupation_table["occupation_group_code"] = occupation_table["soc_code"].str[:2]
    occupation_table["occupation_group_name"] = occupation_table["occupation_group_code"].map(group_names)
    occupation_table["employment_2025"] = occupation_table["employment_2025_thousands"] * 1000
    occupation_table["annual_openings_2025_35"] = occupation_table["annual_openings_2025_35_thousands"] * 1000
    growth = occupation_table["employment_change_percent_2025_35"]
    occupation_table["labor_market_outlook"] = "Unknown"
    occupation_table.loc[growth.gt(0), "labor_market_outlook"] = "Growing"
    occupation_table.loc[growth.eq(0), "labor_market_outlook"] = "Stable"
    occupation_table.loc[growth.lt(0), "labor_market_outlook"] = "Declining"
    occupation_table = occupation_table.sort_values("soc_code", kind="stable").reset_index(drop=True)
    unique_keys(occupation_table, ["soc_code"], "clean occupations")
    occupation_table["bls_match_status"] = occupation_table["_bls_join"].eq("both").map({
        True: "matched", False: "unmatched",
    })
    master = occupation_table.drop(columns="_bls_join").copy()
    occupation_table = master.loc[master["bls_match_status"].eq("matched")].reset_index(drop=True).copy()

    tasks = scored_tasks.loc[scored_tasks["soc_code"].isin(occupation_table["soc_code"]), [
        "soc_code", "Task", "task_normalized", "penetration",
    ]].rename(columns={"Task": "task"})
    tasks = tasks.sort_values(
        ["soc_code", "penetration", "task_normalized"], ascending=[True, False, True], kind="stable"
    ).reset_index(drop=True)
    unique_keys(tasks, ["soc_code", "task_normalized"], "clean task matches")
    unmatched = jobs.loc[~jobs["soc_code"].isin(detailed["soc_code"]), ["soc_code", "title"]]
    audit = {
        "status": "Source reconciliation verified; merge to main remains pending",
        "input_rows": raw_counts,
        "bls_line_item_rows": len(detailed), "bls_summary_rows_excluded": len(bls) - len(detailed),
        "task_exact_duplicate_rows": exact_task_duplicates,
        "task_normalized_duplicate_rows_removed": raw_counts["penetration"] - len(penetration),
        "unique_penetration_task_keys": len(penetration),
        "penetration_task_keys_matched_to_onet": int(penetration["task_normalized"].isin(ot["task_normalized"]).sum()),
        "onet_task_rows_matched_to_penetration": int(ot["task_normalized"].isin(penetration["task_normalized"]).sum()),
        "occupation_rows": len(occupation_table), "occupation_master_rows": len(master),
        "occupation_task_rows": len(tasks),
        "all_onet_scored_soc_task_pairs": len(scored_tasks),
        "metric_precision": "Full calculation precision is retained; round only for display",
        "recovered_categories_in_analysis": {
            field: int(occupation_table[field + "_source"].eq("workbook_verified").sum())
            for field in CATEGORY_FIELDS.values() if field + "_source" in occupation_table
        },
        "unmatched_ai_occupations": unmatched.to_dict(orient="records"),
        "missing_output_values": {c: int(n) for c, n in occupation_table.isna().sum().items() if n},
        "source_release_and_observation_period": "Not supplied. Confirm from original source documentation.",
    }
    return CleanResult(occupation_table, tasks, audit, master)
