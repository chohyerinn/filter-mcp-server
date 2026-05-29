{서버 이름} mcp만 이용해줘.

0. 검색어 사전을 만들어서 키워드 app, apple, application, appstore, banana, bank, baseball, camera, campus, car 을 넣어줘.
1. "apple"이 등록되어 있는지 확인해줘.
2. "applf"가 등록되어 있는지 확인해줘.
3. 새 트렌드 검색어 "applepay"를 등록해줘.
4. "applepay"가 등록되어 있는지 확인해줘.
5. 오래된 검색어 "appstore"를 삭제해줘.
6. "appstore"가 아직 등록되어 있는지 다시 확인해줘.
7. "app"까지만 입력했을 때 자동완성 후보가 몇 개인지 확인해줘. 지원하지 않으면 unsupported라고 알려줘.
8. 사전식 순서로 "app" 이상, "banana" 미만의 검색어 묶음을 확인해줘. 지원하지 않으면 unsupported라고 알려줘.
9. 이 검색어 사전이 사용하는 메모리를 알려줘.
10. 없는 검색어를 있다고 착각할 가능성(false positive rate)을 알려줘.
11. "applepay" 삭제 후에 재검색하면 조회가 안 되는지 확인해줘. 삭제를 지원하지 않으면 unsupported라고 알려줘.

---

#LLM 분석

아래는 동일한 workload를 사용하여 측정한 5개 MCP 서버의 benchmark 결과야.

분석 대상:

* filter-naive
* filter-bloom
* filter-counting-bloom
* filter-cuckoo
* filter-surf

분석 규칙:

* 반드시 benchmark 결과만 사용
* unsupported 기능은 unsupported 그대로 유지
* benchmark 수치와 자료구조 특성을 연결해서 설명
* 단순 숫자 나열보다 trade-off 중심으로 설명

[여기에 benchmark 결과 붙여넣기]

다음을 분석해줘.

1. 각 자료구조의 동작 방식 차이
2. 왜 delete / prefix / range 지원 여부가 다른지
3. exact structure와 approximate structure의 차이
4. 각 workload에 적합한 구조
5. 각 구조의 장점과 한계
6. benchmark 결과에서 나타난 memory usage와 false positive 차이의 원인
7. 실제 검색 서비스에서 어떤 상황에 적합한지

마지막에 아래 표를 작성해줘.

| Structure      | Exact | False Positive | Delete | Prefix/Range | Best Use Case |
| -------------- | ----- | -------------- | ------ | ------------ | ------------- |
| Naive          |       |                |        |              |               |
| Bloom          |       |                |        |              |               |
| Counting Bloom |       |                |        |              |               |
| Cuckoo         |       |                |        |              |               |
| SuRF           |       |                |        |              |               |

그리고 마지막으로 아래 질문에 답해줘.

* 정확도가 가장 중요한 경우
* 메모리가 가장 중요한 경우
* 삭제가 필요한 경우
* 자동완성이 필요한 경우
* 가장 균형 잡힌 구조

각 경우에 가장 적합한 자료구조를 1개씩 추천하고 이유를 설명해.
