"""Tests for mini_git.sort."""

from __future__ import annotations

import unittest

from mini_git.sort import merge_sort


class TestMergeSort(unittest.TestCase):
    # 빈 리스트를 정렬하면 빈 리스트가 반환되는지 검증한다.
    def test_empty(self) -> None:
        self.assertEqual(merge_sort([]), [])

    # 단일 원소 리스트가 그대로 반환되고 입력이 변하지 않는지 검증한다.
    def test_single(self) -> None:
        items = [42]
        result = merge_sort(items)
        self.assertEqual(result, [42])
        self.assertIsNot(result, items)
        self.assertEqual(items, [42])

    # 이미 정렬된 리스트의 순서가 유지되는지 검증한다.
    def test_already_sorted(self) -> None:
        items = [1, 2, 3, 4]
        self.assertEqual(merge_sort(items), [1, 2, 3, 4])

    # 역순 리스트가 오름차순으로 정렬되는지 검증한다.
    def test_reverse(self) -> None:
        self.assertEqual(merge_sort([4, 3, 2, 1]), [1, 2, 3, 4])

    # 무작위 순서 리스트가 기대한 오름차순으로 정렬되는지 검증한다.
    def test_random(self) -> None:
        items = [5, 1, 4, 2, 8, 3, 7, 6]
        self.assertEqual(merge_sort(items), [1, 2, 3, 4, 5, 6, 7, 8])

    # 동일 키일 때 입력 순서(안정성)가 유지되는지 검증한다.
    def test_stability(self) -> None:
        items = [(1, "first"), (1, "second"), (1, "third")]
        result = merge_sort(items, key=lambda x: x[0])
        self.assertEqual([label for _, label in result], ["first", "second", "third"])

    # 역순으로 넣은 동일 키도 안정 정렬 시 상대 순서가 유지되는지 검증한다.
    def test_stability_reverse_input_order(self) -> None:
        items = [(2, "c"), (2, "b"), (2, "a")]
        result = merge_sort(items, key=lambda x: x[0])
        self.assertEqual([label for _, label in result], ["c", "b", "a"])

    # tuple 다중 키(author, timestamp, hash)로 lexicographic 정렬되는지 검증한다.
    def test_multi_key_tuple(self) -> None:
        items = [
            ("bob", 2, "0000002"),
            ("alice", 1, "0000001"),
            ("alice", 2, "0000003"),
            ("alice", 1, "0000004"),
        ]
        result = merge_sort(items, key=lambda x: (x[0], x[1], x[2]))
        self.assertEqual(
            result,
            [
                ("alice", 1, "0000001"),
                ("alice", 1, "0000004"),
                ("alice", 2, "0000003"),
                ("bob", 2, "0000002"),
            ],
        )

    # 정렬 후에도 원본 리스트 내용이 변하지 않는지 검증한다.
    def test_does_not_mutate_input(self) -> None:
        items = [3, 1, 2]
        original = list(items)
        result = merge_sort(items)
        self.assertEqual(items, original)
        self.assertIsNot(result, items)
        self.assertEqual(result, [1, 2, 3])
