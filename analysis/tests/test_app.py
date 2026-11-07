"""Headless UI checks for app.py with Streamlit's AppTest (no browser needed)."""
import unittest
from pathlib import Path

try:
    from streamlit.testing.v1 import AppTest
except ImportError:  # pragma: no cover
    AppTest = None

APP = str(Path(__file__).resolve().parents[2] / "app.py")


@unittest.skipIf(AppTest is None, "streamlit is not installed")
class AppTests(unittest.TestCase):
    def start(self):
        at = AppTest.from_file(APP, default_timeout=90).run()
        self.assertFalse(at.exception)
        return at

    def test_default_view(self):
        at = self.start()
        values = {m.label: m.value for m in at.metric}
        self.assertEqual(values["Jobs shown"], "755")
        self.assertEqual(values["Workers in these jobs"], "154.2M")
        self.assertTrue(any("21.8M workers are in high-AI, shrinking jobs" in m.value for m in at.markdown))
        at.button_group(key="step").set_value("prioritize").run()
        self.assertFalse(at.exception)
        self.assertTrue(any("39 jobs are high-AI and shrinking" in m.value for m in at.markdown))

    def test_no_match_search(self):
        at = self.start()
        at.text_input(key="search").input("zzzz").run()
        self.assertFalse(at.exception)
        self.assertEqual(at.metric[0].value, "0")
        self.assertTrue(any("No jobs match" in i.value for i in at.info))

    def test_invalid_bounds_suppress_views(self):
        at = self.start()
        at.checkbox(key="exp_lower_on").check().run()
        at.number_input(key="exp_lower").set_value(50.0).run()
        at.checkbox(key="exp_upper_on").check().run()
        at.number_input(key="exp_upper").set_value(10.0).run()
        self.assertTrue(any("bigger than its maximum" in e.value for e in at.error))
        self.assertEqual(len(at.metric), 0)

    def test_reset_persists_after_next_interaction(self):  # audit B2-01
        at = self.start()
        at.checkbox(key="exp_lower_on").check().run()
        at.number_input(key="exp_lower").set_value(50.0).run()
        self.assertEqual(at.metric[0].value, "11")
        at.button(key="reset_btn").click().run()
        self.assertFalse(at.checkbox(key="exp_lower_on").value)
        at.button_group(key="step").set_value("prioritize").run()
        at.selectbox(key="sort_label").select("Median annual wage").run()
        self.assertEqual(at.metric[0].value, "755")

    def test_decline_in_percentage_points(self):  # audit B5-01
        at = self.start()
        at.button_group(key="step").set_value("prioritize").run()
        at.selectbox(key="detail_soc").select("23-2011").run()
        rows = [d.value for d in at.dataframe if "Measure" in d.value.columns][0]
        self.assertFalse(at.exception)
        value = rows.set_index("Measure").loc["Projected decline (percentage points)", "Value"]
        self.assertEqual(value, "0.3 pp")


if __name__ == "__main__":
    unittest.main()


@unittest.skipIf(AppTest is None, "streamlit is not installed")
class QuickViewTests(unittest.TestCase):
    def test_preset_fills_filters(self):
        at = AppTest.from_file(APP, default_timeout=90).run()
        at.text_input(key="search").input("zzzz").run()
        at.button_group(key="preset").set_value("Office & admin").run()
        self.assertFalse(at.exception)
        self.assertEqual(at.text_input(key="search").value, "")
        self.assertEqual(len(at.multiselect(key="groups").value), 1)
        self.assertEqual(at.metric[0].value, "50")


@unittest.skipIf(AppTest is None, "streamlit is not installed")
class FlowTests(unittest.TestCase):
    def test_shortlist_flow_and_sticky_detail(self):
        at = AppTest.from_file(APP, default_timeout=90).run()
        at.button_group(key="step").set_value("prioritize").run()
        at.selectbox(key="detail_soc").select("43-9021").run()
        [b for b in at.button if "Add to shortlist" in b.label][0].click().run()
        self.assertEqual(at.session_state["saved_socs"], ["43-9021"])
        at.button_group(key="step").set_value("shortlist").run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.get("download_button")), 1)
        at.button_group(key="step").set_value("prioritize").run()
        self.assertEqual(at.selectbox(key="detail_soc").value, "43-9021")  # selection survives step changes

    def test_job_size_filter(self):
        at = AppTest.from_file(APP, default_timeout=90).run()
        at.selectbox(key="size").select("Large (500K+)").run()
        self.assertFalse(at.exception)
        self.assertTrue(at.checkbox(key="emp_lower_on").value)
        self.assertLess(int(at.metric[0].value), 755)
