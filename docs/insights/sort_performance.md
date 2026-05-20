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
| bubble | 1.34 | 142.19 | 13086.82 | 329366.35 |
| insertion | 0.94 | 63.71 | 6482.20 | 159840.01 |
| quick | 0.31 | 3.37 | 42.35 | 244.12 |
| merge | 0.55 | 7.00 | 93.01 | 536.25 |

### sorted

| algorithm | 100 | 1000 | 10000 | 50000 |
| --- | --- | --- | --- | --- |
| bubble | 0.04 | 0.38 | 4.23 | 20.25 |
| insertion | 0.04 | 0.43 | 4.60 | 22.85 |
| quick | 0.20 | 2.89 | 35.87 | 210.88 |
| merge | 0.27 | 3.88 | 48.22 | 278.06 |

### reverse

| algorithm | 100 | 1000 | 10000 | 50000 |
| --- | --- | --- | --- | --- |
| bubble | 1.31 | 132.36 | 13495.18 | 341609.82 |
| insertion | 1.21 | 121.16 | 12111.06 | 306531.60 |
| quick | 0.25 | 4.45 | 64.91 | 398.31 |
| merge | 0.37 | 4.93 | 65.53 | 376.70 |

### all_equal

| algorithm | 100 | 1000 | 10000 | 50000 |
| --- | --- | --- | --- | --- |
| bubble | 0.05 | 0.38 | 3.89 | 21.98 |
| insertion | 0.04 | 0.42 | 4.37 | 21.19 |
| quick | 1.21 | 106.05 | 10325.08 | 259683.09 |
| merge | 0.35 | 4.79 | 62.81 | 359.89 |

## Discussion

- **Asymptotics:** Bubble and insertion show roughly quadratic growth in comparison counts on `random` and `reverse`; quick and merge stay near O(N log N) across all four patterns.
- **Pattern sensitivity:** Bubble stops early on `sorted` (about N-1 comparisons) but is worst on `reverse`. Insertion is also linear on `sorted` and heavy on `random` / `reverse`.
- **Quick vs merge:** Quick (median-of-three Lomuto) tracks merge on average with fewer comparisons on some cells, but tie-heavy `all_equal` can still degrade quick toward quadratic behavior; merge stays predictable thanks to stable left-first merges.
- **Why merge_sort in core:** Stable ordering, deterministic tie-breaking, and O(N log N) on every pattern — important for `LOG --sort-by=author` and topological tie resolution without surprising regressions on already-sorted input.
