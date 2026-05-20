"""Tests for mini_git.cli REPL and output formatting."""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from io import StringIO

from helpers import FakeClock, make_repo

from mini_git.cli import format_commit, run_repl, tokenize
from mini_git.main import main
from mini_git.repository import Repository


def _run_script(script: str, clock: FakeClock | None = None) -> str:
    """Run a stdin script through the REPL and return captured stdout."""
    repo = Repository(clock=clock or FakeClock())
    stdout = StringIO()
    run_repl(repo, StringIO(script), stdout)
    return stdout.getvalue()


def _response_lines(raw: str) -> list[str]:
    """Strip REPL prompts and return command output lines only."""
    lines: list[str] = []
    for line in raw.splitlines():
        if line.startswith("mini-git> "):
            rest = line[len("mini-git> ") :]
            if rest:
                lines.append(rest)
        elif line and line != "mini-git>":
            lines.append(line)
    return lines


def _expected_timestamp(clock_value: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(clock_value))


class TestTokenize(unittest.TestCase):
    # COMMIT quoted message가 단일 토큰으로 파싱되는지 검증한다.
    def test_tokenize_quoted_commit_message(self) -> None:
        self.assertEqual(
            tokenize('COMMIT "Add login feature"'),
            ["COMMIT", "Add login feature"],
        )

    # SEARCH --author quoted value가 공백을 유지하는지 검증한다.
    def test_tokenize_quoted_author_option(self) -> None:
        self.assertEqual(
            tokenize('SEARCH --author="Alice Liddell"'),
            ["SEARCH", "--author=Alice Liddell"],
        )


class TestFormatCommit(unittest.TestCase):
    # format_commit이 §9.0 한 줄 요약 형식을 따르는지 검증한다.
    def test_format_commit_line(self) -> None:
        from mini_git.commit import Commit

        commit = Commit(
            hash="0000001",
            message="Add login feature",
            author="alice",
            timestamp=1,
        )
        line = format_commit(commit, 0.0)
        self.assertEqual(
            line,
            f"0000001 alice {_expected_timestamp(0.0)} Add login feature",
        )


class TestInitCommitBranchSwitch(unittest.TestCase):
    # §9.1 INIT/COMMIT/BRANCH/SWITCH 성공 메시지를 검증한다.
    def test_basic_command_flow(self) -> None:
        clock = FakeClock()
        script = (
            "INIT alice\n"
            'COMMIT "Add login feature"\n'
            'COMMIT "Fix login bug"\n'
            "BRANCH feature\n"
            "SWITCH feature\n"
            'COMMIT "Add UI polish"\n'
            "exit\n"
        )
        lines = _response_lines(_run_script(script, clock))
        self.assertEqual(lines[0], "Initialized repository for alice")
        self.assertEqual(lines[1], "Committed 0000001")
        self.assertEqual(lines[2], "Committed 0000002")
        self.assertEqual(lines[3], "Created branch feature at 0000002")
        self.assertEqual(lines[4], "Switched to branch feature")
        self.assertEqual(lines[5], "Committed 0000003")


class TestLog(unittest.TestCase):
    # 빈 저장소 LOG가 (no commits)를 출력하는지 검증한다.
    def test_log_empty(self) -> None:
        lines = _response_lines(_run_script("INIT alice\nLOG\nexit\n"))
        self.assertEqual(lines, ["Initialized repository for alice", "(no commits)"])

    # 선형 체인 LOG가 부모 우선 순서와 포맷을 따르는지 검증한다.
    def test_log_linear_chain(self) -> None:
        clock = FakeClock()
        repo = make_repo(clock)
        repo.init("alice")
        repo.commit("Add login feature")
        clock.advance(1.0)
        repo.commit("Fix login bug")
        stdout = StringIO()
        run_repl(repo, StringIO("LOG\nexit\n"), stdout)
        log_lines = _response_lines(stdout.getvalue())
        self.assertEqual(
            log_lines[0],
            f"0000001 alice {_expected_timestamp(0.0)} Add login feature",
        )
        self.assertEqual(
            log_lines[1],
            f"0000002 alice {_expected_timestamp(1.0)} Fix login bug",
        )


class TestLogSorted(unittest.TestCase):
    # LOG --sort-by=date가 timestamp 오름차순인지 검증한다.
    def test_log_sort_by_date(self) -> None:
        clock = FakeClock()
        repo = make_repo(clock)
        repo.init("alice")
        repo.commit("a")
        clock.advance(1.0)
        repo.commit("b")
        stdout = StringIO()
        run_repl(repo, StringIO("LOG --sort-by=date\nexit\n"), stdout)
        lines = _response_lines(stdout.getvalue())
        self.assertEqual(lines[0].startswith("0000001"), True)
        self.assertEqual(lines[1].startswith("0000002"), True)

    # LOG --sort-by=author가 author 오름차순인지 검증한다.
    def test_log_sort_by_author(self) -> None:
        clock = FakeClock()
        repo = make_repo(clock)
        repo.init("alice")
        repo.commit("from alice")
        repo._author = "bob"
        repo.commit("from bob")
        stdout = StringIO()
        run_repl(repo, StringIO("LOG --sort-by=author\nexit\n"), stdout)
        lines = _response_lines(stdout.getvalue())
        self.assertTrue(lines[0].startswith("0000001 alice"))
        self.assertTrue(lines[1].startswith("0000002 bob"))


class TestPath(unittest.TestCase):
    # PATH가 -> 구분 최단 경로를 출력하는지 검증한다.
    def test_path_chain(self) -> None:
        script = (
            "INIT alice\n"
            "COMMIT a\n"
            "COMMIT b\n"
            "COMMIT c\n"
            "PATH 0000001 0000003\n"
            "exit\n"
        )
        lines = _response_lines(_run_script(script))
        self.assertEqual(lines[-1], "0000001 -> 0000002 -> 0000003")

    # 미존재 hash PATH가 Unknown commit을 출력하는지 검증한다.
    def test_path_unknown_commit(self) -> None:
        script = "INIT alice\nCOMMIT a\nPATH 0000001 0000099\nexit\n"
        lines = _response_lines(_run_script(script))
        self.assertEqual(lines[-1], "Unknown commit: 0000099")

    # 연결되지 않은 컴포넌트 PATH가 No path를 출력하는지 검증한다.
    def test_path_no_path(self) -> None:
        from mini_git.commit import Commit

        repo = make_repo()
        repo.init("alice")
        repo.commit("a")
        orphan = Commit(
            hash="0000099",
            message="orphan",
            author="alice",
            timestamp=99,
        )
        repo._commits[orphan.hash] = orphan
        repo._root_hashes.append(orphan.hash)
        stdout = StringIO()
        run_repl(repo, StringIO("PATH 0000001 0000099\nexit\n"), stdout)
        lines = _response_lines(stdout.getvalue())
        self.assertEqual(lines[0], "No path")


class TestAncestors(unittest.TestCase):
    # 루트 ANCESTORS가 (no ancestors)를 출력하는지 검증한다.
    def test_ancestors_root(self) -> None:
        script = "INIT alice\nCOMMIT root\nANCESTORS 0000001\nexit\n"
        lines = _response_lines(_run_script(script))
        self.assertEqual(lines[-1], "(no ancestors)")

    # 비루트 ANCESTORS가 토폴로지 순서로 출력되는지 검증한다.
    def test_ancestors_chain(self) -> None:
        clock = FakeClock()
        repo = make_repo(clock)
        repo.init("alice")
        repo.commit("a")
        repo.commit("b")
        repo.commit("c")
        stdout = StringIO()
        run_repl(repo, StringIO("ANCESTORS 0000003\nexit\n"), stdout)
        lines = _response_lines(stdout.getvalue())
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("0000001"))
        self.assertTrue(lines[1].startswith("0000002"))


class TestSearch(unittest.TestCase):
    # SEARCH keyword가 매칭 커밋을 출력하는지 검증한다.
    def test_search_keyword(self) -> None:
        script = (
            "INIT alice\n"
            'COMMIT "Add login feature"\n'
            'COMMIT "Fix login bug"\n'
            "SEARCH login\n"
            "exit\n"
        )
        lines = _response_lines(_run_script(script))
        self.assertEqual(len([line for line in lines if line.startswith("0000")]), 2)

    # SEARCH --author가 author 커밋을 출력하는지 검증한다.
    def test_search_author(self) -> None:
        script = (
            "INIT alice\n"
            "COMMIT a\n"
            "COMMIT b\n"
            "SEARCH --author=alice\n"
            "exit\n"
        )
        lines = _response_lines(_run_script(script))
        self.assertEqual(len([line for line in lines if line.startswith("0000")]), 2)

    # 매칭 없을 때 No results를 출력하는지 검증한다.
    def test_search_no_results(self) -> None:
        script = "INIT alice\nCOMMIT hello\nSEARCH missing\nexit\n"
        lines = _response_lines(_run_script(script))
        self.assertEqual(lines[-1], "No results")


class TestDiffCli(unittest.TestCase):
    def _write(self, root: str, name: str, content: str) -> str:
        path = os.path.join(root, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return path

    # DIFF가 공통/삭제/추가 줄을 접두사와 함께 순서대로 출력하는지 검증한다.
    def test_diff_outputs_prefixed_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            a_path = self._write(tmpdir, "a.txt", "h\nx\nf\n")
            b_path = self._write(tmpdir, "b.txt", "h\ny\nf\n")
            lines = _response_lines(_run_script(f'DIFF "{a_path}" "{b_path}"\nexit\n'))
            self.assertEqual(lines, ["  h", "- x", "+ y", "  f"])

    # 두 파일 내용이 같을 때 Files are identical를 출력하는지 검증한다.
    def test_diff_identical_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            a_path = self._write(tmpdir, "same.txt", "line1\nline2\n")
            lines = _response_lines(
                _run_script(f'DIFF "{a_path}" "{a_path}"\nexit\n')
            )
            self.assertEqual(lines, ["Files are identical"])

    # 두 파일이 모두 빈 파일일 때 Files are identical를 출력하는지 검증한다.
    def test_diff_both_empty_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            a_path = self._write(tmpdir, "empty_a.txt", "")
            b_path = self._write(tmpdir, "empty_b.txt", "")
            lines = _response_lines(_run_script(f'DIFF "{a_path}" "{b_path}"\nexit\n'))
            self.assertEqual(lines, ["Files are identical"])

    # 한쪽만 trailing newline이 있어도 동일 파일로 처리되는지 검증한다.
    def test_diff_trailing_newline_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            a_path = self._write(tmpdir, "a.txt", "a\nb")
            b_path = self._write(tmpdir, "b.txt", "a\nb\n")
            lines = _response_lines(_run_script(f'DIFF "{a_path}" "{b_path}"\nexit\n'))
            self.assertEqual(lines, ["Files are identical"])

    # 미존재 파일 경로에 대해 File not found 메시지를 출력하는지 검증한다.
    def test_diff_file_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            a_path = self._write(tmpdir, "a.txt", "hello\n")
            missing_path = os.path.join(tmpdir, "missing.txt")
            lines = _response_lines(
                _run_script(f'DIFF "{a_path}" "{missing_path}"\nexit\n')
            )
            self.assertEqual(lines, [f"File not found: {missing_path}"])

    # 인자 개수가 맞지 않으면 Invalid args를 출력하는지 검증한다.
    def test_diff_invalid_args(self) -> None:
        lines_one = _response_lines(_run_script("DIFF only_one_arg\nexit\n"))
        lines_zero = _response_lines(_run_script("DIFF\nexit\n"))
        self.assertEqual(lines_one, ["Invalid args"])
        self.assertEqual(lines_zero, ["Invalid args"])

    # 디렉터리 경로를 파일로 열 때 Cannot read file 메시지를 출력하는지 검증한다.
    def test_diff_cannot_read_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            a_path = self._write(tmpdir, "a.txt", "hello\n")
            lines = _response_lines(_run_script(f'DIFF "{a_path}" "{tmpdir}"\nexit\n'))
            self.assertEqual(lines, [f"Cannot read file: {tmpdir}"])


class TestErrors(unittest.TestCase):
    # 미지정 명령이 Unknown command를 출력하는지 검증한다.
    def test_unknown_command(self) -> None:
        lines = _response_lines(_run_script("FOOBAR\nexit\n"))
        self.assertEqual(lines[0], "Unknown command: FOOBAR")

    # 인자 없는 COMMIT이 Invalid args를 출력하는지 검증한다.
    def test_commit_invalid_args(self) -> None:
        lines = _response_lines(_run_script("INIT alice\nCOMMIT\nexit\n"))
        self.assertEqual(lines[-1], "Invalid args")

    # 미존재 브랜치 SWITCH가 Unknown branch를 출력하는지 검증한다.
    def test_switch_unknown_branch(self) -> None:
        lines = _response_lines(_run_script("INIT alice\nSWITCH nope\nexit\n"))
        self.assertEqual(lines[-1], "Unknown branch: nope")

    # 잘못된 LOG --sort-by가 Invalid args를 출력하는지 검증한다.
    def test_log_invalid_sort_by(self) -> None:
        lines = _response_lines(
            _run_script("INIT alice\nCOMMIT a\nLOG --sort-by=hash\nexit\n")
        )
        self.assertEqual(lines[-1], "Invalid args")


class TestExit(unittest.TestCase):
    # main()이 run_repl 완료 후 종료 코드 0을 반환하는지 검증한다.
    def test_exit_returns_zero(self) -> None:
        from unittest.mock import patch

        with patch("mini_git.main.run_repl"):
            self.assertEqual(main(), 0)

    # quit 명령이 REPL을 종료하는지 검증한다.
    def test_quit_exits_repl(self) -> None:
        raw = _run_script("quit\n")
        self.assertNotIn("Unknown command", raw)

    # EOF가 REPL을 종료하는지 검증한다.
    def test_eof_exits_repl(self) -> None:
        repo = make_repo()
        stdout = StringIO()
        run_repl(repo, StringIO(""), stdout)
        self.assertIn("mini-git> ", stdout.getvalue())

    # Ctrl-C(KeyboardInterrupt)가 REPL을 정상 종료하는지 검증한다.
    def test_keyboard_interrupt_exits_repl(self) -> None:
        class InterruptingStdin(StringIO):
            def readline(self) -> str:
                raise KeyboardInterrupt

        repo = make_repo()
        stdout = StringIO()
        run_repl(repo, InterruptingStdin(), stdout)
        self.assertIn("mini-git> \n", stdout.getvalue())

    # readline()이 EOFError를 던져도 REPL이 정상 종료되는지 검증한다.
    def test_eof_error_exits_repl(self) -> None:
        class EofStdin(StringIO):
            def readline(self) -> str:
                raise EOFError

        repo = make_repo()
        stdout = StringIO()
        run_repl(repo, EofStdin(), stdout)
        self.assertIn("mini-git> ", stdout.getvalue())

    # StringIO 주입(비대화형) 경로에서는 add_history를 호출하지 않는다.
    def test_non_interactive_does_not_record_history(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_readline = MagicMock()
        with patch("mini_git.cli._readline", mock_readline):
            _run_script("init alice\nexit\n")
        mock_readline.add_history.assert_not_called()

    # readline 모듈이 없어도 REPL이 정상 동작하는지 검증한다.
    def test_readline_unavailable_still_runs(self) -> None:
        from unittest.mock import patch

        with patch("mini_git.cli._readline", None):
            raw = _run_script("quit\n")
        self.assertNotIn("Unknown command", raw)
