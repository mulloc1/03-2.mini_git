# Mini Git Bonus Implementation Plan (bonus_plan.md)

This document plans the **bonus tasks** in `docs/subject.md` §5. It assumes the core mission (`docs/plan.md` Phases 0–10) is **done and merged**, and starts a new phase on top of the working `mini_git` package. As in `.cursorrules` §3 (YAGNI), we keep additions **minimal** and only extend modules where the existing responsibility already fits.

Subject §5 lists three optional items:


| Item                            | Subject text                                                                                     |
| ------------------------------- | ------------------------------------------------------------------------------------------------ |
| **Diff**                        | `diff <file1> <file2>`: line-by-line compare; mark **added / deleted / common** lines            |
| **Merge simulation**            | `merge <branch_name>`: merge commit with **two** parents (current HEAD + target branch HEAD)     |
| **Sort performance comparison** | For our sort implementation, document **runtime or comparison counts** by input size and pattern |


---

## 1. Goal Summary

- Add the three bonus features **without changing the public output format** of the existing nine core commands (subject §9 in `plan.md`).
- Keep the **single in-memory** session model. `diff` is the only place that reads from disk; merge does not write the working tree.
- Follow the existing layering: pure logic in `mini_git/*` modules, I/O and formatting in `cli.py`. Pure functions are independently testable (`tests/test_*.py`).
- Sort performance work is **documentation + a small benchmark script**, not a new REPL command.
- Bonus features ship as a **separate branch / set of commits** so the core grading scope is untouched (`.cursorrules` §6 Logical Commit Unit).

---

## 2. Locked Decisions

Decisions for items left free by subject §5 (output format details, conflict handling, etc.) and for choices that would be expensive to reverse later.


| Item                                          | Decision                                                                                                                                     | Rationale                                                                               |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Command case                                  | **Case-insensitive** like core commands                                                                                                      | Consistent with subject §4.1                                                            |
| `diff` arg parsing                            | **Exactly two** positional args; double-quoted paths allowed                                                                                 | Reuse existing `tokenize` from `cli.py`                                                 |
| `diff` file source                            | **Real local files** read at command time; not commits / not staged                                                                          | Subject says “two text files”; YAGNI re: file blobs                                     |
| `diff` algorithm                              | **LCS (longest common subsequence)** over lines                                                                                              | Standard textbook diff; deterministic; aligns with `keywords.md` §18                    |
| `diff` line markers                           | `+ <line>` (added), `- <line>` (deleted), `<line>` (common, two spaces)                                                                      | Familiar to `git diff` users; trivially testable                                        |
| `diff` line ending                            | Strip trailing `\n` / `\r\n` for comparison; print without trailing newline of source                                                        | Cross-platform determinism                                                              |
| `diff` errors                                 | `Invalid args` (wrong count), `File not found: <path>`, `Cannot read file: <path>`                                                           | Consistent with subject §4.1 standardized messages                                      |
| `merge` model                                 | Create one **new commit with two parents** = `(HEAD commit, target branch commit)`                                                           | Subject §5                                                                              |
| `merge` precondition                          | Both branches must have at least one commit; target branch ≠ current branch                                                                  | Two parents must exist and be distinct                                                  |
| `merge` already-ancestor case                 | If target HEAD is an **ancestor of current HEAD**, refuse with `Already up to date` (no new commit)                                          | Avoids degenerate self-merge; matches Git mental model                                  |
| `merge` if current HEAD is ancestor of target | Still create a real **two-parent** commit (no fast-forward)                                                                                  | Subject literally says "two parents"; YAGNI for fast-forward                            |
| `merge` message                               | Default `Merge branch <branch_name>`; no override syntax in this phase                                                                       | YAGNI                                                                                   |
| `merge` graph impact                          | Update `_children[parent]` for **both** parents; everything else (topo, PATH, ANCESTORS, SEARCH) flows through existing algorithms unchanged | Two-parent already allowed by `Commit.parents: tuple[str, ...]`                         |
| `merge` author / timestamp                    | Same rules as `COMMIT` (current author, next monotonic `timestamp`, `clock()` for display)                                                   | Reuse existing `commit()` path                                                          |
| Sort benchmark scope                          | Measure **our `merge_sort`** only; the requirement is "for your sort implementation"                                                         | Subject §5                                                                              |
| Sort benchmark metric                         | **Comparison count** (deterministic) + **wall-clock ms** (informative)                                                                       | Comparison counts repeat across machines; runtime is for intuition                      |
| Sort benchmark inputs                         | Sizes `{100, 1_000, 10_000, 50_000}` × patterns `{random, sorted, reverse, all_equal}`                                                       | Covers best/worst/typical without runaway memory                                        |
| Sort benchmark output                         | Markdown table written to `docs/insights/sort_performance.md` by `scripts/bench_sort.py`                                                     | Keeps repo deterministic; the script is **optional to run**, the doc is the deliverable |
| Sort benchmark RNG                            | Fixed `random.Random(seed=0)`                                                                                                                | Determinism (`.cursorrules` §6 Testing Determinism)                                     |


> All other free choices follow `docs/plan.md` §2 (e.g. hash issuer, clock injection, exit codes). This file does **not** override any decision locked there.

---

## 3. Affected Files (Minimal Footprint)

We aim to **edit existing modules** rather than introduce new layers. Only one new pure-logic module (`diff.py`) is justified because diff has no current home.


| File                                        | Change                                                                                                            |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `mini_git/diff.py` *(new)*                  | Pure LCS line diff; returns a list of `(kind, line)` records                                                      |
| `mini_git/repository.py`                    | Add `merge(branch_name)`; helper for "is ancestor?" reuses `graph.ancestors`; update `_children` for both parents |
| `mini_git/cli.py`                           | New handlers for `diff` and `merge`; read files for `diff`; format output                                         |
| `mini_git/errors.py`                        | No new exception types — reuse `CommandError` / `RepoError` with new messages                                     |
| `scripts/bench_sort.py` *(new)*             | Stdlib-only benchmark; writes `docs/insights/sort_performance.md`                                                 |
| `docs/insights/sort_performance.md` *(new)* | The actual measurement table + a short discussion                                                                 |
| `tests/test_diff.py` *(new)*                | Pure LCS cases                                                                                                    |
| `tests/test_repository.py`                  | Add a `MergeTests` class (two-parent linkage, ancestor / path interplay, error cases)                             |
| `tests/test_cli.py`                         | `DIFF` / `MERGE` end-to-end via the REPL                                                                          |
| `README.md`                                 | Append a “Bonus Commands” section once the features land                                                          |


> No new abstract base classes, no command-registry refactor (`.cursorrules` §3 — same pattern is used only once).

---

## 4. Diff (subject §5 item 1)

### 4.1 Algorithm

Classic LCS line diff:

1. Read both files as `list[str]` of lines, stripped of the trailing newline.
2. Build the LCS length DP table on the two line lists.
3. Walk the table from `(len(A), len(B))` back to `(0, 0)`:
  - Equal → emit a **common** record (push to front).
  - Else go to the larger neighbor: up → **deleted** from A, left → **added** in B.
4. Return records in source order.

Complexity: O(|A| · |B|) time and space. Acceptable for `subject.md` (small text files, no streaming requirement).

### 4.2 Module shape (`mini_git/diff.py`)

A **pure function** that takes two `list[str]` and returns a list of records:

- Public function: `diff_lines(a, b) -> list[DiffLine]`
- `DiffLine` is a small `@dataclass(frozen=True)` with `kind: Literal["common", "added", "deleted"]` and `text: str`. The literal type keeps switch logic readable in `cli.py`.
- No file I/O lives here; the CLI layer reads files (`.cursorrules` §4 SRP / trust boundary).

### 4.3 CLI shape (`mini_git/cli.py`)

`diff <file1> <file2>`:

1. Validate arg count → otherwise `Invalid args`.
2. Open each path with `open(path, encoding="utf-8")`. `FileNotFoundError` → `File not found: <path>`. `OSError` / `UnicodeDecodeError` → `Cannot read file: <path>`.
3. Split on `\n`, strip a trailing `\r`. Drop a final empty element if the file ends with `\n` (matches the visual line count users expect).
4. Call `diff_lines` and print each record (`+` , `-` ,   `` prefixes).
5. If both files are byte-identical (no `added`/`deleted` records), print `Files are identical`.

### 4.4 Output spec

```
mini-git> DIFF a.txt b.txt
  shared header
- removed line
+ added line
  shared footer
```

```
mini-git> DIFF a.txt a.txt
Files are identical
```

```
mini-git> DIFF a.txt missing.txt
File not found: missing.txt
```

---

## 5. Merge Simulation (subject §5 item 2)

### 5.1 Repository change

The existing commit graph already permits two parents (`Commit.parents: tuple[str, ...]`). Topological sort, `ancestors`, and `PATH` already iterate all parents, so **no algorithm change is needed** beyond:

- Add `Repository.merge(branch_name: str) -> Commit`:
  1. `_require_initialized()`.
  2. `branch_name` exists → otherwise `Unknown branch: <name>`.
  3. `branch_name != current branch` → otherwise `Cannot merge a branch with itself`.
  4. Both branches have a commit → otherwise `Cannot merge before first commit`.
  5. If `target_head ∈ ancestors(current_head)` → raise `RepoError("Already up to date")`.
  6. Otherwise issue a new hash, build a `Commit` with `parents = (current_head, target_head)`, default message `f"Merge branch {branch_name}"`, advance `_timestamp_counter`, append both `_children[parent]` lists, register in `_commits`, the inverted index, the human clock map, and update `_branches[current_branch]`.

> Reuses `graph.ancestors` for the "already up to date" check — no new traversal code.

### 5.2 CLI shape

`merge <branch_name>`:

- One arg → otherwise `Invalid args`.
- Call `repo.merge(name)`; print `Merged <branch_name> into <current_branch> as <hash>`.
- `RepoError` propagates and is printed on one line, just like other commands.

### 5.3 Output spec

```
mini-git> MERGE feature
Merged feature into main as 0000007
```

```
mini-git> MERGE main
Cannot merge a branch with itself
```

```
mini-git> MERGE feature
Already up to date
```

### 5.4 Knock-on effects (regressions to cover in tests)

- `LOG` topological order: merge commit must appear **after** both parents.
- `PATH`: merge commit links both branches; new shortest paths may exist — verify with a diamond fixture.
- `ANCESTORS`: ancestors of the merge commit include the union of both parents’ ancestors.
- `SEARCH`: default merge message contains the branch name; ensure the inverted index sees it (consequence of reusing the normal commit path).

---

## 6. Sort Performance Comparison (subject §5 item 3)

### 6.1 Methodology

- Inputs generated by `random.Random(0)`. For each `(pattern, size)` pair build a `list[int]` of length `size`.
- Patterns: `random`, `sorted` (ascending), `reverse` (descending), `all_equal`.
- Wrap `merge_sort` with a comparator that increments a counter every time `<` is evaluated, by passing a `key` that records each call (or by adding an opt-in `_compare_counter` parameter inside the benchmark only — not in `mini_git/sort.py`, to keep production code free of instrumentation).
- Wall clock: `time.perf_counter()` around a single sort per cell (good enough at the assignment scale; mention in the doc that runs vary).
- Report only relative trends; no need to compare with `sorted()` (which is forbidden) or to add other algorithms — subject §5 says "your sort implementation".

### 6.2 Deliverables

- `scripts/bench_sort.py` — stdlib-only; running it prints the table to stdout and overwrites `docs/insights/sort_performance.md`. Idempotent; no command-line flags in this phase (YAGNI).
- `docs/insights/sort_performance.md` — checked into the repo so reviewers can read the result without running anything. Contains:
  1. Method paragraph (what is measured, RNG seed, machine assumptions).
  2. Comparison-count table (deterministic).
  3. Wall-clock table (anecdotal).
  4. Short discussion: why merge sort stays O(N log N) on all four patterns; why the comparison count differs slightly between `sorted` and `reverse` despite the same asymptotic bound; what the constant factor implies about the choice over Bubble / Insertion sort at these sizes.

### 6.3 Why this is documentation, not a REPL command

A REPL command would couple measurement to the user-facing CLI for no benefit and would slow down `python -m mini_git`. Keeping it as `scripts/bench_sort.py` matches `.cursorrules` §3 ("split after evidence") and keeps the core grading scope unchanged.

---

## 7. Phased Plan

Each phase = **one logical change = one commit** (`.cursorrules` §6). Conventional Commits prefix.

### Phase B0 — Branch off & docs

- Create branch (e.g. `bonus`) from the latest core commit.
- Add this file as `docs/bonus_plan.md`.
- Commit: `docs: plan bonus tasks (diff, merge, sort perf)`

### Phase B1 — Diff core

- Add `mini_git/diff.py` (`diff_lines`, `DiffLine`).
- Add `tests/test_diff.py`: empty vs empty, identical, all-added, all-deleted, interleaved, trailing newline handling.
- Commit: `feat: add lcs line diff`

### Phase B2 — Diff CLI

- Add `diff` handler to `cli.py`; file I/O, error messages, `Files are identical`.
- Extend `tests/test_cli.py` with `DiffCliTests` using `tempfile.TemporaryDirectory` (`.cursorrules` §6 Testing Determinism).
- Commit: `feat: add diff command to repl`

### Phase B3 — Merge engine

- Add `Repository.merge`; update `_children` for both parents; reuse `graph.ancestors` for the up-to-date check.
- Extend `tests/test_repository.py` with `MergeTests`: two-parent commit, `_children` updated on both sides, ancestor includes target branch history, `Already up to date`, self-merge, unknown branch, merge before first commit.
- Commit: `feat: add merge command with two-parent commits`

### Phase B4 — Merge CLI

- Wire `merge` handler in `cli.py`; format success message.
- Extend `tests/test_cli.py` for `MergeCliTests` (success, error paths) and add a `LOG` regression that asserts the merge commit appears after both parents.
- Commit: `feat: expose merge command in repl`

### Phase B5 — Sort benchmark

- Add `scripts/bench_sort.py` and generate `docs/insights/sort_performance.md`.
- (Optional) `tests/test_bench_sort.py` smoke test that the script runs and writes the file; skip if it would inflate the test suite.
- Commit: `docs: measure merge sort performance by size and pattern`

### Phase B6 — README sync

- Append a "Bonus Commands" section to `README.md` (`diff`, `merge`) with one short example each, and a link to `docs/insights/sort_performance.md`.
- Commit: `docs: document bonus commands in readme`

---

## 8. Test Strategy

Same rules as `plan.md` §11:

- Runner: `python -m unittest discover -s tests -p 'test_*.py' -v` (`.cursorrules` §6 Stdlib Test Runner). No new third-party deps.
- Determinism: `FakeClock`, fixed RNG seed, `tempfile.TemporaryDirectory` for `diff` fixtures (`.cursorrules` §6).
- One-line **purpose comment** per test function.
- New checklist items (in addition to the existing core checklist):
  - `diff_lines` handles empty inputs, full insertion, full deletion, and identical files.
  - `diff` CLI strips trailing newlines and prints prefixes exactly.
  - `diff` CLI prints `File not found: <path>` for a missing path; `Cannot read file: <path>` for an unreadable file.
  - `Repository.merge` creates exactly one commit with two parents.
  - `_children` index is updated for **both** parents (regression for `PATH` through merge).
  - `LOG` after merge respects parents-before-merge.
  - `ANCESTORS <merge_hash>` includes both parents’ histories without duplicates.
  - `merge` raises on self-merge, unknown branch, and already-up-to-date.
  - `bench_sort.py` produces a non-empty markdown table for every `(pattern, size)` cell (smoke test only; do not assert exact timings).

---

## 9. Risks / Open Points


| Risk                                                                | Mitigation                                                                                                                |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `diff` LCS DP at large file sizes blows memory                      | Subject scope is "text files" at assignment scale; document the O(N·M) bound in the docstring; do not chunk in this phase |
| Encoding edge cases for `diff`                                      | Lock UTF-8; surface decode failures as `Cannot read file: <path>`                                                         |
| Merge regressions on `PATH` lex tie                                 | Add a diamond fixture (`A → B`, `A → C`, merge `M`) and assert the lex-min path through it                                |
| `Already up to date` semantics interpreted differently by reviewers | Document in `bonus_plan.md` §2 and in `README.md` so the choice is visible                                                |
| Comparison counting bleeds into production sort code                | Keep counter inside `scripts/bench_sort.py` only; do **not** mutate `mini_git/sort.py`                                    |
| Wall-clock noise misleads readers                                   | Doc explicitly says the comparison-count table is the source of truth; runtime is illustrative                            |


---

## 10. Definition of Done

- `DIFF <file1> <file2>` prints `+`  / `-`  /   `` lines for the LCS-aligned diff and `Files are identical` when applicable; missing or unreadable paths print the documented error messages.
- `MERGE <branch_name>` creates a single new commit with **two** parents `(current_head, target_head)`, updates `_children` on both, and refuses self-merge / unknown branch / already-up-to-date / pre-first-commit cases with one-line messages.
- All existing core tests still pass; new `tests/test_diff.py`, merge tests in `tests/test_repository.py`, and CLI tests in `tests/test_cli.py` pass under the standard `unittest` runner with no extra packages.
- `docs/insights/sort_performance.md` exists in the repo and contains the comparison-count table for the locked `(pattern, size)` matrix plus a short discussion.
- `scripts/bench_sort.py` runs to completion with stdlib only and rewrites the markdown file deterministically given the locked seed.
- `README.md` documents the two new commands and links to the performance doc.
- No change to the nine core commands' inputs, outputs, or error messages.

