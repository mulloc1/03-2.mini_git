"""Test fixtures: deterministic clock and repository factory."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mini_git.repository import Repository


class FakeClock:
    """Monotonic fake clock for display-time tests."""

    def __init__(self, start: float = 0.0) -> None:
        self._t = start

    def __call__(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        self._t += seconds


def make_repo(clock: Callable[[], float] | None = None) -> Repository:
    """Build a Repository with optional injected clock."""
    from mini_git.repository import Repository

    return Repository(clock=clock or FakeClock())


def commit_linear(repo: Repository, messages: list[str]) -> list[str]:
    """Append commits on the current branch; return hashes in creation order."""
    hashes: list[str] = []
    for message in messages:
        commit = repo.commit(message)
        hashes.append(commit.hash)
    return hashes
