import unittest

from membership_filters.benchmark import SCENARIOS, compare_filters
from membership_filters.registry import FILTER_NAMES, create_filter


class FilterSmokeTests(unittest.TestCase):
    def test_all_filters_build_and_answer_membership(self) -> None:
        items = ["alpha", "beta", "gamma"]

        for filter_name in FILTER_NAMES:
            with self.subTest(filter=filter_name):
                filter_obj = create_filter(filter_name)
                build_result = filter_obj.build(items)

                self.assertTrue(build_result["ok"])
                self.assertEqual(filter_obj.memory_usage()["n_items"], len(items))
                self.assertTrue(filter_obj.contains("alpha")["result"])

                fpr = filter_obj.false_positive_rate(["absent-a", "absent-b"])
                self.assertEqual(fpr["queries_tested"], 2)
                self.assertGreaterEqual(fpr["measured"], 0.0)
                self.assertLessEqual(fpr["measured"], 1.0)

    def test_naive_filter_is_exact_baseline(self) -> None:
        filter_obj = create_filter("naive")
        filter_obj.build(["alpha", "beta", "gamma"])

        self.assertFalse(filter_obj.contains("absent")["result"])
        self.assertTrue(filter_obj.delete("beta")["ok"])
        self.assertFalse(filter_obj.contains("beta")["result"])
        self.assertTrue(filter_obj.prefix_query("a")["supported"])
        self.assertTrue(filter_obj.range_query("a", "z")["supported"])

    def test_benchmark_runs_each_filter_for_each_scenario(self) -> None:
        for scenario_name in SCENARIOS:
            with self.subTest(scenario=scenario_name):
                rows = compare_filters(scenario_name)

                self.assertEqual(len(rows), len(FILTER_NAMES))
                self.assertEqual({row["filter"] for row in rows}, set(FILTER_NAMES))
                for row in rows:
                    self.assertIn("memory", row)
                    self.assertIn("false_positive_rate", row)
                    self.assertIn("measured", row["false_positive_rate"])


if __name__ == "__main__":
    unittest.main()
