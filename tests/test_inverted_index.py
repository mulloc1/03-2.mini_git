"""Tests for mini_git.inverted_index."""

from __future__ import annotations

import unittest

from mini_git.commit import Commit
from mini_git.inverted_index import InvertedIndex, _tokenize


def _commit(
    hash: str,
    message: str,
    author: str = "alice",
    timestamp: int = 1,
) -> Commit:
    return Commit(hash=hash, message=message, author=author, timestamp=timestamp)


class TestTokenize(unittest.TestCase):
    # 메시지를 공백 분리 후 소문자 토큰 집합으로 만드는지 검증한다.
    def test_tokenize_split_and_lower(self) -> None:
        self.assertEqual(
            _tokenize("Add Login Feature"),
            {"add", "login", "feature"},
        )


class TestInvertedIndex(unittest.TestCase):
    # 토큰화·소문자 정규화 후 키워드 검색이 동작하는지 검증한다.
    def test_tokenize_split_and_lower(self) -> None:
        index = InvertedIndex()
        index.add_commit(_commit("0000001", "Add Login Feature"))
        self.assertEqual(index.search_keyword("login"), ["0000001"])
        self.assertEqual(index.search_keyword("LOGIN"), ["0000001"])

    # 동일 커밋 메시지의 중복 토큰은 hash가 한 번만 색인되는지 검증한다.
    def test_dedupe_token_per_commit(self) -> None:
        index = InvertedIndex()
        index.add_commit(_commit("0000001", "login login"))
        self.assertEqual(index.search_keyword("login"), ["0000001"])

    # 미등록 키워드 검색 시 빈 리스트가 반환되는지 검증한다.
    def test_search_keyword_miss(self) -> None:
        index = InvertedIndex()
        index.add_commit(_commit("0000001", "Add login"))
        self.assertEqual(index.search_keyword("missing"), [])

    # 부분 문자열이 아닌 exact token만 매칭되는지 검증한다.
    def test_no_substring_match(self) -> None:
        index = InvertedIndex()
        index.add_commit(_commit("0000001", "Add login feature"))
        self.assertEqual(index.search_keyword("log"), [])

    # 작성자 인덱스가 대소문자를 구분하는지 검증한다.
    def test_author_case_sensitive(self) -> None:
        index = InvertedIndex()
        index.add_commit(_commit("0000001", "one", author="Alice"))
        index.add_commit(_commit("0000002", "two", author="alice"))
        self.assertEqual(index.search_author("Alice"), ["0000001"])
        self.assertEqual(index.search_author("alice"), ["0000002"])
        self.assertEqual(index.search_author("ALICE"), [])

    # 동일 키워드에 여러 커밋이 추가된 순서가 유지되는지 검증한다.
    def test_append_order(self) -> None:
        index = InvertedIndex()
        index.add_commit(_commit("0000001", "fix login"))
        index.add_commit(_commit("0000002", "add login"))
        self.assertEqual(index.search_keyword("login"), ["0000001", "0000002"])

    # remove_commit 후 해당 hash가 검색 결과에서 제거되는지 검증한다.
    def test_remove_commit(self) -> None:
        index = InvertedIndex()
        index.add_commit(_commit("0000001", "fix login", author="alice"))
        index.remove_commit("0000001")
        self.assertEqual(index.search_keyword("login"), [])
        self.assertEqual(index.search_author("alice"), [])

    # remove_commit 후 다른 커밋 hash는 그대로인지 검증한다.
    def test_remove_commit_other_hashes_unchanged(self) -> None:
        index = InvertedIndex()
        index.add_commit(_commit("0000001", "fix login"))
        index.add_commit(_commit("0000002", "add login"))
        index.remove_commit("0000001")
        self.assertEqual(index.search_keyword("login"), ["0000002"])
