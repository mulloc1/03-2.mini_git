"""Commit node and session hash generator (subject §4.2)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Commit:
    """Immutable DAG commit node.

    ``timestamp`` is a monotonic creation-order integer for sort/tie-break.
    ``created_at`` is a ``clock()`` snapshot for human-readable LOG display.
    ``branch`` is the branch name that was HEAD when the commit was created.
    """

    hash: str
    message: str
    author: str
    timestamp: int
    created_at: float = 0.0
    branch: str = ""
    parents: tuple[str, ...] = ()


class HashGenerator:
    """Session monotonic counter producing 7-digit hex commit hashes."""

    def __init__(self) -> None:
        self._counter = 0

    def issue(self) -> str:
        """Return the next unique hash for this session."""
        self._counter += 1
        return f"{self._counter:07x}"

    def reset(self) -> None:
        """Reset counter so the next issue() returns 0000001."""
        self._counter = 0
