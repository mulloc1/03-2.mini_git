"""Application entry composition for Mini Git REPL."""

from __future__ import annotations

from mini_git.cli import run_repl
from mini_git.repository import Repository


def main(argv: list[str] | None = None) -> int:
    """Run Mini Git REPL and return process exit code."""
    del argv
    repo = Repository()
    run_repl(repo)
    return 0
