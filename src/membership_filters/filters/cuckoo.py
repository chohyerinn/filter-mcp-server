"""Cuckoo filter storing compact fingerprints in alternative buckets."""

from __future__ import annotations

import math
import random
from typing import Any

from ..base import MembershipFilter
from ..hashing import hash_int


class CuckooFilter(MembershipFilter):
    filter_name = "cuckoo"
    supports_delete = True
    max_kicks = 500

    def _reset_storage(self) -> None:
        self.bucket_size = int(self.config_used.get("bucket_size", 4))
        self.fingerprint_bits = int(self.config_used.get("fingerprint_bits", 12))
        expected_items = int(self.config_used["expected_items"])
        required_buckets = max(2, math.ceil(expected_items / (self.bucket_size * 0.95)))
        self.bucket_count = 1 << (required_buckets - 1).bit_length()
        self.fingerprint_mask = (1 << self.fingerprint_bits) - 1
        self.buckets: list[list[int]] = [[] for _ in range(self.bucket_count)]
        self.random = random.Random(self.config_used["seed"])
        self.inserted_count = 0

    def _fingerprint(self, item: str) -> int:
        return (hash_int(item, self.config_used["seed"] + 2) & self.fingerprint_mask) or 1

    def _alternate_index(self, index: int, fingerprint: int) -> int:
        return (
            index ^ (hash_int(str(fingerprint), self.config_used["seed"] + 1) % self.bucket_count)
        ) % self.bucket_count

    def _indexes(self, item: str, fingerprint: int) -> tuple[int, int]:
        first = hash_int(item, self.config_used["seed"]) % self.bucket_count
        return first, self._alternate_index(first, fingerprint)

    def _insert(self, item: str) -> bool:
        fingerprint = self._fingerprint(item)
        first, second = self._indexes(item, fingerprint)
        for index in (first, second):
            if len(self.buckets[index]) < self.bucket_size:
                self.buckets[index].append(fingerprint)
                self.inserted_count += 1
                return True

        original_buckets = [bucket.copy() for bucket in self.buckets]
        index = self.random.choice((first, second))
        displaced = fingerprint
        for _ in range(self.max_kicks):
            slot = self.random.randrange(len(self.buckets[index]))
            self.buckets[index][slot], displaced = displaced, self.buckets[index][slot]
            index = self._alternate_index(index, displaced)
            if len(self.buckets[index]) < self.bucket_size:
                self.buckets[index].append(displaced)
                self.inserted_count += 1
                return True
        self.buckets = original_buckets
        return False

    def _contains(self, item: str) -> bool:
        fingerprint = self._fingerprint(item)
        first, second = self._indexes(item, fingerprint)
        return fingerprint in self.buckets[first] or fingerprint in self.buckets[second]

    def _delete(self, item: str) -> bool:
        fingerprint = self._fingerprint(item)
        first, second = self._indexes(item, fingerprint)
        for index in (first, second):
            if fingerprint in self.buckets[index]:
                # Cuckoo filters delete by fingerprint, so a false-positive
                # lookup can delete a colliding fingerprint. That is an
                # inherent trade-off of compact fingerprint filters.
                self.buckets[index].remove(fingerprint)
                self.inserted_count = max(0, self.inserted_count - 1)
                return True
        return False

    def item_count(self) -> int:
        return self.inserted_count

    def storage_bytes(self) -> int:
        # Report ideal fingerprint capacity, including empty slots, so this is
        # comparable to Bloom's packed bit-array memory cost.
        return self.bits_to_bytes(self.bucket_count * self.bucket_size * self.fingerprint_bits)

    def theoretical_fpr(self) -> float:
        return min(1.0, (2 * self.bucket_size) / (2**self.fingerprint_bits))

    def public_config(self) -> dict[str, Any]:
        config = super().public_config()
        config["fingerprint_bits"] = self.fingerprint_bits
        config["bucket_size"] = self.bucket_size
        return config

    def internal_state(self) -> dict[str, Any]:
        return {
            "bucket_count": self.bucket_count,
            "bucket_size": self.bucket_size,
            "fingerprint_bits": self.fingerprint_bits,
            "inserted_count": self.inserted_count,
            "load_factor": self.inserted_count / (self.bucket_count * self.bucket_size),
            "nonempty_buckets": sum(bool(bucket) for bucket in self.buckets),
        }
