"""Repeatable Final-v2 workloads for the five filter MCP servers."""

from __future__ import annotations

import json
from dataclasses import dataclass

from .registry import FILTER_NAMES, create_filter


def numbered(prefix: str, count: int) -> list[str]:
    return [f"{prefix}-{index:05d}" for index in range(count)]


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    build_items: list[str]
    absent_queries: list[str]
    delete_items: list[str]
    range_bounds: tuple[str, str]
    prefix: str


SCENARIOS = {
    "point_membership": Scenario(
        name="point_membership",
        description="Membership lookup with random-like present and absent keys.",
        build_items=numbered("member", 1000),
        absent_queries=numbered("visitor", 1000),
        delete_items=[],
        range_bounds=("member-00100", "member-00149"),
        prefix="member-001",
    ),
    "delete_heavy": Scenario(
        name="delete_heavy",
        description="100 withdrawn members are deleted after build.",
        build_items=numbered("member", 1000),
        absent_queries=numbered("visitor", 1000),
        delete_items=numbered("member", 100),
        range_bounds=("member-00000", "member-00099"),
        prefix="member-000",
    ),
    "prefix_range": Scenario(
        name="prefix_range",
        description="Sorted string keys expose range and prefix support.",
        build_items=[f"user:{region}:{index:04d}" for region in ("aa", "ab", "ac") for index in range(500)],
        absent_queries=[f"user:zz:{index:04d}" for index in range(1000)],
        delete_items=[],
        range_bounds=("user:ab:0100", "user:ab:0199"),
        prefix="user:ab:",
    ),
}


DEFAULT_CONFIG = {
    "target_fpr": 0.01,
    "expected_items": 1000,
    "fingerprint_bits": 12,
    "bucket_size": 4,
    "counter_bits": 4,
    "suffix_bits": 8,
    "trie_depth": 8,
}


def run_filter(filter_name: str, scenario: Scenario, config: dict | None = None) -> dict:
    filter_obj = create_filter(filter_name)
    config_used = dict(DEFAULT_CONFIG)
    config_used["expected_items"] = len(scenario.build_items)
    if config:
        config_used.update(config)

    build_result = filter_obj.build(scenario.build_items, config_used)
    point_false_positives = sum(
        1 for item in scenario.absent_queries if filter_obj.contains(item)["result"]
    )
    delete_results = [filter_obj.delete(item) for item in scenario.delete_items]
    range_result = filter_obj.range_query(*scenario.range_bounds)
    prefix_result = filter_obj.prefix_query(scenario.prefix)
    fpr_result = filter_obj.false_positive_rate(scenario.absent_queries)

    return {
        "filter": filter_name,
        "scenario": scenario.name,
        "build": build_result,
        "false_positive_rate": fpr_result,
        "false_positives": point_false_positives,
        "delete_supported": bool(delete_results[0]["supported"]) if delete_results else filter_obj.supports_delete,
        "successful_deletes": sum(1 for result in delete_results if result.get("ok")),
        "delete_attempts": len(delete_results),
        "range_query": range_result,
        "prefix_query": prefix_result,
        "memory": filter_obj.memory_usage(),
        "state_summary": filter_obj.internal_state(),
    }


def compare_filters(scenario_name: str, config: dict | None = None) -> list[dict]:
    scenario = SCENARIOS[scenario_name]
    return [run_filter(name, scenario, config) for name in FILTER_NAMES]


def run_scenarios(config: dict | None = None) -> dict[str, list[dict]]:
    return {name: compare_filters(name, config) for name in SCENARIOS}


def main() -> None:
    print(json.dumps(run_scenarios(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
