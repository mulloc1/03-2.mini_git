"""Stable merge sort (subject §4.4)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")
K = TypeVar("K")


def merge_sort(
    items: list[T],
    key: Callable[[T], K] = lambda x: x,
) -> list[T]:
    """Stable merge sort; returns a new sorted list."""
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    left = merge_sort(items[:mid], key)
    right = merge_sort(items[mid:], key)
    return _merge(left, right, key)


def _merge(left: list[T], right: list[T], key: Callable[[T], K]) -> list[T]:
    """Merge two sorted lists; on tie, prefer the left element (stable)."""
    result: list[T] = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        left_key = key(left[i])
        right_key = key(right[j])
        if left_key < right_key:
            result.append(left[i])
            i += 1
        elif right_key < left_key:
            result.append(right[j])
            j += 1
        else:
            result.append(left[i])
            i += 1
    while i < len(left):
        result.append(left[i])
        i += 1
    while j < len(right):
        result.append(right[j])
        j += 1
    return result
