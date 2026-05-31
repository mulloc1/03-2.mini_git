# Mini Git 평가 응답서

> [평가문항](./평가문항.md)에 대한 항목별 답변. 코드 경로는 `mini_git/` 기준이다.

---

## 항목 1 · 기능 구현

### 저장소·브랜치

**Q. `INIT <user_name>` 실행 후 `main` 브랜치, `HEAD`, 현재 사용자 설정이 정상적으로 초기화되어 있는가?**

`Repository.init()`(`repository.py:39-53`)이 모든 세션 상태를 초기화한다.

- `_branches = {DEFAULT_BRANCH: None}` — `main` 브랜치 생성, 아직 커밋 없음
- `_head = DEFAULT_BRANCH` — HEAD를 `main`으로 고정
- `_author = user_name` — 현재 사용자 등록
- `_hash_generator.reset()` / `_index = InvertedIndex()` — 해시·역색인도 함께 리셋

이미 초기화된 상태에서 다시 호출되면 **모든 dict·리스트를 새로 할당**하므로 누수 없이 재초기화된다.

**Q. `BRANCH <name>` 생성 후 `SWITCH <name>`으로 전환되며, 이후 `COMMIT`이 해당 브랜치에 반영되는가?**

- `branch()`(`repository.py:55-70`): HEAD 커밋이 있을 때만 새 브랜치를 등록, 중복 이름은 `RepoError`.
- `switch()`(`repository.py:72-77`): `_head`만 새 이름으로 갱신. 존재하지 않으면 거부.
- `commit()`(`repository.py:79-110`): **현재 HEAD가 가리키는 브랜치의 tip을 부모**로 두고, 새 커밋의 `branch` 필드와 `_branches[head_branch]`를 모두 새 해시로 갱신.

→ 결과적으로 새 커밋은 항상 **현재 브랜치에만** 반영된다.

### 로그·그래프 탐색

**Q. `LOG`가 부모 커밋이 자식 커밋보다 먼저 출력되도록 동작하는가?** -> explain khan algorithm

`Repository.log()` → `_topo_commits()` → `topological_order()`(`graph.py:12-47`)는 **Kahn's algorithm**으로 위상 정렬한다.

- In Git's data structure, a child node has a pointer to its a parent node.
- 진입차수 0인 노드부터 큐에 넣고, 꺼낼 때 자식의 진입차수를 1씩 줄임
- 동시에 ready 상태가 되는 노드는 `(timestamp, hash)` 기준 merge sort로 정렬해 큐에 삽입
- → **부모는 자식보다 반드시 먼저** 출력되고, tie-breaking은 결정적

**Q. `PATH <a> <b>`가 경로가 있으면 최단 경로를, 없으면 `No path`를 출력하는가?**

`Repository.path()`(`repository.py:194-204`)는 부모·자식을 모두 이웃으로 간주하는 **무방향 BFS**(`shortest_path`, `graph.py:50-82`)를 호출한다.

- 도달 불가능 → `None` 반환 → CLI에서 `No path` 출력 (`cli.py:201-203`)
- 동률 거리에선 `_path_key`(`->`로 join한 문자열)로 **사전식 최소 경로**를 선택

**Q. `ANCESTORS <hash>`가 모든 조상을 빠짐없이 출력하는가?**

- there is none differences between a DFS and a BFS in implemented ANCESTORS
  `graph.ancestors()`(`graph.py:85-104`)는 `start`에서 부모 간선만 따라가는 BFS로 **도달 가능한 모든 조상**을 집합으로 수집한다(자신은 제외). 이후 `_topo_commits()`로 위상 정렬해 출력하므로 누락이 없다.

### 검색·정렬

**Q. `SEARCH <keyword>` / `SEARCH author=<name>` / `LOG --sort-by=date|author`가 요구사항대로 동작하는가?**

- `SEARCH <keyword>`: `InvertedIndex.search_keyword()`로 메시지 토큰의 hash 리스트 조회 → 위상 정렬 출력 (`repository.py:216-220`)
- `SEARCH --author=<name>`: 동일 흐름이지만 author 인덱스 사용 (`repository.py:222-226`)
- `LOG --sort-by=date|author`: `log_sorted()`(`repository.py:182-192`)가 `merge_sort`로 정렬. 키는 각각 `(timestamp, hash)`, `(author, timestamp, hash)`로 **결정적 tie-break** 적용

---

## 항목 2 · 설계·구조

### 데이터 모델

**Q. 커밋 저장소, 브랜치, HEAD, 사용자 정보를 어떤 구조로 분리했고, 각 책임을 설명할 수 있는가?**

`Repository` 내부에 **역할별로 분리된 dict**를 둔다(`repository.py:26-37`).

| 필드              | 자료구조                 | 책임                                              |
| ----------------- | ------------------------ | ------------------------------------------------- |
| `_commits`        | `dict[str, Commit]`      | hash → 커밋 객체 (커밋 저장소)                    |
| `_branches`       | `dict[str, str \| None]` | 브랜치명 → tip hash                               |
| `_children`       | `dict[str, list[str]]`   | parent hash → child hashes (`PATH` 무방향 탐색용) |
| `_head`           | `str \| None`            | 현재 브랜치명                                     |
| `_author`         | `str \| None`            | 현재 사용자                                       |
| `_index`          | `InvertedIndex`          | author·keyword 역색인                             |
| `_hash_generator` | `HashGenerator`          | 7자리 hex 카운터                                  |

- `Commit`은 `@dataclass(frozen=True)`(`commit.py:8-23`)로 **불변**. 한 번 만들어진 노드는 수정 불가
- `InvertedIndex`(`inverted_index.py`)는 검색 책임만 가진 **독립 모듈** — Repository는 추가/조회만 위임
- `graph.py`는 **순수 함수**로 자료구조에 의존하지 않음 (콜백으로 parents/neighbors 주입)
- 즉, **상태(Repository)**, **검색(InvertedIndex)**, **알고리즘(graph)**, **표현(CLI)** 4계층 분리

### 조회·인덱싱

**Q. 커밋 hash로 빠르게 조회하기 위해 어떤 키-값 구조를 사용했고, 중복·충돌을 어떻게 방지했는지 설명할 수 있는가?**

- `_commits: dict[str, Commit]` — Python dict(해시 테이블)로 **O(1) 평균 조회**
- `HashGenerator`(`commit.py:26-40`)는 **세션 단위 단조 증가 카운터**를 7자리 hex로 변환(`f"{counter:07x}"`)
  - 같은 세션 내에서는 **충돌이 원천 불가능** (카운터가 매번 증가)
  - `init()` 호출 시 `reset()`되므로 새 세션도 `0000001`부터 깨끗하게 시작
- 외부 입력이 아닌 **내부 생성 해시**이므로 사용자 입력 충돌도 없음

**Q. 커밋이 추가될 때 역색인(author/keyword)을 어떤 시점에, 어떤 방식으로 갱신하도록 설계했는지 설명할 수 있는가?**

- **시점**: `Repository.commit()`과 `merge()`가 **새 커밋을 `_commits`에 등록한 직후** `self._index.add_commit(commit)` 호출(`repository.py:109`, `:149`)
- **방식**: `InvertedIndex.add_commit()`(`inverted_index.py:20-24`)이
  1. `_tokenize()`로 메시지를 공백 분할 후 **lowercase 정규화**
  2. 각 토큰 → `_by_keyword[token]`에 hash append
  3. author는 정규화 없이 `_by_author[author]`에 hash append
- `_append()`(`:41-45`)는 **이미 존재하는 hash는 다시 넣지 않음** (중복 검색 결과 방지)
- → 커밋 생성 시점에 **인덱스가 항상 일관**되므로 검색은 단순 dict 조회만 하면 된다

### 그래프 로직·문서화

**Q. `LOG`, `PATH`, `ANCESTORS`에서 사용하는 그래프 탐색 로직을 어떻게 재사용 가능하게 구성했는지 설명할 수 있는가?**

`graph.py`의 세 함수는 **자료구조 비의존적**(주입 의존성, Dependency Injection).

```50:54:03-2.mini_git/mini_git/graph.py
def shortest_path(
    start: str,
    goal: str,
    get_neighbors: Callable[[str], Iterable[str]],
) -> list[str] | None:
```

- `topological_order(hashes, get_parents, get_sort_key)`
- `shortest_path(start, goal, get_neighbors)`
- `ancestors(start, get_parents)`

→ Repository는 **이웃·부모 조회 콜백만 주입**해 동일 함수를 재사용한다.

```200:204:03-2.mini_git/mini_git/repository.py
        def neighbors(commit_hash: str) -> list[str]:
            commit = self._commits[commit_hash]
            return list(commit.parents) + self._children.get(commit_hash, [])

        return shortest_path(start, goal, neighbors)
```

이 패턴 덕에 `LOG`/`ANCESTORS`(parents만)와 `PATH`(parents+children 무방향)가 **같은 코드를 다른 그래프로** 사용할 수 있다.

**Q. 주요 함수·클래스에 docstring·주석을 어떤 기준으로 작성했는지 설명할 수 있는가?**

- **모듈 docstring**: 해당 모듈이 과제 spec의 어느 절(`subject §4.x`)에 대응되는지 명시
- **클래스/함수 docstring**: "무엇을 반환하는지"와 "예외가 언제 발생하는지"를 한두 줄로
- **인라인 주석**: 코드만 봐서는 의도를 알 수 없을 때만(예: `_append`의 중복 방지 분기). **무엇을 하는지 그대로 옮긴 주석은 작성하지 않음**

---

## 항목 3 · 이론·알고리즘

### 커밋 그래프 (DAG)

**Q. 커밋 그래프가 왜 DAG여야 하는지, 사이클이 생기면 어떤 문제가 발생하는지 설명할 수 있는가?**

- 커밋은 **이전 상태(parent)** 를 가리키는 단방향 관계 — 시간상 과거를 참조하므로 **방향성**과 **비순환성**을 동시에 요구
- 사이클이 생기면:
  1. **위상 정렬 불가** → `LOG`의 "부모 먼저" 보장이 깨짐
  2. **`ANCESTORS` 무한 루프** → BFS가 종료되지 않음(현 구현은 `visited` 집합으로 방어하지만 의미 자체가 무너짐)
  3. **머지 베이스 정의 모호** → 두 브랜치의 공통 조상이 유일하지 않게 됨
- 본 구현은 `parents`를 `tuple`로 **불변 저장**하고, 부모는 항상 **이미 존재하는 커밋(현재 HEAD)** 만 가능하므로 사이클이 만들어질 수 없는 구조다.

**Q. `LOG`에서 「부모가 먼저」 조건을 만족시키기 위해 어떤 접근(예: 위상 정렬 성격의 출력)을 적용했는지 설명할 수 있는가?**

**Kahn's algorithm 기반 위상 정렬**(`graph.py:topological_order`).

1. 각 노드의 진입차수(부모 중 입력 집합 안에 있는 개수) 계산
2. 진입차수 0인 노드를 `(timestamp, hash)` 정렬 후 큐에 투입
3. 큐에서 꺼낸 노드를 결과에 추가, 자식의 진입차수 감소
4. 새로 0이 된 자식은 다시 정렬해 큐 뒤에 삽입

→ 부모는 자식보다 반드시 먼저 출력되고, 동일 레벨에서는 `timestamp` 오름차순으로 **결정적**이다.

### 경로·탐색

**Q. `PATH`에서 최단 경로를 찾기 위해 어떤 알고리즘(예: BFS)을 선택했고, 간선을 무방향으로 정의한 이유를 설명할 수 있는가?**

- **BFS**를 선택한 이유: 간선 가중치가 모두 1이므로 **최단 경로 = 최소 간선 수**. BFS가 `O(V+E)`로 최적
- **무방향으로 정의한 이유**: PATH는 두 커밋의 **관계상 거리**를 묻는 것이지 "조상 ↔ 후손" 방향만 묻는 게 아니다. 형제 브랜치 간 경로도 LCA를 거쳐 연결되어야 하므로 `parents + children` 양방향을 이웃으로 본다.
- 동률 최단 경로 처리: 본 구현은 `_path_key`로 사전식 비교 후 더 작은 경로를 채택해 **결정적 출력**을 보장한다.

### 정렬·역색인

**Q. 정렬 알고리즘의 평균·최악 시간복잡도와 안정 정렬 여부를 설명할 수 있는가?**

`sort.merge_sort`(`sort.py`).

| 지표                 | 값                                                                                              |
| -------------------- | ----------------------------------------------------------------------------------------------- |
| 평균/최악 시간복잡도 | **O(n log n)**                                                                                  |
| 공간복잡도           | O(n) (보조 배열)                                                                                |
| 안정성               | **안정 정렬** — `_merge`에서 `left_key < right_key`일 때만 좌측 우선, 동률이면 좌측을 먼저 출력 |
| 비교 횟수            | 최선 `n/2 log n`, 최악 `n log n - n + 1`                                                        |

안정 정렬이 중요한 이유: `LOG --sort-by=author`에서 같은 작성자 커밋들의 **삽입 순서(timestamp 의존)** 가 보존되어야 하기 때문. 또한 `(timestamp, hash)` 같은 합성 키로 tie-break을 명시해 안정성에 의존하지 않고도 결정적 출력을 만든다.

**Q. 역색인이 순회 검색보다 빠른 이유를, 자료구조·시간복잡도 관점에서 설명할 수 있는가?**

- **순회 검색**: 매 쿼리마다 N개 커밋의 메시지를 토큰화·비교 → `O(N·L)` (L은 평균 메시지 길이)
- **역색인**: 토큰 → hash 리스트 dict로 변환해두면 쿼리는 `dict.get(token)` 한 번 → **평균 O(1)** 접근 + 결과 길이 k에 대해 `O(k)` 복사
- 즉, 빈도가 높은 검색을 **사전 계산해서 분할 상환**하는 전략. 커밋 추가 시 `O(L)` 비용이 한 번 들지만, 이후 모든 검색이 `O(k)`가 된다
- 본 구현은 `dict[str, list[str]]` + 삽입 시 중복 제거로, list iteration까지도 결정적이다

---

## 항목 4 · 확장·트레이드오프

### 성능·규모

**Q. 커밋 수가 10배 늘어났을 때 병목이 될 지점을 예측하고, 개선 방향(자료구조·알고리즘)을 설명할 수 있는가?**

| 잠재 병목                                           | 현재 비용                                    | 개선 방향                                                      |
| --------------------------------------------------- | -------------------------------------------- | -------------------------------------------------------------- |
| `topological_order`의 `merge_sort(ready)` 반복 호출 | 큐가 매번 재정렬 → 최악 `O(N² log N)`        | **min-heap**(`heapq`)으로 교체 시 `O((V+E) log V)`             |
| `shortest_path`의 `queue.pop(0)`                    | `O(n)` per pop → BFS 전체가 `O(V²)`          | `collections.deque`로 `O(1)` popleft                           |
| `_path_key`로 매번 join                             | 비교마다 문자열 생성                         | 경로를 튜플로 비교(`tuple` 비교는 lex이고 short-circuit)       |
| `merge_sort` 재귀 슬라이싱                          | 슬라이스마다 list 복사 → 메모리 `O(N log N)` | 인덱스 기반 in-place merge 또는 `Timsort`(`sorted`)            |
| `InvertedIndex._by_keyword[k]`의 list 중복 체크     | `commit_hash not in index[k]`가 `O(k)`       | `set`으로 보조 인덱스를 두거나, 삽입 시점에 중복이 없음을 보장 |
| `ANCESTORS`/`PATH`마다 매번 BFS                     | 같은 노드를 반복 방문                        | **결과 캐시**(LRU) 또는 LCA용 sparse table 전처리              |

10배 증가(예: 1만 → 10만 커밋)에서는 `LOG`의 정렬 비용이 먼저 체감되므로 **heap 기반 위상 정렬**과 **deque 기반 BFS**가 ROI가 가장 크다.

### 요구사항 변경

**Q. `PATH`의 간선 정의를 「부모 방향만 허용」으로 바꾸면 결과가 어떻게 달라지고, 구현은 무엇을 바꿔야 하는지 설명할 수 있는가?**

- **결과 변화**: 두 노드가 **조상-후손 관계**일 때만 경로가 존재. 형제 브랜치는 항상 `No path`. 머지 커밋이 있어도 "후손에서 조상으로" 한 방향만 가능
- **구현 변경**: `repository.py:200-202`의 `neighbors` 함수를
  ```python
  def neighbors(commit_hash: str) -> list[str]:
      return list(self._commits[commit_hash].parents)
  ```
  로 좁히면 끝. `_children` 인덱스는 PATH에서는 더 이상 필요 없고, 경로 길이의 상한은 그래프 깊이로 줄어들어 평균 탐색 비용도 감소
- **추가 고려**: 결과의 의미가 "거리"에서 "역사적 선후 관계"로 바뀌므로 **CLI 출력 문구나 도움말도 같이 갱신**해야 한다

**Q. `LOG --sort-by=author` 요구사항이 「부모·자식 선후도 유지」로 강화된다면, 어떤 전략으로 해결할지 설명할 수 있는가?**

이는 일반적인 정렬이 아니라 **제약 조건(parent < child)을 만족하는 정렬** — 즉 **secondary key 위상 정렬** 문제다.

전략:

1. **Kahn's algorithm을 활용**하되, ready 큐의 우선순위를 `(author, timestamp, hash)`로 둔다
2. 진입차수 0이 된 노드들 중 **author가 가장 작은 노드를 먼저** 꺼냄
3. 같은 author 안에서는 timestamp 순
4. → 부모·자식 선후도는 **위상 정렬이 보장**하고, 동일 위상 레벨 내에서만 author 기준 정렬 적용

이는 본 구현의 `topological_order(get_sort_key=...)`에 키를 바꿔 넣기만 하면 되는 수준이다.

```python
return topological_order(
    hashes,
    get_parents=...,
    get_sort_key=lambda h: (self._commits[h].author, self._commits[h].timestamp, h),
)
```

전역 author 정렬과는 결과가 다름을 **명확히 문서화**하고, 필요하면 두 모드를 모두 제공한다(예: `--sort-by=author --strict-topo`).

### 설계 선택

**Q. 해시 생성 방식을 카운터 기반 → 난수 기반으로 바꿀 때 테스트·재현성·디버깅에 미치는 영향을 설명할 수 있는가?**

| 항목                 | 카운터(현재)                                                        | 난수 기반                                                                     |
| -------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **재현성**           | 같은 명령 시퀀스 → 같은 해시 → **결정적 테스트** 가능               | seed를 고정하지 않으면 매 실행마다 해시가 달라져 골든 테스트(snapshot) 무력화 |
| **테스트 작성**      | 기대값을 `0000001`처럼 명시 가능                                    | 정규식·길이 검증·mocking 필요 → 테스트가 장황해짐                             |
| **디버깅**           | hash만 봐도 **생성 순서** 추정 가능                                 | 순서 정보 손실, 로그 추적 시 timestamp에 의존해야 함                          |
| **충돌 가능성**      | 세션 내 절대 충돌 없음                                              | 비둘기집 원리상 매우 낮지만 0은 아님 → 충돌 시 재시도 로직 필요               |
| **분산 환경 적합성** | 단일 세션에서만 안전, 여러 인스턴스가 동시에 발급하면 충돌          | UUID·암호학적 난수면 사실상 안전                                              |
| **보안/예측성**      | 다음 hash를 쉽게 예측 가능 — 실 git처럼 콘텐츠 무결성 검증엔 부적합 | 예측 불가하지만 **콘텐츠와 무관**하면 무결성 검증은 별도                      |

본 과제는 **단일 세션·결정적 동작이 중요**한 학습용이라 카운터가 맞는 선택이다. 실제 git처럼 콘텐츠 기반 해시(SHA-1/256)로 바꾸면 재현성과 무결성을 동시에 잡을 수 있지만, **테스트는 콘텐츠/타임스탬프를 통제할 수 있게 fixture를 정비**해야 한다.
