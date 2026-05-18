"""Domain exceptions for the Mini Git repository engine."""

from __future__ import annotations


class RepoError(Exception):
    """Raised when a repository operation violates a precondition."""
