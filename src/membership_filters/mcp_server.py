"""FastMCP tools exposing the common filter ADT with schema checks."""

from __future__ import annotations

from typing import Any

from .registry import create_filter


def _require_fields(response: dict[str, Any], method: str, fields: set[str]) -> dict[str, Any]:
    missing = fields - response.keys()
    if missing:
        raise ValueError(f"{method} response missing fields: {sorted(missing)}")
    return response


def _validate_reset_response(response: dict[str, Any]) -> dict[str, Any]:
    return _require_fields(response, "reset", {"ok", "config_used"})


def _validate_build_response(response: dict[str, Any]) -> dict[str, Any]:
    return _require_fields(response, "build", {"ok", "n_items", "build_time_ms", "config_used"})


def _validate_insert_response(response: dict[str, Any]) -> dict[str, Any]:
    _require_fields(response, "insert", {"supported", "ok"})
    if response["supported"]:
        _require_fields(response, "insert", {"insert_time_us"})
    else:
        _require_fields(response, "insert", {"reason"})
    return response


def _validate_contains_response(response: dict[str, Any]) -> dict[str, Any]:
    return _require_fields(
        response,
        "contains",
        {"supported", "result", "exact", "may_contain_false_positive", "query_time_us"},
    )


def _validate_delete_response(response: dict[str, Any]) -> dict[str, Any]:
    _require_fields(response, "delete", {"supported", "ok"})
    if response["supported"]:
        _require_fields(response, "delete", {"delete_time_us"})
    else:
        _require_fields(response, "delete", {"result", "reason"})
    return response


def _validate_lookup_response(method: str, response: dict[str, Any]) -> dict[str, Any]:
    _require_fields(response, method, {"supported"})
    if response["supported"]:
        _require_fields(
            response,
            method,
            {"matched_count", "exact", "may_contain_false_positive", "query_time_us"},
        )
    else:
        _require_fields(response, method, {"result", "reason"})
    return response


def _validate_memory_response(response: dict[str, Any]) -> dict[str, Any]:
    return _require_fields(response, "memory_usage", {"bytes", "bits_per_item", "n_items"})


def _validate_fpr_response(response: dict[str, Any]) -> dict[str, Any]:
    return _require_fields(response, "false_positive_rate", {"theoretical", "measured", "queries_tested"})


def create_server(filter_name: str):
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(f"filter-{filter_name.replace('_', '-')}")
    current: dict[str, Any] = {"filter": create_filter(filter_name)}

    @mcp.tool()
    def reset(config: dict | None = None) -> dict:
        """Clear all data and reinitialize with optional new config.

        After reset, the filter is empty; use build() or insert() to add data again.
        """
        current["filter"] = create_filter(filter_name, config)
        return _validate_reset_response(current["filter"].reset(config))

    @mcp.tool()
    def build(items: list[str], config: dict | None = None) -> dict:
        """Build this filter from an initial string dataset."""
        return _validate_build_response(current["filter"].build(items, config))

    @mcp.tool()
    def insert(x: str) -> dict:
        """Insert one string key. Static structures return a standard unsupported response."""
        return _validate_insert_response(current["filter"].insert(x))

    @mcp.tool()
    def contains(x: str) -> dict:
        """Point membership query for one string key."""
        return _validate_contains_response(current["filter"].contains(x))

    @mcp.tool()
    def delete(x: str) -> dict:
        """Delete one key if the structure supports deletion."""
        return _validate_delete_response(current["filter"].delete(x))

    @mcp.tool()
    def range_query(lo: str, hi: str) -> dict:
        """Lexicographic half-open range query: lo <= key < hi. Unsupported point-only filters return N/A."""
        return _validate_lookup_response("range_query", current["filter"].range_query(lo, hi))

    @mcp.tool()
    def prefix_query(prefix: str) -> dict:
        """Prefix query. Unsupported point-only filters return N/A."""
        return _validate_lookup_response("prefix_query", current["filter"].prefix_query(prefix))

    @mcp.tool()
    def memory_usage() -> dict:
        """Return pure-structure memory estimate and bits per item."""
        return _validate_memory_response(current["filter"].memory_usage())

    @mcp.tool()
    def false_positive_rate(absent_items: list[str] | None = None) -> dict:
        """Return theoretical and measured false positive rate."""
        return _validate_fpr_response(current["filter"].false_positive_rate(absent_items))

    return mcp


def run_server(filter_name: str) -> None:
    create_server(filter_name).run()
