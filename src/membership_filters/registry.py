"""Factory registry for membership-filter MCP servers."""

from __future__ import annotations

from .base import MembershipFilter
from .filters.bloom import BloomFilter
from .filters.counting_bloom import CountingBloomFilter
from .filters.cuckoo import CuckooFilter
from .filters.exact_set import ExactSetFilter
from .filters.surf import SimplifiedSuRFFilter

FILTER_NAMES = ("naive", "bloom", "counting_bloom", "cuckoo", "surf")

FILTER_CLASSES = {
    "naive": ExactSetFilter,
    "bloom": BloomFilter,
    "counting_bloom": CountingBloomFilter,
    "cuckoo": CuckooFilter,
    "surf": SimplifiedSuRFFilter,
}


def create_filter(
    filter_name: str,
    config: dict | None = None,
) -> MembershipFilter:
    try:
        filter_class = FILTER_CLASSES[filter_name]
    except KeyError as exc:
        raise ValueError(f"unknown filter: {filter_name}") from exc
    return filter_class(config)
