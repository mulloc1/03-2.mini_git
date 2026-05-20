"""LCS line diff utilities for bonus subject §5 (O(|a| * |b|))."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DiffKind = Literal["common", "added", "deleted"]


@dataclass(frozen=True)
class DiffLine:
    """One output line in an LCS-aligned diff."""

    kind: DiffKind
    text: str


def diff_lines(a: list[str], b: list[str]) -> list[DiffLine]:
    """Return source-ordered LCS diff records for two line lists."""
    a_len = len(a)
    b_len = len(b)
    dp = [[0] * (b_len + 1) for _ in range(a_len + 1)]

    for i in range(a_len - 1, -1, -1):
        for j in range(b_len - 1, -1, -1):
            if a[i] == b[j]:
                dp[i][j] = dp[i + 1][j + 1] + 1
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])

    i = 0
    j = 0
    out: list[DiffLine] = []
    while i < a_len or j < b_len:
        if i == a_len:
            out.append(DiffLine(kind="added", text=b[j]))
            j += 1
        elif j == b_len:
            out.append(DiffLine(kind="deleted", text=a[i]))
            i += 1
        elif a[i] == b[j]:
            out.append(DiffLine(kind="common", text=a[i]))
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            out.append(DiffLine(kind="deleted", text=a[i]))
            i += 1
        else:
            out.append(DiffLine(kind="added", text=b[j]))
            j += 1

    return out
