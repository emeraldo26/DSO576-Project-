"""Check source reconciliation, missing data, and dashboard behavior."""
from pathlib import Path
import unittest
import pandas as pd

from analysis.cleaning import clean_sources, load_sources, normalize_soc, verify_bls_workbook
from analysis.backend import (
    comparison_data, filter_occupations, group_summary, load_clean_data,
    occupation_details, rank_occupations, shortlist_data, summary_metrics, top_tasks,
)

ROOT = Path(__file__).resolve().parents[1]


class Phase2Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources, cls.metadata, cls.recovery_ledger = load_sources(ROOT / "data")
        cls.occupations, cls.tasks = load_clean_data(ROOT / "data" / "cleaned")

    def test_source_join_and_employment_reconcile_independently(self):
        jobs = self.sources["jobs"]
        bls = self.sources["bls"]
        line_items = bls.loc[bls["Occupation type"].eq("Line item")]
        matched_codes = set(jobs.occ_code) & set(line_items["2025 National Employment Matrix code"])
        self.assertEqual(set(self.occupations.soc_code), matched_codes)
        self.assertEqual(len(matched_codes), 755)
        source_total = line_items.loc[
            line_items["2025 National Employment Matrix code"].isin(matched_codes), "Employment, 2025"
        ].astype(float).sum() * 1000
        self.assertAlmostEqual(summary_metrics(self.occupations)["employment_2025"], source_total)
        self.assertNotIn("11-1031", matched_codes)

    def test_tasks_do_not_inflate_occupation_employment(self):
        self.assertFalse(self.occupations.soc_code.duplicated().any())
        self.assertFalse(self.tasks.duplicated(["soc_code", "task_normalized"]).any())
        self.assertTrue(self.tasks.soc_code.isin(self.occupations.soc_code).all())
        grouped = group_summary(self.occupations)
        self.assertEqual(grouped.occupation_count.sum(), len(self.occupations))
        self.assertAlmostEqual(grouped.employment_2025.sum(), self.occupations.employment_2025.sum())

    def test_missing_wages_and_training_are_preserved(self):
        self.assertEqual(self.occupations.median_annual_wage_2025.isna().sum(), 3)
        self.assertEqual(self.occupations.on_the_job_training.isna().sum(), 0)
        self.assertEqual(self.occupations.related_work_experience.isna().sum(), 0)
        self.assertEqual(self.occupations.on_the_job_training.eq("None").sum(), 295)
        self.assertEqual(self.occupations.related_work_experience.eq("None").sum(), 646)
        missing_wage_codes = set(self.occupations.loc[
            self.occupations.median_annual_wage_2025.isna(), "soc_code"
        ])
        self.assertTrue(missing_wage_codes <= set(comparison_data(self.occupations).soc_code))
        sorted_rows = rank_occupations(self.occupations, "median_annual_wage_2025", ascending=True)
        self.assertTrue(sorted_rows.tail(3).median_annual_wage_2025.isna().all())

    def test_task_mean_matches_independent_source_calculation(self):
        raw_ot = self.sources["onet_tasks"]
        raw_pen = self.sources["penetration"]
        def key(text):
            return " ".join(text.lower().split())
        keys = {key(t) for t in raw_ot.loc[
            raw_ot["O*NET-SOC Code"].str[:7].eq("11-1011"), "Task"
        ]}
        scores = {key(t): float(p) for t, p in zip(raw_pen.task, raw_pen.penetration)}
        values = [scores[t] for t in keys if t in scores]
        detail = occupation_details(self.occupations, self.tasks, "11-1011")
        self.assertAlmostEqual(detail["occupation"]["average_task_penetration"], sum(values) / len(values))
        self.assertEqual(detail["occupation"]["matched_task_count"], len(values))
        self.assertAlmostEqual(detail["top_tasks"].iloc[0].penetration, 0.831)
        self.assertTrue(detail["top_tasks"].penetration.is_monotonic_decreasing)

    def test_duplicate_source_task_conflicts_raise(self):
        changed = {k: v.copy() for k, v in self.sources.items()}
        extra = changed["penetration"].iloc[[0]].copy()
        extra["penetration"] = 0.123
        changed["penetration"] = pd.concat([changed["penetration"], extra], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "Conflicting penetration"):
            clean_sources(changed)

    def test_soc_normalization_does_not_accept_embedded_garbage(self):
        result = normalize_soc(pd.Series(["11-1011.00", " 11-1011 ", "abc11-1011"]))
        self.assertEqual(result.iloc[0], "11-1011")
        self.assertEqual(result.iloc[1], "11-1011")
        self.assertTrue(pd.isna(result.iloc[2]))

    def test_filters_combine_and_include_exact_boundaries(self):
        row = self.occupations.loc[self.occupations.soc_code.eq("43-9021")].iloc[0]
        filtered = filter_occupations(
            self.occupations, groups=["43"], outlooks=["Declining"], query="43-9021",
            employment_min=row.employment_2025, employment_max=row.employment_2025,
            exposure_min=row.observed_exposure, exposure_max=row.observed_exposure,
        )
        self.assertEqual(filtered.soc_code.tolist(), ["43-9021"])
        with self.assertRaises(ValueError):
            filter_occupations(self.occupations, exposure_min=0.8, exposure_max=0.2)

    def test_no_results_stays_empty_and_unavailable(self):
        frame = filter_occupations(self.occupations, query="__no_such_occupation__")
        metrics = summary_metrics(frame)
        self.assertEqual(metrics["occupation_count"], 0)
        self.assertIsNone(metrics["mean_observed_exposure"])
        self.assertIsNone(metrics["employment_2025"])
        self.assertTrue(comparison_data(frame).empty)
        self.assertTrue(group_summary(frame).empty)
        self.assertTrue(filter_occupations(self.occupations, groups=[]).empty)

    def test_zero_penetration_is_not_missing_and_ties_are_deterministic(self):
        zeros = self.tasks.loc[self.tasks.penetration.eq(0)]
        self.assertFalse(zeros.empty)
        code = zeros.soc_code.iloc[0]
        all_for_code = top_tasks(self.tasks, code, limit=1000)
        for _, ties in all_for_code.groupby("penetration"):
            self.assertEqual(ties.task_normalized.tolist(), sorted(ties.task_normalized.tolist()))
        self.assertTrue(all_for_code.penetration.eq(0).any())

    def test_default_sort_and_units_and_input_immutability(self):
        before = self.occupations.copy(deep=True)
        ranks = rank_occupations(self.occupations)
        self.assertEqual(ranks.iloc[0].soc_code, "15-1251")
        chief = occupation_details(self.occupations, self.tasks, "11-1011")["occupation"]
        self.assertEqual(chief["employment_2025"], 291600)
        chart = comparison_data(self.occupations)
        programmers = chart.loc[chart.soc_code.eq("15-1251")].iloc[0]
        self.assertAlmostEqual(programmers.observed_exposure_percent, 74.51)
        pd.testing.assert_frame_equal(before, self.occupations)

    def test_shortlist_uses_full_dataset_and_deduplicates_codes(self):
        result = shortlist_data(self.occupations, ["15-1251", "11-1011", "15-1251"])
        self.assertEqual(len(result), 2)
        self.assertEqual(set(result.soc_code), {"15-1251", "11-1011"})
        with self.assertRaises(KeyError):
            occupation_details(self.occupations, self.tasks, "00-0000")

    def test_unmatched_occupation_is_preserved_in_master(self):
        result = clean_sources(self.sources)
        self.assertEqual(len(result.master), 756)
        row = result.master.loc[result.master.soc_code.eq("11-1031")].iloc[0]
        self.assertEqual(row.bls_match_status, "unmatched")
        self.assertEqual(row.observed_exposure, 0)
        self.assertTrue(pd.isna(row.employment_2025))
        self.assertNotIn("11-1031", set(result.occupations.soc_code))

    def test_full_precision_mean_does_not_depend_on_four_decimal_rounding(self):
        row = self.occupations.loc[self.occupations.soc_code.eq("41-4012")].iloc[0]
        task_values = self.tasks.loc[self.tasks.soc_code.eq("41-4012"), "penetration"].tolist()
        from math import fsum
        self.assertAlmostEqual(row.average_task_penetration, fsum(task_values) / len(task_values), places=12)
        self.assertAlmostEqual(row.average_task_penetration, 0.47965, places=12)

    def test_literal_none_category_is_preserved_when_explicitly_supplied(self):
        # Tests category handling. This does not infer None from a source blank.
        changed = {k: v.copy() for k, v in self.sources.items()}
        bls = changed["bls"]
        column = "Typical on-the-job training needed to attain competency in the occupation"
        bls.loc[bls["2025 National Employment Matrix code"].eq("11-1011"), column] = "None"
        result = clean_sources(changed)
        row = result.occupations.loc[result.occupations.soc_code.eq("11-1011")].iloc[0]
        self.assertEqual(row.on_the_job_training, "None")

    def test_shortlist_uses_selected_sort_and_can_be_resorted(self):
        codes = ["15-1251", "11-1011"]
        frame = shortlist_data(self.occupations, codes, ascending=True)
        self.assertEqual(frame.soc_code.tolist(), ["11-1011", "15-1251"])
        resorted = rank_occupations(frame)
        self.assertEqual(resorted.soc_code.tolist(), ["15-1251", "11-1011"])
        self.assertEqual(resorted.display_rank.tolist(), [1, 2])

    def test_workbook_recoveries_are_verified_and_original_blanks_preserved(self):
        self.assertEqual(len(self.recovery_ledger), 1037)
        counts = self.recovery_ledger.field.value_counts().to_dict()
        self.assertEqual(counts, {"related_work_experience": 716, "on_the_job_training": 321})
        row = self.occupations.loc[self.occupations.soc_code.eq("11-1011")].iloc[0]
        self.assertEqual(row.on_the_job_training, "None")
        self.assertTrue(pd.isna(row.on_the_job_training_csv_raw))
        self.assertEqual(row.on_the_job_training_workbook_raw, "None")
        self.assertEqual(row.on_the_job_training_source, "workbook_verified")
        verification = self.metadata["bls_occupation_tables_2025_35.xlsx"]["verification"]
        self.assertEqual(verification["table_1_10_shared_measure_mismatches"], 0)

    def test_changed_csv_numeric_value_rejects_workbook_recovery(self):
        raw = pd.read_csv(ROOT / "data/bls_table_1_2_2025_35.csv", dtype="string", keep_default_na=False)
        raw.loc[raw["2025 National Employment Matrix code"].eq("11-1011"), "Employment, 2025"] = "999"
        with self.assertRaisesRegex(ValueError, "numeric mismatch"):
            verify_bls_workbook(raw, ROOT / "data/bls_occupation_tables_2025_35.xlsx")


if __name__ == "__main__":
    unittest.main()
