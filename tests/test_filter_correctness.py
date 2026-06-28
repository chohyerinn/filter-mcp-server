import unittest

from membership_filters.registry import FILTER_NAMES, create_filter


class FilterCorrectnessTests(unittest.TestCase):
    def test_inserted_items_are_reported_present(self) -> None:
        items = [f"known-{index:03d}" for index in range(25)]

        for filter_name in FILTER_NAMES:
            with self.subTest(filter=filter_name):
                filter_obj = create_filter(filter_name)
                filter_obj.build(items)

                for item in items:
                    self.assertTrue(filter_obj.contains(item)["result"])

    def test_absent_items_have_reasonable_false_positive_rates(self) -> None:
        items = [f"member-{index:04d}" for index in range(1000)]
        absent = [f"visitor-{index:04d}" for index in range(5000)]

        for filter_name in FILTER_NAMES:
            with self.subTest(filter=filter_name):
                filter_obj = create_filter(filter_name)
                filter_obj.build(items)
                fpr = filter_obj.false_positive_rate(absent)

                if filter_obj.exact:
                    self.assertEqual(fpr["measured"], 0.0)
                else:
                    allowed = max(0.05, fpr["theoretical"] * 5)
                    self.assertLessEqual(fpr["measured"], allowed)

    def test_delete_supported_filters_remove_known_items(self) -> None:
        items = [f"delete-me-{index:03d}" for index in range(20)]

        for filter_name in ("naive", "counting_bloom", "cuckoo"):
            with self.subTest(filter=filter_name):
                filter_obj = create_filter(filter_name)
                filter_obj.build(items)

                before_count = filter_obj.memory_usage()["n_items"]
                delete_result = filter_obj.delete(items[0])

                self.assertTrue(delete_result["supported"])
                self.assertTrue(delete_result["ok"])
                self.assertEqual(filter_obj.memory_usage()["n_items"], before_count - 1)
                self.assertFalse(filter_obj.contains(items[0])["result"])

    def test_unsupported_operations_are_reported_explicitly(self) -> None:
        filter_expectations = {
            "bloom": ["delete", "prefix_query", "range_query"],
            "counting_bloom": ["prefix_query", "range_query"],
            "cuckoo": ["prefix_query", "range_query"],
            "surf": ["insert", "delete"],
        }

        for filter_name, operations in filter_expectations.items():
            with self.subTest(filter=filter_name):
                filter_obj = create_filter(filter_name)
                filter_obj.build(["alpha", "beta", "gamma"])

                if "insert" in operations:
                    self.assertFalse(filter_obj.insert("delta")["ok"])
                if "delete" in operations:
                    self.assertFalse(filter_obj.delete("alpha")["supported"])
                if "prefix_query" in operations:
                    self.assertFalse(filter_obj.prefix_query("a")["supported"])
                if "range_query" in operations:
                    self.assertFalse(filter_obj.range_query("a", "z")["supported"])


if __name__ == "__main__":
    unittest.main()
