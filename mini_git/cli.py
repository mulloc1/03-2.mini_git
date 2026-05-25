"""CLI tokenizer, command dispatch, and REPL loop (subject §2.4, §4.1)."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import IO, TextIO

try:
    import readline as _readline
except ImportError:
    _readline = None

from mini_git.commit import Commit
from mini_git.diff import diff_lines
from mini_git.errors import CommandError, RepoError
from mini_git.repository import Repository
from mini_git.sort import merge_sort

PROMPT = "mini-git> "
_EXIT_COMMANDS = frozenset({"exit", "quit"})
_LOG_SORT_OPTIONS = frozenset({"date", "author"})
_DIFF_PREFIX = {"common": "  ", "added": "+ ", "deleted": "- "}


def tokenize(line: str) -> list[str]:
    """Split a command line into tokens; double-quoted spans are one token."""
    tokens: list[str] = []
    index = 0
    length = len(line)

    def read_quoted() -> str:
        nonlocal index
        index += 1
        start = index
        while index < length and line[index] != '"':
            index += 1
        if index >= length:
            raise CommandError("Unclosed quote")
        content = line[start:index]
        index += 1
        return content

    while index < length:
        while index < length and line[index].isspace():
            index += 1
        if index >= length:
            break
        if line[index] == '"':
            tokens.append(read_quoted())
        else:
            parts: list[str] = []
            while index < length and not line[index].isspace():
                if line[index] == '"':
                    parts.append(read_quoted())
                else:
                    parts.append(line[index])
                    index += 1
            tokens.append("".join(parts))
    return tokens


def format_commit(commit: Commit) -> str:
    """Format one commit summary line per plan §9.0."""
    timestamp = time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime(commit.created_at)
    )
    return (
        f"{commit.hash} {commit.author} {commit.branch} "
        f"{timestamp} {commit.message}"
    )


def _write_line(stdout: TextIO, text: str) -> None:
    stdout.write(text)
    stdout.write("\n")


def _write_commits(commits: list[Commit], stdout: TextIO) -> None:
    for commit in commits:
        _write_line(stdout, format_commit(commit))


def _write_branches(repo: Repository, stdout: TextIO) -> None:
    """Print each branch tip; prefix ``*`` marks the current HEAD branch."""
    head = repo.head
    if head is None:
        return
    branches = repo.branches()
    other_names = merge_sort(
        [name for name in branches if name != head],
        key=lambda name: name,
    )
    ordered_names = [head, *other_names]
    _write_line(stdout, "Branches:")
    for name in ordered_names:
        commit_hash = branches[name]
        tip = commit_hash if commit_hash is not None else "(no commit)"
        prefix = "* " if name == head else "  "
        _write_line(stdout, f"{prefix}{name} -> {tip}")


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
    else:
        _write_commits(commits, stdout)
    _write_branches(repo, stdout)


def _handle_branches(repo: Repository, args: list[str], stdout: TextIO) -> None:
    if len(args) != 0:
        raise CommandError("Invalid args")
    _write_branches(repo, stdout)


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
    _write_commits(commits, stdout)


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
    _write_commits(commits, stdout)


def _read_diff_file(path: str) -> list[str]:
    try:
        with open(path, encoding="utf-8") as handle:
            raw = handle.read()
    except FileNotFoundError as exc:
        raise CommandError(f"File not found: {path}") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise CommandError(f"Cannot read file: {path}") from exc

    parts = raw.split("\n")
    if parts and parts[-1] == "":
        parts.pop()
    return [part.rstrip("\r") for part in parts]


def _handle_diff(repo: Repository, args: list[str], stdout: TextIO) -> None:
    _ = repo
    if len(args) != 2:
        raise CommandError("Invalid args")
    a_lines = _read_diff_file(args[0])
    b_lines = _read_diff_file(args[1])
    records = diff_lines(a_lines, b_lines)
    if all(record.kind == "common" for record in records):
        _write_line(stdout, "Files are identical")
        return
    for record in records:
        _write_line(stdout, f"{_DIFF_PREFIX[record.kind]}{record.text}")


def _handle_merge(repo: Repository, args: list[str], stdout: TextIO) -> None:
    if len(args) != 1:
        raise CommandError("Invalid args")
    current_branch = repo.head
    commit = repo.merge(args[0])
    _write_line(
        stdout,
        f"Merged {args[0]} into {current_branch} as {commit.hash}",
    )


_Handler = Callable[[Repository, list[str], TextIO], None]

_HANDLERS: dict[str, _Handler] = {
    "init": _handle_init,
    "branch": _handle_branch,
    "switch": _handle_switch,
    "commit": _handle_commit,
    "log": _handle_log,
    "branches": _handle_branches,
    "path": _handle_path,
    "ancestors": _handle_ancestors,
    "search": _handle_search,
    "diff": _handle_diff,
    "merge": _handle_merge,
}


def dispatch(repo: Repository, tokens: list[str], stdout: TextIO) -> bool:
    """Execute one command; return False when the REPL should exit."""
    if not tokens:
        return True
    command = tokens[0].lower()
    handler = _HANDLERS.get(command)
    if handler is None:
        raise CommandError(f"Unknown command: {tokens[0]}")
    handler(repo, tokens[1:], stdout)
    return True


def _record_history(line: str) -> None:
    """Append one non-empty line to the in-memory readline history."""
    if _readline is None or not line.strip():
        return
    _readline.add_history(line)


def _read_input_line(
    input_stream: IO[str],
    output_stream: TextIO,
    *,
    interactive: bool,
) -> str | None:
    """Read one REPL line; return None on scripted EOF."""
    if interactive:
        return input(PROMPT)
    output_stream.write(PROMPT)
    output_stream.flush()
    raw = input_stream.readline()
    if raw == "":
        return None
    return raw.rstrip("\n")


def run_repl(
    repo: Repository,
    stdin: IO[str] | None = None,
    stdout: TextIO | None = None,
) -> None:
    """Run the Mini Git REPL until exit, quit, EOF, or interrupt."""
    import sys

    input_stream = stdin if stdin is not None else sys.stdin
    output_stream = stdout if stdout is not None else sys.stdout
    interactive = (
        stdin is None
        and stdout is None
        and input_stream.isatty()
        and _readline is not None
    )
    while True:
        try:
            line = _read_input_line(
                input_stream, output_stream, interactive=interactive
            )
        except EOFError:
            break
        except KeyboardInterrupt:
            output_stream.write("\n")
            break
        if line is None:
            break
        if interactive:
            _record_history(line)
        if not line.strip():
            continue
        try:
            tokens = tokenize(line)
            if not tokens:
                continue
            command = tokens[0].lower()
            if command in _EXIT_COMMANDS:
                break
            if not dispatch(repo, tokens, output_stream):
                break
        except KeyboardInterrupt:
            output_stream.write("\n")
            break
        except (CommandError, RepoError) as exc:
            _write_line(output_stream, str(exc))
