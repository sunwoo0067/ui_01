# 프로젝트 실행 계획 (Project Plan)

> **목적**: 멀티 AI 에디터 간 작업 진행 상황 공유 및 TODO 관리

## 현재 상태 (Current Status)

- ✅ **코드 개발 완료**: Python 멀티공급사/멀티계정 자동화 시스템
- ✅ **데이터베이스 스키마 설계**: 9개 테이블 (SQL 마이그레이션 파일)
- ✅ **공급사 커넥터**: API, 엑셀, 웹 크롤링 추상화
- ✅ **문서화**: README, ARCHITECTURE, DEVELOPMENT, SUPABASE_GUIDE
- ❌ **Supabase 프로젝트**: 아직 생성 안됨
- ❌ **실제 테스트**: 미진행

## Phase 1: Supabase 설정 (진행 예정)

### 1.1 프로젝트 생성
- [ ] Supabase Dashboard에서 프로젝트 `ui_01` 생성
- [ ] Region: Korea 또는 Singapore 선택
- [ ] Database Password 설정 및 안전 보관
- [ ] 생성 완료 대기 (1-2분)

### 1.2 API 키 설정
- [ ] Settings → API에서 키 복사
  - [ ] Project URL
  - [ ] anon (public) key
  - [ ] service_role key
- [ ] `.env` 파일에 키 입력
  ```env
  SUPABASE_URL=https://xxxxx.supabase.co
  SUPABASE_KEY=your_anon_key
  SUPABASE_SERVICE_KEY=your_service_role_key
  ```

### 1.3 데이터베이스 마이그레이션
- [ ] SQL Editor 열기
- [ ] `database/migrations/001_initial_schema.sql` 실행
- [ ] `database/migrations/002_multi_supplier_schema.sql` 실행
- [ ] 테이블 생성 확인 (Table Editor)

### 1.4 확장 기능 활성화
- [ ] Database → Extensions → `vector` Enable
- [ ] pgvector 활성화 확인

### 1.5 Storage 설정
- [ ] Storage → New Bucket
  - [ ] Name: `product-images`
  - [ ] Public: ✅
- [ ] Bucket 생성 확인

## Phase 2: Python 환경 설정

### 2.1 가상환경 설정
- [ ] Python 3.12.10 설치 확인
  ```bash
  python --version
  ```
- [ ] 가상환경 생성
  ```bash
  python -m venv venv
  ```
- [ ] 가상환경 활성화
  ```bash
  venv\Scripts\activate  # Windows
  source venv/bin/activate  # macOS/Linux
  ```

### 2.2 의존성 설치
- [ ] requirements.txt 설치
  ```bash
  pip install -r requirements.txt
  ```
- [ ] 설치 확인
  ```bash
  pip list
  ```

### 2.3 연결 테스트
- [ ] 테스트 스크립트 작성 (`test_connection.py`)
- [ ] Supabase 연결 확인
  ```python
  from src.services import supabase_client
  result = supabase_client.get_table('suppliers').select('*').execute()
  print(f"✅ 연결 성공: {len(result.data)}개 공급사")
  ```
- [ ] 테스트 실행 및 성공 확인

## Phase 3: 첫 공급사 설정 및 테스트

### 3.1 테스트 공급사 등록
- [ ] Supabase Dashboard → Table Editor → `suppliers`
- [ ] 테스트 데이터 삽입:
  ```json
  {
    "name": "테스트 엑셀 공급사",
    "code": "test_excel",
    "type": "excel",
    "excel_config": {
      "column_mapping": {
        "상품명": "title",
        "가격": "price",
        "재고": "stock_quantity"
      }
    }
  }
  ```
- [ ] 공급사 ID 복사

### 3.2 테스트 데이터 준비
- [ ] `test_products.xlsx` 파일 생성
  | 상품명 | 가격 | 재고 |
  |--------|------|------|
  | 테스트 상품 1 | 10000 | 100 |
  | 테스트 상품 2 | 20000 | 50 |
  | 테스트 상품 3 | 15000 | 75 |

### 3.3 수집 테스트
- [ ] 수집 스크립트 작성
  ```python
  from src.services import CollectionService
  service = CollectionService()
  result = await service.collect_from_excel(
      supplier_id=UUID('공급사-uuid'),
      file_path='test_products.xlsx'
  )
  ```
- [ ] 수집 실행
- [ ] `raw_product_data` 테이블 확인

### 3.4 변환 테스트
- [ ] 변환 파이프라인 실행
  ```python
  from src.services import ProductPipeline
  pipeline = ProductPipeline()
  await pipeline.process_all_unprocessed()
  ```
- [ ] `normalized_products` 테이블 확인

## Phase 4: 가격 규칙 & 등록 테스트

### 4.1 판매 마켓플레이스 등록
- [ ] Table Editor → `sales_marketplaces`
  ```json
  {
    "name": "테스트 마켓플레이스",
    "code": "test_marketplace",
    "commission_rate": 10.0
  }
  ```

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

### 5.1 네이버 스마트스토어 (선택사항)
- [ ] 네이버 개발자 센터에서 API 키 발급
- [ ] 공급사 등록 (type: api)
- [ ] 커넥터 테스트

### 5.2 엑셀 공급사
- [ ] 실제 공급사 엑셀 파일 분석
- [ ] column_mapping 설정
- [ ] 공급사 등록
- [ ] 대량 수집 테스트

### 5.3 웹 크롤링 공급사 (선택사항)
- [ ] 타겟 사이트 분석
- [ ] selectors 설정
- [ ] 크롤러 테스트
- [ ] robots.txt 준수 확인

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

### 우선순위 1: Supabase 프로젝트 설정
1. ☐ 프로젝트 생성
2. ☐ API 키 설정
3. ☐ 마이그레이션 실행

### 우선순위 2: 첫 테스트 실행
1. ☐ Python 환경 설정
2. ☐ 연결 테스트
3. ☐ 엑셀 수집 테스트

### 우선순위 3: 실전 데이터
1. ☐ 실제 공급사 연동
2. ☐ 대량 데이터 처리
3. ☐ 마켓플레이스 등록

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

---

## 작업 시 주의사항

1. **체크박스 업데이트**: 작업 완료 시 `[ ]` → `[x]` 변경
2. **날짜 기록**: 주요 마일스톤 완료 시 날짜 추가
3. **이슈 추가**: 새로운 문제 발견 시 "이슈 & 블로커" 섹션에 추가
4. **문서 동기화**: 이 문서는 모든 AI 에디터가 공유하므로 항상 최신 상태 유지
5. **커밋 시 포함**: PLAN.md 변경사항도 Git 커밋에 포함

## 다음 작업할 에디터를 위한 메모

현재 상태: **Supabase 프로젝트 생성 대기 중**

다음 작업:
1. https://supabase.com/dashboard 에서 `ui_01` 프로젝트 생성
2. API 키 복사 후 `.env` 파일 업데이트
3. SQL 마이그레이션 실행

작업 완료 후 이 문서의 체크박스를 업데이트하고 커밋해주세요!
