# Filter Comparison Project - Final Guide

## 1. Project Scenario

**Search Keyword Dictionary Management**  
검색 플랫폼의 키워드 사전 운영

검색 플랫폼은 자동완성, 트렌딩 키워드, 금칙어 목록, 만료 키워드를 관리한다.
이 시나리오 하나로 5개 필터의 membership query, insert/delete 지원 여부,
memory usage, false positive rate, latency, 그리고 SuRF의 prefix/range query
장점을 비교한다.

핵심 메시지:

> 자동완성 서비스를 만드는 것이 아니라, 키워드 사전 운영이라는 하나의 workload를 통해 각 membership filter의 장단점을 비교한다.

---

## 2. Five MCP Servers

| Member | MCP Server | Data Structure | Role |
| --- | --- | --- | --- |
| A | `filter-naive` | Naive Set / Hash Table | Exact baseline |
| B | `filter-bloom` | Standard Bloom Filter | Memory-efficient membership filter |
| C | `filter-counting-bloom` | Counting Bloom Filter | Bloom Filter with deletion support |
| D | `filter-cuckoo` | Cuckoo Filter | Fingerprint-based filter with deletion |
| E | `filter-surf` | Simplified SuRF | Prefix/range query filter |

---

## 3. Common ADT

모든 MCP 서버는 같은 ADT 메서드 이름을 사용한다.
지원하지 않는 기능은 에러를 던지지 않고 `supported: false`와 `"N/A"`를 반환한다.

| Method | Meaning | Used For |
| --- | --- | --- |
| `build(items, config=None)` | 초기 키워드 데이터셋으로 필터 생성 | 실험 시작 |
| `insert(x)` | 새 키워드 삽입 | 트렌딩 키워드 / 새 금칙어 등록 |
| `contains(x)` | 키워드 존재 여부 확인 | membership query / 금칙어 여부 확인 |
| `delete(x)` | 키워드 삭제 | 만료 키워드 제거 / 금칙어 해제 |
| `prefix_query(prefix)` | prefix로 시작하는 키워드 조회 | 자동완성 |
| `range_query(lo, hi)` | 사전식 구간 조회 | 정렬된 키워드 구간 검색 |
| `memory_usage()` | 메모리 사용량 반환 | 운영 비용 비교 |
| `false_positive_rate()` | false positive rate 반환 | 정확도/오탐률 비교 |
| `reset(config=None)` | 데이터 전체 삭제 후 optional config로 빈 필터 재초기화 | 반복 실험 |

`range_query(lo, hi)` 규칙:

```text
lo <= key < hi
```

즉, `lo`는 포함하고 `hi`는 제외하는 half-open interval로 통일한다.

`reset(config=None)` 규칙:

```text
reset() 호출 후 필터는 비어 있다.
새 데이터는 build() 또는 insert()로 다시 넣어야 한다.
config를 넘기면 새 config로 빈 필터를 다시 만든다.
```

---

## 4. Support Matrix

| Server | `contains` | `insert` | `delete` | `prefix_query` | `range_query` |
| --- | --- | --- | --- | --- | --- |
| Naive Set | exact | supported | supported | exact | exact |
| Standard Bloom | approximate | supported | N/A | N/A | N/A |
| Counting Bloom | approximate | supported | supported | N/A | N/A |
| Cuckoo Filter | approximate | supported | supported | N/A | N/A |
| SuRF simplified | approximate | static / N/A | static / N/A | approximate | approximate |

Note:

- Bloom 계열과 Cuckoo Filter는 hash 기반이라 key의 순서나 prefix 정보를 저장하지 않는다.
- Naive Set은 exact baseline이지만 prefix/range query는 전체 scan 기반이라 큰 데이터에서는 비효율적이다.
- SuRF는 trie 기반이라 prefix/range query를 지원할 수 있다.

---

## 5. SuRF Simplified Explanation

SuRF는 **Succinct Range Filter**의 약자이다. Sorted String Table 위에서
prefix/range query를 빠르게 처리하기 위해 설계된 trie 기반 approximate filter이다.

Bloom Filter, Counting Bloom Filter, Cuckoo Filter는 hash 기반 구조이다.
Hash를 거치면 key의 사전식 순서와 prefix 구조가 사라지므로 `prefix_query`나
`range_query`를 직접 지원하기 어렵다.

반면 SuRF는 key의 prefix structure를 저장한다. 그래서 특정 prefix로 시작하는
키워드가 있는지, 또는 사전식 구간 안에 들어가는 키워드가 있는지를 확인할 수 있다.
이 점이 검색어 자동완성이나 정렬된 키워드 구간 조회에서 SuRF를 넣는 이유이다.

이번 프로젝트의 `filter-surf`는 논문 수준의 전체 SuRF 구현이 아니다.
실제 SuRF의 LOUDS-Dense / LOUDS-Sparse encoding 전체를 구현하지 않고,
아래 아이디어만 단순화해서 구현한다.

| Concept | Simplified Implementation |
| --- | --- |
| Sorted keys | build 시 key를 정렬된 list로 저장 |
| Trie prefix | `trie_depth`만큼 잘린 prefix set 저장 |
| Suffix check | `suffix_bits`만큼 hash suffix 저장 가능 |
| Prefix query | 정렬된 list에서 binary search로 prefix 범위 계산 |
| Range query | `bisect_left`로 `lo <= key < hi` 구간 계산 |
| Approximation | prefix/suffix 정보 손실 때문에 false positive 가능 |

발표 멘트:

> SuRF의 강점은 FPR이 가장 낮다는 점이 아니라, 다른 membership filter들이 지원하지 못하는 prefix/range query를 지원한다는 점입니다. 저희 구현은 full LOUDS SuRF가 아니라 핵심 아이디어를 보여주는 simplified trie-based range filter입니다.

---

## 6. Config

```json
{
  "target_fpr": 0.01,
  "expected_items": 1000,
  "fingerprint_bits": 12,
  "bucket_size": 4,
  "counter_bits": 4,
  "suffix_bits": 8,
  "trie_depth": 8
}
```

| Field | Used By | Meaning |
| --- | --- | --- |
| `target_fpr` | Bloom, Counting Bloom | 목표 false positive rate |
| `expected_items` | Bloom, Counting Bloom, Cuckoo | 예상 데이터 개수 |
| `fingerprint_bits` | Cuckoo | fingerprint 크기 |
| `bucket_size` | Cuckoo | bucket당 slot 개수 |
| `counter_bits` | Counting Bloom | counter 하나의 bit 수 |
| `suffix_bits` | SuRF | suffix 저장 bit 수 |
| `trie_depth` | SuRF | simplified trie depth |

SuRF 실험 튜닝:

- `trie_depth`가 크면 false positive가 낮아진다.
- `trie_depth`가 작으면 prefix 충돌이 많아져 false positive가 높아진다.
- 발표에서 SuRF의 approximate 성격을 보여주려면 `trie_depth=5` 정도도 실험해볼 수 있다.
- 단, 최종 결론에서는 SuRF의 핵심을 FPR이 아니라 prefix/range 지원으로 설명한다.

---

## 7. Common Response Schema

Supported response:

```json
{
  "supported": true,
  "result": true,
  "exact": false,
  "may_contain_false_positive": true,
  "query_time_us": 0.8
}
```

Unsupported response:

```json
{
  "supported": false,
  "result": "N/A",
  "reason": "This filter only supports point membership queries."
}
```

`memory_usage()` response:

```json
{
  "bytes": 122880,
  "bits_per_item": 9.83,
  "n_items": 1000
}
```

메모리 측정 기준:

- Bloom / Counting Bloom / Cuckoo는 bit array, counter array, fingerprint buckets의 이론적 packed storage 크기를 계산한다.
- Naive Set과 simplified SuRF는 Python `set`/prefix storage의 `deep_size` 기반 추정값이라 Python 객체 오버헤드가 포함된다.
- 따라서 발표에서는 절대적인 시스템 메모리라기보다, 같은 Python 구현 안에서의 상대 비교 지표로 해석한다.
- 빈 필터에서는 `n_items = 0`이고 `bits_per_item = null`로 반환한다.

`false_positive_rate()` response:

```json
{
  "theoretical": 0.0098,
  "measured": 0.0102,
  "queries_tested": 1000
}
```

SuRF의 FPR 해석:

> SuRF의 FPR은 단순 point membership 성능만을 보기 위한 지표가 아니라, prefix/range query에서 approximate result가 얼마나 오탐을 만들 수 있는지를 보는 지표로 해석한다.

---

## 8. Experiment Metrics

이 프로젝트는 filter 자료구조 비교이므로 정렬 알고리즘용 지표를 사용하지 않는다.

사용하는 지표:

| Metric | Meaning |
| --- | --- |
| `memory_usage()` | 메모리 사용량 |
| `false_positive_rate()` | false positive rate |
| `_time_us` | 각 query/update의 latency |
| `insert/delete support` | 동적 업데이트 가능 여부 |
| `prefix/range support` | 자동완성 및 구간 조회 지원 여부 |
| `exact` / `may_contain_false_positive` | exact 구조와 approximate 구조 구분 |

사용하지 않는 지표:

| Sorting Metric | Why Not Used |
| --- | --- |
| comparison count | 정렬 알고리즘 지표라 membership filter와 맞지 않음 |
| swap count | 정렬 알고리즘 지표라 filter 비교와 무관 |
| stability | 정렬 결과의 상대 순서 보존 여부라 filter ADT와 무관 |

발표 주의:

> Bloom Filter 예시 페이지에 comparison count, stability 같은 표현이 있더라도, 이 프로젝트에서는 filter에 맞는 지표인 FPR, memory, latency, delete support, prefix/range support만 사용한다.

---

## 9. Experiment Call Groups

| Purpose | MCP Calls | What It Shows |
| --- | --- | --- |
| Membership accuracy | `contains("apple")`, `contains("applf")` | 존재 키워드와 없는 오타 키워드 구분 |
| Dynamic insertion | `insert("applepay")` -> `contains("applepay")` | 사전에 없던 새 키워드 등록 가능 여부 |
| Deletion | `delete("appstore")` -> `contains("appstore")` | 만료 키워드 제거 가능 여부 |
| Autocomplete | `prefix_query("app")` | SuRF의 prefix query 장점 |
| Range lookup | `range_query("app", "banana")` | sorted keyword range query |
| Operation cost | `memory_usage()`, `false_positive_rate()`, 각 호출의 `_time_us` | memory, FPR, latency 비교 |

Business action과 ADT의 연결:

| Business Action | ADT Method |
| --- | --- |
| 새 트렌딩 키워드 추가 | `insert(x)` |
| 새 금칙어 등록 | `insert(x)` |
| 등록된 키워드 확인 | `contains(x)` |
| 금칙어 여부 확인 | `contains(x)` |
| 만료 키워드 제거 | `delete(x)` |
| 금칙어 해제 | `delete(x)` |

---

## 10. Dataset Design

Capture keywords:

```text
app
apple
application
appstore
banana
bank
baseball
camera
campus
car
```

주의:

- `applepay`는 build data에 넣지 않는다.
- `applepay`는 새 트렌딩 키워드 insert 실험에 사용한다.

Measurement build data는 위 10개 keyword를 포함한 1,000개 keyword로 구성한다.
예시는 다음과 같다.

```text
app, apple, application, appstore
banana, bank, baseball, camera, campus, car

app_000 ... app_245
ban_000 ... ban_146
cam_000 ... cam_146
dev_000 ... dev_149
game_000 ... game_149
music_000 ... music_149
```

Absent queries:

| Type | Count | Example | Purpose |
| --- | --- | --- | --- |
| Typo-like absent | 500 | `applf`, `bananna`, `cammera` | 사용자 오타 상황 |
| Random absent | 500 | `xyz_001`, `qwerty_042` | 무작위 미존재 키 |

Prefix queries:

| Type | Queries |
| --- | --- |
| Main prefixes | `app`, `ban`, `cam`, `dev`, `game`, `music` |
| Partial prefixes | `ap`, `ba`, `ca`, `de`, `ga`, `mu` |
| Missing prefixes | `xyz`, `qwe` |

---

## 11. Team Member LLM Experiment Prompt

각 팀원은 `{SERVER_NAME}`만 자기 서버 이름으로 바꿔서 사용한다.

```text
{SERVER_NAME} 서버를 실제 MCP tool로 호출해서 실험해줘.

실험 시나리오:
Search Keyword Dictionary Management

검색 플랫폼은 키워드 사전을 운영합니다.
키워드가 이미 등록되어 있는지 확인하고,
새로운 트렌딩 키워드를 추가하며,
만료된 키워드를 삭제해야 합니다.
또한 자동완성을 위해 prefix query가 필요하고,
정렬된 키워드 구간 조회를 위해 range query도 사용할 수 있습니다.

먼저 아래 데이터셋을 build해줘.

build_items:
[
  "app",
  "apple",
  "application",
  "appstore",
  "banana",
  "bank",
  "baseball",
  "camera",
  "campus",
  "car"
]

config:
{
  "target_fpr": 0.01,
  "expected_items": 10,
  "fingerprint_bits": 12,
  "bucket_size": 4,
  "counter_bits": 4,
  "suffix_bits": 8,
  "trie_depth": 8
}

그 다음 아래 실험을 순서대로 실제 MCP tool로 호출해줘.

Experiment 1. Membership accuracy
1. contains("apple")
2. contains("applf")

Experiment 2. Dynamic update
3. insert("applepay")
4. contains("applepay")

Experiment 3. Deletion
5. delete("appstore")
6. contains("appstore")

Experiment 4. Autocomplete / range query
7. prefix_query("app")
8. range_query("app", "banana")

Experiment 5. Operation cost
9. memory_usage()
10. false_positive_rate(["applf", "bananna", "cammera", "xyz_001", "qwerty_042"])

중요:
- 추측하지 말고 반드시 실제 {SERVER_NAME} MCP tool 호출 결과만 사용해줘.
- 지원하지 않는 기능은 N/A로 표시해줘.
- 결과는 아래 표 형식으로 정리해줘.

표 형식:
| Experiment | Method | Result | Supported | Exact | May False Positive | Time | Notes |

마지막에 이 서버가 검색 키워드 사전 운영 시나리오에서 어떤 장점과 한계를 가지는지 3줄로 요약해줘.
```

---

## 12. Slide Mapping

| Slide | Title | Content |
| --- | --- | --- |
| 1 | Title | Search Keyword Dictionary Management with MCP Filters |
| 2 | Scenario | 검색 플랫폼 키워드 사전 운영 |
| 3 | Five MCP Servers | 5개 MCP 서버 소개 |
| 4 | Common ADT | 공통 ADT 메서드와 지원 여부 |
| 5 | SuRF Simplified | 왜 SuRF가 prefix/range query를 지원하는지 설명 |
| 6 | Dataset Design | 1,000 build, 1,000 absent, 100 delete, prefix groups |
| 7 | MCP Call Flow / LLM Tool Capture | LLM이 MCP 서버를 호출하는 실제 화면 |
| 8 | Exp 1-2 Results | Memory + FPR 비교 |
| 9 | Exp 3 Results | Insert/Delete 비교 |
| 10 | Exp 4 Results | Prefix/Range, SuRF 장점 |
| 11 | LLM Summary / Conclusion | 상황별 추천과 trade-off 정리 |

10분 시간 배분:

| Part | Time |
| --- | --- |
| Scenario + servers | 2분 |
| ADT + SuRF 설명 | 2분 |
| Dataset + MCP capture | 2분 |
| Experiments 1-4 | 3분 |
| Conclusion | 1분 |

---

## 13. Conclusion Message

| Situation | Best Choice | Reason |
| --- | --- | --- |
| 정확성이 가장 중요함 | Naive Set | false positive 없음 |
| 메모리를 가장 아껴야 함 | Standard Bloom | compact bit array |
| 삭제가 자주 필요함 | Counting Bloom / Cuckoo | delete 지원 |
| 자동완성 prefix query가 필요함 | SuRF | trie 기반 prefix/range 지원 |
| 균형 잡힌 membership filter가 필요함 | Cuckoo | compact + delete 지원 |

마무리 멘트:

> 하나의 자료구조가 모든 상황에서 최고인 것은 아닙니다. 같은 ADT와 같은 데이터셋으로 5개 MCP 서버를 비교해보면, 각 필터는 정확성, 메모리, 삭제 지원, false positive, prefix/range query에서 서로 다른 trade-off를 가집니다.
