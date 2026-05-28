"""Counting Bloom filter with saturating counters."""

from __future__ import annotations

import math
from array import array
from typing import Any

from ..base import MembershipFilter
from ..hashing import double_hash_positions


class CountingBloomFilter(MembershipFilter):
    filter_name = "counting_bloom"
    supports_delete = True

    def _reset_storage(self) -> None:
        n = int(self.config_used["expected_items"])
        p = float(self.config_used["target_fpr"])
        self.counter_bits = int(self.config_used.get("counter_bits", 4))
        self.max_counter = (1 << self.counter_bits) - 1
        self.counter_count = max(1, math.ceil(-n * math.log(p) / (math.log(2) ** 2)))
        self.hash_count = max(1, round((self.counter_count / n) * math.log(2)))
        counter_type = "H" if self.counter_bits <= 16 else "I"
        self.counters = array(counter_type, [0] * self.counter_count)
        self.inserted_count = 0

    def _positions(self, item: str) -> list[int]:
        return double_hash_positions(item, self.hash_count, self.counter_count, self.config_used["seed"])

    def _insert(self, item: str) -> bool:
        for position in self._positions(item):
            self.counters[position] = min(self.max_counter, self.counters[position] + 1)
        self.inserted_count += 1
        return True

    def _contains(self, item: str) -> bool:
        return all(self.counters[position] > 0 for position in self._positions(item))

    def _delete(self, item: str) -> bool:
        positions = self._positions(item)
        if not all(self.counters[position] > 0 for position in positions):
            return False
        for position in positions:
            self.counters[position] -= 1
        self.inserted_count = max(0, self.inserted_count - 1)
        return True

    def item_count(self) -> int:
        return self.inserted_count

    def storage_bytes(self) -> int:
        # Report the ideal bit-packed counter array size so it is comparable
        # to the Bloom filter's packed bit array. Python's array uses 16/32-bit
        # cells internally, but a low-level implementation can pack 4-bit counters.
        return self.bits_to_bytes(self.counter_count * self.counter_bits)

    def theoretical_fpr(self) -> float:
        n = max(0, self.inserted_count)
        m = self.counter_count
        k = self.hash_count
        return (1 - math.exp(-k * n / m)) ** k if m else 0.0

    def public_config(self) -> dict[str, Any]:
        config = super().public_config()
        config["counter_bits"] = self.counter_bits
        return config

    def internal_state(self) -> dict[str, Any]:
        occupied = sum(1 for counter in self.counters if counter)
        return {
            "counter_count": self.counter_count,
            "hash_count": self.hash_count,
            "counter_bits": self.counter_bits,
            "inserted_count": self.inserted_count,
            "nonzero_counters": occupied,
            "fill_ratio": occupied / self.counter_count,
        }
