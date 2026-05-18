# Mini Git Study Guide

Theory you need to complete the assignment (`subject.md`): data structures, algorithms, and Git structure, organized by topic. See `plan.md` for implementation details.

---

## Table of Contents

1. [Understanding the Mission — What Git and Mini Git Do](#1-understanding-the-mission--what-git-and-mini-git-do)
2. [Version Control and Commit Basics](#2-version-control-and-commit-basics)
3. [Commit Graph and DAG](#3-commit-graph-and-dag)
4. [Branches and HEAD](#4-branches-and-head)
5. [Hash and Commit Identity](#5-hash-and-commit-identity)
6. [Storing Commits with a Hash Map (dict)](#6-storing-commits-with-a-hash-map-dict)
7. [CLI and REPL](#7-cli-and-repl)
8. [Command Parsing (Tokenizer)](#8-command-parsing-tokenizer)
9. [Basic Repository Commands — INIT / BRANCH / SWITCH / COMMIT](#9-basic-repository-commands--init--branch--switch--commit)
10. [Topological Sort and LOG Output](#10-topological-sort-and-log-output)
11. [Graph Traversal — BFS and Shortest Path (PATH)](#11-graph-traversal--bfs-and-shortest-path-path)
12. [Ancestor Traversal (ANCESTORS)](#12-ancestor-traversal-ancestors)
13. [Inverted Index and SEARCH](#13-inverted-index-and-search)
14. [Implementing Sorting Algorithms Yourself](#14-implementing-sorting-algorithms-yourself)
15. [Time Complexity and Stable Sort](#15-time-complexity-and-stable-sort)
16. [Python Basics — dataclass, Type Hints, Exceptions](#16-python-basics--dataclass-type-hints-exceptions)
17. [Module Structure and Testing](#17-module-structure-and-testing)
18. [Bonus Task Topics](#18-bonus-task-topics)
19. [Recommended Study Order](#19-recommended-study-order)
20. [Assignment Checklist and Topic Mapping](#20-assignment-checklist-and-topic-mapping)

---

## 1. Understanding the Mission — What Git and Mini Git Do

### Why study this?

Real Git is huge: file contents, metadata, networking, and more. This assignment isolates **commit graph + traversal + search + sort** as Mini Git. “Using Git” and “Git inside is a graph” are different levels of understanding.

### Core concepts

| Concept | Description |
| --- | --- |
| **Version control (VCS)** | System that stores and compares change history for files/projects |
| **Distributed (DVCS)** | Each machine holds a full (or large) copy of history; Git is DVCS |
| **Mini Git** | Learning program that simulates commit/branch/graph traversal in memory |
| **Assignment link** | `COMMIT` adds nodes; `LOG`/`PATH`/`ANCESTORS` operate on the graph |

### Questions to answer yourself

- How is a commit graph different from copying folders as `v1`, `v2`?
- Why are merge, rebase, and cherry-pick called “graph operations”?

---

## 2. Version Control and Commit Basics

### Why study this?

Each **Commit** in Mini Git is one **node** in the graph. To know what goes in a node (subject §4.2), understand that a commit is “snapshot metadata + links.”

### Core concepts

| Concept | Description | In Mini Git |
| --- | --- | --- |
| **Commit** | Bundle of changes at a point in time + message | `hash`, `message`, `author`, `timestamp`, `parents` |
| **Repository** | Space holding commits and branches | In-memory `dict` + branch map |
| **Working directory** | Where real files live | **Out of scope** (file diff is bonus) |
| **Staging** | Choosing what goes into the next commit | **Out of scope** |
| **author** | User who made the commit | Set at `INIT`, recorded on each `COMMIT` |

### Why this commit is not a “snapshot” (for this assignment)

Real Git commits point to trees and blobs (file contents). Mini Git stores only **message, author, time, and parent links**. Still enough to practice history graphs and search algorithms.

### Questions to answer yourself

- Why is the commit message a target for search and sort?
- What does it mean in the graph when there is no parent (root commit)?

---

## 3. Commit Graph and DAG

### Why study this?

Learning objective 1: explain **why Git’s commit structure is a DAG**. `LOG`, `PATH`, and `ANCESTORS` are all operations on this graph.

### Graph terminology

| Term | Meaning | In Git commit graph |
| --- | --- | --- |
| **Vertex** | Node | One commit |
| **Edge** | Connection | Child → parent (or parent → child if you stay consistent) |
| **Directed graph** | Edges have direction | “This commit came from that one” |
| **DAG** | Directed Acyclic Graph | A commit cannot be its own ancestor |
| **Root** | Vertex with no incoming parent edge | First commit (`parents` empty) |
| **Merge commit** | Two or more parents | Where two branch histories join (bonus `merge`) |

### Why there must be no cycles

If A’s parent is B and B’s parent is A, time order and ancestor relations break. Topological sort fails.

### Linear vs branch vs merge (pictures)

**Linear (one parent each)**

```
C1 ← C2 ← C3
```

**Branch**

```
       C2 ← C4
      /
C1 ←
      \
       C3
```

**Merge (two parents)**

```
       C2 ← C4
      /       \
C1 ←           ← M (parents: C4, C3)
      \       /
       C3 ←
```

### Mini Git connection

- Each `Commit` has `parents: list[str]` (parent hashes).
- `COMMIT` adds a new node with current HEAD as parent → one edge (or two on merge).
- `LOG` lists the DAG in a readable order.

### Questions to answer yourself

- How is a DAG different from a tree? (Can a node have multiple parents?)
- What does rebase do to edges in the graph?

---

## 4. Branches and HEAD

### Why study this?

“Where am I working?” in Git is **HEAD** and **branch names**. `BRANCH`, `SWITCH`, and `COMMIT` all move these pointers.

### Core concepts

| Concept | Description |
| --- | --- |
| **Branch** | Movable label pointing at a commit (`main`, `feature`, …) |
| **HEAD** | Pointer to the current branch (Mini Git stores only the branch name) |
| **Branching** | Different child commits from the same parent |
| **fast-forward** | Branch simply moves forward on a line (near-linear history) |

### Flow (theory)

1. `INIT` → create `main`, HEAD = `main`, no commits yet.
2. `COMMIT` → new commit with previous HEAD commit as parent (or root); branch moves to new commit.
3. `BRANCH feature` → label **current** HEAD commit as `feature`.
4. `SWITCH feature` → HEAD = `feature`; next `COMMIT` extends `feature`.

### Questions to answer yourself

- Does creating a branch add a new graph node, or only a name?
- If you only `SWITCH` without `COMMIT`, does the graph change?

---

## 5. Hash and Commit Identity

### Why study this?

Commits are found, compared, and printed by `hash`. Real Git uses content-based SHA-1/SHA-256; Mini Git only needs a **session-unique ID**.

### Core concepts

| Concept | Description |
| --- | --- |
| **Hash** | Map data to a fixed-length (or short) identifier |
| **Content-based hash** | Hash changes when commit content changes (real Git) |
| **Synthetic ID** | Counter, UUID, etc. — unique in this session only (allowed in Mini Git) |
| **Uniqueness** | Same hash for two commits is forbidden — needed for `dict` keys |

### Real Git vs Mini Git

| | Real Git | Mini Git (assignment) |
| --- | --- | --- |
| Hash | Hash of commit object | Counter, random, etc. **free** |
| Purpose | Integrity, global ID | Graph node ID, `PATH` output |
| Collision | Extremely rare in theory | Only **no duplicates in session** required |

### Questions to answer yourself

- Would integers “commit 1, commit 2” satisfy the assignment?
- Why does `PATH` need lexicographic comparison of hash strings for ties?

---

## 6. Storing Commits with a Hash Map (dict)

### Why study this?

`PATH`, `ANCESTORS`, `SEARCH` repeatedly need “find commit by hash.” A **hash map** gives average O(1) lookup as the base for graph algorithms.

### Hash map structure

| Item | Content |
| --- | --- |
| **Structure** | Key → value. In Python: `dict[str, Commit]` |
| **Average time** | Lookup/insert/delete O(1) |
| **Worst time** | O(n) with many collisions (negligible at assignment scale) |
| **Assignment** | `hash` → `Commit`; traverse via `commit.parents` |

### Two ways to represent the graph

| Style | What you store | Advantage |
| --- | --- | --- |
| **Parent pointers only** | Each node has `parents` | Same as Git, simple storage |
| **Plus children index** | `parent → [children]` map | Easier bidirectional traversal (`PATH` undirected BFS) |

Mini Git naturally keeps a **children list** for `PATH` (plan.md §7.3).

### Questions to answer yourself

- How slow is `ANCESTORS` without hash lookup if you only have a list?
- For N nodes and E edges, cost of one dict lookup?

---

## 7. CLI and REPL

### Why study this?

The deliverable is a **REPL** program. The theory is light, but you need the pipeline: command → parse → repository → print.

### Core concepts

| Concept | Description |
| --- | --- |
| **CLI** | Control the program with text commands in a terminal |
| **REPL** | Read–Eval–Print Loop: read input → run → print result, repeat |
| **Prompt** | `mini-git>` — waits for user input |

### Pipeline

```
input string → tokenizer → command + args → Repository method → stdout format
```

For theory, the **Eval** step is the graph/sort/search algorithms.

---

## 8. Command Parsing (Tokenizer)

### Why study this?

`COMMIT "Add login feature"` must pass the whole message as one argument; plain `split()` is not enough.

### Core rules (subject §4.1)

| Rule | Example |
| --- | --- |
| Commands case-insensitive | `init` = `INIT` |
| Quoted token = one argument | `COMMIT "fix bug"` → `["COMMIT", "fix bug"]` |
| Option form | `SEARCH --author=alice`, `LOG --sort-by=date` |

### Theory: tokenization

Splitting input into **tokens** is preprocessing. Compilers, shells, and CLIs share this problem.

---

## 9. Basic Repository Commands — INIT / BRANCH / SWITCH / COMMIT

### Why study this?

These four commands are the **only way to build the graph**. Later algorithms only read it.

### Graph effect per command

| Command | Graph / state change |
| --- | --- |
| `INIT` | Empty repo, only `main`, zero commits |
| `COMMIT` | One new node + HEAD branch points to it + parent edge |
| `BRANCH` | New name → **current** commit hash (no node copy) |
| `SWITCH` | HEAD moves to another branch |

### Practice scenario

```
INIT alice
COMMIT "A"
COMMIT "B"
BRANCH feature
SWITCH feature
COMMIT "C"
```

Graph: `A ← B`, `B ← C`; `main` at B, `feature` at C.

---

## 10. Topological Sort and LOG Output

### Why study this?

Learning objective 2: log where **parents appear before children**. That is **topological sort**, not “newest first.”

### What is topological sort?

List all vertices of a DAG so that for every edge u→v, **u comes before v**.

- Here, edge direction: **parent → child** (parent printed first).
- Order may not be unique → need **tie-break rules** (timestamp, hash, …).

### Kahn's algorithm (conceptual steps)

1. Count **in-degree** (incoming edges). (Parent→child: count parents.)
2. Put in-degree 0 nodes (roots) in a queue.
3. Dequeue one, print it, decrement children's in-degree.
4. Enqueue children that reach in-degree 0.
5. Repeat until the queue is empty.

### `LOG` vs `LOG --sort-by=date`

| Command | Meaning |
| --- | --- |
| `LOG` | Topological (parents first). **Not** reverse chronological |
| `LOG --sort-by=date` | Sort by `timestamp` (no topological constraint) |
| `LOG --sort-by=author` | Sort by author name |

### Questions to answer yourself

- What graph shape makes topological sort impossible? (Hint: cycle)
- Is there always exactly one topological order?

---

## 11. Graph Traversal — BFS and Shortest Path (PATH)

### Why study this?

Part of learning objective 3: **shortest path** between two commits. `PATH` is shortest path on an **undirected** view of the graph.

### BFS (breadth-first search)

| Item | Content |
| --- | --- |
| **Structure** | Queue |
| **Visits** | `visited` set avoids revisiting |
| **Property** | On **unweighted** graphs, finds **minimum number of edges** from start |
| **Time** | O(V + E), V = commits, E = parent/child links |

### `PATH` graph model

- Treat each commit–parent link as **bidirectional**.
- Example: `A—B—C` → two edges from A to C.
- Multiple shortest paths → pick **lexicographically smallest** `hash1->hash2->...` string.

### BFS vs DFS

| | BFS | DFS |
| --- | --- | --- |
| Structure | Queue | Stack (or recursion) |
| Shortest path (unweighted, undirected) | **Good** | **Bad** (first path found may not be shortest) |
| Collect all ancestors | OK | OK (also used for `ANCESTORS`) |

### Questions to answer yourself

- Why can parent-only traversal miss the shortest route to a “sibling” commit?
- What if two commits are in disconnected components?

---

## 12. Ancestor Traversal (ANCESTORS)

### Why study this?

Learning objective 3: find **all ancestors** of a commit without omission.

### Definition

- **Ancestor:** Any commit reachable by following **parents** upward.
- **Do not include** the start commit itself (subject §4.5).

### Algorithm

1. Start from given hash.
2. Follow `parents` with BFS or DFS.
3. Skip hashes already in `visited` (merge graphs can reach the same ancestor twice).
4. Output collected hashes in topological order or hash order.

### Caution in merge graphs

```
    B
   / \
  A   C
   \ /
    D  (D's parents: B, C)
```

`ANCESTORS D` → A, B, C (not D). B and C may both have parent A.

### Questions to answer yourself

- Is the ancestor **set** the same for DFS and BFS?
- Why does the assignment fix **output order**? (Deterministic tests)

---

## 13. Inverted Index and SEARCH

### Why study this?

Learning objective 5: **inverted index** vs linear scan. A miniature of search engines and DB indexes.

### Forward index vs inverted index

| Approach | Structure | On search |
| --- | --- | --- |
| **Linear scan** | Commit list only | Read every message O(N) |
| **Inverted index** | `keyword → [commit_hash, ...]` | dict lookup O(1) + check candidates |

### Two Mini Git indexes (subject §4.3)

| Index | Key | Value |
| --- | --- | --- |
| Keyword | **Token** from message (split + `lower`) | List of commit hashes |
| Author | `author` string (case-sensitive) | That author's commit hashes |

### Tokenization rules

- `"Add Login Feature"` → `["add", "login", "feature"]`
- Search `login` → **exact token** match (not substring `"log"`)
- Update index on `COMMIT`; **reset** index on `INIT`

### Time complexity (intuition)

| Operation | Linear scan | Inverted index |
| --- | --- | --- |
| Add one commit | O(1) | O(token count) index update |
| Keyword search | O(N × avg tokens) | O(1) lookup + O(result size) |

Inverted index wins more as N grows.

### Questions to answer yourself

- Why is author not passed through `lower()`?
- If the message is `"login login"`, should the index list the hash twice?

---

## 14. Implementing Sorting Algorithms Yourself

### Why study this?

Learning objective 4: **implement yourself** + complexity + **stable sort**. `sorted()` and `list.sort()` are forbidden.

### Comparison sorts (common idea)

- Compare two elements to order them.
- `LOG --sort-by=date` → compare `timestamp`.
- `LOG --sort-by=author` → compare `author`, then **multi-key** ties with `timestamp`, etc.

### Algorithm comparison (theory)

| Algorithm | Average | Worst | Extra memory | Stable |
| --- | --- | --- | --- | --- |
| **Bubble Sort** | O(n²) | O(n²) | O(1) | Yes |
| **Insertion Sort** | O(n²) | O(n²) | O(1) | Yes |
| **Merge Sort** | O(n log n) | O(n log n) | O(n) | **Yes** |
| **Quick Sort** | O(n log n) | O(n²) | O(log n) | No (usually) |
| **Heap Sort** | O(n log n) | O(n log n) | O(1) | No |

### Merge sort (concept)

1. Split list in half, sort recursively.
2. **Merge** two sorted halves by comparing ends.
3. **Stable:** on tie, take from the **left** (earlier) side first.

### Why Merge Sort for this assignment (plan.md)

- Average and worst O(n log n).
- **Stable** → predictable output with tie keys `timestamp`/`hash`.

### Questions to answer yourself

- Why does stable sort matter for two commits with the same key?
- What assignment requirement conflicts with Quick Sort?

---

## 15. Time Complexity and Stable Sort

### Why study this?

You should explain choices in **Big-O** for interviews, tests, and assignment evaluation.

### Big-O cheat sheet (this assignment)

| Operation | Complexity | Notes |
| --- | --- | --- |
| Lookup commit by hash | O(1) avg | dict |
| One `COMMIT` | O(1) + O(tokens) index | |
| `LOG` topological | O(V + E) | Kahn |
| `PATH` BFS | O(V + E) | undirected neighbors |
| `ANCESTORS` | O(V + E) | parent direction only |
| `SEARCH` (inverted index) | O(1) + O(results) | scan is O(N) |
| `merge_sort` n items | O(n log n) | |

### Stable sort definition

Elements with **equal keys keep their input order** in the output.

Example: for equal `author`, the commit that appeared first in input should stay first — matches tests and expectations.

---

## 16. Python Basics — dataclass, Type Hints, Exceptions

### Why study this?

Supports **immutable commit nodes**, clear function contracts, and **standard error messages**. Bridge from theory to code.

### Essentials

| Topic | Role in assignment |
| --- | --- |
| `@dataclass(frozen=True)` | Immutable commit (DAG node) |
| Type hints e.g. `def path(a: str, b: str) -> list[str] \| None` | Document signatures |
| `RepoError` etc. | CLI prints `Unknown commit: ...` |

---

## 17. Module Structure and Testing

### Why study this?

**Pure functions** for graph/sort/index let you unit test without a full repository.

### Separation (theory)

| Layer | Responsibility | Example |
| --- | --- | --- |
| `graph.py` | Topological sort, BFS, ancestor set | Input: hash, parent lookup fn |
| `sort.py` | merge_sort | Input: list, key fn |
| `inverted_index.py` | Tokenize, index | |
| `repository.py` | Command semantics, state | |
| `cli.py` | I/O only | |

**Pure logic vs I/O** makes algorithms easier to learn and test.

---

## 18. Bonus Task Topics

| Bonus | Theory |
| --- | --- |
| **Diff** | LCS, line-by-line text diff |
| **Merge simulation** | Two-parent node → in-degree 2 in DAG; regression on `ANCESTORS`/`PATH` |
| **Sort performance** | Comparison counts vs input size/pattern (sorted, reverse, random); measure Big-O |

---

## 19. Recommended Study Order

```
Step 1 (Git structure)  → §2 version control, §3 DAG, §4 branch/HEAD, §5 hash
Step 2 (data structures)→ §6 hash map, §13 inverted index
Step 3 (algorithms)     → §10 topological sort, §11 BFS, §12 ancestors, §14–§15 sort & complexity
Step 4 (integration)    → §9 build graph with commands, §7–§8 CLI
Step 5 (implementation) → §16–§17 Python & tests, implement per plan.md
Step 6 (optional)       → §18 bonus
```

**Tip:** Draw the DAG on paper from §3, then hand-compute `LOG`/`PATH`/`ANCESTORS` before coding.

---

## 20. Assignment Checklist and Topic Mapping

| Learning objective (subject §3) | Study sections |
| --- | --- |
| 1. Commit graph · explain DAG | §3, §6, §9 |
| 2. Parent-first LOG · topological sort | §10 |
| 3. Shortest path · all ancestors | §11, §12 |
| 4. Implement sort · complexity · stable sort | §14, §15 |
| 5. Inverted index · speed vs scan | §13, §15 |

| Feature (subject §4) | Study sections |
| --- | --- |
| Commit graph §4.2 | §2–§6, §9 |
| Inverted index §4.3 | §13 |
| Sort §4.4 | §14, §15 |
| LOG / PATH / ANCESTORS / SEARCH §4.5 | §10–§13 |
| CLI §4.1, §2.4 | §7, §8 |

---

## Further Reading (Optional)

- **Graphs:** topological sort, BFS/DFS (coding interview books, ch. 1–2)
- **Git:** Pro Git “Git Internals” / `git log --graph`
- **Search:** inverted index, full-text search overview
- **Sort:** Merge sort stability proof, Master Theorem (divide-and-conquer sorts)
