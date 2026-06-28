# Approximate Filters using MCP Servers

## Overview

This project compares several approximate filter data structures using MCP servers and LLM tool calls.

Approximate filters reduce memory usage by storing compressed summaries instead of full keys.  
Because of this trade-off, some filters may return false positives or support limited operations.

The project compares:

- Bloom Filter
- Counting Bloom Filter
- Cuckoo Filter
- SuRF (Simplified Version)

An exact hash-set server is also included as a baseline for comparison.



## Implemented MCP Servers

| MCP Server | Data Structure | Description |
|---|---|---|
| `filter-naive` | Exact Set / Hash Table | Exact membership baseline |
| `filter-bloom` | Bloom Filter | Memory-efficient approximate membership filter |
| `filter-counting-bloom` | Counting Bloom Filter | Bloom Filter with deletion support |
| `filter-cuckoo` | Cuckoo Filter | Fingerprint-based approximate filter |
| `filter-surf` | Simplified SuRF | Approximate prefix/range filter |



## Project Goal

The goal of this project is to compare how different filter structures behave under the same workload.

The comparison focuses on:

- membership query accuracy
- false positive rate
- memory usage
- query latency
- insertion and deletion support
- prefix and range query capability

All servers expose the same ADT-style interface through MCP tools so that they can be tested consistently.



## Scenario

### Search Keyword Dictionary Management

The servers simulate a keyword search system.

Examples:
- search autocomplete
- keyword lookup
- blocked-word checking
- dictionary membership testing

The same keyword dataset and queries are used across all filters to compare performance and behavior.



## ADT

All MCP servers provide the following tools:

| Tool | Description |
|---|---|
| `build(items)` | Build filter from dataset |
| `insert(x)` | Insert a key |
| `contains(x)` | Membership query |
| `delete(x)` | Delete a key if supported |
| `range_query(lo, hi)` | Range query |
| `prefix_query(prefix)` | Prefix query |
| `memory_usage()` | Return estimated memory usage |
| `false_positive_rate()` | Measure false positive rate |


## Theoretical / Qualitative Structure Comparison

| Structure | False Positives | Delete Support | Prefix/Range Query | Memory Efficiency |
|---|---|---|---|---|
| Exact Set | No | Yes | Yes | Low |
| Bloom Filter | Yes | No | No | Very High |
| Counting Bloom Filter | Yes | Yes | No | High |
| Cuckoo Filter | Yes | Yes | No | High |
| Simplified SuRF | Yes | No | Yes | Medium |

This table describes the expected qualitative behavior of each structure. It is not a measured benchmark result.



## Benchmark Results

Measured results are available in [docs/benchmark_results.md](docs/benchmark_results.md).

The benchmark uses fixed synthetic workloads from `src/membership_filters/benchmark.py` and compares all filters with the same build items and absent-query probes. It reports estimated memory from `memory_usage()`, measured false positive rate from `false_positive_rate()`, and average local `contains()` latency.

Run it locally:

```bash
PYTHONPATH=src python -m membership_filters.benchmark
```

```powershell
$env:PYTHONPATH='src'; python -m membership_filters.benchmark
```

Run the smoke tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

```powershell
$env:PYTHONPATH='src'; python -m unittest discover -s tests
```



## Notes

- `filter-naive` is included as the exact baseline.
- The SuRF server is a simplified educational implementation, not a full LOUDS-based production SuRF.
- The project focuses on comparison and experimentation rather than production optimization.



## Example Claude Desktop MCP Configuration

```json
{
  "mcpServers": {
    "filter-naive": {
      "command": "python",
      "args": ["src/filter_/filter_naive_server.py"]
    },
    "filter-bloom": {
      "command": "python",
      "args": ["src/filter_/filter_bloom_server.py"]
    },
    "filter-counting-bloom": {
      "command": "python",
      "args": ["src/filter_/filter_counting_bloom_server.py"]
    },
    "filter-cuckoo": {
      "command": "python",
      "args": ["src/filter_/filter_cuckoo_server.py"]
    },
    "filter-surf": {
      "command": "python",
      "args": ["src/filter_/filter_surf_server.py"]
    }
  }
}
```
## System Flow

```text
Claude / LLM
        ↓
MCP Tool Call
        ↓
mcp_server.py
        ↓
registry.py
        ↓
Selected Filter Class
        ↓
Bloom / Counting Bloom / Cuckoo / SuRF / Exact Set
```

### Flow Description

1. The LLM sends an MCP tool request.
2. `mcp_server.py` exposes the common ADT-style tools.
3. `registry.py` selects the requested filter implementation.
4. The selected filter processes the query.
5. The result is returned back through the MCP server.

This design allows all filters to be tested through the same interface and workload.


## Repository Structure


```text
src/
├── filter_/
│   ├── filter_naive_server.py
│   ├── filter_bloom_server.py
│   ├── filter_counting_bloom_server.py
│   ├── filter_cuckoo_server.py
│   └── filter_surf_server.py
│
└── membership_filters/
    ├── base.py
    ├── hashing.py
    ├── mcp_server.py
    ├── registry.py
    └── filters/
```
