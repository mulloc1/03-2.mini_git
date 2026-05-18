"""Repository engine combining commit graph, branches, and inverted index.

Phase 5 surface (subject §4.5): ``init`` / ``branch`` / ``switch`` / ``commit``.
Pure logic layer — returns Python values and raises :class:`RepoError`
on precondition violations. CLI layer is responsible for formatting.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from mini_git.commit import Commit, HashIssuer
from mini_git.errors import RepoError
from mini_git.inverted_index import InvertedIndex

DEFAULT_BRANCH = "main"


class Repository:
    """In-memory Mini Git repository state."""

    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        """Build an uninitialized repository; ``init`` must be called first."""
        self._clock = clock
        self._issuer = HashIssuer()
        self._index = InvertedIndex()
        self._commits: dict[str, Commit] = {}
        self._branches: dict[str, str | None] = {}
        self._children: dict[str, list[str]] = {}
        self._root_hashes: list[str] = []
        self._human_clock_at: dict[str, float] = {}
        self._head: str | None = None
        self._author: str | None = None
        self._timestamp_counter = 0

    def init(self, user_name: str) -> None:
        """Reset all session state and start a fresh repository.

        Creates the default ``main`` branch with no commit yet, makes
        ``user_name`` the active author, and rewinds the hash issuer.
        """
        self._issuer.reset()
        self._index = InvertedIndex()
        self._commits = {}
        self._branches = {DEFAULT_BRANCH: None}
        self._children = {}
        self._root_hashes = []
        self._human_clock_at = {}
        self._head = DEFAULT_BRANCH
        self._author = user_name
        self._timestamp_counter = 0

    def branch(self, branch_name: str) -> str:
        """Register a new branch pointing at the current HEAD commit.

        Returns the commit hash the branch points to. Raises
        :class:`RepoError` if there is no commit yet on HEAD or the
        branch name already exists.
        """
        self._require_initialized()
        head_branch = self._current_branch()
        head_commit = self._branches[head_branch]
        if head_commit is None:
            raise RepoError("Cannot branch before first commit")
        if branch_name in self._branches:
            raise RepoError(f"Branch already exists: {branch_name}")
        self._branches[branch_name] = head_commit
        return head_commit

    def switch(self, branch_name: str) -> None:
        """Move HEAD to an existing branch; unknown name raises ``RepoError``."""
        self._require_initialized()
        if branch_name not in self._branches:
            raise RepoError(f"Unknown branch: {branch_name}")
        self._head = branch_name

    def commit(self, message: str) -> Commit:
        """Create a commit on the current branch and return it.

        The parent is the current HEAD commit (or none for the very first
        commit). Updates the commit graph, branch pointer, child index,
        inverted index, and human-readable clock map.
        """
        self._require_initialized()
        head_branch = self._current_branch()
        parent = self._branches[head_branch]
        parents: tuple[str, ...] = () if parent is None else (parent,)

        new_hash = self._issuer.issue()
        self._timestamp_counter += 1
        commit = Commit(
            hash=new_hash,
            message=message,
            author=self._author or "",
            timestamp=self._timestamp_counter,
            parents=parents,
        )

        self._commits[new_hash] = commit
        self._branches[head_branch] = new_hash
        self._human_clock_at[new_hash] = self._clock()
        if parent is None:
            self._root_hashes.append(new_hash)
        else:
            self._children.setdefault(parent, []).append(new_hash)
        self._index.add_commit(commit)
        return commit

    @property
    def head(self) -> str | None:
        """Current branch name, or ``None`` if the repository is uninitialized."""
        return self._head

    @property
    def author(self) -> str | None:
        """Active author name, or ``None`` if the repository is uninitialized."""
        return self._author

    def head_commit(self) -> str | None:
        """Return the current branch's commit hash (``None`` before first commit)."""
        return self._branches[self._current_branch()]

    def branches(self) -> dict[str, str | None]:
        """Return a snapshot copy of the branch name → commit hash map."""
        return dict(self._branches)

    def get_commit(self, commit_hash: str) -> Commit:
        """Look up a commit by hash; unknown hashes raise ``RepoError``."""
        self._require_initialized()
        if commit_hash not in self._commits:
            raise RepoError(f"Unknown commit: {commit_hash}")
        return self._commits[commit_hash]

    def _current_branch(self) -> str:
        self._require_initialized()
        assert self._head is not None
        return self._head

    def _require_initialized(self) -> None:
        if self._head is None:
            raise RepoError("Repository not initialized")
