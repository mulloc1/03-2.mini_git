"""Graph algorithms for commit DAG (subject §4.5)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import Any

from mini_git.sort import merge_sort


def topological_order(
    
    hashes: Iterable[str],
    get_parents: Callable[[str], Iterable[str]],
    get_sort_key: Callable[[str], Any],
) -> list[str]:
    """Return hashes in parent-before-child order (Kahn's algorithm)."""
    hash_set = set(hashes)
    if not hash_set:
        return []

    in_degree: dict[str, int] = {h: 0 for h in hash_set}
    children: dict[str, list[str]] = defaultdict(list)

    for child in hash_set:
        for parent in get_parents(child):
            if parent not in hash_set:
                continue
            children[parent].append(child)
            in_degree[child] += 1

    ready = [h for h in hash_set if in_degree[h] == 0]
    queue = merge_sort(ready, key=get_sort_key)
    result: list[str] = []

    while queue:
        current = queue.pop(0)
        result.append(current)
        newly_ready: list[str] = []
        for child in children[current]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                newly_ready.append(child)
        if newly_ready:
            queue.extend(merge_sort(newly_ready, key=get_sort_key))

    return result


def shortest_path(
    start: str,
    goal: str,
    get_neighbors: Callable[[str], Iterable[str]],
) -> list[str] | None:
    """Return lexicographically smallest shortest path, or None if unreachable."""
    if start == goal:
        return [start]

    dist: dict[str, int] = {start: 0}
    best: dict[str, list[str]] = {start: [start]}
    queue: list[str] = [start]

    while queue:
        current = queue.pop(0)
        current_dist = dist[current]
        for neighbor in merge_sort(list(get_neighbors(current)), key=lambda h: h):
            next_dist = current_dist + 1
            candidate = best[current] + [neighbor]
            if neighbor not in dist:
                dist[neighbor] = next_dist
                best[neighbor] = candidate
                queue.append(neighbor)
                if neighbor == goal:
                    return best[goal]
            elif next_dist == dist[neighbor] and _path_key(candidate) < _path_key(
                best[neighbor]
            ):
                best[neighbor] = candidate
                if neighbor == goal:
                    return best[goal]

    return None


def ancestors(
    start: str,
    get_parents: Callable[[str], Iterable[str]],
) -> set[str]:
    """Return all ancestor hashes reachable via parents; excludes start."""
    visited: set[str] = {start}
    queue: list[str] = list(get_parents(start))
    found: set[str] = set()

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        found.add(current)
        for parent in get_parents(current):
            if parent not in visited:
                queue.append(parent)

    return found


def _path_key(path: list[str]) -> str:
    """Build the PATH output string used for lexicographic comparison."""
    return "->".join(path)
