{서버 이름} mcp만 이용해줘.
0. 검색어 사전을 만들어서 키워드 app, apple, application, appstore, banana, bank, baseball, camera, campus, car 을 넣어줘.
1. apple
2. applf
3. 새 트렌드 검색어 "applepay"를 등록해줘.
4. applepay 
5. 오래된 검색어 "appstore"를 삭제해줘.
6. "appstore"가 아직 등록되어 있는지 다시 확인해줘.
7. "app"까지만 입력했어. 자동완성 후보가 몇 개인지 확인해줘.
8. 사전식 순서로 "app" 이상, "banana" 미만의 검색어 묶음을 확인해줘.
9. 이 검색어 사전이 사용하는 메모리를 알려줘.
10. 없는 검색어를 있다고 착각할 가능성(false positive rate)을 알려줘.
11. "applepay" 삭제 후에 재검색하면 조회 안돼?

---

#LLM 분석

아래는 동일한 workload를 5개의 MCP 서버로 실험한 결과이다.

분석 대상:

* filter-naive
* filter-bloom
* filter-counting-bloom
* filter-cuckoo
* filter-surf

중요:

* 아래 결과만 기반으로 분석해줘.
* unsupported는 unsupported 그대로 유지해줘.
* 단순 숫자 비교보다,
  왜 이런 차이가 발생하는지와
  자료구조 trade-off 중심으로 설명해줘.

[여기에 5개 서버 결과 붙여넣기]

다음을 분석해줘:

1. 각 자료구조의 동작 방식 차이
2. 왜 delete/prefix/range 지원 여부가 달라지는지
3. exact vs approximate 차이
4. 어떤 workload에 적합한지
5. 각 구조의 장점과 한계

마지막에 아래 표를 작성해줘.

| Structure | Exact | False Positive | Delete | Prefix/Range | Best Use Case |
| --------- | ----- | -------------- | ------ | ------------ | ------------- |
