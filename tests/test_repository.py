"""Tests for mini_git.repository."""

from __future__ import annotations

import unittest

from helpers import FakeClock, make_repo

from mini_git.commit import Commit
from mini_git.errors import RepoError


class TestInit(unittest.TestCase):
    # INIT 후 HEAD가 main이고 author/브랜치 시드가 설정되는지 검증한다.
    def test_init_sets_head_main_and_author(self) -> None:
        repo = make_repo()
        repo.init("alice")
        self.assertEqual(repo.head, "main")
        self.assertEqual(repo.author, "alice")
        self.assertEqual(repo.branches(), {"main": None})
        self.assertIsNone(repo.head_commit())

    # 재 INIT 시 커밋·인덱스·HashIssuer가 전부 초기화되는지 검증한다.
    def test_init_resets_all_state(self) -> None:
        repo = make_repo()
        repo.init("alice")
        first_hash = repo.commit("first").hash
        repo.init("bob")
        self.assertEqual(repo.author, "bob")
        self.assertEqual(repo.branches(), {"main": None})
        self.assertIsNone(repo.head_commit())
        # HashIssuer reset → 다음 커밋이 다시 0000001
        self.assertEqual(repo.commit("again").hash, first_hash)


class TestRequireInit(unittest.TestCase):
    # INIT 전 commit/branch/switch 호출이 모두 RepoError를 발생시키는지 검증한다.
    def test_commands_before_init_raise(self) -> None:
        repo = make_repo()
        with self.assertRaises(RepoError):
            repo.commit("x")
        with self.assertRaises(RepoError):
            repo.branch("feature")
        with self.assertRaises(RepoError):
            repo.switch("main")


class TestCommit(unittest.TestCase):
    # 첫 commit은 parents가 비어 있고 hash가 0000001인지 검증한다.
    def test_first_commit_is_root(self) -> None:
        repo = make_repo()
        repo.init("alice")
        c = repo.commit("first")
        self.assertEqual(c.hash, "0000001")
        self.assertEqual(c.parents, ())
        self.assertEqual(c.author, "alice")
        self.assertEqual(repo.head_commit(), "0000001")

    # 연속 commit이 직전 commit을 단일 parent로 연결하는지 검증한다.
    def test_commit_parent_chain(self) -> None:
        repo = make_repo()
        repo.init("alice")
        a = repo.commit("a")
        b = repo.commit("b")
        c = repo.commit("c")
        self.assertEqual(b.parents, (a.hash,))
        self.assertEqual(c.parents, (b.hash,))

    # commit 직후 HEAD 브랜치 포인터가 새 commit으로 이동하는지 검증한다.
    def test_commit_advances_head_branch(self) -> None:
        repo = make_repo()
        repo.init("alice")
        repo.commit("a")
        latest = repo.commit("b")
        self.assertEqual(repo.head_commit(), latest.hash)

    # commit timestamp가 단조 증가하며 clock과 분리되는지 검증한다.
    def test_commit_timestamp_monotonic_and_clock_injected(self) -> None:
        clock = FakeClock(start=1000.0)
        repo = make_repo(clock=clock)
        repo.init("alice")
        a = repo.commit("a")
        clock.advance(5)
        b = repo.commit("b")
        self.assertEqual(a.timestamp, 1)
        self.assertEqual(b.timestamp, 2)


class TestBranch(unittest.TestCase):
    # 첫 commit 이전 BRANCH 호출 시 RepoError가 발생하는지 검증한다.
    def test_branch_before_first_commit_raises(self) -> None:
        repo = make_repo()
        repo.init("alice")
        with self.assertRaises(RepoError):
            repo.branch("feature")

    # BRANCH가 현재 HEAD commit 위치에 새 브랜치를 만들고 HEAD는 그대로인지 검증한다.
    def test_branch_points_at_current_head(self) -> None:
        repo = make_repo()
        repo.init("alice")
        repo.commit("first")
        head = repo.commit("second").hash
        repo.branch("feature")
        self.assertEqual(repo.branches()["feature"], head)
        self.assertEqual(repo.head, "main")

    # 동일 이름 브랜치 중복 등록 시 RepoError가 발생하는지 검증한다.
    def test_branch_duplicate_name_raises(self) -> None:
        repo = make_repo()
        repo.init("alice")
        repo.commit("first")
        repo.branch("feature")
        with self.assertRaises(RepoError):
            repo.branch("feature")


class TestSwitch(unittest.TestCase):
    # 미존재 브랜치로 SWITCH 시 RepoError가 발생하는지 검증한다.
    def test_switch_unknown_branch_raises(self) -> None:
        repo = make_repo()
        repo.init("alice")
        with self.assertRaises(RepoError):
            repo.switch("missing")

    # SWITCH 후 새 브랜치에서 commit이 fork-point를 부모로 공유하는지 검증한다.
    def test_branch_fork_shares_parent(self) -> None:
        repo = make_repo()
        repo.init("alice")
        repo.commit("first")
        fork_point = repo.commit("second").hash
        repo.branch("feature")
        main_tip = repo.commit("main-third")
        repo.switch("feature")
        feature_tip = repo.commit("feature-third")
        self.assertEqual(main_tip.parents, (fork_point,))
        self.assertEqual(feature_tip.parents, (fork_point,))
        self.assertNotEqual(
            repo.branches()["main"], repo.branches()["feature"]
        )

    # SWITCH 직후에 HEAD 브랜치명이 갱신되는지 검증한다.
    def test_switch_updates_head(self) -> None:
        repo = make_repo()
        repo.init("alice")
        repo.commit("first")
        repo.branch("feature")
        repo.switch("feature")
        self.assertEqual(repo.head, "feature")


class TestGetCommit(unittest.TestCase):
    # 미존재 hash 조회 시 RepoError가 발생하는지 검증한다.
    def test_get_unknown_commit_raises(self) -> None:
        repo = make_repo()
        repo.init("alice")
        with self.assertRaises(RepoError):
            repo.get_commit("9999999")

    # 등록된 hash 조회 시 동일 Commit 인스턴스를 돌려주는지 검증한다.
    def test_get_known_commit(self) -> None:
        repo = make_repo()
        repo.init("alice")
        c = repo.commit("first")
        self.assertEqual(repo.get_commit(c.hash), c)


class TestLog(unittest.TestCase):
    # 커밋 없는 저장소에서 log()가 빈 리스트를 반환하는지 검증한다.
    def test_log_empty_repo(self) -> None:
        repo = make_repo()
        repo.init("alice")
        self.assertEqual(repo.log(), [])

    # 선형 체인에서 log()가 부모→자식 순서인지 검증한다.
    def test_log_linear_chain(self) -> None:
        repo = make_repo()
        repo.init("alice")
        a = repo.commit("a")
        b = repo.commit("b")
        c = repo.commit("c")
        self.assertEqual(
            [commit.hash for commit in repo.log()],
            [a.hash, b.hash, c.hash],
        )

    # 브랜치 fork 후 log()가 fork-point 이후 자식들을 timestamp 순으로 정렬하는지 검증한다.
    def test_log_branch_fork(self) -> None:
        repo = make_repo()
        repo.init("alice")
        a = repo.commit("a")
        b = repo.commit("b")
        repo.branch("feature")
        main_tip = repo.commit("main-third")
        repo.switch("feature")
        feature_tip = repo.commit("feature-third")
        hashes = [commit.hash for commit in repo.log()]
        self.assertEqual(len(hashes), 4)
        self.assertEqual(hashes[0], a.hash)
        self.assertEqual(hashes[1], b.hash)
        self.assertLess(hashes.index(b.hash), hashes.index(main_tip.hash))
        self.assertLess(hashes.index(b.hash), hashes.index(feature_tip.hash))
        self.assertEqual(
            hashes[2:],
            sorted([main_tip.hash, feature_tip.hash], key=lambda h: h),
        )

    # log_sorted("date")가 timestamp 오름차순인지 검증한다.
    def test_log_sorted_by_date(self) -> None:
        repo = make_repo()
        repo.init("alice")
        a = repo.commit("a")
        b = repo.commit("b")
        c = repo.commit("c")
        self.assertEqual(
            [commit.hash for commit in repo.log_sorted("date")],
            [a.hash, b.hash, c.hash],
        )

    # log_sorted("author")가 author→timestamp→hash 순인지 검증한다.
    def test_log_sorted_by_author(self) -> None:
        repo = make_repo()
        repo.init("alice")
        alice_commit = repo.commit("from alice")
        repo._author = "bob"
        bob_commit = repo.commit("from bob")
        self.assertEqual(
            [commit.hash for commit in repo.log_sorted("author")],
            [alice_commit.hash, bob_commit.hash],
        )

    # log_sorted에 잘못된 키를 넘기면 RepoError가 발생하는지 검증한다.
    def test_log_sorted_invalid_key_raises(self) -> None:
        repo = make_repo()
        repo.init("alice")
        repo.commit("a")
        with self.assertRaises(RepoError):
            repo.log_sorted("hash")


class TestPath(unittest.TestCase):
    # 선형 체인 PATH가 최단 경로를 반환하는지 검증한다.
    def test_path_chain(self) -> None:
        repo = make_repo()
        repo.init("alice")
        a = repo.commit("a")
        b = repo.commit("b")
        c = repo.commit("c")
        self.assertEqual(repo.path(a.hash, c.hash), [a.hash, b.hash, c.hash])

    # fork 그래프에서 PATH가 fork-point를 경유하는지 검증한다.
    def test_path_fork_through_fork_point(self) -> None:
        repo = make_repo()
        repo.init("alice")
        repo.commit("a")
        fork_point = repo.commit("b")
        repo.branch("feature")
        main_tip = repo.commit("main-third")
        repo.switch("feature")
        feature_tip = repo.commit("feature-third")
        self.assertEqual(
            repo.path(main_tip.hash, feature_tip.hash),
            [main_tip.hash, fork_point.hash, feature_tip.hash],
        )

    # 시작과 목표가 같으면 단일 노드 경로를 반환하는지 검증한다.
    def test_path_start_equals_goal(self) -> None:
        repo = make_repo()
        repo.init("alice")
        a = repo.commit("a")
        self.assertEqual(repo.path(a.hash, a.hash), [a.hash])

    # 미존재 hash로 PATH 시 RepoError가 발생하는지 검증한다.
    def test_path_unknown_commit_raises(self) -> None:
        repo = make_repo()
        repo.init("alice")
        a = repo.commit("a")
        with self.assertRaises(RepoError):
            repo.path(a.hash, "9999999")

    # 연결되지 않은 컴포넌트 사이 PATH는 None을 반환하는지 검증한다.
    def test_path_disconnected_returns_none(self) -> None:
        repo = make_repo()
        repo.init("alice")
        a = repo.commit("a")
        orphan = Commit(
            hash="0000099",
            message="orphan",
            author="alice",
            timestamp=99,
        )
        repo._commits[orphan.hash] = orphan
        repo._root_hashes.append(orphan.hash)
        self.assertIsNone(repo.path(a.hash, orphan.hash))


class TestAncestors(unittest.TestCase):
    # 루트 커밋 ANCESTORS는 빈 리스트인지 검증한다.
    def test_ancestors_root_empty(self) -> None:
        repo = make_repo()
        repo.init("alice")
        root = repo.commit("root")
        self.assertEqual(repo.ancestors(root.hash), [])

    # 선형 체인 ANCESTORS가 부모 순 토폴로지 순서인지 검증한다.
    def test_ancestors_chain(self) -> None:
        repo = make_repo()
        repo.init("alice")
        a = repo.commit("a")
        b = repo.commit("b")
        c = repo.commit("c")
        self.assertEqual(
            [commit.hash for commit in repo.ancestors(c.hash)],
            [a.hash, b.hash],
        )

    # fork 그래프 ANCESTORS가 형제 브랜치 커밋을 제외하는지 검증한다.
    def test_ancestors_fork_excludes_sibling(self) -> None:
        repo = make_repo()
        repo.init("alice")
        a = repo.commit("a")
        b = repo.commit("b")
        repo.branch("feature")
        main_tip = repo.commit("main-third")
        repo.switch("feature")
        feature_tip = repo.commit("feature-third")
        ancestor_hashes = {commit.hash for commit in repo.ancestors(main_tip.hash)}
        self.assertEqual(ancestor_hashes, {a.hash, b.hash})
        self.assertNotIn(feature_tip.hash, ancestor_hashes)

    # 미존재 hash로 ANCESTORS 시 RepoError가 발생하는지 검증한다.
    def test_ancestors_unknown_commit_raises(self) -> None:
        repo = make_repo()
        repo.init("alice")
        with self.assertRaises(RepoError):
            repo.ancestors("9999999")
