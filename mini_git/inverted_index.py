"""Inverted index for keyword and author search (subject §4.3)."""

from __future__ import annotations

from mini_git.commit import Commit


def _tokenize(message: str) -> set[str]:
    """Split message on whitespace and normalize tokens to lowercase."""
    return {token.lower() for token in message.split()}


class InvertedIndex:
    """Keyword and author inverted indexes mapping to commit hashes."""

    def __init__(self) -> None:
        self._by_keyword: dict[str, list[str]] = {}
        self._by_author: dict[str, list[str]] = {}

    def add_commit(self, commit: Commit) -> None:
        """Index commit message tokens and author."""
        for token in _tokenize(commit.message):
            self._append(self._by_keyword, token, commit.hash)
        self._append(self._by_author, commit.author, commit.hash)

    def search_keyword(self, token: str) -> list[str]:
        """Return commit hashes whose message contains the exact token."""
        return list(self._by_keyword.get(token.lower(), []))

    def search_author(self, name: str) -> list[str]:
        """Return commit hashes by exact author name (case-sensitive)."""
        return list(self._by_author.get(name, []))

    def remove_commit(self, commit_hash: str) -> None:
        """Remove a commit hash from all keyword and author lists."""
        for hashes in self._by_keyword.values():
            self._remove_hash(hashes, commit_hash)
        for hashes in self._by_author.values():
            self._remove_hash(hashes, commit_hash)

    def _append(self, index: dict[str, list[str]], key: str, commit_hash: str) -> None:
        if key not in index:
            index[key] = []
        if commit_hash not in index[key]:
            index[key].append(commit_hash)

    @staticmethod
    def _remove_hash(hashes: list[str], commit_hash: str) -> None:
        while commit_hash in hashes:
            hashes.remove(commit_hash)
