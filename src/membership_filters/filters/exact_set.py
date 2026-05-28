"""Naive exact set/hash-table baseline."""

from __future__ import annotations

from typing import Any

from ..base import MembershipFilter, deep_size


class ExactSetFilter(MembershipFilter):
    filter_name = "naive_set"
    exact = True
    may_contain_false_positive = False
    supports_delete = True
    supports_range = True
    supports_prefix = True

    def _reset_storage(self) -> None:
        self.items: set[str] = set()

    def _insert(self, item: str) -> bool:
        self.items.add(item)
        return True

    def _contains(self, item: str) -> bool:
        return item in self.items

    def _delete(self, item: str) -> bool:
        if item not in self.items:
            return False
        self.items.remove(item)
        return True

    def _range_query(self, lo: str, hi: str) -> int:
        return sum(1 for item in self.items if lo <= item < hi)

    def _prefix_query(self, prefix: str) -> int:
        return sum(1 for item in self.items if item.startswith(prefix))

    def item_count(self) -> int:
        return len(self.items)

    def storage_bytes(self) -> int:
        return deep_size(self.items)

    def internal_state(self) -> dict[str, Any]:
        return {
            "stored_item_count": len(self.items),
            "sample_items": sorted(self.items)[:5],
            "range_prefix_note": "Exact but scans the set, so it is slow for large data.",
        }
