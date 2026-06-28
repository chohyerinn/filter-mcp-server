# Benchmark Results

These are measured outputs from the repeatable workloads in `src/membership_filters/benchmark.py`.

- Command: `PYTHONPATH=src python -m membership_filters.benchmark`
- Python: 3.14.2
- Workloads: `point_membership`, `delete_heavy`, `prefix_range`
- Default configuration: `target_fpr=0.01`, `fingerprint_bits=12`, `bucket_size=4`, `counter_bits=4`, `suffix_bits=8`, `trie_depth=8`

The memory values are estimates returned by each filter's `memory_usage()` method. The FPR values are measured by probing fixed absent-key sets through `false_positive_rate()`. `Avg us/q` is the average Python `contains()` method time over 10,000 point queries; it does not include MCP transport or client latency.

## point_membership

| Filter | Items | Memory (B) | Bits/Item | FPR | False Positives | Avg us/q | Delete | Prefix | Range |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| naive | 1000 | 85984 | 687.87 | 0.0000 | 0 | 0.44 | True | True | True |
| bloom | 1000 | 1199 | 9.59 | 0.0110 | 11 | 4.19 | False | False | False |
| counting_bloom | 1000 | 4793 | 38.34 | 0.0110 | 11 | 3.42 | True | False | False |
| cuckoo | 1000 | 3072 | 24.58 | 0.0000 | 0 | 3.35 | True | False | False |
| surf | 1000 | 515 | 4.12 | 0.0000 | 0 | 1.13 | False | True | True |

## delete_heavy

| Filter | Items | Memory (B) | Bits/Item | FPR | False Positives | Avg us/q | Delete | Prefix | Range |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| naive | 900 | 80684 | 717.19 | 0.0000 | 0 | 0.45 | True | True | True |
| bloom | 1000 | 1199 | 9.59 | 0.0110 | 11 | 3.52 | False | False | False |
| counting_bloom | 900 | 4793 | 42.60 | 0.0070 | 11 | 2.90 | True | False | False |
| cuckoo | 900 | 3072 | 27.31 | 0.0000 | 0 | 3.26 | True | False | False |
| surf | 1000 | 515 | 4.12 | 0.0000 | 0 | 1.16 | False | True | True |

## prefix_range

| Filter | Items | Memory (B) | Bits/Item | FPR | False Positives | Avg us/q | Delete | Prefix | Range |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| naive | 1500 | 210788 | 1124.20 | 0.0000 | 0 | 0.42 | True | True | True |
| bloom | 1500 | 1798 | 9.59 | 0.0060 | 6 | 3.38 | False | False | False |
| counting_bloom | 1500 | 7189 | 38.34 | 0.0060 | 6 | 3.11 | True | False | False |
| cuckoo | 1500 | 3072 | 16.38 | 0.0010 | 1 | 3.11 | True | False | False |
| surf | 1500 | 1026 | 5.47 | 0.0000 | 0 | 1.13 | False | True | True |

## Notes

- The exact set is the correctness baseline, not an approximate filter.
- Bloom and Counting Bloom show measured false positives on the fixed absent-query probes.
- Latency values are small local method-call measurements, not end-to-end MCP tool-call timings.
- SuRF here is a simplified educational implementation, so its results should not be read as production SuRF performance.
- These results are for small synthetic workloads and are intended to make the comparison reproducible, not to claim general benchmark superiority.
