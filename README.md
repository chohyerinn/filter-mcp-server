# Approximate Filters

## Bloom Filter, Counting Bloom Filter, Cuckoo Filter, and SuRF Comparison using MCP Servers

This project compares approximate filters through MCP servers and LLM tool calls.

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
