"""Stable hash helpers shared by probabilistic filters."""

from __future__ import annotations

import hashlib


def hash_int(value: str, seed: int = 0) -> int:
    payload = f"{seed}:{value}".encode("utf-8")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "big")


def double_hash_positions(value: str, count: int, modulus: int, seed: int = 0) -> list[int]:
    first = hash_int(value, seed)
    second = hash_int(value, seed + 1) or 1
    return [(first + index * second) % modulus for index in range(count)]
