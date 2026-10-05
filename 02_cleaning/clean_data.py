"""Reproduce Chang's occupation/task cleaning outputs from the five raw CSVs.

Run from the repository root: python code/cleaning_chang/clean_data.py
The script refuses changed source hashes and pre-existing output files. See README.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "job_exposure": ("job_exposure.csv", "4f0a3adf5feeb2ec5f5d02ab18cc5e851a2a4b8470bde84c0c9335017be12d68"),
    "task_penetration": ("task_penetration.csv", "85bee872db1d55d3e9a7f4e89da5ae4a5d59aa8ec875d728fbf4b7d820984616"),
    "onet_task_statements": ("onet_task_statements.csv", "4568e14d8db6f05551ad37e056e909b13ebae4a26bcb5ff915bb5f281d582c57"),
    "onet_occupation_data": ("onet_occupation_data.csv", "a09eae1d6609686e44e05b7290993a1c8b523d8ca224bc0eedc194c855c3ee02"),
    "bls": ("bls_table_1_2_2025_35.csv", "460af8e1eaf961732bc29b56cc92b25c4d6ef85c587b8b566f834beaebededa2"),
}

BLS_NUMERIC = {
    "Employment, 2025": "employment_2025_thousands",
    "Employment, 2035": "employment_2035_thousands",
    "Employment distribution, percent, 2025": "employment_distribution_percent_2025",
    "Employment distribution, percent, 2035": "employment_distribution_percent_2035",
    "Employment change, numeric, 2025–35": "employment_change_2025_35_thousands",
    "Employment change, percent, 2025–35": "employment_change_percent_2025_35",
    "Percent self-employed, 2025": "self_employed_percent_2025",
    "Occupational openings, 2025–35 annual average": "annual_openings_2025_35_thousands",
    "Median annual wage, dollars, 2025": "median_annual_wage_2025_dollars",
}
BLS_CATEGORICAL = {
    "Typical education needed for entry": "typical_education",
    "Work experience in a related occupation": "related_work_experience",
    "Typical on-the-job training needed to attain competency in the occupation": "on_the_job_training",
}
PRESS_KEY = (
    "write interesting and effective press releases, prepare information for media kits, "
    "and develop and maintain company internet or intranet web pages."
)
ADVISERS_KEY = "act as advisers to student organizations."


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "cleaning_chang" / "review_01")
    parser.add_argument("--sample-file", type=Path, default=ROOT / "code" / "cleaning_chang" / "cleaned_sample_review_01.csv")
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_sources(data_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    frames = {}
    hashes = {}
    for key, (filename, expected_hash) in SOURCES.items():
        path = data_dir / filename
        require(path.is_file(), f"Missing raw source: {path}")
        actual_hash = hash_file(path)
        require(actual_hash == expected_hash, f"Changed source hash for {filename}: {actual_hash}; review before cleaning")
        hashes[filename] = actual_hash
        # Preserve every original cell as text; create typed fields separately.
        frames[key] = pd.read_csv(path, dtype="string", keep_default_na=False, low_memory=False)
        frames[key].insert(0, "source_row", range(2, len(frames[key]) + 2))
    return frames, hashes


def check_columns(frame: pd.DataFrame, expected: set[str], name: str) -> None:
    actual = set(frame.columns) - {"source_row"}
    require(actual == expected, f"Column schema changed for {name}: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")


def soc_key(values: pd.Series, full_onet: bool = False) -> pd.Series:
    pattern = r"\d{2}-\d{4}\.\d{2}" if full_onet else r"\d{2}-\d{4}"
    require(bool(values.str.fullmatch(pattern).all()), f"Invalid SOC code examples: {values.loc[~values.str.fullmatch(pattern)].head().tolist()}")
    return values.str.slice(0, 7)


def task_key(values: pd.Series) -> pd.Series:
    result = values.str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    require(bool(result.ne("").all()), "A task normalizes to an empty key")
    return result


def parsed_number(values: pd.Series, label: str, allowed_markers: tuple[str, ...] = ()) -> pd.Series:
    compact = values.str.replace(",", "", regex=False).str.strip()
    marker = compact.isin(allowed_markers)
    result = pd.to_numeric(compact.mask(marker), errors="coerce")
    bad = result.isna() & ~marker
    require(not bool(bad.any()), f"Unexpected nonnumeric {label}: {values.loc[bad].head().tolist()}")
    return result


def profile(frame: pd.DataFrame, numeric: list[str] | None = None, categories: list[str] | None = None, keys: list[str] | None = None) -> dict:
    numeric = numeric or []
    categories = categories or []
    keys = keys or []
    result = {
        "rows": len(frame),
        "missing_by_column": {c: int(frame[c].isna().sum() + frame[c].eq("").sum()) for c in frame.columns},
        "exact_duplicate_rows_excluding_source_row": int(frame.drop(columns="source_row", errors="ignore").duplicated().sum()),
        "duplicate_keys": {"+".join(cols): int(frame.duplicated(cols).sum()) for cols in ([keys] if keys else [])},
        "numeric": {}, "categories": {},
    }
    for col in numeric:
        series = pd.to_numeric(frame[col], errors="coerce")
        result["numeric"][col] = {
            "nonmissing": int(series.notna().sum()),
            "min": None if series.notna().sum() == 0 else float(series.min()),
            "max": None if series.notna().sum() == 0 else float(series.max()),
            "negative": int(series.lt(0).sum()), "zero": int(series.eq(0).sum()),
        }
    for col in categories:
        result["categories"][col] = {str(k): int(v) for k, v in frame[col].fillna("<missing>").replace("", "<missing>").value_counts(dropna=False).items()}
    return result


def stage_log(report: dict, name: str, frame: pd.DataFrame, *, numeric=None, categories=None, keys=None, note: str = "") -> None:
    report["stages"].append({"stage": name, "profile": profile(frame, numeric, categories, keys), "note": note})
    item = report["stages"][-1]
    print(f"{name}: rows={item['profile']['rows']:,}; missing={sum(item['profile']['missing_by_column'].values())}; duplicate_rows={item['profile']['exact_duplicate_rows_excluding_source_row']}; {note}")
    if item["profile"]["numeric"]:
        print("  numeric:", json.dumps(item["profile"]["numeric"], ensure_ascii=False))
    if item["profile"]["categories"]:
        print("  categories:", json.dumps(item["profile"]["categories"], ensure_ascii=False))


def conversion_evidence(raw: pd.DataFrame, cleaned: pd.DataFrame, mapping: dict[str, str]) -> dict[str, dict[str, int]]:
    """Reconcile source blanks/dashes with missing values in derived fields."""
    evidence = {}
    for raw_col, derived_col in mapping.items():
        before = raw[raw_col].astype("string")
        after = cleaned[derived_col]
        blank = int(before.str.strip().eq("").sum())
        dash = int(before.str.strip().eq("—").sum())
        missing = int(after.isna().sum())
        require(missing == blank + dash, f"Missing/sentinel conversion mismatch: {raw_col}: {blank} blanks + {dash} dashes versus {missing} derived missing")
        require(bool(raw[raw_col].eq(cleaned[raw_col]).all()), f"Source values changed: {raw_col}")
        evidence[raw_col] = {
            "source_blank": blank, "source_em_dash": dash,
            "source_missing_or_sentinel": blank + dash,
            "derived_missing": missing,
            "derived_nonmissing": int(after.notna().sum()),
        }
    return evidence


def clean_sources(raw: dict[str, pd.DataFrame], report: dict) -> dict[str, pd.DataFrame]:
    expected = {
        "job_exposure": {"occ_code", "title", "observed_exposure"},
        "task_penetration": {"task", "penetration"},
        "onet_occupation_data": {"O*NET-SOC Code", "Title", "Description"},
        "onet_task_statements": {"O*NET-SOC Code", "Title", "Task ID", "Task", "Task Type", "Incumbents Responding", "Date", "Domain Source"},
        "bls": {"2025 National Employment Matrix title", "2025 National Employment Matrix code", "Occupation type", *BLS_NUMERIC, *BLS_CATEGORICAL},
    }
    for name, frame in raw.items():
        check_columns(frame, expected[name], name)
        stage_log(report, f"raw_{name}", frame, categories=["Occupation type"] if name == "bls" else [], note="read without changing source values")

    jobs = raw["job_exposure"].copy()
    jobs["soc_code"] = soc_key(jobs["occ_code"])
    jobs["observed_exposure_value"] = parsed_number(jobs["observed_exposure"], "observed_exposure")
    require(jobs["soc_code"].is_unique, "Exposure SOC keys are not unique")
    require(bool(jobs["observed_exposure_value"].between(0, 1).all()), "Exposure outside 0–1")
    stage_log(report, "clean_job_exposure", jobs, numeric=["observed_exposure_value"], keys=["soc_code"], note="added six-digit key and numeric exposure; zero source rows removed")

    penetration = raw["task_penetration"].copy()
    penetration["task_normalized"] = task_key(penetration["task"])
    penetration["penetration_value"] = parsed_number(penetration["penetration"], "penetration")
    require(bool(penetration["penetration_value"].between(0, 1).all()), "Task penetration outside 0–1")
    conflicts = penetration.groupby("task_normalized")["penetration_value"].nunique(dropna=False)
    require(not bool(conflicts.gt(1).any()), f"Conflicting task penetration keys: {conflicts[conflicts.gt(1)].index[:5].tolist()}")
    stage_log(report, "clean_task_penetration", penetration, numeric=["penetration_value"], keys=["task_normalized"], note=f"source rows retained; {int(penetration.duplicated('task_normalized').sum())} repeated normalized-key rows flagged")

    occupations = raw["onet_occupation_data"].copy()
    occupations["soc_code"] = soc_key(occupations["O*NET-SOC Code"], True)
    occupations["is_base_record"] = occupations["O*NET-SOC Code"].str.endswith(".00")
    require(occupations["O*NET-SOC Code"].is_unique, "Duplicate full O*NET occupation codes")
    bases = occupations.groupby("soc_code")["is_base_record"].sum()
    require(bool(bases.eq(1).all()), f"Missing/ambiguous .00 records: {bases[bases.ne(1)].head().to_dict()}")
    stage_log(report, "clean_onet_occupations", occupations, categories=["is_base_record"], keys=["O*NET-SOC Code"], note="all child occupation records preserved")

    tasks = raw["onet_task_statements"].copy()
    tasks["soc_code"] = soc_key(tasks["O*NET-SOC Code"], True)
    tasks["task_normalized"] = task_key(tasks["Task"])
    require(tasks["Task ID"].is_unique, "Task ID is not unique")
    require(bool(tasks["Date"].str.fullmatch(r"\d{2}/\d{4}").all()), "Unexpected O*NET task date format")
    tasks["incumbents_responding_count"] = parsed_number(tasks["Incumbents Responding"], "Incumbents Responding", ("",))
    tasks["task_type_clean"] = tasks["Task Type"].replace("", pd.NA)
    require(bool(tasks["incumbents_responding_count"].dropna().ge(0).all()), "Negative incumbent respondent count")
    require(set(tasks["O*NET-SOC Code"]).issubset(set(occupations["O*NET-SOC Code"])), "Task code missing from O*NET occupation file")
    title_pairs = tasks[["O*NET-SOC Code", "Title"]].drop_duplicates().merge(occupations[["O*NET-SOC Code", "Title"]], on="O*NET-SOC Code", suffixes=("_task", "_occupation"), validate="one_to_one")
    require(bool(title_pairs["Title_task"].eq(title_pairs["Title_occupation"]).all()), "O*NET task and occupation titles conflict")
    stage_log(report, "clean_onet_tasks", tasks, numeric=["incumbents_responding_count"], categories=["task_type_clean", "Domain Source"], keys=["Task ID"], note="all .00 and child task statements preserved")
    report["onet_missing_conversion"] = conversion_evidence(raw["onet_task_statements"], tasks, {
        "Task Type": "task_type_clean", "Incumbents Responding": "incumbents_responding_count",
    })
    print("O*NET missing conversion:", json.dumps(report["onet_missing_conversion"], ensure_ascii=False))

    bls = raw["bls"].copy()
    bls["soc_code"] = soc_key(bls["2025 National Employment Matrix code"])
    require(bls["2025 National Employment Matrix code"].is_unique, "Duplicate BLS codes")
    require(set(bls["Occupation type"]) == {"Summary", "Line item"}, "Unexpected BLS occupation type")
    for raw_col, typed_col in BLS_NUMERIC.items():
        markers = ("—",) if raw_col in {"Percent self-employed, 2025", "Median annual wage, dollars, 2025"} else ()
        bls[typed_col] = parsed_number(bls[raw_col], raw_col, markers)
    for raw_col, typed_col in BLS_CATEGORICAL.items():
        bls[typed_col] = bls[raw_col].replace({"": pd.NA, "—": pd.NA})
    for col in ["employment_2025_thousands", "employment_2035_thousands", "annual_openings_2025_35_thousands", "median_annual_wage_2025_dollars"]:
        require(bool(bls[col].dropna().ge(0).all()), f"Unexpected negative BLS {col}")
    for col in ["employment_distribution_percent_2025", "employment_distribution_percent_2035", "self_employed_percent_2025"]:
        require(bool(bls[col].dropna().between(0, 100).all()), f"BLS percent outside 0–100: {col}")
    bls["negative_projected_change_flag"] = bls["employment_change_percent_2025_35"].lt(0)
    stage_log(report, "clean_bls", bls, numeric=list(BLS_NUMERIC.values()), categories=["Occupation type", *BLS_CATEGORICAL.values(), "negative_projected_change_flag"], keys=["soc_code"], note="raw units retained; missing symbols mapped only in derived fields; negative outlook flagged")
    report["bls_missing_conversion"] = conversion_evidence(raw["bls"], bls, {
        **BLS_NUMERIC, **BLS_CATEGORICAL,
    })
    print("BLS missing conversion:", json.dumps(report["bls_missing_conversion"], ensure_ascii=False))
    return {"job_exposure": jobs, "task_penetration": penetration, "onet_occupation_data": occupations, "onet_task_statements": tasks, "bls": bls}


def build_outputs(clean: dict[str, pd.DataFrame], report: dict) -> dict[str, pd.DataFrame]:
    jobs, penetration, occupations, tasks, bls = (clean[k] for k in ["job_exposure", "task_penetration", "onet_occupation_data", "onet_task_statements", "bls"])
    bls_line = bls.loc[bls["Occupation type"].eq("Line item")].copy()
    bls_summary = bls.loc[bls["Occupation type"].eq("Summary")].copy()
    require(bls_line["soc_code"].is_unique, "BLS line-item join key is not unique")
    stage_log(report, "bls_line_items", bls_line, numeric=["employment_2025_thousands", "employment_change_percent_2025_35", "annual_openings_2025_35_thousands", "median_annual_wage_2025_dollars"], categories=[*BLS_CATEGORICAL.values()], keys=["soc_code"], note=f"separate grain; {len(bls_summary)} Summary rows retained separately")
    stage_log(report, "bls_summaries", bls_summary, keys=["soc_code"], note="not joined to occupation-level data")

    base = occupations.loc[occupations["is_base_record"], ["soc_code", "O*NET-SOC Code", "Title", "Description"]].rename(columns={"O*NET-SOC Code": "base_onet_soc_code", "Title": "onet_base_title", "Description": "occupation_description"})
    require(base["soc_code"].is_unique, "Base descriptions not one per SOC")
    stage_log(report, "onet_base_descriptions", base, keys=["soc_code"], note=f"{len(occupations)-len(base)} child descriptions remain in source-grain output")

    lookup = penetration.sort_values(["task_normalized", "source_row"], kind="stable").drop_duplicates("task_normalized")[["task_normalized", "penetration_value"]].copy()
    require(lookup["task_normalized"].is_unique, "Penetration lookup key not unique")
    stage_log(report, "penetration_lookup", lookup, numeric=["penetration_value"], keys=["task_normalized"], note=f"{len(penetration)-len(lookup)} agreeing duplicate source rows collapsed only for lookup")

    task_join = tasks.merge(lookup, on="task_normalized", how="left", validate="many_to_one", indicator="task_match_status")
    require(len(task_join) == len(tasks), "Task lookup multiplied or lost source rows")
    task_join["task_match_status"] = task_join["task_match_status"].map({"both": "matched", "left_only": "unmatched"}).astype("string")
    stage_log(report, "task_penetration_join", task_join, numeric=["penetration_value"], categories=["task_match_status"], keys=["Task ID"], note="many-to-one left join; unmatched task statements retained")

    matched = task_join.loc[task_join["task_match_status"].eq("matched")].copy()
    matched = matched.sort_values(["soc_code", "task_normalized", "Task ID"], key=lambda s: pd.to_numeric(s) if s.name == "Task ID" else s, kind="stable")
    associations = matched.drop_duplicates(["soc_code", "task_normalized"]).copy()
    contributions = matched.groupby(["soc_code", "task_normalized"], sort=False).agg(
        contributing_task_ids=("Task ID", lambda s: ";".join(s.astype(str))),
        contributing_onet_codes=("O*NET-SOC Code", lambda s: ";".join(dict.fromkeys(s.astype(str)))),
        contributing_statement_count=("Task ID", "size"),
    ).reset_index()
    associations = associations[["soc_code", "task_normalized", "Task", "Task ID", "O*NET-SOC Code", "penetration_value"]].rename(columns={"Task": "task_text", "Task ID": "representative_task_id", "O*NET-SOC Code": "representative_onet_soc_code"}).merge(contributions, on=["soc_code", "task_normalized"], validate="one_to_one")
    require(not bool(associations.duplicated(["soc_code", "task_normalized"]).any()), "Duplicate derived occupation-task association")
    stage_log(report, "occupation_tasks", associations, numeric=["penetration_value", "contributing_statement_count"], keys=["soc_code", "task_normalized"], note=f"{len(matched)-len(associations)} repeated within-SOC associations collapsed; each source task remains in audit output")

    summary = associations.groupby("soc_code", as_index=False).agg(
        average_task_penetration=("penetration_value", "mean"),
        matched_task_count=("penetration_value", "count"),
    )
    stage_log(report, "task_summary", summary, numeric=["average_task_penetration", "matched_task_count"], keys=["soc_code"], note="average denominator is matched_task_count, not all O*NET statements")
    top_tasks = associations.sort_values(["soc_code", "penetration_value", "task_normalized", "representative_task_id"], ascending=[True, False, True, True], kind="stable").copy()
    top_tasks["task_rank"] = top_tasks.groupby("soc_code").cumcount() + 1
    top_tasks = top_tasks.loc[top_tasks["task_rank"].le(5)]
    stage_log(report, "top_five_tasks", top_tasks, numeric=["penetration_value", "task_rank"], keys=["soc_code", "task_normalized"], note="up to five matched tasks per SOC; ties broken by normalized text then Task ID")

    bls_fields = ["soc_code", "2025 National Employment Matrix code", "2025 National Employment Matrix title", *BLS_NUMERIC.values(), *BLS_CATEGORICAL.values(), "negative_projected_change_flag"]
    occupation = jobs[["occ_code", "title", "observed_exposure", "soc_code", "observed_exposure_value"]].merge(bls_line[bls_fields], on="soc_code", how="left", validate="one_to_one", indicator="bls_match_status")
    occupation["bls_match_status"] = occupation["bls_match_status"].map({"both": "matched", "left_only": "unmatched"}).astype("string")
    require(len(occupation) == len(jobs), "BLS join multiplied or lost occupations")
    stage_log(report, "occupation_bls_join", occupation, numeric=["observed_exposure_value", "employment_2025_thousands", "employment_change_percent_2025_35", "median_annual_wage_2025_dollars"], categories=["bls_match_status", *BLS_CATEGORICAL.values()], keys=["soc_code"], note="one-to-one left join; all exposure occupations retained")
    occupation = occupation.merge(base, on="soc_code", how="left", validate="one_to_one", indicator="onet_description_match_status")
    occupation["onet_description_match_status"] = occupation["onet_description_match_status"].map({"both": "matched", "left_only": "unmatched"}).astype("string")
    require(len(occupation) == len(jobs), "O*NET description join multiplied or lost occupations")
    stage_log(report, "occupation_description_join", occupation, categories=["onet_description_match_status"], keys=["soc_code"], note="one .00 description per matched six-digit SOC")
    occupation = occupation.merge(summary, on="soc_code", how="left", validate="one_to_one", indicator="task_summary_match_status")
    occupation["task_summary_match_status"] = occupation["task_summary_match_status"].map({"both": "matched", "left_only": "unmatched"}).astype("string")
    occupation.insert(4, "occupation_group_code", occupation["soc_code"].str.slice(0, 2))
    require(len(occupation) == len(jobs), "Task summary join multiplied or lost occupations")
    stage_log(report, "occupation_final", occupation, numeric=["observed_exposure_value", "employment_2025_thousands", "employment_change_percent_2025_35", "annual_openings_2025_35_thousands", "median_annual_wage_2025_dollars", "average_task_penetration", "matched_task_count"], categories=["bls_match_status", "onet_description_match_status", "task_summary_match_status"], keys=["soc_code"], note="all 756 current exposure occupations retained; missing task average has missing denominator")

    unmatched_penetration = penetration.loc[~penetration["task_normalized"].isin(set(tasks["task_normalized"]))].copy()
    unmatched_task = task_join.loc[task_join["task_match_status"].eq("unmatched")].copy()
    unmatched_bls = occupation.loc[occupation["bls_match_status"].eq("unmatched")].copy()
    unmatched_description = occupation.loc[occupation["onet_description_match_status"].eq("unmatched")].copy()
    unmatched_bls_line = bls_line.loc[~bls_line["soc_code"].isin(set(jobs["soc_code"]))].copy()
    matched_bls_line = bls_line.loc[bls_line["soc_code"].isin(set(jobs["soc_code"]))].copy()
    require(len(matched_bls_line) + len(unmatched_bls_line) == len(bls_line), "BLS line-item partition does not reconcile")
    bls_total_reconciliation = {}
    for field in ["employment_2025_thousands", "annual_openings_2025_35_thousands"]:
        total, matched_total, unmatched_total = (float(frame[field].sum()) for frame in [bls_line, matched_bls_line, unmatched_bls_line])
        total_count, matched_count, unmatched_count = (int(frame[field].notna().sum()) for frame in [bls_line, matched_bls_line, unmatched_bls_line])
        occupation_total = float(occupation[field].sum())
        require(abs(total - matched_total - unmatched_total) < 1e-6, f"BLS {field} totals do not reconcile")
        require(total_count == matched_count + unmatched_count, f"BLS {field} nonmissing counts do not reconcile")
        require(abs(matched_total - occupation_total) < 1e-6, f"Occupation output changed matched BLS {field} total")
        bls_total_reconciliation[field] = {
            "unit": "thousands" if field == "employment_2025_thousands" else "thousands per year",
            "all_line_items": {"rows": len(bls_line), "nonmissing": total_count, "sum": total},
            "matched_to_exposure": {"rows": len(matched_bls_line), "nonmissing": matched_count, "sum": matched_total},
            "unmatched_to_exposure": {"rows": len(unmatched_bls_line), "nonmissing": unmatched_count, "sum": unmatched_total},
            "occupation_output_matched_sum": occupation_total,
            "sum_difference": total - matched_total - unmatched_total,
        }
    report["bls_line_item_totals"] = bls_total_reconciliation
    print("BLS line-item totals:", json.dumps(bls_total_reconciliation, ensure_ascii=False))
    unmatched_keys = pd.concat([
        pd.DataFrame({"source": "job_exposure", "target": "bls_line_item", "key_type": "soc_code", "key": unmatched_bls["soc_code"]}),
        pd.DataFrame({"source": "job_exposure", "target": "onet_base_description", "key_type": "soc_code", "key": unmatched_description["soc_code"]}),
        pd.DataFrame({"source": "onet_task_statements", "target": "task_penetration", "key_type": "task_normalized", "key": unmatched_task["task_normalized"]}),
        pd.DataFrame({"source": "task_penetration", "target": "onet_task_statements", "key_type": "task_normalized", "key": unmatched_penetration["task_normalized"]}),
        pd.DataFrame({"source": "bls_line_item", "target": "job_exposure", "key_type": "soc_code", "key": unmatched_bls_line["soc_code"]}),
    ], ignore_index=True).drop_duplicates().sort_values(["source", "target", "key"], kind="stable")
    stage_log(report, "unmatched_keys", unmatched_keys, categories=["source", "target"], keys=["source", "target", "key"], note="distinct unmatched keys; full source rows remain in source-grain and unmatched-row outputs")

    report["reconciliation"] = {
        "source_rows": {k: len(v) for k, v in clean.items()},
        "bls_line_items": len(bls_line), "bls_summaries": len(bls_summary),
        "penetration_lookup_keys": len(lookup), "collapsed_penetration_lookup_rows": len(penetration)-len(lookup),
        "task_join_rows": len(task_join), "matched_task_statement_rows": len(matched), "unmatched_task_statement_rows": len(unmatched_task),
        "occupation_task_rows": len(associations), "collapsed_within_soc_associations": len(matched)-len(associations),
        "occupation_rows": len(occupation), "bls_matched_occupations": int(occupation["bls_match_status"].eq("matched").sum()),
        "bls_unmatched_occupations": len(unmatched_bls), "onet_unmatched_occupations": len(unmatched_description),
        "task_summary_matched_occupations": int(occupation["task_summary_match_status"].eq("matched").sum()),
        "unmatched_penetration_rows": len(unmatched_penetration), "unmatched_bls_line_item_rows": len(unmatched_bls_line),
        "negative_bls_projected_change_rows": int(bls["negative_projected_change_flag"].sum()),
        "bls_line_item_totals": bls_total_reconciliation,
    }
    return {
        "source_grain_job_exposure": jobs, "source_grain_task_penetration": penetration,
        "source_grain_onet_occupations": occupations, "source_grain_onet_tasks": task_join,
        "source_grain_bls": bls, "bls_line_items": bls_line, "bls_summaries": bls_summary,
        "penetration_lookup": lookup, "occupation_tasks": associations, "top_five_tasks": top_tasks,
        "occupation": occupation, "unmatched_keys": unmatched_keys,
        "unmatched_exposure_bls_rows": unmatched_bls,
        "unmatched_exposure_onet_rows": unmatched_description,
        "unmatched_onet_task_rows": unmatched_task,
        "unmatched_penetration_rows": unmatched_penetration,
        "unmatched_bls_line_item_rows": unmatched_bls_line,
    }


def record_checks(outputs: dict[str, pd.DataFrame], clean: dict[str, pd.DataFrame]) -> pd.DataFrame:
    occupation = outputs["occupation"]
    bls_summary = outputs["bls_summaries"]
    penetration = clean["task_penetration"]
    lookup = outputs["penetration_lookup"]
    task_source = clean["onet_task_statements"]
    associations = outputs["occupation_tasks"]
    jobs = clean["job_exposure"]
    checks: list[dict] = []

    def add(case: str, source_file: str, source_row: str, source_key: str, original: dict, expected: dict, actual: dict, passed: bool, reason: str, related_source_rows: str = "") -> None:
        checks.append({
            "case": case, "source_file": source_file, "source_row": source_row,
            "source_key": source_key, "related_source_rows": related_source_rows,
            "original_value": json.dumps(original, ensure_ascii=False),
            "expected_value": json.dumps(expected, ensure_ascii=False),
            "actual_value": json.dumps(actual, ensure_ascii=False),
            "pass": bool(passed), "reason": reason,
        })

    # Expectations below are the ones recorded in plan.md before comparing outputs.
    chief_source = jobs.loc[jobs["soc_code"].eq("11-1011")].iloc[0]
    chief = occupation.loc[occupation["soc_code"].eq("11-1011")]
    chief_actual = {
        "output_rows": len(chief), "exposure_text": str(chief.iloc[0]["observed_exposure"]),
        "bls_status": str(chief.iloc[0]["bls_match_status"]),
        "base_onet_soc_code": str(chief.iloc[0]["base_onet_soc_code"]),
    }
    add("Chief Executives", "job_exposure.csv", str(chief_source["source_row"]), "occ_code=11-1011",
        {"observed_exposure": str(chief_source["observed_exposure"]), "title": str(chief_source["title"])},
        {"output_rows": 1, "exposure_text": "0.0333", "bls_status": "matched", "base_onet_soc_code": "11-1011.00"},
        chief_actual, chief_actual == {"output_rows": 1, "exposure_text": "0.0333", "bls_status": "matched", "base_onet_soc_code": "11-1011.00"},
        "Normal one-to-one occupation join")

    legislators_source = jobs.loc[jobs["soc_code"].eq("11-1031")].iloc[0]
    legislators = occupation.loc[occupation["soc_code"].eq("11-1031")]
    legislators_actual = {
        "output_rows": len(legislators), "exposure_text": str(legislators.iloc[0]["observed_exposure"]),
        "bls_status": str(legislators.iloc[0]["bls_match_status"]),
        "employment_missing": bool(pd.isna(legislators.iloc[0]["employment_2025_thousands"])),
    }
    legislators_expected = {"output_rows": 1, "exposure_text": "0.0", "bls_status": "unmatched", "employment_missing": True}
    add("Legislators", "job_exposure.csv", str(legislators_source["source_row"]), "occ_code=11-1031",
        {"observed_exposure": str(legislators_source["observed_exposure"]), "title": str(legislators_source["title"])},
        legislators_expected, legislators_actual, legislators_actual == legislators_expected,
        "Preserve source text and unmatched occupation")

    top_exec = bls_summary.loc[bls_summary["soc_code"].eq("11-1000")]
    top_source = top_exec.iloc[0]
    top_expected = {"summary_rows": 1, "occupation_rows": 0, "occupation_type": "Summary"}
    top_actual = {"summary_rows": len(top_exec), "occupation_rows": int(occupation["soc_code"].eq("11-1000").sum()), "occupation_type": str(top_source["Occupation type"])}
    add("Top executives Summary", "bls_table_1_2_2025_35.csv", str(top_source["source_row"]), "2025 National Employment Matrix code=11-1000",
        {"title": str(top_source["2025 National Employment Matrix title"]), "occupation_type": str(top_source["Occupation type"])},
        top_expected, top_actual, top_actual == top_expected, "Summary/line-item grain boundary")

    press_source = penetration.loc[penetration["task_normalized"].eq(PRESS_KEY)].sort_values("source_row")
    press_record = press_source.iloc[0]
    press_lookup = lookup.loc[lookup["task_normalized"].eq(PRESS_KEY)]
    press_expected = {"source_rows": 8, "lookup_rows": 1, "normalized_key": PRESS_KEY, "penetration_value": 0.7263}
    press_actual = {
        "source_rows": len(press_source), "lookup_rows": len(press_lookup),
        "normalized_key": str(press_lookup.iloc[0]["task_normalized"]),
        "penetration_value": float(press_lookup.iloc[0]["penetration_value"]),
    }
    add("Press-release duplicate task", "task_penetration.csv", str(press_record["source_row"]), f"task_normalized={PRESS_KEY}",
        {"task": str(press_record["task"]), "penetration": str(press_record["penetration"])},
        press_expected, press_actual,
        press_actual == press_expected and set(press_source["penetration"]) == {"0.7263"},
        "One specific source row and all agreeing duplicate rows remain traceable; lookup has one value",
        ";".join(press_source["source_row"].astype(str)))

    advisers_source = task_source.loc[task_source["task_normalized"].eq(ADVISERS_KEY)].sort_values("source_row")
    adviser_record = advisers_source.iloc[0]
    advisers_assoc = associations.loc[associations["task_normalized"].eq(ADVISERS_KEY)]
    adviser_assoc = advisers_assoc.loc[advisers_assoc["soc_code"].eq(adviser_record["soc_code"])].iloc[0]
    adviser_expected = {
        "soc_code": str(adviser_record["soc_code"]), "task_text": str(adviser_record["Task"]),
        "source_task_id_in_contributors": True, "all_source_socs_retained": True,
    }
    adviser_actual = {
        "soc_code": str(adviser_assoc["soc_code"]), "task_text": str(adviser_assoc["task_text"]),
        "source_task_id_in_contributors": str(adviser_record["Task ID"]) in str(adviser_assoc["contributing_task_ids"]).split(";"),
        "all_source_socs_retained": set(advisers_source["soc_code"]) == set(associations.loc[associations["task_normalized"].eq(ADVISERS_KEY), "soc_code"]),
    }
    add("Student-organization advisers", "onet_task_statements.csv", str(adviser_record["source_row"]),
        f"O*NET-SOC Code={adviser_record['O*NET-SOC Code']}; Task ID={adviser_record['Task ID']}",
        {"Task": str(adviser_record["Task"]), "O*NET-SOC Code": str(adviser_record["O*NET-SOC Code"]), "Task ID": str(adviser_record["Task ID"])},
        adviser_expected, adviser_actual, adviser_actual == adviser_expected and advisers_source["soc_code"].nunique() > 1,
        "Specific teacher task survives and all occupation associations are retained",
        ";".join(advisers_source["source_row"].astype(str)))

    result = pd.DataFrame(checks)
    require(bool(result["pass"].all()), f"Record checks failed: {result.loc[~result['pass'], ['case','original_value','expected_value','actual_value']].to_dict('records')}")
    return result


def cleaned_sample(occupation: pd.DataFrame, limit: int = 50) -> pd.DataFrame:
    # Explicit difficult cases first, then deterministic spread across occupation groups.
    selected = ["11-1011", "11-1031"]
    flags = occupation.loc[occupation["median_annual_wage_2025_dollars"].isna() | occupation["average_task_penetration"].isna(), "soc_code"].tolist()
    selected.extend(sorted(flags)[:12])
    for _, group in occupation.sort_values("soc_code").groupby("occupation_group_code", sort=True):
        selected.extend(group["soc_code"].head(1).tolist())
    selected = list(dict.fromkeys(selected))[:limit]
    sample = occupation.set_index("soc_code").loc[selected].reset_index()
    require(len(sample) <= 50 and sample["soc_code"].is_unique, "Invalid cleaned sample")
    return sample


def write_outputs(outputs: dict[str, pd.DataFrame], checks: pd.DataFrame, sample: pd.DataFrame, report: dict, hashes: dict[str, str], output_dir: Path, sample_file: Path) -> None:
    paths = {name: output_dir / f"{name}.csv" for name in outputs}
    paths["record_checks"] = output_dir / "record_checks.csv"
    paths["validation_report"] = output_dir / "validation_report.json"
    paths["cleaned_sample"] = sample_file
    existing = [str(p) for p in paths.values() if p.exists()]
    require(not existing, f"Refusing to overwrite existing outputs: {existing}. Choose a fresh output directory/sample path.")
    output_dir.mkdir(parents=True, exist_ok=True)
    sample_file.parent.mkdir(parents=True, exist_ok=True)
    for name, frame in outputs.items():
        frame.to_csv(paths[name], index=False)
    checks.to_csv(paths["record_checks"], index=False)
    sample.to_csv(sample_file, index=False)
    report["source_hashes"] = hashes
    report["sample_soc_codes"] = sample["soc_code"].tolist()
    report["record_checks_passed"] = int(checks["pass"].sum())
    paths["validation_report"].write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    args = arguments()
    report: dict = {"stages": [], "source_version": "unknown", "download_date": "unknown"}
    raw, hashes = load_sources(args.data_dir)
    clean = clean_sources(raw, report)
    outputs = build_outputs(clean, report)
    checks = record_checks(outputs, clean)
    sample = cleaned_sample(outputs["occupation"])
    write_outputs(outputs, checks, sample, report, hashes, args.output_dir, args.sample_file)
    print("Record checks: 5/5 passed")
    print(checks[["case", "source_file", "source_row", "source_key", "original_value", "expected_value", "actual_value", "pass"]].to_string(index=False))
    print("Reconciliation:", json.dumps(report["reconciliation"], indent=2))
    print(f"Wrote outputs to {args.output_dir} and sample to {args.sample_file}")


if __name__ == "__main__":
    main()
