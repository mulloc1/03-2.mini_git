"""CLI tokenizer, command dispatch, and REPL loop (subject §2.4, §4.1)."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import IO, TextIO

from mini_git.commit import Commit
from mini_git.errors import CommandError, RepoError
from mini_git.repository import Repository

PROMPT = "mini-git> "
_EXIT_COMMANDS = frozenset({"exit", "quit"})
_LOG_SORT_OPTIONS = frozenset({"date", "author"})


def tokenize(line: str) -> list[str]:
    """Split a command line into tokens; double-quoted spans are one token."""
    tokens: list[str] = []
    index = 0
    length = len(line)
    while index < length:
        while index < length and line[index].isspace():
            index += 1
        if index >= length:
            break
        if line[index] == '"':
            index += 1
            start = index
            while index < length and line[index] != '"':
                index += 1
            tokens.append(line[start:index])
            if index < length:
                index += 1
        else:
            parts: list[str] = []
            while index < length and not line[index].isspace():
                if line[index] == '"':
                    index += 1
                    while index < length and line[index] != '"':
                        parts.append(line[index])
                        index += 1
                    if index < length:
                        index += 1
                else:
                    parts.append(line[index])
                    index += 1
            tokens.append("".join(parts))
    return tokens


def format_commit(commit: Commit, human_at: float) -> str:
    """Format one commit summary line per plan §9.0."""
    timestamp = time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime(human_at)
    )
    return f"{commit.hash} {commit.author} {timestamp} {commit.message}"


def _write_line(stdout: TextIO, text: str) -> None:
    stdout.write(text)
    stdout.write("\n")


def _write_commits(
    repo: Repository, commits: list[Commit], stdout: TextIO
) -> None:
    for commit in commits:
        human_at = repo.human_clock_at(commit.hash)
        _write_line(stdout, format_commit(commit, human_at))


def _handle_init(repo: Repository, args: list[str], stdout: TextIO) -> None:
    if len(args) != 1:
        raise CommandError("Invalid args")
    repo.init(args[0])
    _write_line(stdout, f"Initialized repository for {args[0]}")


def _handle_branch(repo: Repository, args: list[str], stdout: TextIO) -> None:
    if len(args) != 1:
        raise CommandError("Invalid args")
    commit_hash = repo.branch(args[0])
    _write_line(stdout, f"Created branch {args[0]} at {commit_hash}")


def _handle_switch(repo: Repository, args: list[str], stdout: TextIO) -> None:
    if len(args) != 1:
        raise CommandError("Invalid args")
    repo.switch(args[0])
    _write_line(stdout, f"Switched to branch {args[0]}")


def _handle_commit(repo: Repository, args: list[str], stdout: TextIO) -> None:
    if len(args) != 1:
        raise CommandError("Invalid args")
    commit = repo.commit(args[0])
    _write_line(stdout, f"Committed {commit.hash}")


def _handle_log(repo: Repository, args: list[str], stdout: TextIO) -> None:
    if len(args) == 0:
        commits = repo.log()
    elif len(args) == 1 and args[0].startswith("--sort-by="):
        sort_by = args[0][len("--sort-by=") :]
        if sort_by not in _LOG_SORT_OPTIONS:
            raise CommandError("Invalid args")
        commits = repo.log_sorted(sort_by)
    else:
        raise CommandError("Invalid args")
    if not commits:
        _write_line(stdout, "(no commits)")
        return
    _write_commits(repo, commits, stdout)


def _handle_path(repo: Repository, args: list[str], stdout: TextIO) -> None:
    if len(args) != 2:
        raise CommandError("Invalid args")
    path_hashes = repo.path(args[0], args[1])
    if path_hashes is None:
        _write_line(stdout, "No path")
        return
    _write_line(stdout, " -> ".join(path_hashes))


def _handle_ancestors(
    repo: Repository, args: list[str], stdout: TextIO
) -> None:
    if len(args) != 1:
        raise CommandError("Invalid args")
    commits = repo.ancestors(args[0])
    if not commits:
        _write_line(stdout, "(no ancestors)")
        return
    _write_commits(repo, commits, stdout)


def _handle_search(repo: Repository, args: list[str], stdout: TextIO) -> None:
    if len(args) != 1:
        raise CommandError("Invalid args")
    token = args[0]
    if token.startswith("--author="):
        name = token[len("--author=") :]
        if not name:
            raise CommandError("Invalid args")
        commits = repo.search_author(name)
    else:
        commits = repo.search_keyword(token)
    if not commits:
        _write_line(stdout, "No results")
        return
    _write_commits(repo, commits, stdout)


_Handler = Callable[[Repository, list[str], TextIO], None]

_HANDLERS: dict[str, _Handler] = {
    "init": _handle_init,
    "branch": _handle_branch,
    "switch": _handle_switch,
    "commit": _handle_commit,
    "log": _handle_log,
    "path": _handle_path,
    "ancestors": _handle_ancestors,
    "search": _handle_search,
}


def dispatch(repo: Repository, tokens: list[str], stdout: TextIO) -> bool:
    """Execute one command; return False when the REPL should exit."""
    if not tokens:
        return True
    command = tokens[0].lower()
    if command in _EXIT_COMMANDS:
        return False
    handler = _HANDLERS.get(command)
    if handler is None:
        raise CommandError(f"Unknown command: {tokens[0]}")
    handler(repo, tokens[1:], stdout)
    return True


def run_repl(
    repo: Repository,
    stdin: IO[str] | None = None,
    stdout: TextIO | None = None,
) -> None:
    """Run the Mini Git REPL until exit, quit, EOF, or interrupt."""
    import sys

    input_stream = stdin if stdin is not None else sys.stdin
    output_stream = stdout if stdout is not None else sys.stdout
    while True:
        try:
            output_stream.write(PROMPT)
            output_stream.flush()
            line = input_stream.readline()
        except EOFError:
            break
        except KeyboardInterrupt:
            output_stream.write("\n")
            break
        if line == "":
            break
        line = line.rstrip("\n")
        if not line.strip():
            continue
        tokens = tokenize(line)
        if not tokens:
            continue
        command = tokens[0].lower()
        if command in _EXIT_COMMANDS:
            break
        try:
            if not dispatch(repo, tokens, output_stream):
                break
        except KeyboardInterrupt:
            output_stream.write("\n")
            break
        except (CommandError, RepoError) as exc:
            _write_line(output_stream, str(exc))
