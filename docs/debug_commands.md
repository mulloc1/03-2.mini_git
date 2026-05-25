# Mini Git 디버깅 명령어 셋

[subject.md](subject.md) 기능을 **REPL·테스트·브레이크포인트**로 따라가며 전체 구조를 파악하기 위한 가이드입니다.  
코어 실행 흐름은 `main.py` → `mini_git.main` → `Repository` + `cli.run_repl` → `dispatch` → `_HANDLERS` → `repository.*` → `graph` / `sort` / `inverted_index` 순입니다.

---

## 1. 실행 전 준비

프로젝트 루트로 이동합니다.

```bash
cd /Users/baejaemin/Project/codyssey/03-2.mini_git
```

| 방식                 | 명령                                                           |
| -------------------- | -------------------------------------------------------------- |
| REPL (대화형)        | `python3 main.py` 또는 `python3 -m mini_git`                   |
| REPL (스크립트 입력) | 아래 §3의 `printf` / heredoc 파이프                            |
| 전체 테스트          | `python3 -m unittest discover -s tests -p 'test_*.py' -v`      |
| 모듈별 테스트        | `python3 -m unittest tests.test_graph -v` (파일명만 바꿔 실행) |

**VS Code / Cursor 디버그** (`03-2.mini_git` 기준 `cwd`):

| 구성 이름 (제안)          | module / program                               | 용도                              |
| ------------------------- | ---------------------------------------------- | --------------------------------- |
| mini_git: REPL            | `module`: `mini_git`, `cwd`: `03-2.mini_git`   | `run_repl` · `dispatch` 단계 추적 |
| mini_git: unittest all    | `unittest discover -s tests -p 'test_*.py' -v` | 회귀 전체                         |
| mini_git: test_cli        | `tests.test_cli`                               | REPL·토크나이저·출력              |
| mini_git: test_repository | `tests.test_repository`                        | 저장소 엔진                       |
| mini_git: test_graph      | `tests.test_graph`                             | 토폴로지·PATH·ANCESTORS           |

`launch.json` 예시 스니펫:

```json
{
  "name": "mini_git: REPL (module)",
  "type": "debugpy",
  "request": "launch",
  "module": "mini_git",
  "cwd": "${workspaceFolder}/03-2.mini_git",
  "console": "integratedTerminal"
}
```

---

## 2. 모듈 ↔ 책임 ↔ 추천 브레이크포인트

| 모듈                         | 역할 (subject 연결)                 | 멈춰볼 함수                                                       |
| ---------------------------- | ----------------------------------- | ----------------------------------------------------------------- |
| `mini_git/main.py`           | 진입·`Repository()` 생성            | `main`                                                            |
| `mini_git/cli.py`            | 토크나이저·디스패치·REPL·출력       | `tokenize`, `dispatch`, `run_repl`, `_handle_*`                   |
| `mini_git/repository.py`     | 상태·브랜치·HEAD·명령 비즈니스 로직 | `init`, `commit`, `log`, `path`, `ancestors`, `search_*`, `merge` |
| `mini_git/commit.py`         | `Commit`, `HashGenerator`           | `HashGenerator.issue`                                             |
| `mini_git/graph.py`          | DAG 알고리즘 (§4.5)                 | `topological_order`, `shortest_path`, `ancestors`                 |
| `mini_git/sort.py`           | 직접 구현 정렬 (§4.4)               | `merge_sort`                                                      |
| `mini_git/inverted_index.py` | 역색인 (§4.3)                       | `add_commit`, `search_keyword`, `search_author`                   |
| `mini_git/diff.py`           | 보너스 DIFF                         | `diff_lines`                                                      |
| `mini_git/errors.py`         | `CommandError`, `RepoError`         | (예외 발생 지점에서 확인)                                         |

```mermaid
flowchart LR
  stdin[stdin / script] --> repl[cli.run_repl]
  repl --> tok[cli.tokenize]
  tok --> disp[cli.dispatch]
  disp --> repo[repository.Repository]
  repo --> graph[graph.py]
  repo --> sort[sort.py]
  repo --> idx[inverted_index.py]
  repo --> commit[commit.py]
  disp --> out[stdout format]
```

---

## 3. REPL 시나리오 (기능별)

아래는 `mini-git>` 프롬프트에 **한 줄씩** 입력하거나, §4 스크립트로 한 번에 넣을 수 있습니다.  
해시는 `0000001`, `0000002`, … 순서로 나온다고 가정합니다 (`INIT` 이후 세션 내 단조 증가).

### 3.1 저장소·브랜치·커밋 (subject §2.1, §4.5 INIT~COMMIT)

**목표:** `Repository.init` → `commit` → `branch` / `switch` / `_children` 갱신

```text
INIT alice
COMMIT "Add login feature"
COMMIT "Fix login bug"
BRANCH feature
SWITCH feature
COMMIT "Add UI polish"
LOG
exit
```

| 단계                | 관찰 포인트                                               |
| ------------------- | --------------------------------------------------------- |
| `INIT`              | `_branches["main"] is None`, `_head == "main"`, `_author` |
| 첫 `COMMIT`         | `parents == ()`, `_root_hashes`                           |
| 두 번째 `COMMIT`    | 부모 = 이전 HEAD 커밋 해시                                |
| `BRANCH feature`    | `feature`가 **현재** HEAD 커밋(`0000002`)을 가리킴        |
| `SWITCH` + `COMMIT` | `feature`만 앞으로 진행, `main`은 `0000002`에 머무름      |

**브레이크포인트:** `repository.init`, `repository.commit`, `repository.branch`, `repository.switch`

---

### 3.2 선형 LOG·정렬 (subject §2.3, §4.5 LOG)

```text
INIT bob
COMMIT "one"
COMMIT "two"
COMMIT "three"
LOG
LOG --sort-by=date
LOG --sort-by=author
exit
```

| 명령                   | 알고리즘                                                            |
| ---------------------- | ------------------------------------------------------------------- |
| `LOG`                  | Kahn 토폴로지 — **부모가 항상 자식 앞** (`graph.topological_order`) |
| `LOG --sort-by=date`   | `timestamp` 오름차순 (`merge_sort`, `repository.log_sorted`)        |
| `LOG --sort-by=author` | `author` → `timestamp` → `hash`                                     |

빈 저장소 확인:

```text
INIT empty
LOG
exit
```

→ `(no commits)`

**브레이크포인트:** `repository.log`, `graph.topological_order`, `sort.merge_sort`

**단위 테스트:** `tests.test_graph.TestTopologicalOrder`, `tests.test_repository.test_log_linear_chain`

---

### 3.3 포크·PATH·ANCESTORS (subject §2.2, §4.5 PATH / ANCESTORS)

```text
INIT alice
COMMIT "root"
COMMIT "main-tip"
BRANCH feature
SWITCH feature
COMMIT "feature-tip"
SWITCH main
LOG
PATH 0000001 0000004
PATH 0000002 0000004
ANCESTORS 0000004
ANCESTORS 0000001
exit
```

| 명령          | 기대 동작                                           |
| ------------- | --------------------------------------------------- |
| `PATH A B`    | 커밋–부모를 **무방향** 간선으로 BFS 최단 경로       |
| 동률 경로     | `hash1 -> hash2 -> ...` 문자열 **사전순 최소** 선택 |
| `ANCESTORS H` | `H`의 모든 조상, **`H` 자신 제외**, 토폴로지 순     |
| 루트 조상     | `(no ancestors)`                                    |

경로 없음 (분리된 그래프):

```text
INIT split
COMMIT "a"
BRANCH other
SWITCH other
COMMIT "b"
PATH 0000001 0000002
exit
```

→ `No path` (형제 서브트리만 있고 공통 조상 없음 — 실제로는 fork point가 있으면 경로 있음; **의도적으로 INIT 두 번은 안 됨** — 아래 MERGE 전 diamond 만들기 참고)

Diamond + lex tie (`test_graph`와 동일 패턴):

```text
INIT d
COMMIT "A"
BRANCH left
SWITCH left
COMMIT "B"
SWITCH main
BRANCH right
SWITCH right
COMMIT "C"
COMMIT "D"
PATH 0000002 0000005
exit
```

**브레이크포인트:** `graph.shortest_path`, `graph.ancestors`, `repository.path`

**단위 테스트:** `tests.test_graph.TestShortestPath`, `tests.test_repository.test_path_fork_through_fork_point`

---

### 3.4 SEARCH·역색인 (subject §2.3, §4.3)

```text
INIT alice
COMMIT "Add login feature"
COMMIT "Fix login bug"
SEARCH login
SEARCH log
SEARCH --author=alice
SEARCH --author=Alice
exit
```

| 입력                    | 매칭 규칙                                                        |
| ----------------------- | ---------------------------------------------------------------- |
| `SEARCH login`          | 메시지 **토큰** exact match (소문자 정규화) → `login` O, `log` X |
| `SEARCH --author=alice` | 작성자 **대소문자 구분** 완전 일치                               |

결과 없음:

```text
INIT alice
COMMIT "hello"
SEARCH missing
exit
```

→ `No results`

**브레이크포인트:** `inverted_index.add_commit`, `inverted_index.search_keyword`, `repository.search_keyword`

**단위 테스트:** `tests.test_inverted_index`, `tests.test_repository.test_search_keyword_no_substring`

---

### 3.5 오류·경계 (subject §4.1)

```text
LOG
INIT alice
BRANCH feature
COMMIT "first"
BRANCH feature
SWITCH ghost
COMMIT
PATH 0000099 0000001
ANCESTORS 0000099
SEARCH
LOG --sort-by=message
UNKNOWN
exit
```

| 입력                             | 기대 메시지                         |
| -------------------------------- | ----------------------------------- |
| `LOG` (INIT 전)                  | `Repository not initialized`        |
| `BRANCH` (첫 커밋 전)            | `Cannot branch before first commit` |
| `BRANCH feature` (중복)          | `Branch already exists: feature`    |
| `SWITCH ghost`                   | `Unknown branch: ghost`             |
| `COMMIT` (인자 없음)             | `Invalid args`                      |
| `PATH` / `ANCESTORS` (없는 해시) | `Unknown commit: 0000099`           |
| `UNKNOWN`                        | `Unknown command: UNKNOWN`          |

**브레이크포인트:** `cli.dispatch` (알 수 없는 명령), 각 `_handle_*`의 `CommandError` / `repository`의 `RepoError`

**단위 테스트:** `tests.test_cli` 오류 클래스들, `tests.test_repository.test_commands_before_init_raise`

---

### 3.6 INIT 재실행 (상태 리셋)

```text
INIT alice
COMMIT "will disappear"
INIT bob
LOG
exit
```

→ `(no commits)` — 해시 카운터·역색인·그래프 전부 리셋 (`repository.init` 내부 `HashGenerator.reset`)

---

### 3.7 보너스: MERGE (subject §5)

```text
INIT alice
COMMIT "base"
BRANCH feature
SWITCH feature
COMMIT "on feature"
SWITCH main
COMMIT "on main"
MERGE feature
LOG
ANCESTORS 0000005
exit
```

| 단계            | 관찰                                             |
| --------------- | ------------------------------------------------ |
| `MERGE feature` | **두 부모** (main HEAD + feature HEAD) 머지 커밋 |
| `LOG`           | 머지 후에도 부모→자식 토폴로지 유지              |

거절 케이스:

```text
INIT alice
COMMIT "only"
MERGE main
MERGE feature
exit
```

→ `Cannot merge a branch with itself` / `Unknown branch: feature` 등

**브레이크포인트:** `repository.merge`, `repository.commit` (parents 길이 2)

**단위 테스트:** `tests.test_repository.test_merge_creates_two_parent_commit`, `tests.test_cli.test_merge_success_message`

---

### 3.8 보너스: DIFF (subject §5)

터미널에서 임시 파일을 만든 뒤 REPL에서 실행합니다.

```bash
printf 'line1\nline2\n' > /tmp/a.txt
printf 'line1\nline3\n' > /tmp/b.txt
python3 main.py
```

```text
DIFF /tmp/a.txt /tmp/b.txt
DIFF /tmp/a.txt /tmp/a.txt
exit
```

**브레이크포인트:** `cli._handle_diff`, `diff.diff_lines`

**단위 테스트:** `tests.test_diff`, `tests.test_cli` 내 `TestDiff*`

---

## 4. 스크립트 한 번에 실행 (비대화형 REPL)

디버거 없이 출력만 빠르게 볼 때:

```bash
cd /Users/baejaemin/Project/codyssey/03-2.mini_git

# 기본 플로우 (README 예시)
printf '%s\n' \
  'INIT alice' \
  'COMMIT "Add login feature"' \
  'COMMIT "Fix login bug"' \
  'BRANCH feature' \
  'SWITCH feature' \
  'COMMIT "Add UI polish"' \
  'LOG' \
  'SEARCH login' \
  'PATH 0000001 0000003' \
  'exit' | python3 main.py
```

heredoc:

```bash
python3 main.py <<'EOF'
INIT alice
COMMIT "Add login feature"
COMMIT "Fix login bug"
BRANCH feature
SWITCH feature
COMMIT "Add UI polish"
LOG
SEARCH login
PATH 0000001 0000003
exit
EOF
```

**디버깅 팁:** `cli.run_repl`에 `stdin=StringIO(script)`, `stdout=StringIO()`를 넘기는 방식이 `tests/test_cli.py`의 `_run_script`와 동일합니다. 테스트 하나에 브레이크포인트를 걸면 REPL 전체를 스텝 없이 재현할 수 있습니다.

---

## 5. unittest로 레이어별 들어가기

| 테스트 모듈              | 주로 검증하는 코드              | 대표 실행                                  |
| ------------------------ | ------------------------------- | ------------------------------------------ |
| `test_commit.py`         | `Commit`, `HashGenerator`       | `python3 -m unittest tests.test_commit -v` |
| `test_sort.py`           | `merge_sort` 안정성·복잡도 전제 | `tests.test_sort`                          |
| `test_inverted_index.py` | 토큰화·역색인                   | `tests.test_inverted_index`                |
| `test_graph.py`          | 토폴로지·BFS·조상 (저장소 없음) | `tests.test_graph`                         |
| `test_repository.py`     | 엔진 전체 (stdout 없음)         | `tests.test_repository`                    |
| `test_cli.py`            | REPL·포맷·통합                  | `tests.test_cli`                           |
| `test_diff.py`           | LCS diff                        | `tests.test_diff`                          |

**추천 학습 순서 (디버깅):**

1. `test_graph` + `graph.py` — DAG만 집중
2. `test_sort` + `sort.py` — `LOG` 동률·정렬 키
3. `test_inverted_index` — `SEARCH` 후보 축소
4. `test_repository` — 브랜치·머지·인덱스 연동
5. `test_cli` — 사용자가 보는 문자열까지

단일 테스트만 디버그할 때:

```bash
python3 -m unittest tests.test_graph.TestShortestPath.test_diamond_lex_tie -v
```

---

## 6. subject §2 체크리스트 ↔ 명령 매핑

| subject §2 영역                    | 이 문서 시나리오                            |
| ---------------------------------- | ------------------------------------------- |
| §2.1 Repository · Branch           | §3.1                                        |
| §2.2 Log · Path                    | §3.2, §3.3                                  |
| §2.3 Search · Sort                 | §3.2 (`LOG --sort-by`), §3.4                |
| §2.4 REPL                          | 전체 + §4 파이프                            |
| §2.5 Run                           | §1 `python3 main.py`                        |
| §5 Bonus Diff / Merge / Sort bench | §3.7, §3.8, `python3 scripts/bench_sort.py` |

---

## 7. 한 번에 구조를 훑는 추천 루트 (약 30분)

1. `python3 -m mini_git` 실행 → §3.1 수동 입력, `repository.commit`에 브레이크
2. 동일 세션에서 `LOG` → `graph.topological_order` 스텝
3. 테스트 디버그: `tests.test_graph.TestTopologicalOrder.test_diamond`
4. §3.3 `PATH` / `ANCESTORS` → `shortest_path`, `ancestors`
5. §3.4 `SEARCH` → `inverted_index`
6. `tests.test_cli.TestInitCommitBranchSwitch.test_basic_command_flow`로 REPL 통합 확인
7. (선택) §3.7 `MERGE` → 두 부모 커밋·`LOG` 회귀 (`test_log_after_merge_topology_regression`)

---

## 8. 관련 문서

| 문서                                                         | 내용                   |
| ------------------------------------------------------------ | ---------------------- |
| [subject.md](subject.md)                                     | 과제 요구사항 원문     |
| [plan.md](plan.md)                                           | 잠금 결정·출력 형식 §9 |
| [study_guide.md](study_guide.md)                             | 이론·학습 순서         |
| [../README.md](../README.md)                                 | 명령·출력 요약         |
| [insights/sort_performance.md](insights/sort_performance.md) | 정렬 벤치 결과         |
