# Mini Git Mission

---

## 1. Mission Overview

A single Git commit holds a **graph data structure** and **hashing**. Understanding that changes how you see rebase, merge, and cherry-pick, and it connects to algorithm study. By implementing Mini Git yourself, you verify that structure hands-on.

Git is a **distributed version control system** used by developers worldwide. It supports parallel work with branches, tracks change history, and at its core are **graphs** and **search algorithms**.

In this mission, you complete a **CLI-based Mini Git** by implementing Git’s core structure yourself: commit structure, branch management, commit search, sorting, and more—so you internalize how real Git works. This experience is a foundation for broader algorithm learning and helps with coding test preparation.

---

## 2. Final Deliverable

Complete **one CLI-based Mini Git program** with the following working correctly.

### 2.1 Repository and Branch Management


| Area                | Input / Request                                                                        | Output / Display                                                                  |
| ------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Repository · Branch | `INIT <user_name>`, `BRANCH <branch_name>`, `SWITCH <branch_name>`, `COMMIT <message>` | Repository init, branch create/switch, commit creation (**commit hash** included) |


### 2.2 Commit Log and Traversal


| Area       | Input / Request                                              | Output / Display                                                |
| ---------- | ------------------------------------------------------------ | --------------------------------------------------------------- |
| Log · Path | `LOG`, `PATH <commit1> <commit2>`, `ANCESTORS <commit_hash>` | Commit list, shortest path (**No path** if none), ancestor list |


### 2.3 Search and Sort


| Area          | Input / Request                                                           | Output / Display                          |
| ------------- | ------------------------------------------------------------------------- | ----------------------------------------- |
| Search · Sort | `SEARCH <keyword>`, `SEARCH --author=<name>`, `LOG --sort-by=date|author` | Matching commits, log ordered by sort key |


### 2.4 CLI Interface (REPL)


| Area | Input / Request                | Output / Display                             |
| ---- | ------------------------------ | -------------------------------------------- |
| REPL | Commands at `mini-git>` prompt | Parse → run → print; exit with `exit`/`quit` |


### 2.5 Required Submission and Run


| Item              | Content                                            |
| ----------------- | -------------------------------------------------- |
| **Submit**        | One entry point (e.g. `main.py`) + one `README.md` |
| **Run (example)** | `python main.py`                                   |


---

## 3. Learning Objectives

After finishing this assignment, learners should be able to explain on their own:

1. How to implement a commit graph and why Git’s commit structure is a **DAG**.
2. What approach is needed for log output where **parents appear before children** (e.g. topological-order-style output).
3. How to find the **shortest path** between two commits and **traverse all ancestors** of a given commit.
4. How to implement a **sorting algorithm** yourself and explain average/worst time complexity and whether it is **stable**.
5. How an **inverted index** works and why it is faster than full traversal, in terms of time complexity.

---

## 4. Functional Requirements

All of the following must be satisfied.

### 4.1 CLI Common Rules (Syntax Standard)


| Item            | Requirement                                                                                                                         |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Case**        | Commands are **case-insensitive** (e.g. `INIT`, `init` both allowed)                                                                |
| **String args** | User names, commit messages, search keywords may **contain spaces**. Use **quotes** when needed (e.g. `COMMIT "Add login feature"`) |
| **Options**     | `SEARCH --author=<name>`, `LOG --sort-by=date|author`                                                                               |
| **Errors**      | At minimum, standardized messages such as: `Invalid args`, `Unknown branch: <name>`, `Unknown commit: <hash>`                       |


### 4.2 Commit Graph (Core Data Structure)


| Item                | Requirement                                                                                 |
| ------------------- | ------------------------------------------------------------------------------------------- |
| **Commit node**     | At minimum: `hash`, `message`, `author`, `timestamp`, `parents`                             |
| **Parents**         | Each commit has **zero or more** parents                                                    |
| **Graph**           | **DAG** (directed acyclic)                                                                  |
| **Repository**      | Fast lookup by commit `hash` (e.g. hash map)                                                |
| **Hash uniqueness** | **Unique within a session**. Implementation free (counter, random, etc.); **no duplicates** |


### 4.3 Inverted Index


| Item                   | Requirement                                                                |
| ---------------------- | -------------------------------------------------------------------------- |
| **Goal**               | Quickly narrow candidates without scanning every commit on search          |
| **Keyword extraction** | **Split** commit message on whitespace → normalize tokens to **lowercase** |
| **Two indexes**        | `keyword → commit_hash` list, `author → commit_hash` list                  |


### 4.4 Sorting Algorithm (Direct Implementation)


| Item           | Requirement                                     |
| -------------- | ----------------------------------------------- |
| **Forbidden**  | Do **not** use `sorted()` or `list.sort()`      |
| **Comparison** | Sort keys may change (by date, by author, etc.) |


### 4.5 Command Requirements


| Command                       | Requirement                                                                                                                                                                                            |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **INIT user_name**            | Initialize repository, set `main` branch, HEAD, current user (author)                                                                                                                                  |
| **BRANCH branch_name**        | New branch pointing at current commit (HEAD)                                                                                                                                                           |
| **SWITCH branch_name**        | Move HEAD to named branch                                                                                                                                                                              |
| **COMMIT message**            | New commit with current HEAD as parent; update inverted index (author/keyword)                                                                                                                         |
| **LOG**                       | Not “newest first”: output so **parents appear before children** (topological flavor). Lines must identify hash, author, timestamp, message                                                            |
| **LOG --sort-by=date|author** | `date`: by timestamp. `author`: by author name. Tie-break rules are free                                                                                                                               |
| **PATH commit1 commit2**      | **Shortest path** (minimum edge count) treating commit–parent links as **undirected edges**. If none: **No path**. If multiple: choose path whose hash concatenation is **lexicographically smallest** |
| **ANCESTORS commit_hash**     | Output **all reachable ancestors** without omission                                                                                                                                                    |
| **SEARCH keyword**            | Commits whose message contains keyword → via inverted index                                                                                                                                            |
| **SEARCH --author=name**      | Commits by that author → via inverted index                                                                                                                                                            |


---

## 5. Bonus Tasks (Optional)


| Item                            | Content                                                                                                                                   |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Diff**                        | `diff <file1> <file2>`: **line-by-line** compare of two text files; mark added, deleted, common lines                                     |
| **Merge simulation**            | `merge <branch_name>`: merge commit with **two** parents (current HEAD + target branch HEAD)                                              |
| **Sort performance comparison** | For your sort implementation, briefly measure and document **runtime or comparison counts** by input size/pattern (detail level optional) |


