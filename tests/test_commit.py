"""Tests for mini_git.commit."""

from __future__ import annotations

import dataclasses
import unittest

from mini_git.commit import Commit, HashIssuer


class TestHashIssuer(unittest.TestCase):
    # 연속 issue()가 0000001, 0000002, 0000003 순서로 고유한지 검증한다.
    def test_hash_issuer_sequential_unique(self) -> None:
        issuer = HashIssuer()
        h1 = issuer.issue()
        h2 = issuer.issue()
        h3 = issuer.issue()
        self.assertEqual(h1, "0000001")
        self.assertEqual(h2, "0000002")
        self.assertEqual(h3, "0000003")
        self.assertNotEqual(h1, h2)
        self.assertNotEqual(h2, h3)

    # reset() 후 다음 issue()가 0000001부터 다시 시작하는지 검증한다.
    def test_hash_issuer_reset(self) -> None:
        issuer = HashIssuer()
        issuer.issue()
        issuer.issue()
        issuer.reset()
        self.assertEqual(issuer.issue(), "0000001")

    # 해시가 7자리 16진수 형식인지 검증한다.
    def test_hash_format_seven_hex_digits(self) -> None:
        h = HashIssuer().issue()
        self.assertEqual(len(h), 7)
        int(h, 16)


class TestCommit(unittest.TestCase):
    # frozen Commit 필드 변경 시 FrozenInstanceError가 나는지 검증한다.
    def test_commit_immutable(self) -> None:
        commit = Commit(
            hash="0000001",
            message="init",
            author="alice",
            timestamp=1,
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            commit.message = "changed"  # type: ignore[misc]

    # 루트 커밋의 parents가 빈 tuple인지 검증한다.
    def test_commit_root_empty_parents(self) -> None:
        commit = Commit(
            hash="0000001",
            message="root",
            author="alice",
            timestamp=1,
        )
        self.assertEqual(commit.parents, ())
        self.assertEqual(len(commit.parents), 0)

    # parents가 tuple 타입으로 보존되는지 검증한다.
    def test_commit_parents_tuple(self) -> None:
        parents = ("0000001", "0000002")
        commit = Commit(
            hash="0000003",
            message="merge",
            author="bob",
            timestamp=3,
            parents=parents,
        )
        self.assertIsInstance(commit.parents, tuple)
        self.assertEqual(commit.parents, ("0000001", "0000002"))
