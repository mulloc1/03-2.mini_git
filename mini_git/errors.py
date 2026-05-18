"""Domain exceptions for the Mini Git repository engine."""

from __future__ import annotations


class RepoError(Exception):
    """Raised when a repository operation violates a precondition."""


class CommandError(Exception):
    """Raised when CLI input is malformed or violates command syntax."""
