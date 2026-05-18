# Mini Git Learning Keywords

A topic-indexed list of **core terms, commands, and algorithms** covered in `study_guide.md`. For explanations, see the matching section in `study_guide.md`.

---

## Table of Contents

1. [Mission · Git Overview](#1-mission--git-overview)
2. [Version Control · Commits](#2-version-control--commits)
3. [Commit Graph · DAG](#3-commit-graph--dag)
4. [Branches · HEAD](#4-branches--head)
5. [Hash · Commit Identity](#5-hash--commit-identity)
6. [Hash Map (dict)](#6-hash-map-dict)
7. [CLI · REPL](#7-cli--repl)
8. [Command Parsing](#8-command-parsing)
9. [Basic Repository Commands](#9-basic-repository-commands)
10. [Topological Sort · LOG](#10-topological-sort--log)
11. [Graph Traversal · PATH](#11-graph-traversal--path)
12. [Ancestor Traversal](#12-ancestor-traversal)
13. [Inverted Index · SEARCH](#13-inverted-index--search)
14. [Sorting Algorithms](#14-sorting-algorithms)
15. [Time Complexity · Stable Sort](#15-time-complexity--stable-sort)
16. [Python Basics](#16-python-basics)
17. [Module Structure · Testing](#17-module-structure--testing)
18. [Bonus Tasks](#18-bonus-tasks)

---

## 1. Mission · Git Overview

| Keywords |
| --- |
| Version control (VCS) |
| Distributed (DVCS) |
| Mini Git |
| Commit graph |
| merge, rebase, cherry-pick |

---

## 2. Version Control · Commits

| Keywords |
| --- |
| Commit |
| Repository |
| Working directory |
| Staging |
| Snapshot |
| author |
| hash, message, timestamp, parents |
| Parent commit |
| Root commit |

---

## 3. Commit Graph · DAG

| Keywords |
| --- |
| Vertex |
| Edge |
| Directed graph |
| DAG (Directed Acyclic Graph) |
| Acyclic graph |
| Root |
| Merge commit |
| Linear history |
| Branching |
| Merge |
| rebase |

---

## 4. Branches · HEAD

| Keywords |
| --- |
| Branch |
| HEAD |
| Branching (fork) |
| fast-forward |
| main, feature |

---

## 5. Hash · Commit Identity

| Keywords |
| --- |
| Hash |
| Content-based hash |
| Synthetic ID |
| Uniqueness |
| SHA-1, SHA-256 |
| Lexicographically smallest |

---

## 6. Hash Map (dict)

| Keywords |
| --- |
| Hash map |
| dict |
| Parent pointer |
| Children index |
| O(1), O(n) |

---

## 7. CLI · REPL

| Keywords |
| --- |
| CLI |
| REPL (Read–Eval–Print Loop) |
| Prompt (`mini-git>`) |
| Tokenizer |
| Read, Eval, Print |

---

## 8. Command Parsing

| Keywords |
| --- |
| Tokenization |
| Token |
| Quoted arguments |
| Options (`--author=`, `--sort-by=`) |
| Case-insensitive |

---

## 9. Basic Repository Commands

| Command | Related keywords |
| --- | --- |
| `INIT` | Empty repository, set author |
| `COMMIT` | New node, parent edge, update HEAD |
| `BRANCH` | Branch name → current commit hash |
| `SWITCH` | Move HEAD |

---

## 10. Topological Sort · LOG

| Keywords |
| --- |
| Topological sort |
| Kahn's algorithm |
| In-degree |
| Queue |
| Parents before children in output |
| `LOG` |
| `LOG --sort-by=date` |
| `LOG --sort-by=author` |
| timestamp, hash (tie-break rules) |

---

## 11. Graph Traversal · PATH

| Keywords |
| --- |
| BFS (breadth-first search) |
| DFS (depth-first search) |
| Queue |
| Stack |
| visited |
| Shortest path |
| Undirected graph |
| Bidirectional edges |
| `PATH` |
| Lexicographically smallest path |
| O(V + E) |

---

## 12. Ancestor Traversal

| Keywords |
| --- |
| Ancestor |
| Parent-direction traversal |
| `ANCESTORS` |
| visited (dedupe shared ancestors) |
| Merge graph |
| in-degree 2 |

---

## 13. Inverted Index · SEARCH

| Keywords |
| --- |
| Inverted index |
| Forward index / linear scan |
| Keyword index |
| Author index |
| Token |
| `lower()` |
| Exact match |
| `SEARCH` |
| `SEARCH --author=` |
| Index update / reset |

---

## 14. Sorting Algorithms

| Keywords |
| --- |
| Comparison-based sort |
| Bubble Sort |
| Insertion Sort |
| Merge Sort |
| Quick Sort |
| Heap Sort |
| Stable sort |
| Multi-key sort |
| `sorted()`, `list.sort()` forbidden |
| merge_sort |

---

## 15. Time Complexity · Stable Sort

| Keywords |
| --- |
| Big-O |
| O(1), O(n), O(n log n), O(n²) |
| O(V + E) |
| Stable sort definition |
| Average / worst time |
| Extra memory |

---

## 16. Python Basics

| Keywords |
| --- |
| `@dataclass` |
| `frozen=True` |
| Type hints |
| `RepoError` |
| Exception handling |

---

## 17. Module Structure · Testing

| Keywords |
| --- |
| `graph.py` |
| `sort.py` |
| `inverted_index.py` |
| `repository.py` |
| `cli.py` |
| Pure functions |
| Pure logic vs I/O separation |
| Unit tests |

---

## 18. Bonus Tasks

| Keywords |
| --- |
| Diff |
| LCS (longest common subsequence) |
| Merge simulation |
| Two-parent node |
| Sort performance measurement |
| Master Theorem |

---

## Mini Git Commands (Full List)

```
INIT
COMMIT
BRANCH
SWITCH
LOG
LOG --sort-by=date
LOG --sort-by=author
PATH
ANCESTORS
SEARCH
SEARCH --author=
```

---

## Algorithms · Data Structures (At a Glance)

| Category | Keywords |
| --- | --- |
| Graph | DAG, topological sort, Kahn, BFS, DFS, ancestor traversal |
| Data structures | dict (hash map), queue, stack, visited set, inverted index |
| Sort | Merge Sort (recommended), stable sort |
| Complexity | Big-O, O(1), O(V+E), O(n log n) |

---

## Learning Objectives ↔ Keywords

| Learning objective | Core keywords |
| --- | --- |
| 1. Explain DAG | DAG, vertex, edge, merge commit, parent pointer |
| 2. LOG · topological sort | Topological sort, Kahn, parents first |
| 3. PATH · ANCESTORS | BFS, shortest path, ancestor, visited |
| 4. Implement sort yourself | Merge Sort, stable sort, Big-O |
| 5. Inverted index | Inverted index, token, dict lookup, vs linear scan |
