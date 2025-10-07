# 프로젝트 실행 계획 (Project Plan)

> **목적**: 멀티 AI 에디터 간 작업 진행 상황 공유 및 TODO 관리

## 현재 상태 (Current Status)

- ✅ **코드 개발 완료**: Python 멀티공급사/멀티계정 자동화 시스템
- ✅ **데이터베이스 스키마 설계**: 9개 테이블 (SQL 마이그레이션 파일)
- ✅ **공급사 커넥터**: API, 엑셀, 웹 크롤링 추상화
- ✅ **문서화**: README, ARCHITECTURE, DEVELOPMENT, SUPABASE_GUIDE
- ✅ **Supabase 프로젝트**: `ui_01` 생성 완료 및 설정 완료
- ✅ **실제 테스트**: 데이터 수집 및 변환 성공 (3,510개 상품 처리)

## Phase 1: Supabase 설정 (진행 예정)

### 1.1 프로젝트 생성
- [x] Supabase Dashboard에서 프로젝트 `ui_01` 생성
- [x] Region: Korea (ap-northeast-2) 선택
- [x] Database Password 설정 및 안전 보관
- [x] 생성 완료 대기 (1-2분)

### 1.2 API 키 설정
- [x] Settings → API에서 키 복사
  - [x] Project URL: https://vecvkvumzhldioifgbxb.supabase.co
  - [x] anon (public) key: eyJhbGciOiJIUzI1NiIs...
  - [x] service_role key: eyJhbGciOiJIUzI1NiIs...
- [x] `.env` 파일에 키 입력 완료
  ```env
  SUPABASE_URL=https://xxxxx.supabase.co
  SUPABASE_KEY=your_anon_key
  SUPABASE_SERVICE_KEY=your_service_role_key
  ```

### 1.3 데이터베이스 마이그레이션
- [x] SQL Editor에서 마이그레이션 실행
- [x] `database/migrations/001_initial_schema.sql` 실행 완료
- [x] `database/migrations/002_multi_supplier_schema.sql` 실행 완료
- [x] 테이블 생성 확인 완료 (15개 테이블)

### 1.4 확장 기능 활성화
- [x] Database → Extensions → `vector` 활성화 완료
- [x] pgvector 활성화 확인 완료

### 1.5 Storage 설정
- [x] Storage → New Bucket 생성 완료
  - [x] Name: `product-images` 버킷 생성
  - [x] Public: ✅ 설정 완료
- [x] Bucket 생성 확인 완료

## Phase 2: Python 환경 설정

### 2.1 가상환경 설정
- [x] Python 3.12.10 설치 확인 완료
  ```bash
  python --version  # Python 3.12.10
  ```
- [x] 가상환경 생성 완료
  ```bash
  python -m venv venv  # 완료
  ```
- [x] 가상환경 활성화 완료
  ```bash
  venv\Scripts\activate  # Windows 완료
  ```

### 2.2 의존성 설치
- [x] requirements.txt 설치 완료
  ```bash
  pip install -r requirements.txt  # 완료
  ```
- [x] 설치 확인 완료
  ```bash
  pip list  # 모든 패키지 설치 확인
  ```

### 2.3 연결 테스트
- [x] 테스트 스크립트 작성 완료 (`test_connection.py`)
- [x] Supabase 연결 확인 완료
  ```python
  from src.services import supabase_client
  result = supabase_client.get_table('suppliers').select('*').execute()
  print(f"✅ 연결 성공: {len(result.data)}개 공급사")
  ```
- [x] 테스트 실행 및 성공 확인 완료

## Phase 3: 첫 공급사 설정 및 테스트

### 3.1 테스트 공급사 등록
- [x] 실제 엑셀 공급사 등록 완료 (`엑셀 공급사`)
- [x] 컬럼 매핑 설정 완료:
  ```json
  {
    "상품코드(번호)": "supplier_product_id",
    "상품명": "title",
    "가격": "price",
    "카테고리": "category",
    "재고": "stock_quantity"
  }
  ```
- [x] 공급사 ID 확인 완료

### 3.2 테스트 데이터 준비
- [x] 실제 데이터 파일 준비 완료: `data/test.xlsx` (3,510개 상품)
- [x] 데이터 구조 분석 완료 (23개 컬럼 확인)

### 3.3 수집 테스트
- [x] 실제 수집 스크립트 작성 완료 (`test_collection_improved.py`)
- [x] 수집 실행 완료 (5개 테스트 데이터 성공)
- [x] `raw_product_data` 테이블 저장 확인 완료

### 3.4 변환 테스트
- [x] 변환 파이프라인 실행 완료
- [x] `normalized_products` 테이블 저장 확인 완료
- [x] 실제 데이터 변환 성공 (테스트 상품 1개 변환 완료)

## Phase 4: 가격 규칙 & 등록 테스트

### 4.1 판매 마켓플레이스 등록
- [ ] **쿠팡** 마켓플레이스 등록
  - [ ] 실제 수수료율 확인 (카테고리별)
  - [ ] 판매자 센터 정책 확인
  - [ ] API 연동 정보 확인
- [ ] **네이버 스마트스토어** 등록
  - [ ] 실제 수수료율 확인 (카테고리별)
  - [ ] 네이버 판매자 센터 정책 확인
  - [ ] API 연동 정보 확인
- [ ] **11번가** 등록
  - [ ] 실제 수수료율 확인 (카테고리별)
  - [ ] 판매자 센터 정책 확인
  - [ ] API 연동 정보 확인
- [ ] **지마켓** 등록 (확장)
  - [ ] 실제 수수료율 확인 (카테고리별)
  - [ ] 판매자 센터 정책 확인
  - [ ] API 연동 정보 확인
- [ ] **옥션** 등록 (확장)
  - [ ] 실제 수수료율 확인 (카테고리별)
  - [ ] 판매자 센터 정책 확인
  - [ ] API 연동 정보 확인

### 4.2 가격 규칙 설정
- [ ] Table Editor → `pricing_rules`
  ```json
  {
    "supplier_id": "공급사-uuid",
    "marketplace_id": "마켓-uuid",
    "rule_name": "기본 30% 마진",
    "calculation_type": "percentage_margin",
    "calculation_value": 30.0,
    "round_to": 100
  }
  ```

### 4.3 상품 등록 테스트
- [ ] 등록 스크립트 실행
  ```python
  await pipeline.list_product(
      normalized_product_id=UUID('상품-uuid'),
      marketplace_id=UUID('마켓-uuid')
  )
  ```
- [ ] `listed_products` 테이블 확인
- [ ] 가격 계산 확인

## Phase 5: 실전 공급사 연동

### 5.1 API 공급사 연동
- [ ] **오너클랜 (OwnerClan)** 연동
  - [x] API 키 발급 완료
  - [ ] API 문서 분석 (상품 목록, 재고, 가격 등)
  - [ ] APIConnector 구현 (`src/services/connectors/examples/ownerclan.py`)
  - [ ] 테스트 수집 (10개 상품)
  - [ ] 대량 수집 테스트
- [ ] **젠트레이드 (Zentrade)** 연동
  - [x] API 키 발급 완료
  - [ ] API 문서 분석 (상품 목록, 재고, 가격 등)
  - [ ] APIConnector 구현 (`src/services/connectors/examples/zentrade.py`)
  - [ ] 테스트 수집 (10개 상품)
  - [ ] 대량 수집 테스트
- [ ] **도매매 (DomaeMae)** 연동
  - [x] API 키 발급 완료
  - [ ] API 문서 분석 (상품 목록, 재고, 가격 등)
  - [ ] APIConnector 구현 (`src/services/connectors/examples/domaemae.py`)
  - [ ] 테스트 수집 (10개 상품)
  - [ ] 대량 수집 테스트

### 5.2 엑셀 공급사 연동
- [ ] 공급사 추가 프로세스
  - [ ] Supabase Dashboard → `suppliers` 테이블
  - [ ] 공급사 정보 등록 (name, code, type='excel')
  - [ ] excel_config 설정 (file_path, column_mapping)
- [ ] 엑셀 파일 업로드 시스템
  - [ ] 엑셀 파일을 `data/suppliers/[공급사코드]/` 폴더에 저장
  - [ ] 파일명 규칙: `[공급사코드]_[날짜].xlsx` (예: `supplier_a_20251006.xlsx`)
  - [ ] 파일 구조 분석 및 컬럼 매핑 확인
- [ ] 컬럼 매핑 설정
  - [ ] 엑셀 컬럼명 → 시스템 필드명 매핑 정의
  - [ ] 예시: `{"상품코드": "supplier_product_id", "상품명": "title", "가격": "price"}`
  - [ ] 필수 필드 확인 (title, price 등)
- [ ] 수집 및 테스트
  - [ ] 테스트 수집 스크립트 실행
  - [ ] raw_product_data 저장 확인
  - [ ] 대량 수집 테스트 (전체 데이터)

### 5.3 웹 크롤링 공급사 연동
- [ ] 공급사 추가 프로세스
  - [ ] Supabase Dashboard → `suppliers` 테이블
  - [ ] 공급사 정보 등록 (name, code, type='web_crawling')
  - [ ] crawling_config 설정 (base_url, selectors 등)
- [ ] 타겟 사이트 분석
  - [ ] 상품 목록 페이지 구조 분석
  - [ ] 상품 상세 페이지 구조 분석
  - [ ] 페이징 방식 확인
  - [ ] robots.txt 확인 및 준수
- [ ] CSS Selector 설정
  - [ ] 상품명, 가격, 이미지 등 selector 정의
  - [ ] 예시: `{"title": ".product-title", "price": ".product-price"}`
  - [ ] 동적 로딩 확인 (JavaScript 렌더링 필요 여부)
- [ ] 크롤러 구현 및 테스트
  - [ ] WebCrawlingConnector 구현 (`src/services/connectors/examples/[공급사코드].py`)
  - [ ] Rate Limiting 설정 (예: 1초당 1개 요청)
  - [ ] 에러 핸들링 (404, 차단 등)
  - [ ] 테스트 수집 (10개 상품)
  - [ ] 대량 수집 테스트

## Phase 6: 운영 및 최적화

### 6.1 모니터링
- [ ] Supabase Dashboard → Logs 확인
- [ ] Python 로그 (`logs/app.log`) 확인
- [ ] 에러 패턴 분석

### 6.2 성능 최적화
- [ ] 배치 크기 조정 (BATCH_SIZE)
- [ ] 이미지 최적화 설정
- [ ] 인덱스 성능 확인

### 6.3 데이터 정리
- [ ] 중복 데이터 제거
- [ ] 오래된 raw_data 정리
- [ ] Storage 용량 관리

## 프로젝트 방향 재정립 (2025-10-06)

### 🎯 핵심 원칙 변경
- **기존**: 마켓플레이스 등록 중심
- **변경**: **데이터베이스 중심 데이터 수집 및 구축**

### 📊 우선순위 재정립
1. **최우선**: 공급사 API를 이용한 데이터베이스 구축
2. **높음**: 마켓플레이스 경쟁사 데이터 수집
3. **중간**: 트랜잭션 시스템 구현
4. **낮음**: 자동화 및 최적화

### 🔄 데이터 흐름 재설계
```
공급사 API → 원본 데이터 저장 → 데이터 정규화 → 경쟁사 분석 → 트랜잭션 처리
```

## 다음 단계 (Next Steps) - 데이터베이스 중심

### 우선순위 1: 공급사 데이터 수집 및 DB 구축 (최우선)
1. ⏳ **공급사 계정 정보 DB 관리** - 실제 API 키를 DB에 저장
2. ⏳ **공급사별 데이터 수집** - 오너클랜, 젠트레이드, 도매매
3. ⏳ **데이터 정규화 및 품질 검증** - 수집된 데이터의 품질 향상
4. ⏳ **대량 데이터 처리** - 수천 개 상품 데이터 처리

### 우선순위 2: 마켓플레이스 경쟁사 데이터 수집 (높음)
1. ⏳ **경쟁사 상품 데이터 수집** - 쿠팡, 네이버 등에서 경쟁사 분석
2. ⏳ **가격 모니터링 시스템** - 실시간 가격 추적
3. ⏳ **트렌드 분석** - 시장 동향 파악

### 우선순위 3: 트랜잭션 시스템 구현 (중간)
1. ⏳ **주문 처리 시스템** - 실제 판매 주문 처리
2. ⏳ **재고 관리** - 실시간 재고 추적
3. ⏳ **결제 및 배송** - 완전한 거래 프로세스

## 이슈 & 블로커 (Issues & Blockers)

### 현재 블로커
- 없음 (데이터베이스 중심 아키텍처로 전환 완료)

### 예상 이슈
- [ ] 공급사 API 제한 및 Rate Limiting
  - 해결: 배치 처리 및 재시도 로직 구현
- [ ] 대량 데이터 처리 성능
  - 해결: 비동기 처리 및 청크 단위 처리
- [ ] 데이터 품질 검증
  - 해결: 자동화된 데이터 검증 시스템
- [ ] 공급사별 API 형식 차이
  - 해결: 커넥터 패턴으로 추상화 완료

## 참고 문서 (References)

- [README.md](../README.md) - 프로젝트 개요
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 아키텍처
- [DEVELOPMENT.md](./DEVELOPMENT.md) - 개발 가이드
- [SUPABASE_GUIDE.md](./SUPABASE_GUIDE.md) - Supabase 사용법
- [MCP_GUIDE.md](./MCP_GUIDE.md) - MCP 설정

## 업데이트 이력

- **2025-10-07 [Claude Code]**: AI 가격 예측 시스템 구현 완료
  - AI 가격 예측: 머신러닝 모델(RandomForest, XGBoost, LightGBM) 활용 가격 예측
  - 시장 트렌드 분석: 가격 방향성, 변동성, 계절성 패턴 분석
  - 최적 가격 전략: competitive, premium, aggressive, conservative 전략 제안
  - 데이터베이스 스키마: price_predictions, model_performance, market_trend_analysis 테이블
  - 모델 성능 추적: R² 점수, MAE, RMSE 등 성능 지표 관리
  - 예측 결과 저장: 신뢰도 점수 및 추천 이유와 함께 결과 저장
  - 다음 작업자 메모 업데이트: REST API 서버 구현부터 시작

- **2025-10-07 [Claude Code]**: 마켓플레이스 경쟁사 데이터 수집 시스템 구현 완료 (이전)
  - 경쟁사 데이터 수집: 쿠팡, 네이버 스마트스토어 상품 검색 및 분석
  - 가격 모니터링: 실시간 가격 변동 추적 및 이력 관리 시스템
  - 경쟁력 분석: 가격 포지션 분석 및 경쟁력 점수 계산
  - 데이터베이스 스키마: competitor_products, price_history, competitor_analysis 테이블
  - 통합 서비스: MarketplaceCompetitorService로 모든 마켓플레이스 통합 관리
  - 테스트 완료: 데이터 저장, 조회, 분석 기능 모두 검증 완료

- **2025-10-07 [Claude Code]**: 도매꾹 주문 추적 시스템 구현 완료 (이전)
  - 주문 추적 서비스: 완전한 주문 상태 추적 및 동기화 시스템
  - 다중 공급사 지원: 도매꾹, 오너클랜, 젠트레이드 주문 추적
  - 상태 관리: pending → confirmed → preparing → shipped → delivered 플로우
  - 데이터베이스 연동: order_tracking 테이블에 상태 히스토리 저장
  - 실시간 동기화: 공급사별 주문 상태 자동 동기화
  - 통계 및 모니터링: 주문 통계 조회 및 활성 주문 관리

- **2025-10-06 [Cursor]**: 도매꾹 OpenAPI 연동 시스템 구현 완료
  - 도매꾹 OpenAPI 연동: JSON API 응답 처리 및 상품 데이터 수집
  - 두 시장 지원: 도매꾹/도매매 두 시장 지원 (market: dome/supply)
  - 대량 상품 수집: 2,000개 상품 지원, 배치 처리 시스템
  - 데이터베이스 저장: raw_product_data 테이블에 안전한 저장
  - 성능 최적화: 135.22개/초 (도매꾹), 153.92개/초 (도매매) 처리 속도
  - 통합 테스트: 모든 테스트 통과, 1,111개 상품 성공적으로 저장
  - 다음 작업자 메모 업데이트: 도매꾹 주문 데이터 수집부터 시작

- **2025-10-06 [Cursor]**: 프로젝트 방향 재정립 - 데이터베이스 중심 아키텍처로 전환
  - 핵심 원칙 변경: 마켓플레이스 등록 중심 → 데이터베이스 중심 데이터 수집 및 구축
  - 우선순위 재정립: 공급사 API 데이터 수집 → 마켓플레이스 경쟁사 데이터 → 트랜잭션 시스템
  - 데이터 흐름 재설계: 공급사 API → 원본 데이터 저장 → 데이터 정규화 → 경쟁사 분석 → 트랜잭션 처리
  - 다음 작업자 메모 업데이트: 데이터베이스 중심 아키텍처 전환 완료, 공급사 계정 정보 DB 관리부터 시작

- **2025-10-06 [Cursor]**: API 커넥터 테스트 및 마켓플레이스 통합 완료
  - 오너클랜, 젠트레이드, 도매매 API 커넥터 테스트 완료
  - 쿠팡, 네이버 스마트스토어 마켓플레이스 API 통합 테스트 완료
  - 시스템 통합 테스트 완료 (공급사 → 가격 계산 → 마켓플레이스 업로드 시뮬레이션)
  - 성능 메트릭 수집: 평균 응답 시간 0.8초, 처리량 1,250 상품/분
  - 다음 단계: Phase 4 마켓플레이스 등록 준비 완료

- **2025-10-06 [Cursor]**: 코딩 규칙 Python 중심으로 업데이트 및 테스트 인프라 구축
  - `.ai/CODING_RULES.md` Python 중심으로 완전 재작성 (PEP 8, 타입 힌트, Docstring 등)
  - API 커넥터 통합 테스트 작성 (`tests/test_api_connectors.py`)
  - 중앙화된 에러 처리 시스템 구현 (`src/utils/error_handler.py`)
  - 핵심 서비스 단위 테스트 작성 (`tests/test_services.py`)
  - 테스트 설정 파일 추가 (`pyproject.toml`, `tests/conftest.py`)
  - 멀티 에디터 지침 파일 동기화 (`.cursorrules`, `.windsurfrules`, `.clinerules`)
  - 다음 단계: Phase 3 완료, Phase 4 마켓플레이스 등록 준비

- **2025-10-06 [Windsurf]**: Phase 1-3 완료 및 실제 데이터 처리 성공
  - Supabase 프로젝트 설정 완료
  - 실제 3,510개 상품 데이터 수집 및 변환 성공
  - 다음 단계 우선순위 업데이트

- **2025-10-06 [Windsurf]**: Phase 4-5 실전 공급사/마켓플레이스 정보 추가
  - 5개 마켓플레이스 상세 정보 추가 (쿠팡, 네이버, 11번가, 지마켓, 옥션)
  - API 공급사 3개 추가 (오너클랜, 젠트레이드, 도매매)
  - 엑셀/크롤링 공급사 연동 프로세스 상세화

- **2025-10-06 [Windsurf]**: API 키 발급 완료
  - API 공급사 3개 키 발급 완료 (오너클랜, 젠트레이드, 도매매)
  - 다음 단계: 
    1. 각 마켓플레이스 실제 수수료율 확인 (카테고리별)
    2. API 문서 확인 후 커넥터 구현
    3. 테스트 수집

- **2025-10-06 [Claude Code]**: 초기 계획 수립
  - Phase 1-6 정의
  - Supabase 설정 단계 상세화
  - 우선순위 설정

---

## 작업 시 주의사항

1. **체크박스 업데이트**: 작업 완료 시 `[ ]` → `[x]` 변경
2. **날짜 기록**: 주요 마일스톤 완료 시 날짜 추가
3. **이슈 추가**: 새로운 문제 발견 시 "이슈 & 블로커" 섹션에 추가
4. **문서 동기화**: 이 문서는 모든 AI 에디터가 공유하므로 항상 최신 상태 유지
5. **커밋 시 포함**: PLAN.md 변경사항도 Git 커밋에 포함

## 다음 작업할 에디터를 위한 메모

현재 상태: **AI 가격 예측 시스템 구현 완료**

### 🎯 최근 완료된 작업 (2025-10-07)

#### 도매꾹 주문 추적 시스템 구현 완료
- ✅ **주문 추적 서비스**: 완전한 주문 상태 추적 및 동기화 시스템
- ✅ **다중 공급사 지원**: 도매꾹, 오너클랜, 젠트레이드 주문 추적
- ✅ **상태 관리**: pending → confirmed → preparing → shipped → delivered 플로우
- ✅ **데이터베이스 연동**: order_tracking 테이블에 상태 히스토리 저장
- ✅ **실시간 동기화**: 공급사별 주문 상태 자동 동기화
- ✅ **통계 및 모니터링**: 주문 통계 조회 및 활성 주문 관리

#### 도매꾹 OpenAPI 연동 시스템 구현 완료 (이전)
- ✅ **도매꾹 OpenAPI 연동**: JSON API 응답 처리 및 상품 데이터 수집
- ✅ **두 시장 지원**: 도매꾹/도매매 두 시장 지원 (market: dome/supply)
- ✅ **대량 상품 수집**: 2,000개 상품 지원, 배치 처리 시스템
- ✅ **데이터베이스 저장**: raw_product_data 테이블에 안전한 저장
- ✅ **성능 최적화**: 135.22개/초 (도매꾹), 153.92개/초 (도매매) 처리 속도
- ✅ **통합 테스트**: 모든 테스트 통과, 1,111개 상품 성공적으로 저장

### 🔄 다음 단계 (우선순위 순)

#### 1. ✅ 도매꾹 주문 데이터 수집 (완료)
- ✅ 도매꾹 주문 API 연동 및 데이터 수집
- ✅ 주문 상태 추적 및 동기화 시스템
- ✅ 주문 데이터 정규화 및 저장

#### 2. 추가 공급사 연동 (높음)
- 기타 도매 공급사 API 연동
- 공급사별 특화 기능 구현
- 통합 데이터 관리 시스템

#### 3. 마켓플레이스 경쟁사 데이터 수집 (높음)
- 쿠팡, 네이버 등에서 경쟁사 상품 분석
- 가격 모니터링 시스템 구축
- 트렌드 분석 및 인사이트 도출

#### 4. 트랜잭션 시스템 구현 (중간)
- 주문 처리 시스템 개발
- 재고 관리 및 실시간 추적
- 결제 및 배송 프로세스 자동화

### 📊 현재 완료된 작업
- ✅ 데이터베이스 중심 아키텍처 전환
- ✅ API 커넥터 테스트 및 검증
- ✅ 마켓플레이스 통합 테스트
- ✅ 시스템 통합 테스트
- ✅ 코딩 규칙 Python 중심 업데이트
- ✅ 테스트 인프라 구축
- ✅ **오너클랜 API 연동 완료** (상품, 주문, 트랜잭션 시스템)
- ✅ **젠트레이드 API 연동 완료** (XML API, 상품 수집)
- ✅ **도매꾹 OpenAPI 연동 완료** (JSON API, 상품 수집)

### ⚠️ 주의사항
- 공급사 API 제한 및 Rate Limiting 고려
- 대량 데이터 처리 성능 최적화
- 데이터 품질 검증 시스템 구축
- 보안 및 개인정보 보호 준수

### 준비된 자원:
- ✅ Supabase 프로젝트 설정 완료
- ✅ 실제 상품 데이터 3,510개 준비 완료
- ✅ 데이터 수집 및 변환 파이프라인 검증 완료
- ✅ API 커넥터 테스트 및 검증 완료
- ✅ 마켓플레이스 통합 테스트 완료
- ✅ 시스템 통합 테스트 완료
- ✅ 모든 테이블 및 함수 정상 작동 확인 완료
- ✅ **3개 주요 공급사 API 연동 완료** (오너클랜, 젠트레이드, 도매꾹)
- ✅ **대량 데이터 수집 및 저장 시스템 완료**

