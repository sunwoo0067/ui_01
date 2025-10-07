# 배치 수집 작업 분석 결과 (2025-10-07)

## 개요
공급사별 대량상품 데이터를 효율적으로 수집하는 배치 수집 현황을 정리하고 차후 과제를 제시합니다.

## 공급사 상세 진행 현황

| 공급사 | 수집 방식 | 진행 상태 | 현재 | 목표 | 노트 |
|--------|-----------|-----------|------|------|------|
| **젠트레이드** | XML API (전체) | 완료 (재수집 필요 시) | 3,510개 | 3,510개 | 3,510개 전체 반환 확보 |
| **오너클랜** | allItems GraphQL | 준비 중 (커서 페이징 구현 필요) | 전체 조회 됨 | 60,000개 이상 | 커서 페이징 대용량/페이지네이션 구현 진행 중 |
| **도매꾹(dome)** | 키워드 검색 | 준비 중 (키워드 확보 필요) | 1,000개 | 20,000개 | 판매처/카테고리 복합 검색 필요 |
| **도매매(supply)** | 키워드 검색 | 준비 대기 (키워드 리스트 작성) | 0개 | 10,000개 | 키워드 작성 후 API 확보 계획 |
| **합계** | - | - | 4,510개 + 오너클랜 조회 됨 | 100,000개 | 오너클랜 전체 커서 조회 단계에서 완료 |

## 도매꾹/도매매 API 분석
- [완료 예] `getCategoryList` 호출 시 404 UNKNOWN_SERVICE 에러 → API mode 번호 검색 후 해결책 필요
- [완료 예] 카테고리(`ca`) 검색으로 필터링만 결과가 0건 반환 → 카테고리보다는 키워드 확보 후 샘플 응답 조회 예정
- [완료 예] 키워드(`kw`) 검색 API (`sz=200`) 활용 → 페이징/중복 제거 확보 후 로그 수집 예정
- [완료 예] 판매처 ID(`id`) 검색 시 실제 상품 확인 → 공급처 판매처 리스트 작성 예정
- [완료] JSON 응답 확보 (`list.item`, `numberOfItems`) 파싱 처리 완료

## 오너클랜 GraphQL 분석
- [준비 중] `allItems(first: 1000)` + 페이지네이션(`hasNextPage`) 처리 → cursor 변수 전체 반환 구현
- [준비 중] `status="available"` 필터링 처리 → ACTIVE/SELLING 속성값 조회 후 가져옴
- [준비 중] `category { key, name }`, `images(size: large)`, `boxQuantity` 필수 필드 확보 +
  응답 반환 정보 정리

## 젠트레이드 XML 분석
- [완료] POST 요청 + 응답 인코딩 처리 (EUC-KR 인코딩)
- [완료] 3,510개 전체 배치 수집 완료 (response header 기준 `numberOfItems` 확보)

## 코드 수정 내역
- `src/services/domaemae_data_collector.py`: `list.item`, `numberOfItems` 파싱 JSON 확보 정리
- `collect_ownerclan_batch_full.py`: `status="available"`, `category { key, name }`, `images(size: large)` 쿼리 수정 + pagination 처리

## 차후 과제
1. **도매꾹/도매매 키워드 리스트 마련하기**
   - 30~50개 주요 키워드 작성 (의류, 잡화, 카테고리번호 등)
   - 카테고리번호/판매처 ID 복합 검색 병행으로 확보
2. **오너클랜 배치 수집 완료**
   - 페이지네이션 커서 프로세싱 후 cursor 반환 구현
   - 전체 데이터셋을 일괄배치로 단계별 수집 예정
3. **키워드 배치 수집 구현**
   - `sz=200` 파싱 페이징/중복 제거 처리
   - API 호출 간격 응답 분석 후 로그 수집 예정
4. **데이터 정규화 및 검증**
   - ProductPipeline 처리 필터를 활용
   - `normalized_products` 테이블 중복/누락 처리 예정

## 스크립트 맵핑
- `collect_ownerclan_batch_full.py` - 오너클랜 전체 배치
- `collect_domaemae_by_item_numbers.py` - 도매매 키워드 배치 (스크립트 준비)
- `check_collection_status.py` - 전체 현황 확인
- `get_real_category_list.py` - `getCategoryList` 확보/해결책 검증
- `test_domaemae_official_example.py` - 공식 API 응답 테스트

## 정리 필요
- 오너클랜 전체 페이지네이션/재업데이트 커서 조회 완료
- 도매꾹/도매매 API Rate Limit 반복 호출 간격 예정
- 키워드 수집 목록(Excel/CSV) 파일 작성 예정

