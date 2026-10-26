"""Checks that use only the committed Phase 2 clean tables."""
from pathlib import Path
import unittest

from analysis.backend import (
    comparison_data, filter_occupations, load_clean_data, occupation_details,
    rank_occupations, shortlist_data, summary_metrics,
)

ROOT = Path(__file__).resolve().parents[2]


class BackendOnlyChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.occupations, cls.tasks = load_clean_data(ROOT / "data" / "cleaned")

    def test_clean_tables_load_and_score(self):
        self.assertEqual((len(self.occupations), len(self.tasks)), (755, 17760))
        self.assertEqual(rank_occupations(self.occupations).iloc[0].soc_code, "43-4111")

    def test_summary_and_chart_use_clean_data(self):
        metrics = summary_metrics(self.occupations)
        self.assertEqual(metrics["occupation_count"], 755)
        self.assertEqual(metrics["employment_2025"], 154223400.0)
        self.assertEqual(len(comparison_data(self.occupations)), 755)

    def test_filters_details_and_shortlist(self):
        frame = filter_occupations(self.occupations, query="43-9021")
        self.assertEqual(frame.soc_code.tolist(), ["43-9021"])
        self.assertEqual(occupation_details(self.occupations, self.tasks, "11-1011")["occupation"]["employment_2025"], 291600)
        self.assertEqual(len(shortlist_data(self.occupations, ["11-1011", "43-9021", "43-9021"])), 2)


if __name__ == "__main__":
    unittest.main()
