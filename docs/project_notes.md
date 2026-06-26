# Project Notes

## Why I built this

Bloom Filter, Counting Bloom Filter, Cuckoo Filter, SuRF는 모두 “집합에 어떤 값이 있는지 빠르게 확인한다”는 비슷한 목적을 가진다. 하지만 지원하는 연산과 trade-off는 다르다. 어떤 구조는 메모리를 적게 쓰는 대신 false positive가 있고, 어떤 구조는 삭제를 지원하지만 더 많은 공간이 필요하다.

이 프로젝트는 이런 차이를 MCP 도구 형태로 노출해서, AI 클라이언트가 같은 인터페이스로 여러 자료구조를 비교해볼 수 있게 만든 실습 프로젝트다.

## What was difficult

가장 어려웠던 부분은 서로 다른 자료구조를 같은 ADT처럼 보이게 만드는 것이었다. Bloom Filter는 삭제를 지원하지 않고, SuRF는 prefix/range query 쪽에 강점이 있다. 모든 서버가 같은 도구 이름을 갖게 하되, 지원하지 않는 연산은 명확히 실패하거나 제한 사항을 반환하도록 정리해야 했다.

또 하나 어려웠던 부분은 approximate structure의 결과를 설명하는 것이었다. false positive가 있는 구조는 `contains()`가 true라고 해서 실제로 반드시 존재한다는 뜻이 아니다. 이 차이를 README와 tool 설명에 분명히 남기는 것이 중요했다.

## Issues I ran into

### 1. 같은 연산 이름이 항상 같은 의미가 아니었다

`delete()`는 Exact Set이나 Counting Bloom, Cuckoo에서는 의미가 있지만 Bloom Filter에서는 지원되지 않는다. `range_query()`도 SuRF나 exact baseline에는 자연스럽지만 Bloom 계열에는 맞지 않는다.

그래서 모든 서버에 공통 tool을 두되, 각 자료구조가 지원하지 않는 연산은 제한 사항을 문서화했다.

### 2. false positive를 어떻게 보여줄지 고민했다

approximate filter는 메모리를 줄이는 대신 존재하지 않는 값을 존재한다고 답할 수 있다. 단순히 `contains()` 결과만 보여주면 사용자가 정확한 set처럼 오해할 수 있다.

그래서 `false_positive_rate()`와 `memory_usage()`를 함께 두고, 정확도와 메모리 사용량을 같이 비교하도록 했다.

### 3. SuRF는 완전한 구현으로 가면 범위가 너무 커졌다

실제 SuRF는 LOUDS 기반 trie와 succinct structure가 필요해서 학기 프로젝트 범위에서는 너무 컸다. 그래서 simplified SuRF로 구현하고, README에 production SuRF가 아니라 교육용 단순화 구현이라고 명시했다.

## How I fixed them

- `build`, `insert`, `contains`, `delete`, `prefix_query`, `range_query`, `memory_usage`, `false_positive_rate`를 공통 tool 인터페이스로 정리했다.
- exact set baseline을 함께 두어 approximate filter 결과를 비교할 기준을 만들었다.
- 지원하지 않는 연산은 자료구조별 limitation으로 명확히 분리했다.
- false positive와 memory usage를 함께 보도록 README 표를 구성했다.
- simplified SuRF라는 점을 숨기지 않고 프로젝트 범위로 명시했다.

## What I learned

자료구조는 “더 좋다/나쁘다”보다 어떤 연산을 중요하게 보는지에 따라 선택이 달라진다는 걸 배웠다. Bloom Filter는 메모리 효율이 좋지만 삭제가 어렵고, Counting Bloom은 삭제를 지원하지만 더 많은 메모리가 필요하다. SuRF는 prefix/range query에는 맞지만 구현 복잡도가 크다.

또 MCP는 단순 API와 다르게, AI 클라이언트가 발견하고 호출할 수 있는 tool 설명이 중요하다는 것도 배웠다. 도구 이름과 입력/출력이 명확하지 않으면 AI가 잘못 호출할 수 있다.

## What I would improve next

- 각 filter별 benchmark 결과를 JSON/Markdown 리포트로 자동 저장하고 싶다.
- 더 큰 데이터셋에서 false positive rate와 latency를 비교하고 싶다.
- full SuRF 구현과 simplified SuRF의 차이를 더 명확히 실험해보고 싶다.
- Glama 같은 MCP 검증 환경에서 더 안정적으로 introspection이 통과되도록 Dockerfile과 example config를 다듬고 싶다.
