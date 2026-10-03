"""Create reproducible inspection evidence for the untouched source files.

This script intentionally does not clean or overwrite source data. It records
the starting state needed to justify the cleaning decisions in the assignment.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "outputs"


def inspect_table(path: Path, sheet_name: str | None = None) -> tuple[dict, list[dict], dict]:
    """Return table-level, missing-value, and duplicate evidence."""
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
        table_name = path.name
    else:
        frame = pd.read_excel(path, sheet_name=sheet_name)
        table_name = f"{path.name}::{sheet_name}"

    table_summary = {
        "table": table_name,
        "rows": len(frame),
        "columns": len(frame.columns),
        "exact_duplicate_rows": int(frame.duplicated().sum()),
        "columns_with_missing_values": int(frame.isna().any().sum()),
    }

    missing_rows = [
        {
            "table": table_name,
            "column": column,
            "dtype": str(frame[column].dtype),
            "missing_count": int(frame[column].isna().sum()),
            "missing_percent": round(float(frame[column].isna().mean() * 100), 3),
            "unique_count": int(frame[column].nunique(dropna=True)),
        }
        for column in frame.columns
    ]

    dtypes = {column: str(dtype) for column, dtype in frame.dtypes.items()}
    return table_summary, missing_rows, dtypes


def main() -> None:
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"Raw data directory not found: {RAW_DIR}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    table_summaries: list[dict] = []
    missing_values: list[dict] = []
    dtype_rows: list[dict] = []
    sheet_rows: list[dict] = []

    for path in sorted(RAW_DIR.iterdir()):
        if path.suffix.lower() == ".csv":
            summary, missing, dtypes = inspect_table(path)
            table_summaries.append(summary)
            missing_values.extend(missing)
            dtype_rows.append({"table": summary["table"], **dtypes})
        elif path.suffix.lower() == ".xlsx":
            workbook = pd.ExcelFile(path)
            for sheet_name in workbook.sheet_names:
                summary, missing, dtypes = inspect_table(path, sheet_name)
                table_summaries.append(summary)
                missing_values.extend(missing)
                dtype_rows.append({"table": summary["table"], **dtypes})
                sheet_rows.append(
                    {
                        "workbook": path.name,
                        "sheet": sheet_name,
                        "rows": summary["rows"],
                        "columns": summary["columns"],
                    }
                )

    pd.DataFrame(table_summaries).to_csv(OUTPUT_DIR / "initial_table_inventory.csv", index=False)
    pd.DataFrame(missing_values).to_csv(OUTPUT_DIR / "initial_column_inventory.csv", index=False)
    pd.DataFrame(dtype_rows).to_json(OUTPUT_DIR / "initial_dtypes.json", orient="records", indent=2)
    pd.DataFrame(sheet_rows).to_csv(OUTPUT_DIR / "initial_excel_sheet_inventory.csv", index=False)

    print(f"Inspected {len(table_summaries)} tables from {RAW_DIR}")
    print(pd.DataFrame(table_summaries).to_string(index=False))
    print(f"Evidence written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
