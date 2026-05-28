"""Standard Bloom filter."""

from __future__ import annotations

import math
from typing import Any

from ..base import MembershipFilter
from ..hashing import double_hash_positions


class BloomFilter(MembershipFilter):
    filter_name = "standard_bloom"

    def _reset_storage(self) -> None:
        n = int(self.config_used["expected_items"])
        p = float(self.config_used["target_fpr"])
        self.bit_count = max(1, math.ceil(-n * math.log(p) / (math.log(2) ** 2)))
        self.hash_count = max(1, round((self.bit_count / n) * math.log(2)))
        self.bits = bytearray((self.bit_count + 7) // 8)
        self.inserted_count = 0

    def _positions(self, item: str) -> list[int]:
        return double_hash_positions(item, self.hash_count, self.bit_count, self.config_used["seed"])

    def _insert(self, item: str) -> bool:
        for position in self._positions(item):
            self.bits[position // 8] |= 1 << (position % 8)
        self.inserted_count += 1
        return True

    def _contains(self, item: str) -> bool:
        return all(self.bits[position // 8] & (1 << (position % 8)) for position in self._positions(item))

    def item_count(self) -> int:
        return self.inserted_count

    def storage_bytes(self) -> int:
        return len(self.bits)

    def theoretical_fpr(self) -> float:
        n = max(0, self.inserted_count)
        m = self.bit_count
        k = self.hash_count
        return (1 - math.exp(-k * n / m)) ** k if m else 0.0

    def internal_state(self) -> dict[str, Any]:
        set_bits = sum(byte.bit_count() for byte in self.bits)
        return {
            "bit_count": self.bit_count,
            "hash_count": self.hash_count,
            "inserted_count": self.inserted_count,
            "set_bits": set_bits,
            "fill_ratio": set_bits / self.bit_count,
        }
