# 아키텍처 문서 (Architecture)

## 개요
이 문서는 드롭쉬핑 대량등록 자동화 프로그램의 전체 아키텍처를 정의합니다.

## 프로젝트 타입
**Python 백엔드 자동화 시스템** (Supabase 기반)

## 프로젝트 구조

```
ui_01/
├── .ai/                    # AI 에디터 공유 문서
│   ├── DEVELOPMENT.md      # 메인 개발 가이드
│   ├── ARCHITECTURE.md     # 아키텍처 문서 (본 문서)
│   ├── CODING_RULES.md     # 코딩 규칙
│   ├── MCP_GUIDE.md        # MCP 설정 가이드
│   └── SUPABASE_GUIDE.md   # Supabase 사용 가이드
├── src/                    # Python 소스 코드
│   ├── config/             # 설정 (settings.py)
│   ├── models/             # 데이터 모델 (Pydantic)
│   ├── services/           # 비즈니스 로직
│   │   ├── supabase_client.py      # Supabase 클라이언트
│   │   ├── batch_upload.py         # 배치 업로드
│   │   └── image_processor.py      # 이미지 처리
│   └── utils/              # 유틸리티 함수
├── database/               # SQL 마이그레이션
│   └── migrations/         # 스키마 파일
├── tests/                  # 테스트 코드
├── requirements.txt        # Python 의존성
├── .python-version         # Python 버전 (3.12.10)
├── .env                    # 환경 변수 (Git 제외)
├── .env.example            # 환경 변수 템플릿
├── .cursorrules            # Cursor AI 설정
├── .windsurfrules          # Windsurf AI 설정
├── .clinerules             # Codex/Claude 설정
├── .editorconfig           # 공통 에디터 설정
└── .mcp.json               # MCP 서버 설정
```

## 시스템 아키텍처

### 기술 스택
- **언어**: Python 3.12.10
- **데이터베이스**: Supabase (PostgreSQL + pgvector)
- **스토리지**: Supabase Storage
- **실시간**: Supabase Realtime (WebSocket)
- **ORM**: Pydantic (데이터 검증)
- **이미지 처리**: Pillow

### 레이어 아키텍처

#### 1. Service Layer (비즈니스 로직)
- **위치**: `src/services/`
- **역할**: 핵심 비즈니스 로직 및 외부 API 통합
- **주요 서비스**:
  - `supabase_client.py`: Supabase 클라이언트 관리 (동기/비동기)
  - `database_service.py`: 범용 데이터베이스 CRUD 추상화 레이어
  - `batch_upload.py`: 대량 상품 배치 업로드
  - `image_processor.py`: 이미지 최적화 및 Storage 업로드
  - `collection_service.py`: API/엑셀/웹 크롤링 수집을 오케스트레이션
  - `product_pipeline.py`: raw_product_data → normalized_products 변환 파이프라인
  - `transaction_system.py`: 주문 생성·변경·취소를 담당하는 트랜잭션 허브
  - `payment_shipping_automation.py`: 결제/배송 자동화 워크플로
  - `supplier_credit_manager.py`: 공급사 적립금 결제 시스템 (크레딧 잔액·거래 관리)
  - `order_tracking_service.py`: 주문 상태 추적 및 업데이트 자동화
  - `marketplace_competitor_service.py`: 오픈마켓 경쟁 정보 수집/분석
  - `ai_price_prediction_service.py`: AI 기반 가격 예측 및 시장 분석 (ML 모델)
  - **공급사별 데이터 수집기**:
    - `ownerclan_data_collector.py`: 오너클랜 GraphQL API (allItems 쿼리)
    - `zentrade_data_collector.py`: 젠트레이드 XML API (POST 요청)
    - `domaemae_data_collector.py`: 도매꾹/도매매 키워드 검색 API

#### 2. Model Layer (데이터 모델)
- **위치**: `src/models/`
- **역할**: Pydantic 기반 데이터 검증 및 직렬화
- **주요 모델**:
  - `Product`: 상품 데이터
  - `ProductBatch`: 배치 업로드
  - `ProductImage`: 이미지 메타데이터

#### 3. Data Layer (데이터 접근)
- **위치**: `database/migrations/`
- **역할**: PostgreSQL 스키마 및 RLS 정책
- **주요 테이블**:
  - **상품 데이터**:
    - `suppliers`: 공급사 마스터 (3개: OwnerClan, Zentrade, Domaemae)
    - `supplier_accounts`: 공급사 API 계정 및 인증 정보 (JSONB)
    - `raw_product_data`: 원본 수집 데이터 (공급사별 JSON 원본 보존)
    - `normalized_products`: 정규화된 상품 데이터 (통합 스키마)
    - `products`: 상품 마스터 (레거시)
    - `upload_batches`: 업로드 배치 관리
  - **마켓플레이스 연동**:
    - `marketplaces`: 연동 쇼핑몰 (네이버, 쿠팡, 11번가 등)
    - `marketplace_accounts`: 마켓플레이스별 판매 계정
    - `product_mappings`: 상품-쇼핑몰 매핑
  - **거래 및 결제**:
    - `orders`: 주문 정보
    - `order_tracking`: 주문 상태 추적 (배송·처리 단계)
    - `supplier_points_balance`: 공급사별 적립금 잔액
    - `supplier_points_transactions`: 적립금 충전·사용 내역
    - `supplier_credits`: 공급사 크레딧 잔액 (레거시)
    - `credit_transactions`: 크레딧 거래 내역 (레거시)
  - **경쟁사 분석 및 AI**:
    - `competitor_products`: 경쟁사 상품 데이터 (쿠팡/네이버)
    - `price_predictions`: AI 가격 예측 결과
    - `market_trend_analysis`: 시장 트렌드 분석 결과
  - **이미지 및 메타데이터**:
    - `image_metadata`: 이미지 메타데이터 (Supabase Storage 연동)

#### 4. Configuration Layer (설정)
- **위치**: `src/config/`
- **역할**: 환경 변수 및 앱 설정 관리
- **파일**: `settings.py` (Pydantic Settings)

## Supabase 기능 활용

### 1. PostgreSQL Database
- **테이블**: 정규화된 관계형 스키마
- **RLS**: Row Level Security로 멀티 셀러 데이터 격리
- **Triggers**: 자동 업데이트 (updated_at, 배치 진행률)
- **Functions**: 시맨틱 검색 (`find_similar_products`)

### 2. pgvector (벡터 검색)
- **임베딩**: OpenAI ada-002 (1536 차원)
- **용도**: 유사 상품 매칭, 중복 감지
- **인덱스**: IVFFlat (코사인 유사도)

### 3. Storage API
- **버킷**: `product-images`
- **이미지 처리**: 자동 리사이징/최적화
- **CDN**: Public URL 생성
- **RLS**: 판매자별 접근 제어

### 4. Realtime
- **채널**: `upload-progress`
- **구독**: PostgreSQL Changes (UPDATE on upload_batches)
- **용도**: 실시간 진행 상황 모니터링

### 5. Edge Functions (향후)
- **언어**: TypeScript/Deno
- **용도**: 외부 API 통합, 웹훅 처리

## 데이터 흐름

### 공급사 데이터 수집 프로세스

#### 오너클랜 (OwnerClan) - GraphQL API
1. **인증** → JWT 토큰 발급 (30일 유효)
2. **1차 수집** → `allItems` 쿼리 (1000개씩 pagination)
3. **데이터 정규화** → 공통 포맷 변환
4. **DB 저장** → `raw_product_data` 테이블
5. **배치 완료** → 수집 상태 업데이트

#### 도매매 (Domaemae) - JSON API
1. **인증** → API Key 인증
2. **1차 수집** → `getItemList` (200개씩 기본 정보)
   - 키워드 검색 필수
   - 페이징으로 전체 수집
3. **DB 저장** → `raw_product_data` 테이블 (1차 데이터만)
4. **소싱 대기** → 사용자가 상품 선택
5. **2차 수집** → `getItemView` (100개씩 상세 정보)
   - 선택된 상품만 상세 조회
   - DB 업데이트 → 상세 정보 추가
6. **배치 완료** → 최종 상태 업데이트

**핵심 전략**: 1차 수집만 DB 저장 → 소싱 후 2차 수집 (DB 용량 절약, API 호출 최소화)

#### 젠트레이드 (Zentrade) - XML API
1. **인증** → API Key 인증
2. **데이터 수집** → XML 응답 파싱
3. **데이터 정규화** → 공통 포맷 변환
4. **DB 저장** → `raw_product_data` 테이블

### 대량 업로드 프로세스
1. **CSV 로드** → `BatchUploadService.load_from_csv()`
2. **배치 레코드 생성** → `upload_batches` 테이블
3. **청킹** → 500개씩 분할
4. **비동기 업로드** → `AsyncSupabaseClient.batch_insert()`
5. **진행 상황 업데이트** → Realtime 전송
6. **이미지 처리** → `ImageProcessor.upload_product_images()`
7. **배치 완료** → 최종 상태 업데이트

### 이미지 업로드 프로세스
1. **이미지 최적화** → Pillow 리사이징/압축
2. **Storage 업로드** → Supabase Storage API
3. **Public URL 생성** → CDN 경로
4. **메타데이터 저장** → `image_metadata` 테이블
5. **상품 연결** → `products.images` (JSONB)

## 디자인 패턴

### 1. Singleton Pattern
- **적용**: `SupabaseClient` (동기 클라이언트)
- **이유**: 연결 재사용, 리소스 절약

### 2. Context Manager Pattern
- **적용**: `AsyncSupabaseClient` (async with)
- **이유**: 자동 리소스 정리

### 3. Service Layer Pattern
- **적용**: 모든 비즈니스 로직
- **이유**: 관심사 분리, 테스트 용이성

### 4. Repository Pattern
- **적용**: 데이터 접근 추상화
- **이유**: 데이터 소스 변경 시 유연성

## 네이밍 규칙 (Python)
- **모듈**: snake_case (예: `batch_upload.py`)
- **클래스**: PascalCase (예: `BatchUploadService`)
- **함수/변수**: snake_case (예: `upload_batch()`)
- **상수**: UPPER_SNAKE_CASE (예: `BATCH_SIZE`)
- **Private**: _underscore prefix (예: `_update_batch_status()`)
- **Async 함수**: async def (명시적)

## 에러 핸들링
- 모든 비동기 작업에 try-catch 블록 사용
- 사용자 친화적 에러 메시지 표시
- 에러 로깅 시스템 구현

## 성능 최적화

### 배치 처리
- **청킹**: 500~1,000개씩 분할 처리
- **비동기 병렬**: asyncio.gather로 동시 업로드
- **PostgreSQL COPY**: 대량 삽입 시 REST API 대비 10~100배 빠름
- **Minimal Response**: 반환 데이터 최소화

### 이미지 최적화
- **리사이징**: Pillow LANCZOS 알고리즘
- **압축**: JPEG 품질 85% (용량 50% 절감)
- **포맷 통일**: WebP/PNG → JPEG 변환
- **썸네일**: 300x300 정사각형 크롭

### 데이터베이스
- **인덱스**: seller_id, status, category, embedding (IVFFlat)
- **RLS 최적화**: Service Key로 우회 (신뢰 서버만)
- **Connection Pooling**: Supabase Supavisor 활용

## 보안

### Row Level Security (RLS)
- **정책**: seller_id 기반 데이터 격리
- **적용 테이블**: sellers, products, upload_batches, product_mappings, image_metadata
- **Service Key**: 신뢰 서버에서만 RLS 우회

### 환경 변수 관리
- **민감 정보**: .env 파일 (Git 제외)
- **API 키**: SUPABASE_KEY, SUPABASE_SERVICE_KEY, OPENAI_API_KEY
- **템플릿**: .env.example 제공

### Storage 보안
- **RLS 정책**: 판매자별 업로드/다운로드 권한
- **Private Bucket**: 인증된 사용자만 접근
- **Signed URLs**: 임시 접근 URL 생성

### 입력 검증
- **Pydantic**: 데이터 모델 자동 검증
- **SQL Injection**: Parameterized queries 사용
- **이미지 검증**: 포맷, 크기, MIME 타입 체크

## 확장성

### 모듈식 아키텍처
- **Service Layer**: 독립적인 비즈니스 로직
- **Plugin Pattern**: 새로운 마켓플레이스 쉽게 추가
- **Interface**: ABC 기반 추상화

### 스케일업 전략
1. **데이터베이스**: Supabase Pro (더 큰 DB, PITR 백업)
2. **Edge Functions**: 외부 API 통합 (TypeScript)
3. **멀티 리전**: Supabase 리전 복제
4. **Worker Pool**: Celery/RQ로 비동기 작업 분산
5. **Cache**: Redis 도입 (중복 쿼리 캐싱)

### 마켓플레이스 확장
- **추상 인터페이스**: `MarketplaceConnector` ABC
- **구현체**: Naver SmartStore, Coupang, 11번가 등
- **설정**: marketplace 테이블에 credentials 저장

## 모니터링 및 로깅

### 로깅
- **라이브러리**: Loguru
- **레벨**: DEBUG, INFO, WARNING, ERROR
- **저장**: `logs/app.log` (로테이션)
- **외부 서비스**: Sentry (에러 트래킹)

### 메트릭
- **배치 통계**: 성공/실패 건수, 처리 시간
- **이미지 처리**: 최적화율, 업로드 속도
- **데이터베이스**: 쿼리 성능 (Supabase Dashboard)

## 테스트 전략

### 단위 테스트 (pytest)
- **Service Layer**: 모든 public 메서드 테스트
- **Model Layer**: Pydantic 검증 테스트
- **커버리지**: 80% 이상 유지

### 통합 테스트
- **Supabase**: 실제 DB 연결 테스트 (테스트 프로젝트)
- **Storage**: 이미지 업로드/다운로드
- **Realtime**: WebSocket 구독

### 부하 테스트
- **대량 데이터**: 10,000개 상품 배치 업로드
- **동시성**: 10개 배치 동시 실행
- **성능 측정**: 처리 시간, 메모리 사용량

## 업데이트 이력
- 2025-10-06: 초기 문서 생성 [Claude Code]
- 2025-10-06: Python 백엔드 아키텍처로 전환, Supabase 기능 상세화 [Claude Code]
