# Sort performance (bubble / insertion / quick / merge)

## Method

Inputs use `random.Random(0)` for the `random` pattern; `sorted`, `reverse`, and `all_equal` are deterministic. Sizes: 100, 1_000, 10_000, 50_000. Every comparison goes through a `_Counted` wrapper (`<` increments a counter) so bubble, insertion, quick (bench-only implementations in this script), and production `mini_git.sort.merge_sort` are measured the same way. Wall-clock times are single runs with `time.perf_counter()` and vary by machine; comparison counts are deterministic given the fixed seed.

## Comparison counts

Source of truth (deterministic).

### random

| algorithm | 100 | 1000 | 10000 | 50000 |
| --- | --- | --- | --- | --- |
| bubble | 4929 | 499310 | 49987979 | 1249956085 |
| insertion | 2696 | 257723 | 25127405 | 624168644 |
| quick | 717 | 10986 | 145516 | 870468 |
| merge | 826 | 13112 | 181776 | 1081538 |

### sorted

| algorithm | 100 | 1000 | 10000 | 50000 |
| --- | --- | --- | --- | --- |
| bubble | 99 | 999 | 9999 | 49999 |
| insertion | 99 | 999 | 9999 | 49999 |
| quick | 606 | 9009 | 125439 | 750015 |
| merge | 316 | 4932 | 64608 | 382512 |

### reverse

| algorithm | 100 | 1000 | 10000 | 50000 |
| --- | --- | --- | --- | --- |
| bubble | 4950 | 499500 | 49995000 | 1249975000 |
| insertion | 4950 | 499500 | 49995000 | 1249975000 |
| quick | 825 | 15773 | 239905 | 1491785 |
| merge | 712 | 10088 | 138016 | 803904 |

### all_equal

| algorithm | 100 | 1000 | 10000 | 50000 |
| --- | --- | --- | --- | --- |
| bubble | 99 | 999 | 9999 | 49999 |
| insertion | 99 | 999 | 9999 | 49999 |
| quick | 5247 | 502497 | 50024997 | 1250124997 |
| merge | 632 | 9864 | 129216 | 765024 |

## Wall-clock (ms)

Anecdotal; re-run `python3 scripts/bench_sort.py` on your machine.

### random

| algorithm | 100 | 1000 | 10000 | 50000 |
| --- | --- | --- | --- | --- |
| bubble | 1.23 | 125.93 | 12992.75 | 330325.95 |
| insertion | 0.66 | 63.90 | 6436.27 | 162856.04 |
| quick | 0.22 | 3.27 | 42.66 | 245.49 |
| merge | 0.46 | 7.11 | 94.36 | 548.42 |

### sorted

| algorithm | 100 | 1000 | 10000 | 50000 |
| --- | --- | --- | --- | --- |
| bubble | 0.05 | 0.38 | 4.26 | 21.08 |
| insertion | 0.04 | 0.42 | 4.55 | 23.32 |
| quick | 0.20 | 2.71 | 36.05 | 212.74 |
| merge | 0.28 | 3.93 | 49.22 | 282.50 |

### reverse

| algorithm | 100 | 1000 | 10000 | 50000 |
| --- | --- | --- | --- | --- |
| bubble | 1.32 | 134.40 | 13850.43 | 348357.71 |
| insertion | 1.24 | 121.48 | 12297.20 | 310025.23 |
| quick | 0.26 | 4.50 | 65.52 | 400.75 |
| merge | 0.38 | 5.04 | 65.79 | 376.06 |

### all_equal

| algorithm | 100 | 1000 | 10000 | 50000 |
| --- | --- | --- | --- | --- |
| bubble | 0.05 | 0.41 | 3.90 | 21.30 |
| insertion | 0.04 | 0.42 | 4.41 | 21.25 |
| quick | 1.18 | 105.45 | 10368.21 | 263105.82 |
| merge | 0.36 | 4.89 | 62.07 | 363.54 |

## Discussion

- **Asymptotics:** Bubble and insertion show roughly quadratic growth in comparison counts on `random` and `reverse`; quick and merge stay near O(N log N) across all four patterns.
- **Pattern sensitivity:** Bubble stops early on `sorted` (about N-1 comparisons) but is worst on `reverse`. Insertion is also linear on `sorted` and heavy on `random` / `reverse`.
- **Quick vs merge:** Quick (median-of-three Lomuto) tracks merge on average with fewer comparisons on some cells, but tie-heavy `all_equal` can still degrade quick toward quadratic behavior; merge stays predictable thanks to stable left-first merges.
- **Why merge_sort in core:** Stable ordering, deterministic tie-breaking, and O(N log N) on every pattern — important for `LOG --sort-by=author` and topological tie resolution without surprising regressions on already-sorted input.
