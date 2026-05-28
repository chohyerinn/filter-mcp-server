# Approximate Filters

## Bloom Filter, Counting Bloom Filter, Cuckoo Filter, and SuRF Comparison using MCP Servers

This project compares approximate filters through MCP servers and LLM tool calls.
Approximate filters reduce memory usage by storing compact summaries instead of
full keys. The trade-off is that some structures may return false positives or
support only limited operations.

Implemented servers:

| MCP Server | Data Structure | Role |
| --- | --- | --- |
| `filter-naive` | Naive Set / Hash Table | Exact baseline |
| `filter-bloom` | Standard Bloom Filter | Memory-efficient approximate membership filter |
| `filter-counting-bloom` | Counting Bloom Filter | Bloom Filter with deletion support |
| `filter-cuckoo` | Cuckoo Filter | Fingerprint-based approximate membership filter |
| `filter-surf` | Simplified SuRF | Approximate prefix/range filter |

Scenario:

> Search Keyword Dictionary Management

The same keyword workload is used across all servers to compare membership lookup,
false positive rate, memory usage, latency, insertion/deletion support, and
prefix/range query capability.

Project flow:

1. Start with exact set membership as the baseline.
2. Compare approximate membership filters: Bloom, Counting Bloom, and Cuckoo.
3. Extend the comparison to SuRF, an approximate range filter for prefix/range queries.
4. Let an LLM call the MCP servers using the same ADT and workload.

Note:

- `filter-naive` is not an approximate filter. It is included as the exact baseline.
- SuRF is not only a point membership filter. It is included because approximate filters can also target prefix/range workloads.

Claude Desktop MCP config example:

```json
{
  "mcpServers": {
    "filter-naive": {
      "command": "C:\\Users\\chohy\\OneDrive\\문서\\DataStructure\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\chohy\\OneDrive\\문서\\DataStructure\\src\\filter_\\filter_naive_server.py"]
    },
    "filter-bloom": {
      "command": "C:\\Users\\chohy\\OneDrive\\문서\\DataStructure\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\chohy\\OneDrive\\문서\\DataStructure\\src\\filter_\\filter_bloom_server.py"]
    },
    "filter-counting-bloom": {
      "command": "C:\\Users\\chohy\\OneDrive\\문서\\DataStructure\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\chohy\\OneDrive\\문서\\DataStructure\\src\\filter_\\filter_counting_bloom_server.py"]
    },
    "filter-cuckoo": {
      "command": "C:\\Users\\chohy\\OneDrive\\문서\\DataStructure\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\chohy\\OneDrive\\문서\\DataStructure\\src\\filter_\\filter_cuckoo_server.py"]
    },
    "filter-surf": {
      "command": "C:\\Users\\chohy\\OneDrive\\문서\\DataStructure\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\chohy\\OneDrive\\문서\\DataStructure\\src\\filter_\\filter_surf_server.py"]
    }
  }
}
```

See:

- `filter_project_final_guide.md`
- `LLM 실험예시.txt`
