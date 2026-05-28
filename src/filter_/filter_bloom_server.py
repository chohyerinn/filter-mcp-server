"""Claude MCP server entry point for Member B: Standard Bloom Filter."""

from __future__ import annotations

import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from membership_filters.mcp_server import run_server


if __name__ == "__main__":
    run_server("bloom")
