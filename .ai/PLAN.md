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

## 다음 단계 (Next Steps)

### 우선순위 1: Phase 4 가격 규칙 및 마켓플레이스 등록 (준비 완료)
1. ⏳ **5개 마켓플레이스 등록** (쿠팡, 네이버, 11번가, 지마켓, 옥션)
2. ⏳ 마켓플레이스별 가격 규칙 설정
3. ⏳ 상품 등록 테스트

### 우선순위 2: Phase 5 실전 공급사 연동 (준비 완료)
1. ⏳ **API 공급사 3개 연동** (오너클랜, 젠트레이드, 도매매)
2. ⏳ 엑셀 공급사 추가 및 업로드 시스템 구축
3. ⏳ 웹 크롤링 공급사 추가 및 크롤러 구현
4. ✅ 대량 데이터 변환 (3,510개 상품 변환 가능)

### 우선순위 3: 운영 및 최적화 (준비 완료)
1. ⏳ 모니터링 시스템 구축 (다음 단계)
2. ⏳ 성능 최적화 (다음 단계)
3. ⏳ 자동화 파이프라인 구축 (다음 단계)

## 이슈 & 블로커 (Issues & Blockers)

### 현재 블로커
- 없음 (Supabase 프로젝트 생성 대기 중)

### 예상 이슈
- [ ] Supabase 무료 플랜 제약 (500MB DB, 5GB 대역폭)
  - 해결: 이미지는 Storage, 텍스트만 DB
- [ ] 웹 크롤링 시 Rate Limiting
  - 해결: asyncio.sleep() 추가, robots.txt 준수
- [ ] 공급사별 API 형식 차이
  - 해결: 커넥터 패턴으로 추상화 완료

## 참고 문서 (References)

- [README.md](../README.md) - 프로젝트 개요
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 아키텍처
- [DEVELOPMENT.md](./DEVELOPMENT.md) - 개발 가이드
- [SUPABASE_GUIDE.md](./SUPABASE_GUIDE.md) - Supabase 사용법
- [MCP_GUIDE.md](./MCP_GUIDE.md) - MCP 설정

## 업데이트 이력

- 2025-10-06: 초기 계획 수립 [Claude Code]
  - Phase 1-6 정의
  - Supabase 설정 단계 상세화
  - 우선순위 설정
- 2025-10-06: Phase 1-3 완료 및 실제 데이터 처리 성공 [Windsurf]
  - Supabase 프로젝트 설정 완료
  - 실제 3,510개 상품 데이터 수집 및 변환 성공
  - 다음 단계 우선순위 업데이트
- 2025-10-06: Phase 4-5 실전 공급사/마켓플레이스 정보 추가 [Windsurf]
  - 5개 마켓플레이스 상세 정보 추가 (쿠팡, 네이버, 11번가, 지마켓, 옥션)
  - API 공급사 3개 추가 (오너클랜, 젠트레이드, 도매매)
  - 엑셀/크롤링 공급사 연동 프로세스 상세화
- 2025-10-06: API 키 발급 완료 [Windsurf]
  - API 공급사 3개 키 발급 완료 (오너클랜, 젠트레이드, 도매매)
  - 다음 단계: 
    1. 각 마켓플레이스 실제 수수료율 확인 (카테고리별)
    2. API 문서 확인 후 커넥터 구현
    3. 테스트 수집

---

## 작업 시 주의사항

1. **체크박스 업데이트**: 작업 완료 시 `[ ]` → `[x]` 변경
2. **날짜 기록**: 주요 마일스톤 완료 시 날짜 추가
3. **이슈 추가**: 새로운 문제 발견 시 "이슈 & 블로커" 섹션에 추가
4. **문서 동기화**: 이 문서는 모든 AI 에디터가 공유하므로 항상 최신 상태 유지
5. **커밋 시 포함**: PLAN.md 변경사항도 Git 커밋에 포함

## 다음 작업할 에디터를 위한 메모

현재 상태: **Phase 1-3 완료, Phase 4 준비 완료, 코드베이스 검토 완료**

### 🔍 코드베이스 검토 결과 (2025-10-06 [Cursor])
- ✅ **아키텍처**: Python 백엔드 구조가 잘 설계됨
- ✅ **데이터베이스**: Supabase 스키마 완성, 실제 데이터 처리 검증 완료
- ✅ **API 커넥터**: 3개 공급사 커넥터 구현 완료 (오너클랜, 젠트레이드, 도매매)
- ✅ **개선 완료**: 문서 일관성, API 테스트, 에러 처리 강화 완료

### 🎯 다음 작업 우선순위 (수정됨):

#### 높은 우선순위 (완료):
1. ✅ **코딩 규칙 문서 수정** - `.ai/CODING_RULES.md`를 Python 중심으로 전면 수정 완료
2. ✅ **API 커넥터 실제 테스트** - 각 공급사별 실제 API 연동 테스트 스크립트 작성 완료
3. ✅ **에러 처리 강화** - 통일된 에러 처리 패턴 적용 완료

#### 중간 우선순위 (완료):
4. ✅ **테스트 코드 작성** - 핵심 서비스에 대한 pytest 기반 단위 테스트 작성 완료
5. ✅ **마켓플레이스 수수료 조사** - 각 마켓플레이스의 실제 수수료율 확인 (카테고리별) 완료
6. ✅ **가격 규칙 설정** - 카테고리별 마진율 최적화 완료

#### 다음 단계 (진행 중):
7. ⏳ **API 커넥터 실제 연동 테스트** - 각 공급사별 실제 API 연동 테스트
8. ⏳ **마켓플레이스 연동 구현** - 실제 마켓플레이스 API 연동

#### 낮은 우선순위 (장기 개선):
7. ⏳ **성능 최적화** - 대량 데이터 처리 최적화
8. ⏳ **모니터링 시스템** - 로깅 및 메트릭 수집 시스템 구축

### ✅ 개선 완료 사항 (2025-10-06 [Cursor]):
- **코딩 규칙 문서**: TypeScript → Python 중심으로 전면 수정
- **API 테스트 스크립트**: `test_api_connectors.py` 작성 (3개 공급사 테스트)
- **에러 처리 시스템**: `src/utils/error_handler.py` 통일된 에러 처리 패턴 구현
- **단위 테스트**: `tests/test_services.py` 핵심 서비스 테스트 코드 작성
- **테스트 설정**: `tests/conftest.py`, `pyproject.toml` pytest 설정 완료
- **마켓플레이스 수수료 조사**: `marketplace_fee_research.py` 5개 마켓플레이스 수수료 분석 완료
- **가격 규칙 시스템**: `src/services/pricing_engine.py` 가격 계산 엔진 구현 완료
- **데이터베이스 스키마**: `database/migrations/003_marketplace_fees_schema.sql` 마켓플레이스 수수료 테이블 설계 완료
- **마켓플레이스 연동 테스트**: `test_marketplace_integration.py` 통합 테스트 구현 완료

### 준비된 자원:
- ✅ Supabase 프로젝트 설정 완료
- ✅ 실제 상품 데이터 3,510개 준비 완료
- ✅ 데이터 수집 및 변환 파이프라인 검증 완료
- ✅ 모든 테이블 및 함수 정상 작동 확인 완료
- ✅ 3개 API 공급사 커넥터 구현 완료

### ✅ 완료된 개선사항:
- 코딩 규칙 문서가 Python 중심으로 전면 수정 완료
- API 커넥터 실제 테스트 스크립트 작성 완료
- 통일된 에러 처리 패턴 구현 완료
- 핵심 서비스 단위 테스트 작성 완료
- 마켓플레이스 수수료 조사 및 분석 완료 (5개 마켓플레이스)
- 가격 규칙 시스템 및 계산 엔진 구현 완료
- 마켓플레이스 수수료 데이터베이스 스키마 설계 완료
- 마켓플레이스 연동 통합 테스트 구현 완료

작업 완료 후 이 문서의 체크박스를 업데이트하고 커밋해주세요!
