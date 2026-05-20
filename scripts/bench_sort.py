"""Benchmark bubble, insertion, quick, and merge sort (bonus §5 item 3)."""

from __future__ import annotations

import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mini_git.sort import merge_sort

SEED = 0
PATTERNS = ("random", "sorted", "reverse", "all_equal")
SIZES = (100, 1_000, 10_000, 50_000)
ALGORITHMS = ("bubble", "insertion", "quick", "merge")
OUTPUT_PATH = ROOT / "docs" / "insights" / "sort_performance.md"


class _Counted:
    """Comparison wrapper; every `<` increments a class-level counter."""

    count = 0
    __slots__ = ("value",)

    def __init__(self, value: int) -> None:
        self.value = value

    def __lt__(self, other: _Counted) -> bool:
        _Counted.count += 1
        return self.value < other.value


def _wrap(items: list[int]) -> list[_Counted]:
    return [_Counted(x) for x in items]


def _make_input(pattern: str, size: int, rng: random.Random) -> list[int]:
    if pattern == "random":
        return [rng.randint(0, 10**9) for _ in range(size)]
    if pattern == "sorted":
        return list(range(size))
    if pattern == "reverse":
        return list(range(size, 0, -1))
    if pattern == "all_equal":
        return [0] * size
    raise ValueError(pattern)


def _bubble_sort(items: list[_Counted]) -> None:
    n = len(items)
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            if items[j + 1] < items[j]:
                items[j], items[j + 1] = items[j + 1], items[j]
                swapped = True
        if not swapped:
            return


def _insertion_sort(items: list[_Counted]) -> None:
    for i in range(1, len(items)):
        cur = items[i]
        j = i - 1
        while j >= 0 and cur < items[j]:
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = cur


def _quick_sort(items: list[_Counted]) -> None:
    def _median_of_three(lo: int, hi: int) -> int:
        mid = (lo + hi) // 2
        a, b, c = items[lo], items[mid], items[hi]
        if a < b:
            if b < c:
                return mid
            return hi if a < c else lo
        if a < c:
            return lo
        return hi if b < c else mid

    def _partition(lo: int, hi: int) -> int:
        pivot_idx = _median_of_three(lo, hi)
        items[pivot_idx], items[hi] = items[hi], items[pivot_idx]
        pivot = items[hi]
        store = lo
        for k in range(lo, hi):
            if items[k] < pivot:
                items[store], items[k] = items[k], items[store]
                store += 1
        items[store], items[hi] = items[hi], items[store]
        return store

    stack: list[tuple[int, int]] = [(0, len(items) - 1)]
    while stack:
        lo, hi = stack.pop()
        if lo >= hi:
            continue
        p = _partition(lo, hi)
        stack.append((lo, p - 1))
        stack.append((p + 1, hi))


_DISPATCH = {
    "bubble": _bubble_sort,
    "insertion": _insertion_sort,
    "quick": _quick_sort,
}


def _run_sort(algo: str, base: list[int]) -> None:
    if algo == "merge":
        merge_sort(list(base), key=_Counted)
    else:
        _DISPATCH[algo](_wrap(base))


def _sorted_values(algo: str, base: list[int]) -> list[int]:
    if algo == "merge":
        return merge_sort(list(base), key=_Counted)
    data = _wrap(base)
    _DISPATCH[algo](data)
    return [c.value for c in data]


def _measure_all() -> tuple[dict[tuple[str, str, int], int], dict[tuple[str, str, int], float]]:
    counts: dict[tuple[str, str, int], int] = {}
    wall_ms: dict[tuple[str, str, int], float] = {}
    for pattern in PATTERNS:
        rng = random.Random(SEED)
        for size in SIZES:
            base = _make_input(pattern, size, rng)
            for algo in ALGORITHMS:
                _Counted.count = 0
                t0 = time.perf_counter()
                _run_sort(algo, base)
                wall_ms[(algo, pattern, size)] = (time.perf_counter() - t0) * 1000
                counts[(algo, pattern, size)] = _Counted.count
                print(f"done {algo} {pattern} n={size}", file=sys.stderr, flush=True)
    return counts, wall_ms


def _format_table(
    pattern: str,
    values: dict[tuple[str, str, int], int | float],
    *,
    float_fmt: bool = False,
) -> str:
    header = "| algorithm | " + " | ".join(str(s) for s in SIZES) + " |"
    sep = "| --- | " + " | ".join("---" for _ in SIZES) + " |"
    rows: list[str] = [header, sep]
    for algo in ALGORITHMS:
        cells: list[str] = []
        for size in SIZES:
            val = values[(algo, pattern, size)]
            if float_fmt:
                cells.append(f"{val:.2f}")
            else:
                cells.append(str(val))
        rows.append("| " + algo + " | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def _build_markdown(
    counts: dict[tuple[str, str, int], int],
    wall_ms: dict[tuple[str, str, int], float],
) -> str:
    parts: list[str] = [
        "# Sort performance (bubble / insertion / quick / merge)",
        "",
        "## Method",
        "",
        "Inputs use `random.Random(0)` for the `random` pattern; "
        "`sorted`, `reverse`, and `all_equal` are deterministic. "
        "Sizes: 100, 1_000, 10_000, 50_000. "
        "Every comparison goes through a `_Counted` wrapper (`<` increments a counter) "
        "so bubble, insertion, quick (bench-only implementations in this script), "
        "and production `mini_git.sort.merge_sort` are measured the same way. "
        "Wall-clock times are single runs with `time.perf_counter()` and vary by machine; "
        "comparison counts are deterministic given the fixed seed.",
        "",
        "## Comparison counts",
        "",
        "Source of truth (deterministic).",
        "",
    ]
    for pattern in PATTERNS:
        parts.append(f"### {pattern}")
        parts.append("")
        parts.append(_format_table(pattern, counts))
        parts.append("")
    parts.extend(
        [
            "## Wall-clock (ms)",
            "",
            "Anecdotal; re-run `python3 scripts/bench_sort.py` on your machine.",
            "",
        ]
    )
    for pattern in PATTERNS:
        parts.append(f"### {pattern}")
        parts.append("")
        parts.append(_format_table(pattern, wall_ms, float_fmt=True))
        parts.append("")
    parts.extend(
        [
            "## Discussion",
            "",
            "- **Asymptotics:** Bubble and insertion show roughly quadratic growth in "
            "comparison counts on `random` and `reverse`; quick and merge stay near "
            "O(N log N) across all four patterns.",
            "- **Pattern sensitivity:** Bubble stops early on `sorted` (about N-1 comparisons) "
            "but is worst on `reverse`. Insertion is also linear on `sorted` and heavy on "
            "`random` / `reverse`.",
            "- **Quick vs merge:** Quick (median-of-three Lomuto) tracks merge on average "
            "with fewer comparisons on some cells, but tie-heavy `all_equal` can still "
            "degrade quick toward quadratic behavior; merge stays predictable thanks to "
            "stable left-first merges.",
            "- **Why merge_sort in core:** Stable ordering, deterministic tie-breaking, and "
            "O(N log N) on every pattern — important for `LOG --sort-by=author` and "
            "topological tie resolution without surprising regressions on already-sorted input.",
            "",
        ]
    )
    return "\n".join(parts)


def _sanity_check() -> None:
    base = [3, 1, 4, 1, 5, 9, 2, 6]
    expected = sorted(base)
    for algo in ALGORITHMS:
        assert _sorted_values(algo, base) == expected, algo


def main() -> None:
    _sanity_check()
    counts, wall_ms = _measure_all()
    markdown = _build_markdown(counts, wall_ms)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
