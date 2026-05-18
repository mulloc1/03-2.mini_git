"""Commit node and session hash issuer (subject §4.2)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Commit:
    """Immutable DAG commit node."""

    hash: str
    message: str
    author: str
    timestamp: int
    parents: tuple[str, ...] = ()


class HashIssuer:
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
