"""Tests for mini_git.graph."""

from __future__ import annotations

import unittest
from collections.abc import Callable

from mini_git.graph import ancestors, shortest_path, topological_order


def _parents_map(edges: dict[str, list[str]]) -> Callable[[str], list[str]]:
    return lambda h: list(edges.get(h, []))


def _neighbors_map(edges: dict[str, list[str]]) -> Callable[[str], list[str]]:
    return lambda h: list(edges.get(h, []))


class TestTopologicalOrder(unittest.TestCase):
    # 선형 체인에서 부모가 자식보다 앞에 오는지 검증한다.
    def test_chain(self) -> None:
        parents = {
            "0000001": [],
            "0000002": ["0000001"],
            "0000003": ["0000002"],
        }
        result = topological_order(
            parents.keys(),
            _parents_map(parents),
            get_sort_key=lambda h: h,
        )
        self.assertEqual(result, ["0000001", "0000002", "0000003"])

    # 다이아몬드 DAG에서 부모 선행과 동일 레벨 tie-break를 검증한다.
    def test_diamond(self) -> None:
        parents = {
            "0000001": [],
            "0000002": ["0000001"],
            "0000003": ["0000001"],
            "0000004": ["0000002", "0000003"],
        }
        timestamps = {
            "0000001": 1,
            "0000002": 2,
            "0000003": 3,
            "0000004": 4,
        }
        result = topological_order(
            parents.keys(),
            _parents_map(parents),
            get_sort_key=lambda h: (timestamps[h], h),
        )
        self.assertEqual(result.index("0000001"), 0)
        self.assertLess(result.index("0000002"), result.index("0000004"))
        self.assertLess(result.index("0000003"), result.index("0000004"))
        self.assertEqual(result, ["0000001", "0000002", "0000003", "0000004"])

    # 부분 집합 입력 시 집합 밖 부모는 in-degree 계산에서 무시되는지 검증한다.
    def test_subgraph_ignores_external_parent(self) -> None:
        parents = {
            "0000001": [],
            "0000002": ["0000001"],
            "0000003": ["0000001"],
        }
        result = topological_order(
            ["0000002", "0000003"],
            _parents_map(parents),
            get_sort_key=lambda h: h,
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(set(result), {"0000002", "0000003"})

    # 동일 timestamp일 때 hash lex 순으로 tie-break되는지 검증한다.
    def test_deterministic_ties(self) -> None:
        parents = {
            "0000001": [],
            "0000002": ["0000001"],
            "0000003": ["0000001"],
        }
        result = topological_order(
            parents.keys(),
            _parents_map(parents),
            get_sort_key=lambda h: (0, h),
        )
        self.assertEqual(result, ["0000001", "0000002", "0000003"])


class TestShortestPath(unittest.TestCase):
    # 무방향 체인에서 최단 경로가 반환되는지 검증한다.
    def test_chain_shortest(self) -> None:
        neighbors = {
            "0000001": ["0000002"],
            "0000002": ["0000001", "0000003"],
            "0000003": ["0000002"],
        }
        result = shortest_path(
            "0000001",
            "0000003",
            _neighbors_map(neighbors),
        )
        self.assertEqual(result, ["0000001", "0000002", "0000003"])

    # 동일 길이 최단 경로가 여러 개일 때 lex-min 경로를 선택하는지 검증한다.
    def test_diamond_lex_tie(self) -> None:
        neighbors = {
            "0000001": ["0000002", "0000003"],
            "0000002": ["0000001", "0000004"],
            "0000003": ["0000001", "0000004"],
            "0000004": ["0000002", "0000003"],
        }
        result = shortest_path(
            "0000001",
            "0000004",
            _neighbors_map(neighbors),
        )
        self.assertEqual(result, ["0000001", "0000002", "0000004"])

    # 연결되지 않은 컴포넌트 사이에서는 None을 반환하는지 검증한다.
    def test_no_path_disconnected(self) -> None:
        neighbors = {
            "0000001": ["0000002"],
            "0000002": ["0000001"],
            "0000005": ["0000006"],
            "0000006": ["0000005"],
        }
        result = shortest_path(
            "0000001",
            "0000005",
            _neighbors_map(neighbors),
        )
        self.assertIsNone(result)

    # 시작과 목표가 같으면 단일 노드 경로를 반환하는지 검증한다.
    def test_start_equals_goal(self) -> None:
        neighbors = {"0000001": []}
        result = shortest_path(
            "0000001",
            "0000001",
            _neighbors_map(neighbors),
        )
        self.assertEqual(result, ["0000001"])


class TestAncestors(unittest.TestCase):
    # 선형 체인에서 모든 조상 hash가 수집되는지 검증한다.
    def test_chain_ancestors(self) -> None:
        parents = {
            "0000001": [],
            "0000002": ["0000001"],
            "0000003": ["0000002"],
        }
        result = ancestors("0000003", _parents_map(parents))
        self.assertEqual(result, {"0000001", "0000002"})

    # 다이아몬드 merge 그래프에서 모든 조상이 누락 없이 수집되는지 검증한다.
    def test_diamond_ancestors(self) -> None:
        parents = {
            "0000001": [],
            "0000002": ["0000001"],
            "0000003": ["0000001"],
            "0000004": ["0000002", "0000003"],
        }
        result = ancestors("0000004", _parents_map(parents))
        self.assertEqual(result, {"0000001", "0000002", "0000003"})

    # 시작 커밋 자신은 조상 결과에 포함되지 않는지 검증한다.
    def test_excludes_start(self) -> None:
        parents = {"0000001": []}
        result = ancestors("0000001", _parents_map(parents))
        self.assertEqual(result, set())

    # 공통 조상이 merge diamond에서 중복 없이 한 번만 포함되는지 검증한다.
    def test_merge_duplicate_parent(self) -> None:
        parents = {
            "0000001": [],
            "0000002": ["0000001"],
            "0000003": ["0000001"],
            "0000004": ["0000002", "0000003"],
        }
        result = ancestors("0000004", _parents_map(parents))
        self.assertEqual(len(result), 3)
        self.assertIn("0000001", result)
