"""Run from the repository root with: python -m analysis.run_phase2"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from .cleaning import clean_sources, load_sources
from .backend import summary_metrics


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=root / "data")
    parser.add_argument("--output-dir", type=Path, default=root / "data" / "cleaned")
    args = parser.parse_args()
    sources, metadata, recovery_ledger = load_sources(args.data_dir)
    result = clean_sources(sources)
    result.audit["source_files"] = metadata
    result.audit["summary_metrics"] = summary_metrics(result.occupations)
    comparison = root / "docs" / "team_comparison_evidence.json"
    if comparison.exists():
        result.audit["team_comparison"] = json.loads(comparison.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result.occupations.to_csv(args.output_dir / "occupation_clean_merged.csv", index=False)
    result.master.to_csv(args.output_dir / "occupation_master.csv", index=False)
    recovery_ledger.to_csv(args.output_dir / "bls_category_recovery.csv", index=False)
    result.tasks.to_csv(args.output_dir / "occupation_task_matches.csv", index=False)
    (args.output_dir / "data_audit.json").write_text(
        json.dumps(result.audit, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: result.audit[k] for k in [
        "status", "occupation_rows", "occupation_task_rows", "unmatched_ai_occupations", "summary_metrics",
    ]}, indent=2))


if __name__ == "__main__":
    main()
