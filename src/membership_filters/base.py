"""Common ADT and response helpers for filter-comparison MCP servers."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from math import ceil
from sys import getsizeof
from typing import Any


DEFAULT_CONFIG = {
    "target_fpr": 0.01,
    "expected_items": 1000,
    "seed": 42,
}


@dataclass
class FilterStats:
    builds: int = 0
    insert_attempts: int = 0
    successful_inserts: int = 0
    failed_inserts: int = 0
    queries: int = 0
    reported_present: int = 0
    delete_attempts: int = 0
    successful_deletes: int = 0
    range_queries: int = 0
    prefix_queries: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def deep_size(value: Any, seen: set[int] | None = None) -> int:
    visited = seen if seen is not None else set()
    object_id = id(value)
    if object_id in visited:
        return 0
    visited.add(object_id)
    size = getsizeof(value)
    if isinstance(value, dict):
        size += sum(deep_size(key, visited) + deep_size(item, visited) for key, item in value.items())
    elif isinstance(value, (list, tuple, set, frozenset)):
        size += sum(deep_size(item, visited) for item in value)
    return size


def elapsed_us(start_ns: int) -> float:
    return (time.perf_counter_ns() - start_ns) / 1000


def elapsed_ms(start_ns: int) -> float:
    return (time.perf_counter_ns() - start_ns) / 1_000_000


def unsupported(reason: str, *, ok: bool | None = None) -> dict[str, Any]:
    response: dict[str, Any] = {
        "supported": False,
        "result": "N/A",
        "reason": reason,
    }
    if ok is not None:
        response["ok"] = ok
    return response


class MembershipFilter(ABC):
    """Final-v2 common ADT implemented by every server."""

    filter_name = "base"
    exact = False
    may_contain_false_positive = True
    supports_insert = True
    supports_delete = False
    supports_range = False
    supports_prefix = False

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.metrics = FilterStats()
        self.config_used: dict[str, Any] = {}
        self.n_items = 0
        self.reset(config)

    @staticmethod
    def normalize_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
        merged = dict(DEFAULT_CONFIG)
        if config:
            merged.update(config)
        if "capacity" in merged and "expected_items" not in (config or {}):
            merged["expected_items"] = merged["capacity"]
        if "error_rate" in merged and "target_fpr" not in (config or {}):
            merged["target_fpr"] = merged["error_rate"]
        merged["expected_items"] = int(merged["expected_items"])
        merged["target_fpr"] = float(merged["target_fpr"])
        merged["seed"] = int(merged.get("seed", 42))
        if merged["expected_items"] <= 0:
            raise ValueError("expected_items must be a positive integer")
        if not 0 < merged["target_fpr"] < 1:
            raise ValueError("target_fpr must be between 0 and 1")
        return merged

    @staticmethod
    def validate_item(item: str) -> str:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("item must be a non-empty string")
        return item.strip()

    def reset(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        self.config_used = self.normalize_config(config)
        self.metrics = FilterStats()
        self.n_items = 0
        self._reset_storage()
        return {"ok": True, "config_used": self.public_config()}

    def build(self, items: list[str], config: dict[str, Any] | None = None) -> dict[str, Any]:
        clean_items = [self.validate_item(item) for item in items]
        start = time.perf_counter_ns()
        self.reset(config)
        self._build(clean_items)
        self.metrics.builds += 1
        self.n_items = self.item_count()
        return {
            "ok": True,
            "n_items": self.n_items,
            "build_time_ms": elapsed_ms(start),
            "config_used": self.public_config(),
        }

    def insert(self, item: str) -> dict[str, Any]:
        item = self.validate_item(item)
        if not self.supports_insert:
            return unsupported(f"{self.filter_name} is build-once; use build() instead.", ok=False)
        start = time.perf_counter_ns()
        ok = self._insert(item)
        self.metrics.insert_attempts += 1
        if ok:
            self.metrics.successful_inserts += 1
            self.n_items = self.item_count()
        else:
            self.metrics.failed_inserts += 1
        return {
            "supported": True,
            "ok": ok,
            "insert_time_us": elapsed_us(start),
        }

    def contains(self, item: str) -> dict[str, Any]:
        item = self.validate_item(item)
        start = time.perf_counter_ns()
        result = self._contains(item)
        self.metrics.queries += 1
        if result:
            self.metrics.reported_present += 1
        return {
            "supported": True,
            "result": result,
            "exact": self.exact,
            "may_contain_false_positive": self.may_contain_false_positive,
            "query_time_us": elapsed_us(start),
        }

    def delete(self, item: str) -> dict[str, Any]:
        item = self.validate_item(item)
        if not self.supports_delete:
            return unsupported(f"{self.filter_name} does not support deletion.", ok=False)
        start = time.perf_counter_ns()
        ok = self._delete(item)
        self.metrics.delete_attempts += 1
        if ok:
            self.metrics.successful_deletes += 1
            self.n_items = self.item_count()
        return {"supported": True, "ok": ok, "delete_time_us": elapsed_us(start)}

    def range_query(self, lo: str, hi: str) -> dict[str, Any]:
        lo = self.validate_item(lo)
        hi = self.validate_item(hi)
        if not self.supports_range:
            return unsupported("This filter only supports point membership queries.")
        if lo >= hi:
            return {
                "supported": True,
                "matched_count": 0,
                "exact": self.exact,
                "may_contain_false_positive": self.may_contain_false_positive,
                "query_time_us": 0.0,
                "warning": "lo >= hi, returning empty range",
            }
        start = time.perf_counter_ns()
        matched_count = self._range_query(lo, hi)
        self.metrics.range_queries += 1
        return {
            "supported": True,
            "matched_count": matched_count,
            "exact": self.exact,
            "may_contain_false_positive": self.may_contain_false_positive,
            "query_time_us": elapsed_us(start),
        }

    def prefix_query(self, prefix: str) -> dict[str, Any]:
        prefix = self.validate_item(prefix)
        if not self.supports_prefix:
            return unsupported("This filter only supports point membership queries.")
        start = time.perf_counter_ns()
        matched_count = self._prefix_query(prefix)
        self.metrics.prefix_queries += 1
        return {
            "supported": True,
            "matched_count": matched_count,
            "exact": self.exact,
            "may_contain_false_positive": self.may_contain_false_positive,
            "query_time_us": elapsed_us(start),
        }

    def memory_usage(self) -> dict[str, Any]:
        n_items = self.item_count()
        bytes_used = self.storage_bytes()
        return {
            "bytes": bytes_used,
            "bits_per_item": bytes_used * 8 / n_items if n_items > 0 else None,
            "n_items": n_items,
        }

    def false_positive_rate(self, absent_items: list[str] | None = None) -> dict[str, Any]:
        probes = [self.validate_item(item) for item in (absent_items or [f"absent-{index:05d}" for index in range(1000)])]
        false_positives = sum(1 for item in probes if self._contains(item))
        return {
            "theoretical": self.theoretical_fpr(),
            "measured": false_positives / len(probes) if probes else 0.0,
            "queries_tested": len(probes),
        }

    def stats(self) -> dict[str, Any]:
        return {"filter": self.filter_name, **self.metrics.to_dict()}

    def state(self) -> dict[str, Any]:
        return {
            "filter": self.filter_name,
            "config_used": self.public_config(),
            "support": {
                "insert": self.supports_insert,
                "delete": self.supports_delete,
                "range_query": self.supports_range,
                "prefix_query": self.supports_prefix,
            },
            "internal_state": self.internal_state(),
            "stats": self.stats(),
        }

    def public_config(self) -> dict[str, Any]:
        return dict(self.config_used)

    def _build(self, items: list[str]) -> None:
        for item in items:
            self._insert(item)

    def _delete(self, item: str) -> bool:
        return False

    def _range_query(self, lo: str, hi: str) -> int:
        return 0

    def _prefix_query(self, prefix: str) -> int:
        return 0

    def storage_bytes(self) -> int:
        return deep_size(self.storage_for_memory())

    def storage_for_memory(self) -> Any:
        return self.internal_state()

    def theoretical_fpr(self) -> float:
        return 0.0

    def item_count(self) -> int:
        return self.n_items

    @staticmethod
    def bits_to_bytes(bits: int) -> int:
        return ceil(bits / 8)

    @abstractmethod
    def _reset_storage(self) -> None:
        """Initialize structure-specific storage after config is normalized."""

    @abstractmethod
    def _insert(self, item: str) -> bool:
        """Insert one item."""

    @abstractmethod
    def _contains(self, item: str) -> bool:
        """Return this structure's membership answer."""

    @abstractmethod
    def internal_state(self) -> dict[str, Any]:
        """Return compact structure state for explanation."""
