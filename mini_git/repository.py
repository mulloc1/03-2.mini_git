"""Repository engine combining commit graph, branches, and inverted index.

Pure logic layer — returns Python values and raises :class:`RepoError`
on precondition violations. CLI layer is responsible for formatting.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable

from mini_git.commit import Commit, HashIssuer
from mini_git.errors import RepoError
from mini_git.graph import ancestors as graph_ancestors
from mini_git.graph import shortest_path, topological_order
from mini_git.inverted_index import InvertedIndex
from mini_git.sort import merge_sort

DEFAULT_BRANCH = "main"
_LOG_SORT_KEYS = ("date", "author")


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

    def merge(self, branch_name: str) -> Commit:
        """Create a two-parent merge commit on the current branch and return it."""
        self._require_initialized()
        current_branch = self._current_branch()
        if branch_name not in self._branches:
            raise RepoError(f"Unknown branch: {branch_name}")
        if branch_name == current_branch:
            raise RepoError("Cannot merge a branch with itself")

        current_head = self._branches[current_branch]
        target_head = self._branches[branch_name]
        if current_head is None or target_head is None:
            raise RepoError("Cannot merge before first commit")

        ancestor_hashes = graph_ancestors(
            current_head,
            get_parents=lambda h: self._commits[h].parents,
        )
        if target_head in ancestor_hashes:
            raise RepoError("Already up to date")

        new_hash = self._issuer.issue()
        self._timestamp_counter += 1
        commit = Commit(
            hash=new_hash,
            message=f"Merge branch {branch_name}",
            author=self._author or "",
            timestamp=self._timestamp_counter,
            parents=(current_head, target_head),
        )

        self._commits[new_hash] = commit
        self._branches[current_branch] = new_hash
        self._human_clock_at[new_hash] = self._clock()
        self._children.setdefault(current_head, []).append(new_hash)
        self._children.setdefault(target_head, []).append(new_hash)
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

    def human_clock_at(self, commit_hash: str) -> float:
        """Return the human-readable clock value stored at commit creation."""
        self._require_initialized()
        self.get_commit(commit_hash)
        return self._human_clock_at[commit_hash]

    def log(self) -> list[Commit]:
        """Return all commits in parent-before-child topological order."""
        self._require_initialized()
        return self._topo_commits(self._commits)

    def log_sorted(self, by: str) -> list[Commit]:
        """Return all commits sorted by ``date`` or ``author`` via merge sort."""
        self._require_initialized()
        if by not in _LOG_SORT_KEYS:
            raise RepoError(f"Invalid sort key: {by}")
        commits = list(self._commits.values())
        if by == "date":
            return merge_sort(commits, key=lambda c: (c.timestamp, c.hash))
        return merge_sort(
            commits, key=lambda c: (c.author, c.timestamp, c.hash)
        )

    def path(self, start: str, goal: str) -> list[str] | None:
        """Return lex-min shortest undirected path between two commits."""
        self._require_initialized()
        self.get_commit(start)
        self.get_commit(goal)

        def neighbors(commit_hash: str) -> list[str]:
            commit = self._commits[commit_hash]
            return list(commit.parents) + self._children.get(commit_hash, [])

        return shortest_path(start, goal, neighbors)

    def ancestors(self, commit_hash: str) -> list[Commit]:
        """Return all ancestors of ``commit_hash`` in topological order."""
        self._require_initialized()
        self.get_commit(commit_hash)
        ancestor_hashes = graph_ancestors(
            commit_hash,
            get_parents=lambda h: self._commits[h].parents,
        )
        return self._topo_commits(ancestor_hashes)

    def search_keyword(self, keyword: str) -> list[Commit]:
        """Return commits whose message contains the exact token."""
        self._require_initialized()
        hashes = self._index.search_keyword(keyword)
        return self._topo_commits(hashes)

    def search_author(self, name: str) -> list[Commit]:
        """Return commits by exact author name (case-sensitive)."""
        self._require_initialized()
        hashes = self._index.search_author(name)
        return self._topo_commits(hashes)

    def _topo_commits(self, hashes: Iterable[str]) -> list[Commit]:
        ordered = topological_order(
            hashes,
            get_parents=lambda h: self._commits[h].parents,
            get_sort_key=lambda h: (self._commits[h].timestamp, h),
        )
        return [self._commits[h] for h in ordered]

    def _current_branch(self) -> str:
        self._require_initialized()
        assert self._head is not None
        return self._head

    def _require_initialized(self) -> None:
        if self._head is None:
            raise RepoError("Repository not initialized")
