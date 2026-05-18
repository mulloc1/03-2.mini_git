# Mini Git

Python으로 구현한 **인메모리(in-memory) Mini Git CLI**입니다. 커밋 그래프(DAG), 역색인, 직접 구현한 정렬·그래프 알고리즘을 REPL에서 사용할 수 있습니다.

- **Python**: 3.14 권장 (표준 라이브러리만 사용)
- **저장**: 디스크·네트워크 없음 — 프로세스 종료 시 모든 데이터 소멸
- **과제 명세**: [docs/subject.md](docs/subject.md) · 구현 계획: [docs/plan.md](docs/plan.md)

---

## 실행 방법

프로젝트 루트(`03-2.mini_git/`)에서:

```bash
python3 main.py
```

또는 모듈로 실행:

```bash
python3 -m mini_git
```

`mini-git>` 프롬프트가 나타나면 명령을 입력합니다. 종료는 `exit`, `quit`(대소문자 무관), 또는 `Ctrl-D`(EOF)입니다. 종료 코드는 `0`입니다.

터미널(TTY)에서 실행할 때는 표준 라이브러리 `readline`으로 **↑/↓** 키로 직전 명령을 다시 불러올 수 있습니다(세션 한정, 파일에 저장하지 않음). `readline` 모듈이 없는 환경(일부 Windows Python 등)에서는 자동으로 비활성화됩니다.

### 테스트

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

추가 패키지 없이 표준 `unittest`만 사용합니다.

---

## 제한 사항 (중요)

| 항목 | 설명 |
| --- | --- |
| **인메모리** | 커밋·브랜치·인덱스는 RAM에만 존재합니다. 파일로 저장하지 않습니다. |
| **휘발성** | REPL을 종료하면 저장소가 사라집니다. |
| **`INIT` 재실행** | 같은 세션에서 `INIT`을 다시 호출하면 **전체 상태가 초기화**됩니다(커밋, 브랜치, 역색인, 해시 카운터 모두 리셋). |
| **해시 유일성** | `0000001`, `0000002`, … 형식의 7자리 hex는 **마지막 `INIT` 이후 세션 안에서만** 유일합니다. |
| **정렬 API** | `sorted()`, `list.sort()`는 사용하지 않습니다. Merge Sort를 직접 구현했습니다. |

---

## 명령어 요약

명령어는 **대소문자를 구분하지 않습니다** (`init` = `INIT`).

| 명령 | 설명 |
| --- | --- |
| `INIT <user_name>` | 저장소 초기화. 기본 브랜치 `main`, HEAD·작성자 설정 |
| `BRANCH <branch_name>` | 현재 HEAD 커밋을 가리키는 새 브랜치 생성 |
| `SWITCH <branch_name>` | HEAD를 해당 브랜치로 이동 |
| `COMMIT <message>` | 현재 브랜치에 커밋 생성(부모 = HEAD 커밋) |
| `LOG` | 전체 커밋을 **부모 → 자식** 토폴로지 순으로 출력 |
| `LOG --sort-by=date` | `timestamp` 오름차순 정렬 |
| `LOG --sort-by=author` | `author` 오름차순, 동률 시 `timestamp` → `hash` |
| `PATH <commit1> <commit2>` | 두 커밋 사이 **무방향** 최단 경로 |
| `ANCESTORS <commit_hash>` | 조상 커밋 전체(시작 커밋 제외), 토폴로지 순 |
| `SEARCH <keyword>` | 메시지 **토큰** exact match (대소문자 무시) |
| `SEARCH --author=<name>` | 작성자 **정확히** 일치 (대소문자 구분) |
| `exit` / `quit` | REPL 종료 |

### 인자·옵션 규칙

- 공백이 있는 메시지·이름은 **큰따옴표**로 감쌉니다.  
  예: `COMMIT "Add login feature"`
- 옵션은 **`--키=값`** 형식만 지원합니다 (`--key value` 불가).  
  예: `LOG --sort-by=date`, `SEARCH --author=alice`
- 옵션 값에 공백이 있으면 따옴표를 쓸 수 있습니다.  
  예: `SEARCH --author="Alice Liddell"`
- 이스케이프 시퀀스(`\"` 등)는 지원하지 않습니다.

---

## 출력 형식

### 커밋 한 줄 요약

`LOG`, `ANCESTORS`, `SEARCH` 결과는 다음 형식입니다.

```
<hash> <author> <YYYY-MM-DD HH:MM:SS> <message>
```

예:

```
0000001 alice 2026-05-16 09:00:00 Add login feature
```

표시 시각은 커밋 생성 시점의 `time.time()` 값을 `localtime`으로 포맷한 것입니다. 정렬·동률 처리에는 별도의 **단조 증가 `timestamp` 정수**를 사용합니다.

### 명령별 성공 메시지

```
mini-git> INIT alice
Initialized repository for alice

mini-git> COMMIT "Add login feature"
Committed 0000001

mini-git> BRANCH feature
Created branch feature at 0000002

mini-git> SWITCH feature
Switched to branch feature

mini-git> LOG
0000001 alice 2026-05-16 09:00:00 Add login feature
0000002 alice 2026-05-16 09:00:01 Fix login bug

mini-git> PATH 0000001 0000003
0000001 -> 0000002 -> 0000003
```

### 빈 결과·특수 메시지

| 상황 | 출력 |
| --- | --- |
| 커밋 없이 `LOG` | `(no commits)` |
| 루트 커밋 `ANCESTORS` | `(no ancestors)` |
| 검색 결과 없음 | `No results` |
| 경로 없음 | `No path` |

### 오류 메시지 (대표)

| 상황 | 출력 |
| --- | --- |
| 알 수 없는 명령 | `Unknown command: <cmd>` |
| 인자 오류 | `Invalid args` |
| 없는 브랜치 | `Unknown branch: <name>` |
| 없는 커밋 해시 | `Unknown commit: <hash>` |
| `INIT` 전 명령 | `Repository not initialized` |
| 첫 커밋 전 `BRANCH` | `Cannot branch before first commit` |
| 중복 브랜치 | `Branch already exists: <name>` |

---

## 동작 세부 (잠금 결정)

과제에서 자유였던 규칙은 [docs/plan.md](docs/plan.md) §2에 고정했습니다. README에서 자주 헷갈리는 항목만 정리합니다.

### 저장소·브랜치

- `INIT` 후 기본 브랜치는 **`main`**이며, 첫 `COMMIT` 전까지 `main`은 커밋을 가리키지 않습니다(`None`).
- HEAD는 **브랜치 이름**만 가리킵니다(detached HEAD 없음).
- `BRANCH`는 현재 HEAD의 커밋 해시를 복사해 새 브랜치를 만듭니다. HEAD 브랜치 자체는 바뀌지 않습니다.

### `LOG`

- 기본 `LOG`: **Kahn 알고리즘** 토폴로지 정렬 — 항상 부모가 자식보다 앞에 옵니다.
- 동률: `timestamp` 오름차순 → `hash` 사전순.
- `LOG --sort-by=date`: `timestamp` 오름차순(최신 우선이 **아님**).
- `LOG --sort-by=author`: `author` → `timestamp` → `hash`.

### `PATH`

- 커밋–부모 연결을 **무방향 간선**으로 보고 BFS로 최단 경로를 찾습니다.
- 최단 경로가 여러 개면, 해시를 `->`로 이은 문자열이 **사전순으로 가장 작은** 경로를 선택합니다.

### `ANCESTORS`

- 시작 커밋은 결과에 **포함하지 않습니다**.
- 출력 순서: 토폴로지(부모 우선), 동률 시 `hash` 사전순.

### `SEARCH`

- 키워드: 메시지를 **공백으로 분할** → 각 토큰을 **소문자화** → **토큰 전체 일치**만 인정합니다.  
  - `login`은 `"Add login feature"`에 매칭되지만, `log`는 `"login"`의 부분 문자열이 아니므로 매칭되지 않습니다.
- `--author`: 작성자 문자열 **완전 일치**, **대소문자 구분**.
- `SEARCH` / `ANCESTORS` 결과 순서: 토폴로지(부모 우선).

---

## 프로젝트 구조

```
03-2.mini_git/
├── main.py              # 진입점 (mini_git.main 위임)
├── mini_git/
│   ├── commit.py        # Commit, HashIssuer
│   ├── inverted_index.py
│   ├── graph.py         # topological_order, shortest_path, ancestors
│   ├── sort.py          # merge_sort (stable)
│   ├── repository.py    # 저장소 엔진 (순수 로직)
│   ├── cli.py           # 토크나이저, REPL, 출력 포맷
│   └── errors.py
└── tests/               # unittest (helpers.py: FakeClock 등)
```

- **`repository`**: 데이터 변경·조회만 담당. stdout에 쓰지 않습니다.
- **`cli`**: 입력 파싱, 명령 디스패치, §9 고정 출력 형식.

---

## 구현 하이라이트 (학습 목표 연결)

1. **커밋 그래프 (DAG)**  
   `dict[hash → Commit]`로 O(1) 조회. `parents`는 불변 `tuple`. 루트는 `parents == ()`.

2. **토폴로지 `LOG`**  
   Kahn 알고리즘 + 큐 삽입 시 `merge_sort`로 동률을 고정해 결정론적 출력을 보장합니다.

3. **최단 경로·조상**  
   `PATH`: 무방향 BFS + lex-min 경로. `ANCESTORS`: 부모 방향 BFS/DFS + `visited`.

4. **Merge Sort**  
   `sorted()` / `list.sort()` 없이 직접 구현. 평균·최악 O(N log N), **안정 정렬**로 다중 키 동률 처리에 유리합니다.

5. **역색인**  
   `keyword → [hash…]`, `author → [hash…]`. 키워드 조회 O(1) 후 후보만 정렬·토폴로지 처리 — 전체 커밋 선형 스캔 대비 검색 비용을 줄입니다.

---

## 예시 세션

```text
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
mini-git> LOG
0000001 alice 2026-05-16 09:00:00 Add login feature
0000002 alice 2026-05-16 09:00:01 Fix login bug
0000003 alice 2026-05-16 09:00:02 Add UI polish
mini-git> SEARCH login
0000001 alice 2026-05-16 09:00:00 Add login feature
0000002 alice 2026-05-16 09:00:01 Fix login bug
mini-git> PATH 0000001 0000003
0000001 -> 0000002 -> 0000003
mini-git> exit
```

---

## 보너스 (미구현)

[docs/subject.md](docs/subject.md) §5의 선택 과제는 아직 포함하지 않았습니다.

- `diff <file1> <file2>` — 줄 단위 LCS diff
- `merge <branch_name>` — 두 부모를 가진 머지 커밋
- 정렬 성능 측정·문서화
