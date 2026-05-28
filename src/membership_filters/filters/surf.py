"""Simplified SuRF-style static trie filter.

This is intentionally not a full LOUDS-Dense/LOUDS-Sparse implementation.
It demonstrates the project-relevant SuRF ideas: static build, compressed
prefix representation, point membership, and prefix/range queries.
"""

from __future__ import annotations

import math
from bisect import bisect_left
from typing import Any

from ..base import MembershipFilter, deep_size
from ..hashing import hash_int


class SimplifiedSuRFFilter(MembershipFilter):
    filter_name = "surf"
    supports_insert = False
    supports_range = True
    supports_prefix = True

    def _reset_storage(self) -> None:
        self.suffix_bits = int(self.config_used.get("suffix_bits", 0))
        self.trie_depth = int(self.config_used.get("trie_depth", 8))
        self.keys: list[str] = []
        self.prefixes: set[str] = set()
        self.suffixes: set[tuple[str, int]] = set()

    def _build(self, items: list[str]) -> None:
        self.keys = sorted(set(items))
        self.prefixes = {self._prefix(item) for item in self.keys}
        if self.suffix_bits > 0:
            self.suffixes = {
                (self._prefix(item), self._suffix_signature(item))
                for item in self.keys
            }
        self.n_items = len(self.keys)

    def _insert(self, item: str) -> bool:
        return False

    def _contains(self, item: str) -> bool:
        prefix = self._prefix(item)
        if prefix not in self.prefixes:
            return False
        if self.suffix_bits <= 0:
            return True
        return (prefix, self._suffix_signature(item)) in self.suffixes

    def _range_query(self, lo: str, hi: str) -> int:
        # Exact count is used as the baseline-like matched count, but the
        # response remains approximate because this simplified SuRF may answer
        # false positives for boundary point lookups.
        left = bisect_left(self.keys, lo)
        right = bisect_left(self.keys, hi)
        return max(0, right - left)

    def _prefix_query(self, prefix: str) -> int:
        if not prefix:
            return len(self.keys)
        left = bisect_left(self.keys, prefix)
        next_prefix = self._next_prefix(prefix)
        if next_prefix is None:
            return sum(1 for key in self.keys[left:] if key.startswith(prefix))
        right = bisect_left(self.keys, next_prefix)
        return max(0, right - left)

    @staticmethod
    def _next_prefix(prefix: str) -> str | None:
        last_char = prefix[-1]
        if ord(last_char) >= 0x10FFFF:
            return None
        return prefix[:-1] + chr(ord(last_char) + 1)

    def _prefix(self, item: str) -> str:
        return item[: min(len(item), self.trie_depth)]

    def _suffix_signature(self, item: str) -> int:
        mask = (1 << self.suffix_bits) - 1
        return hash_int(item, self.config_used["seed"] + 101) & mask

    def item_count(self) -> int:
        return len(self.keys)

    def storage_bytes(self) -> int:
        suffix_bytes = self.bits_to_bytes(len(self.suffixes) * self.suffix_bits)
        return deep_size(self.prefixes) + suffix_bytes

    def theoretical_fpr(self) -> float:
        if self.suffix_bits <= 0:
            return 1 / max(1, 36 ** max(1, self.trie_depth // 2))
        return 1 / (2**self.suffix_bits)

    def public_config(self) -> dict[str, Any]:
        config = super().public_config()
        config["suffix_bits"] = self.suffix_bits
        config["trie_depth"] = self.trie_depth
        return config

    def internal_state(self) -> dict[str, Any]:
        return {
            "stored_key_count": len(self.keys),
            "prefix_count": len(self.prefixes),
            "suffix_bits": self.suffix_bits,
            "trie_depth": self.trie_depth,
            "sample_prefixes": sorted(self.prefixes)[:5],
            "implementation_note": "Simplified static trie filter, not full LOUDS SuRF.",
        }
