"""Tests for mini_git.diff."""

from __future__ import annotations

import unittest

from mini_git.diff import DiffLine, diff_lines


class TestDiffLines(unittest.TestCase):
    # 두 입력이 모두 비어 있을 때 빈 결과가 반환되는지 검증한다.
    def test_both_empty(self) -> None:
        self.assertEqual(diff_lines([], []), [])

    # 동일한 입력은 모두 common 레코드로 원본 순서대로 반환되는지 검증한다.
    def test_identical(self) -> None:
        self.assertEqual(
            diff_lines(["a", "b"], ["a", "b"]),
            [
                DiffLine(kind="common", text="a"),
                DiffLine(kind="common", text="b"),
            ],
        )

    # 왼쪽이 비어 있으면 모든 줄이 added로 반환되는지 검증한다.
    def test_all_added(self) -> None:
        self.assertEqual(
            diff_lines([], ["x", "y"]),
            [
                DiffLine(kind="added", text="x"),
                DiffLine(kind="added", text="y"),
            ],
        )

    # 오른쪽이 비어 있으면 모든 줄이 deleted로 반환되는지 검증한다.
    def test_all_deleted(self) -> None:
        self.assertEqual(
            diff_lines(["x", "y"], []),
            [
                DiffLine(kind="deleted", text="x"),
                DiffLine(kind="deleted", text="y"),
            ],
        )

    # 중간 한 줄이 바뀐 경우 common-deleted-added-common 순서가 유지되는지 검증한다.
    def test_interleaved(self) -> None:
        self.assertEqual(
            diff_lines(["h", "x", "f"], ["h", "y", "f"]),
            [
                DiffLine(kind="common", text="h"),
                DiffLine(kind="deleted", text="x"),
                DiffLine(kind="added", text="y"),
                DiffLine(kind="common", text="f"),
            ],
        )

    # LCS 동률일 때 deleted를 우선하는 타이브레이크가 적용되는지 검증한다.
    def test_prefers_deletion_then_addition_on_tie(self) -> None:
        self.assertEqual(
            diff_lines(["x"], ["y"]),
            [
                DiffLine(kind="deleted", text="x"),
                DiffLine(kind="added", text="y"),
            ],
        )

    # 공백 문자를 포함한 라인이 정규화 없이 그대로 비교되는지 검증한다.
    def test_preserves_trailing_whitespace_verbatim(self) -> None:
        self.assertEqual(
            diff_lines(["abc"], ["abc "]),
            [
                DiffLine(kind="deleted", text="abc"),
                DiffLine(kind="added", text="abc "),
            ],
        )

    # 결과 원소가 DiffLine 데이터클래스 레코드로 생성되는지 검증한다.
    def test_returns_dataclass_records(self) -> None:
        result = diff_lines(["a"], ["a", "b"])
        self.assertTrue(all(isinstance(item, DiffLine) for item in result))
        self.assertEqual([item.kind for item in result], ["common", "added"])

