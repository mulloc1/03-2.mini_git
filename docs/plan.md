# Mini Git Implementation Plan (plan.md)

This document is a phased implementation plan that satisfies both the requirements in `docs/subject.md` and the coding/structure rules in the repository `.cursorrules`. Following the **Minimal-First / YAGNI** principle (.cursorrules §3), we start with the **minimum structure that meets requirements**; bonus tasks (subject §5) are separated into a later phase after the core assignment is done.

---

## 1. Goal Summary

- Implement a CLI (REPL) Mini Git application in Python 3.14 as a **single package** (`mini_git`).
- Unify the entry point as `python -m mini_git` (or `python main.py`) and provide a **REPL** with the `mini-git>` prompt (subject §2.4, §4.1).
- All data is **in-memory**; external files and network dependencies are out of scope for this assignment.
- Commit graph (DAG), inverted index, and sorting algorithms must be **implemented directly** without relying on standard sort/built-in graph libraries (subject §4.2–§4.4).
  - **Forbidden:** `sorted()`, `list.sort()` (subject §4.4).
- Apply **type hints** to all function signatures and add short docstrings to public functions (.cursorrules §4).
- Output format is **fixed** per §9 of this document.

---

## 2. Locked Decisions

Decisions for items left open in subject (“implementation free”, “tie-break rules free”, etc.) and other choices fixed for this assignment.

| Item                                     | Decision                                                                                                       | Rationale                                                                                         |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Command case (subject §4.1)              | **Case-insensitive** (`INIT`/`init`/`Init` all allowed)                                                        | As stated in subject §4.1                                                                         |
| Argument parsing (subject §4.1)          | Support **unquoted tokens** and **double-quoted values**; no escape sequences                                  | Subject example (`COMMIT "Add login feature"`) + YAGNI                                            |
| Option syntax                            | `SEARCH --author=<name>`, `LOG --sort-by=date`, `LOG --sort-by=author` (`=` required, no space)                | Matches subject §4.1 examples; simpler tokenizer                                                  |
| Hash generation (subject §4.2)           | **Session monotonic counter** → `f"{n:07x}"` 7-digit hex (`0000001`, `0000002`, …)                             | Session uniqueness only; readable output and deterministic lex order for `PATH` ties              |
| Commit store                             | **dict** (`hash → Commit`)                                                                                     | Subject “e.g. hash map” — average O(1) lookup is enough; custom DS focus is inverted index (§4.3) |
| Parent representation                    | `Commit.parents: list[str]` (hash strings). Root commit: empty list                                            | Subject §4.2 “zero or more parents”                                                               |
| timestamp                                | **Monotonic integer sequence** (`Commit` creation order = timestamp). Real clock stored separately for display | Deterministic ties for `LOG --sort-by=date` and topological `LOG`; test determinism               |
| Display clock                            | Inject `clock: Callable[[], float] = time.time` (tests use `FakeClock`)                                        | .cursorrules §5 Testing Determinism                                                               |
| HEAD model                               | Single pointer to **branch name**. No detached HEAD                                                            | Within subject commands (`SWITCH branch_name` only), YAGNI                                        |
| Initial branch                           | `main`                                                                                                         | subject §4.5 INIT                                                                                 |
| Duplicate `BRANCH` name                  | **Error** (`Branch already exists: <name>`)                                                                    | Safety; subject “standardize errors” spirit                                                       |
| `SWITCH` to missing branch               | `Unknown branch: <name>`                                                                                       | subject §4.1 standard message                                                                     |
| `INIT` re-invocation                     | **Reset current session** (discard all commits, branches, inverted index, rebuild)                             | subject §4.5 “initialize repository”                                                              |
| `LOG` topological output (subject §4.5)  | **Kahn's algorithm** parent→child order. Ties (same in-degree): ascending `timestamp` → lex `hash`             | “Parents before children” + determinism                                                           |
| `LOG --sort-by=date`                     | Ascending `timestamp`; ties: lex `hash`                                                                        | Not “newest first”; ascending aligns with parent-first principle                                  |
| `LOG --sort-by=author`                   | Lex `author`; ties: ascending `timestamp` → lex `hash`                                                         | Multi-key stable-sort effect                                                                      |
| `PATH` graph model (subject §4.5)        | Treat commit–parent links as **undirected edges**, BFS. Ties: **lexicographically smallest** hash path string  | As stated in subject                                                                              |
| `ANCESTORS`                              | Exclude start commit; list in topological order (parents first); ties: lex `hash`                              | subject “ancestor” meaning + deterministic output                                                 |
| `SEARCH keyword` matching (subject §4.3) | **Whitespace split + lower normalization**, then **exact token match** (not substring)                         | subject §4.3                                                                                      |
| `SEARCH --author=<name>` matching        | **Exact** author string (case-sensitive)                                                                       | User names are identifiers; lower only for keywords                                               |
| Result order (SEARCH/ANCESTORS)          | Topological (parents first); ties: lex `hash`                                                                  | Unspecified in subject → determinism                                                              |
| Exit commands (subject §4.1)             | `exit` or `quit` (case-insensitive); `Ctrl-D` (EOF) equivalent                                                 | subject §2.4 + consistency                                                                        |
| REPL command history (optional)          | Stdlib `readline` in-memory only when stdin is a TTY; no file persistence; not a subject requirement           | UX helper; tests use injected `StringIO` (non-interactive path)                                   |
| Sort algorithm (subject §4.4)            | **Merge Sort** implemented directly (key function + stable)                                                    | Average and worst O(N log N); **stable** for readable tie handling                                |
| Test runner                              | Standard `unittest` (`python -m unittest discover -s tests -p 'test_*.py' -v`)                                 | .cursorrules §5 Stdlib Test Runner                                                                |

---

## 3. Directory / Module Layout

Follows subject §4.2–§4.5 responsibilities (commit graph, inverted index, sort, CLI). Per .cursorrules §3, keep a **flat** single package (split only with evidence). `tests/` mirrors `mini_git/` modules (.cursorrules §5).

```
03-2.mini_git/
├── README.md                 # How to run · command table · output examples
├── docs/
│   ├── subject.md
│   └── plan.md               # (this document)
├── pytest.ini                # pythonpath = . tests
├── main.py                   # subject §2.5 entry point (delegates to mini_git.main)
├── mini_git/
│   ├── __init__.py
│   ├── __main__.py           # python -m mini_git → main()
│   ├── main.py               # Entry assembly · REPL loop
│   ├── commit.py             # Commit dataclass + hash issuer
│   ├── inverted_index.py     # Inverted index (keyword/author → hash list) (subject §4.3)
│   ├── graph.py              # Topological sort · BFS shortest path · all ancestors (subject §4.5)
│   ├── sort.py               # Stable merge sort (subject §4.4)
│   ├── repository.py         # Repo engine: branches · HEAD · commit graph · index assembly
│   ├── cli.py                # Tokenizer · command dispatch · output formatting
│   └── errors.py             # Domain exceptions (CommandError, RepoError, etc.)
└── tests/
    ├── helpers.py            # Temp repo factory · FakeClock · commit sequence helpers
    ├── test_commit.py
    ├── test_inverted_index.py
    ├── test_graph.py
    ├── test_sort.py
    ├── test_repository.py
    └── test_cli.py
```

**Split rationale** (.cursorrules §3 “split after evidence”):

- `commit.py` / `inverted_index.py` / `graph.py` / `sort.py` — subject names separate requirements (§4.2·§4.3·§4.4·§4.5), each independently testable.
- `repository.py` ↔ `cli.py` — `repository` returns **pure values**; `cli` handles **I/O (REPL) + formatting** (.cursorrules §4 SRP).
- Root `main.py` is a **thin delegate** for subject §2.5 (`from mini_git.main import main; main()`).
- No extra `parser`/`commands`/`tokenizer` modules in this phase (single use site, insufficient evidence).

---

## 4. Data Structure Design (subject §4.2, §4.3)

### 4.1 Commit Node (`commit.py`)

| Item         | Design                                                                                                               |
| ------------ | -------------------------------------------------------------------------------------------------------------------- |
| `Commit`     | `@dataclass(frozen=True)` — `hash: str`, `message: str`, `author: str`, `timestamp: int`, `parents: tuple[str, ...]` |
| Immutability | Commits are immutable once created (DAG node semantics). Parents as immutable `tuple`                                |
| `HashIssuer` | Monotonic counter → `f"{n:07x}"`. `reset()` on `INIT`                                                                |
| Display time | `Commit.timestamp` for sort/ties; `Commit.created_at` (`clock()` snapshot) for LOG display                           |

### 4.2 Commit Graph Store (inside `repository.py`)

subject §4.2 “repository: fast lookup by hash (e.g. hash map)” via dict.

| Class / field  | Description                                                                  |
| -------------- | ---------------------------------------------------------------------------- |
| `_commits`     | `dict[str, Commit]` — hash → Commit node                                     |
| `_branches`    | `dict[str, str]` — branch name → current commit hash                         |
| `_head`        | `str` — current branch name                                                  |
| `_author`      | `str` — current user                                                         |
| `_root_hashes` | `list[str]` — root commits (`parents == ()`). Used to seed topological `LOG` |
| `_issuer`      | `HashIssuer` — session counter                                               |

> This assignment does **not** forbid built-in dict (subject §4.2). Differentiation is direct inverted index, sort, and graph algorithms (§4.3–§4.5).

### 4.3 Inverted Index (`inverted_index.py`, subject §4.3)

| Item           | Design                                                                                                                                   |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Methods        | `add_commit(commit)`, `search_keyword(token) -> list[str]`, `search_author(name) -> list[str]`, `remove_commit(hash)` (for `INIT` reset) |
| Internal       | `_by_keyword: dict[str, list[str]]`, `_by_author: dict[str, list[str]]`                                                                  |
| Tokenize       | `commit.message.split()` → each token `lower()` → **dedupe** tokens per commit (set then list)                                           |
| Order          | Preserve hash append order (caller sorts in §5). Determinism is caller's job                                                             |
| Empty          | Missing key → `[]`                                                                                                                       |
| Private helper | `_tokenize(message) -> set[str]` (.cursorrules §4)                                                                                       |

> “Quick candidates without scanning every commit” — keyword/author dict lookup O(1), then §5 sort only. vs linear scan: single key lookup vs tokenizing every message — explained in evaluation answers (§9).

---

## 5. Sorting Algorithm (`sort.py`, subject §4.4)

Direct implementation to satisfy `sorted()` / `list.sort()` ban. **Merge Sort** (average and worst O(N log N), stable).

| Item       | Design                                                                                           |
| ---------- | ------------------------------------------------------------------------------------------------ |
| Public API | `merge_sort(items: list[T], key: Callable[[T], K] = lambda x: x) -> list[T]` — returns new list  |
| Compare    | `<` on `key(item)` — tuples like `(timestamp, hash)` for multi-key                               |
| Stable     | On tie, **left (earlier) element wins** in merge                                                 |
| Private    | `_merge(left, right, key)`                                                                       |
| Used by    | `LOG --sort-by=...`, topological tie breaks, `SEARCH`/`ANCESTORS` result order, `PATH` tie paths |

> Merge Sort: satisfies subject §4.4 explanation of average/worst complexity and **stable sort**. Quick Sort worst O(N²) and usually unstable; Heap Sort unstable.

---

## 6. Graph Algorithms (`graph.py`, subject §4.5)

Pure functions over (commits dict, hash → parents). No I/O. Tie-breaking unified via §5 `merge_sort`.

### 6.1 Topological Sort (`topological_order`)

- **Purpose:** `LOG` “parents before children” (subject §4.5).
- **Algorithm:** Kahn's algorithm.
- **Signature:** `topological_order(hashes: Iterable[str], get_parents: Callable[[str], Iterable[str]], get_sort_key: Callable[[str], Any]) -> list[str]`
- **Steps:**
  1. Compute in-degrees on **child → parent** edges within input hash set (ignore parents outside set — safe for `ANCESTORS` subgraphs).
  2. Initialize queue with in-degree 0 nodes sorted by `get_sort_key`.
  3. On pop, decrement children's in-degree; enqueue when 0, sorted by same key.
- **Determinism:** `get_sort_key` fully fixes tie order.

### 6.2 Shortest Path (`shortest_path`, subject §4.5 `PATH`)

- **Model:** commit–parent links as **undirected** edges, BFS.
- **Signature:** `shortest_path(start: str, goal: str, get_neighbors: Callable[[str], Iterable[str]]) -> list[str] | None`
- **Neighbors:** `repository.neighbors(hash)` returns `parents + children` (§7.3).
- **Ties:** Multiple shortest paths → **lexicographically smallest** hash path string (subject).
  - Implementation: prefer BFS with per-node “lexicographically smallest predecessor” and backtrack single path (§6.2 latter). Avoid enumerating all paths (explodes on wide graphs); fine at assignment scale.
- **Missing:** return `None` → CLI prints `No path`.

### 6.3 All Ancestors (`ancestors`, subject §4.5 `ANCESTORS`)

- **Signature:** `ancestors(start: str, get_parents: Callable[[str], Iterable[str]]) -> set[str]`
- **Algorithm:** BFS/DFS **parent direction only** from start hash.
- **Exclude:** start hash **not** in result (subject “ancestor” meaning).
- **DAG:** `visited` set prevents duplicates (defensive).

---

## 7. Repository Engine (`repository.py`)

Combines structures and algorithms. **Pure logic layer** — returns Python values, no CLI (.cursorrules §4 SRP). Violations raise `RepoError`; CLI standardizes messages.

### 7.1 Command Mapping

| Method                                      | Behavior                                                                                                                                                                  |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `init(user_name: str) -> None`              | Reset all state. Create `main` (no commit until first `COMMIT` — `_branches["main"]` empty; see §7.4). HEAD = `main`. author = `user_name`. Reset index and `HashIssuer`. |
| `branch(branch_name: str) -> None`          | Register current HEAD commit as new branch (error if no commit yet). Duplicate name → `RepoError`.                                                                        |
| `switch(branch_name: str) -> None`          | Missing → `RepoError`. Else update HEAD.                                                                                                                                  |
| `commit(message: str) -> Commit`            | Error if not initialized. Parent = current HEAD commit hash (or none). Issue hash, update `_commits`, `_branches[head]`, index; return.                                   |
| `log() -> list[Commit]`                     | Topological sort all `_commits`, key `(timestamp, hash)` ascending.                                                                                                       |
| `log_sorted(by: Literal["date", "author"])` | `merge_sort` all commits. `date` → `(timestamp, hash)`. `author` → `(author, timestamp, hash)`.                                                                           |
| `path(a: str, b: str) -> list[str] \| None` | Undirected BFS shortest path; lex-min tie.                                                                                                                                |
| `ancestors(h: str) -> list[Commit]`         | Unknown hash → `RepoError`. §6.3 then topological order (exclude self).                                                                                                   |
| `search_keyword(kw: str) -> list[Commit]`   | `kw.lower()` index lookup → map to commits → topological order.                                                                                                           |
| `search_author(name: str) -> list[Commit]`  | Author index → topological order.                                                                                                                                         |

### 7.2 Clock Injection

- Constructor: `Repository(clock: Callable[[], float] = time.time)`.
- Human time: `clock()` stored in `Commit.created_at` at creation. Sort/ties use monotonic `timestamp` only.
- Tests: `FakeClock` (.cursorrules §5).

### 7.3 Adjacency (`PATH` helper)

Undirected BFS needs children index:

- `_children: dict[str, list[str]]` — parent hash → child hashes; updated on each `commit()`.
- `neighbors(h) -> list[str]` — `parents + children` for §6.2.

### 7.4 Empty Branch and First Commit

- After `INIT`, `main` has no commit (`_branches["main"] is None`).
- Before first commit:
  - `BRANCH` → `RepoError("Cannot branch before first commit")`.
  - `SWITCH` — only existing branches (e.g. `main`); missing → standard error.

---

## 8. CLI Specification (`cli.py`, subject §2.4, §4.1)

### 8.1 Tokenizer

- Whitespace split + **double-quoted** values as one token. No escapes (YAGNI).
- Options: `--key=value` only (not `--key value`).
- Examples: `COMMIT "Add login feature"` → `["COMMIT", "Add login feature"]`.
- `SEARCH --author="Alice Liddell"` → `["SEARCH", "--author=Alice Liddell"]`.

### 8.2 Dispatch Table

| Input                   | Call                        | Success response                         |
| ----------------------- | --------------------------- | ---------------------------------------- |
| `INIT user_name`        | `repo.init(user_name)`      | `Initialized repository for <user_name>` |
| `BRANCH branch_name`    | `repo.branch(name)`         | `Created branch <name> at <hash>`        |
| `SWITCH branch_name`    | `repo.switch(name)`         | `Switched to branch <name>`              |
| `COMMIT message`        | `repo.commit(message)`      | `Committed <hash>`                       |
| `LOG`                   | `repo.log()`                | One summary line per commit (§9.2)       |
| `LOG --sort-by=date`    | `repo.log_sorted("date")`   | Same format, ascending timestamp         |
| `LOG --sort-by=author`  | `repo.log_sorted("author")` | Same format, ascending author            |
| `PATH commit1 commit2`  | `repo.path(c1, c2)`         | Hashes joined with `->`, or `No path`    |
| `ANCESTORS commit_hash` | `repo.ancestors(h)`         | One line per ancestor, exclude self      |
| `SEARCH keyword`        | `repo.search_keyword(kw)`   | Matching commits, or `No results`        |
| `SEARCH --author=name`  | `repo.search_author(name)`  | Same format                              |
| `exit` / `quit`         | End REPL                    | No output, exit code `0`                 |

### 8.3 Error Output (subject §4.1)

Print `RepoError` / `CommandError` message on one line. Fixed messages per this plan.

| Situation                    | Output                              |
| ---------------------------- | ----------------------------------- |
| Unknown command              | `Unknown command: <cmd>`            |
| Bad arg count/type           | `Invalid args`                      |
| Unknown branch               | `Unknown branch: <name>`            |
| Unknown commit hash          | `Unknown commit: <hash>`            |
| Command before `INIT`        | `Repository not initialized`        |
| `BRANCH` before first commit | `Cannot branch before first commit` |
| Duplicate `BRANCH`           | `Branch already exists: <name>`     |
| Invalid `LOG --sort-by`      | `Invalid args` (only date/author)   |

`EOF` (`Ctrl-D`) same as `exit`.

### 8.4 Optional: readline history (not required by subject)

When `run_repl()` uses default `sys.stdin` on a TTY and `import readline` succeeds, use `input(PROMPT)` so **Up/Down** recall prior lines. Record each non-blank line with `readline.add_history()` (in-memory only; no `read_history_file` / `write_history_file`). Injected stdin (`unittest` / pipes) keeps the scripted `write` + `readline()` path with no history side effects.

---

## 9. Output Specification

Fixed stdout format. Tests (§11) capture stdout against this section.

### 9.0 Common One-Line Commit Summary

```
<hash> <author> <human_timestamp> <message>
```

- `<hash>` — 7-digit hex (§2).
- `<human_timestamp>` — `time.strftime("%Y-%m-%d %H:%M:%S", ...)` from `clock()`.
- `<message>` — as given (quotes stripped).

### 9.1 INIT / COMMIT / BRANCH / SWITCH

```
mini-git> INIT alice
Initialized repository for alice
mini-git> COMMIT "Add login feature"
Committed 0000001
mini-git> COMMIT "Fix login bug"
Committed 0000002
mini-git> BRANCH feature
Created branch feature at 0000002
mini-git> SWITCH feature
Switched to branch feature
mini-git> COMMIT "Add UI polish"
Committed 0000003
```

### 9.2 LOG (Topological)

```
mini-git> LOG
0000001 alice 2026-05-16 09:00:00 Add login feature
0000002 alice 2026-05-16 09:00:01 Fix login bug
0000003 alice 2026-05-16 09:00:02 Add UI polish
```

If empty:

```
mini-git> LOG
(no commits)
```

### 9.3 LOG --sort-by=date / --sort-by=author

```
mini-git> LOG --sort-by=date
0000001 alice ...
0000002 alice ...
0000003 alice ...
mini-git> LOG --sort-by=author
0000001 alice ...
0000003 alice ...
0000002 bob ...
```

### 9.4 PATH

```
mini-git> PATH 0000001 0000003
0000001 -> 0000002 -> 0000003
mini-git> PATH 0000001 0000099
Unknown commit: 0000099
mini-git> PATH 0000005 0000007
No path
```

### 9.5 ANCESTORS

```
mini-git> ANCESTORS 0000003
0000001 alice ... Add login feature
0000002 alice ... Fix login bug
```

Exclude self. If no ancestors (root):

```
mini-git> ANCESTORS 0000001
(no ancestors)
```

### 9.6 SEARCH

```
mini-git> SEARCH login
0000001 alice ... Add login feature
0000002 alice ... Fix login bug
mini-git> SEARCH --author=alice
0000001 alice ... Add login feature
0000002 alice ... Fix login bug
0000003 alice ... Add UI polish
mini-git> SEARCH missing
No results
```

### 9.7 Invalid Input

```
mini-git> FOOBAR
Unknown command: FOOBAR
mini-git> COMMIT
Invalid args
mini-git> SWITCH nope
Unknown branch: nope
mini-git> LOG --sort-by=hash
Invalid args
```

### 9.8 Exit

```
mini-git> exit
```

→ REPL ends, exit code `0`. `quit` and `Ctrl-D` equivalent.

---

## 10. Phased Implementation Plan

Each phase = **one logical change = one commit** (.cursorrules §5), Conventional Commits prefix.

### Phase 0 — Project Scaffolding

- Empty package: `mini_git/__init__.py`, `__main__.py`, `main.py`.
- Root `main.py` — one-line delegate (subject §2.5).
- `pytest.ini` — `pythonpath = . tests`.
- `tests/helpers.py` — `make_repo(clock=FakeClock())`, `FakeClock`, linear commit helper.
- Commit: `chore: scaffold mini_git package and test layout`

### Phase 1 — Commit Node & Hash Issuer (subject §4.2)

- `commit.py` — frozen `Commit`, `HashIssuer`.
- `test_commit.py` — uniqueness, reset on `INIT`, immutable root `parents`.
- Commit: `feat: add commit node and hash issuer`

### Phase 2 — Stable Merge Sort (subject §4.4)

- `sort.py` — `merge_sort`, `_merge`.
- `test_sort.py` — empty, single, sorted/reverse/random, **stability**, multi-key.
- Commit: `feat: add stable merge sort`

### Phase 3 — Inverted Index (subject §4.3)

- `inverted_index.py` — add/remove/search, `_tokenize`.
- `test_inverted_index.py` — split+lower, dedupe tokens, `[]`, author case, remove.
- Commit: `feat: add inverted index for keyword and author search`

### Phase 4 — Graph Algorithms (subject §4.5)

- `graph.py` — `topological_order`, `shortest_path`, `ancestors`; ties via `merge_sort`.
- `test_graph.py` — diamond, chain, undirected path lex tie, exclude self in ancestors.
- Commit: `feat: add topological sort, shortest path, ancestors`

### Phase 5 — Repository Basic Commands (subject §4.5: INIT/BRANCH/SWITCH/COMMIT)

- `repository.py`, `errors.py` `RepoError`.
- `init`/`branch`/`switch`/`commit` + index updates, clock injection.
- `test_repository.py` (1) — INIT/main/HEAD, BRANCH guards, SWITCH errors, parent linkage, branch fork.
- Commit: `feat: add repository with init, branch, switch, commit`

### Phase 6 — LOG / Sort Options (subject §4.5)

- `log()`, `log_sorted(by)`.
- `test_repository.py` — topological parent-first, date/author multi-key, bad `by`.
- Commit: `feat: add log with topological and sorted views`

### Phase 7 — PATH / ANCESTORS (subject §4.5)

- `path`, `ancestors`; maintain `_children` on `commit()`.
- `test_repository.py` — chain PATH, fork PATH, `No path`, ANCESTORS exclude self.
- Commit: `feat: add path and ancestors commands`

### Phase 8 — SEARCH (subject §4.5)

- `search_keyword`, `search_author`.
- `test_repository.py` — exact token, no substring, author case-sensitive, topological result order.
- Commit: `feat: add keyword and author search`

### Phase 9 — CLI / REPL Integration (subject §2.4, §4.1)

- `cli.py` — tokenizer, dispatch, formatting; wire `__main__` / `main.py` / `run_repl()`.
- `exit`/`quit`/EOF, code `0`.
- `test_cli.py` — stdin scripts, stdout vs §9; error cases.
- Commit: `feat: add cli repl with command dispatch`

### Phase 10 — README / Docs

- `README.md`: run instructions, commands, output samples, limits (in-memory, volatile on exit), `INIT` reset meaning; sync §2 locked decisions.
- Commit: `docs: add README with usage and command reference`

### Phase 11 (Optional) — Bonus (subject §5)

- Only after core passes (.cursorrules §3 YAGNI). Separate branch/commits.
  1. **`diff <file1> <file2>`** — LCS line diff; file I/O + `tests/fixtures`.
  2. **`merge <branch>`** — two-parent commit; update `_children` for both parents; regression on PATH/ANCESTORS.
  3. **Sort performance** — measure merge sort by size/pattern in `docs/insights/`.

---

## 11. Test Strategy

- Runner: `python -m unittest discover -s tests -p 'test_*.py' -v` (.cursorrules §5).
- Determinism: inject `clock`; tests use `FakeClock`. In-memory only.
- Assertions: `self.assertEqual` etc. only (.cursorrules §5 Assert First).
- One-line **purpose comment** per test function (.cursorrules §5).
- Shared fixtures in `tests/helpers.py`.

Checklist:

- `Commit` immutability; `HashIssuer` reset on `INIT`.
- Merge sort stability and multi-key.
- Inverted index: split+lower, dedupe token per commit.
- `topological_order` parent-first + deterministic ties.
- `shortest_path` undirected BFS min edges; lex-min path tie.
- `ancestors` excludes self.
- `INIT` → `BRANCH` before first commit rejected; unknown `SWITCH`.
- `COMMIT` parents: forked branches share fork-point parent.
- `LOG --sort-by=date|author` multi-key.
- Unknown hash → `Unknown commit: <hash>`.
- `SEARCH` no substring match.
- **CLI output** matches §9 (spacing, `->`).

---

## 12. Risks / Deferred Decisions

| Item                                  | Risk                                   | Mitigation                                                               |
| ------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------ |
| `PATH` lex-min path                   | Enumerating all paths explodes         | BFS backtrack with lex-min predecessor only (§6.2)                       |
| `SEARCH` token rules                  | Substring vs token ambiguity           | **Exact token match** locked (§2), documented in README/plan             |
| `INIT` hash counter                   | “New session” vs “restart”             | `HashIssuer.reset()`; define uniqueness as “since last `INIT`” in README |
| `BRANCH`/`SWITCH` before first commit | `_branches["main"] is None`            | `BRANCH` rejected; `SWITCH main` only (§7.4)                             |
| Topological ties                      | Unsorted enqueue → nondeterministic    | `merge_sort` at every enqueue (§6.1) + regression test                   |
| `clock` in output                     | Nondeterministic real time             | Mandatory `FakeClock` in CLI output tests                                |
| Heavy `key` in merge sort             | Key recomputed each compare            | Fine at assignment scale; optional Schwartzian cache                     |
| Bonus `merge`                         | Two parents affect topo/ancestors/PATH | Update plan + diamond/merge regression tests                             |

---

## 13. Definition of Done

- All **9 commands** from subject §2.1–§2.4 work with §9 output format.
- Commit graph is a **DAG** with average O(1) hash lookup (subject §4.2).
- Inverted index uses **split + lower** tokens; keyword and author indexes separate (subject §4.3).
- **Merge Sort** implemented without `sorted()`/`list.sort()`; stability proven by tests (subject §4.4).
- `LOG` prints **parents before children**; ties: timestamp → hash (subject §4.5).
- `PATH`: **undirected** shortest path; lex-min hash path string on ties (subject §4.5).
- `ANCESTORS`: all reachable ancestors, **excluding self** (subject §4.5).
- REPL at `mini-git>`; `exit`/`quit`/`EOF` exit `0` (subject §2.4).
- Type hints and short docstrings on public functions (.cursorrules §4).
- `python -m unittest discover -s tests -p 'test_*.py' -v` passes with no extra packages (.cursorrules §5).
- `README.md`: run, commands, output examples, in-memory limits, `INIT` reset meaning.
- subject §3 five learning objectives explainable from §4–§6 implementation and tests.
