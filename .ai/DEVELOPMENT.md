# 개발 문서 (Development Guide)

## 프로젝트 개요
이 문서는 Claude Code, Codex, Cursor, Windsurf 등 여러 AI 에디터를 사용한 멀티 에디터 개발 환경의 중앙 참조 문서입니다.

## 프로젝트 정보
- **프로젝트명**: 드롭쉬핑 멀티공급사/멀티계정 자동화 시스템
- **프로젝트 타입**: Python 백엔드 자동화 (개인용, 배포 없음)
- **현재 상태**: **Phase 3 진행 중 (90% 완료) - 공급사 결제·거래 정규화 단계 완료**
- **개발 환경**: Multi-AI Editor (Claude Code, Cursor, Windsurf, Codex/Cline)
- **언어**: Python 3.12.10
- **데이터베이스**: Supabase (PostgreSQL + pgvector)
- **코드베이스 규모**: 550개 Python 파일, 171,064행 실행 코드, 10개 SQL 마이그레이션 2,699행

## 핵심 원칙

### 1. 일관성 (Consistency)
- 모든 AI 에디터는 이 문서를 참조하여 동일한 컨텍스트로 작업합니다
- 코드 스타일, 네이밍 규칙, 아키텍처 패턴을 엄격히 준수합니다
- 변경사항은 반드시 이 문서에 반영합니다

### 2. 투명성 (Transparency)
- 각 AI 에디터가 수행한 작업은 커밋 메시지에 명시합니다
- 중요한 의사결정은 문서화합니다

### 3. 협업 (Collaboration)
- 에디터 간 충돌을 최소화하기 위해 명확한 역할 분담을 권장합니다
- Git을 통한 버전 관리로 모든 변경사항을 추적합니다

## 핵심 기능

### 1. 멀티공급사 지원
- **3가지 수집 방식**: API, 엑셀, 웹 크롤링
- **원본 데이터 보존**: JSONB 형식으로 공급사별 데이터 원본 저장
- **실제 테스트 완료**: Excel 파일 3,510개 상품 데이터 수집 성공
- **커넥터 추상화**: 공급사별 API 형식 차이 자동 처리

### 2. 상품 처리 파이프라인
```
수집 → 원본 저장 → 변환 → 정규화 → 가격 계산 → 등록
```
- **실제 데이터 처리 완료**: 테스트 데이터 5개 상품 변환 성공
- **데이터베이스 연동 완료**: 모든 테이블 정상 작동 확인

### 3. 멀티마켓플레이스 등록
- 네이버, 쿠팡, 11번가 등
- 마켓플레이스당 여러 판매 계정
- 공급사/마켓플레이스별 가격 규칙

### 4. 고급 기능
- 데이터 해시 기반 중복 감지
- pgvector 시맨틱 검색 (유사 상품)
- 조건별 가격 규칙 (마진율/고정가)
- Realtime 진행 상황 모니터링

## 기술 스택
- **언어**: Python 3.12.10
- **DB**: Supabase (PostgreSQL + pgvector)
- **웹 크롤링**: BeautifulSoup4, aiohttp
- **데이터 처리**: Pandas (엑셀)
- **이미지**: Pillow
- **검증**: Pydantic

## 아키텍처
- 상세한 아키텍처는 [ARCHITECTURE.md](.ai/ARCHITECTURE.md) 참조

## 코딩 규칙
- 상세한 코딩 규칙은 [CODING_RULES.md](.ai/CODING_RULES.md) 참조

## Supabase 사용
- 상세한 Supabase 가이드는 [SUPABASE_GUIDE.md](.ai/SUPABASE_GUIDE.md) 참조

## MCP (Model Context Protocol) 통합
- MCP를 통해 외부 도구, 데이터베이스, API와 연동 가능
- 상세한 MCP 설정 가이드는 [MCP_GUIDE.md](.ai/MCP_GUIDE.md) 참조
- 프로젝트 공유 MCP 설정: `.mcp.json`
- Claude Desktop과 MCP 서버 공유 가능

### MCP 주요 기능
- 파일 시스템 접근
- 데이터베이스 쿼리 (PostgreSQL, SQLite 등)
- 이슈 트래커 연동 (GitHub, Jira, Linear 등)
- 외부 API 통합 (Notion, Slack 등)

## 개발 워크플로우

### 새 공급사 추가
1. `src/services/connectors/examples/`에 커넥터 클래스 생성
2. `APIConnector`, `ExcelConnector`, `WebCrawlingConnector` 중 상속
3. 필수 메서드 구현:
   - `collect_products()`: 상품 수집
   - `transform_product()`: 데이터 변환
   - `validate_credentials()`: 인증 검증
4. `ConnectorFactory.register()`로 등록

### 상품 수집 → 등록 흐름
```python
# 1. 실제 데이터 수집 (완료된 예시)
collection = CollectionService()
result = await collection.collect_from_excel(
    supplier_id=supplier_uuid,
    file_path='data/test.xlsx',
    limit=3510  # 실제 3,510개 상품 처리 가능
)

# 2. 상품 변환 (완료된 예시)
pipeline = ProductPipeline()
processed = await pipeline.process_all_unprocessed(supplier_uuid)
# 결과: 원본 데이터 → 정규화된 상품 변환 완료

# 3. 마켓플레이스 등록 (다음 단계 준비 완료)
await pipeline.list_product(
    normalized_product_id=product_uuid,
    marketplace_id=marketplace_uuid
)
```

### 실제 데이터 처리 결과
- **수집 성공**: Excel 파일 3,510개 상품 데이터 처리
- **변환 성공**: 테스트 데이터 5개 상품 정규화 완료
- **저장 성공**: 모든 데이터가 Supabase에 정상 저장됨

### 가격 규칙 추가
1. Supabase Dashboard → `pricing_rules` 테이블
2. 조건 설정: `{"category": "의류"}`
3. 계산 방식: `percentage_margin` (30% 마진)
4. 우선순위 설정

## AI 에디터 사용 가이드

### 작업 시작 전
1. 최신 코드를 pull 받습니다
2. 이 문서와 관련 참조 문서를 확인합니다
3. 작업 범위를 명확히 정의합니다

### 작업 중
1. **Python 코딩 규칙** 준수 (snake_case, PEP 8)
2. **비동기 함수** 사용 시 `async def` 명시
3. **타입 힌팅** 필수 (Pydantic 활용)
4. **로깅** 추가 (Loguru 사용)
5. 테스트 작성 (pytest)
6. 문서 업데이트

### 작업 완료 후
1. 코드 리뷰를 수행합니다
2. 커밋 메시지에 사용한 AI 에디터를 명시합니다
   - 예: `feat: Add Taobao connector [Cursor]`
   - 예: `fix: Excel column mapping bug [Claude Code]`
3. 푸시 전 충돌을 확인합니다

## 문서 업데이트 규칙
- 이 문서는 프로젝트의 단일 진실 공급원(Single Source of Truth)입니다
- 중요한 결정사항은 반드시 이 문서에 기록합니다
- 문서 수정 시 날짜와 수정자(에디터)를 명시합니다

## 주요 디렉토리 구조

```
src/
├── config/              # 설정 (settings.py)
├── models/              # Pydantic 데이터 모델
├── services/
│   ├── connectors/      # 공급사 커넥터
│   │   ├── base.py     # 추상 베이스
│   │   ├── factory.py  # 팩토리
│   │   └── examples/   # 구현체
│   ├── collection_service.py  # 수집 서비스
│   ├── product_pipeline.py    # 변환 파이프라인
│   └── supabase_client.py     # DB 클라이언트
└── utils/               # 유틸리티

database/
└── migrations/
    ├── 001_initial_schema.sql
    └── 002_multi_supplier_schema.sql
```

## 배치 데이터 수집 최적화 (2025-10-07)

### 배치 수집 최적화 완료 ✅

#### 오너클랜
- **처리 성능**: 64,845개 상품을 **7.97분**에 처리 (약 8,100개/분)
- **중복 제거**: API 응답 내부 중복 90개 사전 제거
- **배치 크기**: 1000개 → 5000개로 증가 (네트워크 왕복 80% 감소)

#### 젠트레이드
- **처리 성능**: 3,510개 상품을 **19.75초**에 처리 (약 10,700개/시간)
- **수집 속도**: 584개/초
- **저장 속도**: 255개/초

#### 공통 최적화
- **저장 최적화**: 신규/업데이트 분리로 성능 향상
  - 신규 상품: bulk insert (빠름)
  - 업데이트 상품: bulk upsert
- **JSON 최적화**: 직렬화 2회 → 1회로 감소 (CPU 50% 절감)

### 최적화 상세 내용
1. **중복 사전 필터링**: 데이터베이스 기존 ID 조회 후 메모리에서 신규/업데이트 분류
2. **배치 내 중복 제거**: API 응답의 중복 상품을 메모리에서 제거
3. **대량 작업**: 5000개 단위 bulk insert/upsert
4. **에러 처리**: 실패 시 작은 배치로 자동 재시도

자세한 내용: `BATCH_OPTIMIZATION_SUMMARY.md` 참조

## 대량 데이터 정규화 완료 (2025-10-07)

### 전체 공급사 대량 정규화 완료 ✅
- **오너클랜**: 65,434개 → 67,535개 (100% 처리)
- **젠트레이드**: 3,510개 → 3,670개 (100% 처리)
- **도매꾹**: 1,171개 → 1,171개 (100% 처리)
- **총계**: **72,376개 정규화 상품**
- **평균 속도**: 약 400개/초
- **총 소요 시간**: 약 3-4분 (전체 배치 처리)

### 성과
- 전체 데이터 파이프라인 완성: **수집 → 저장 → 정규화**
- 실제 사용 가능한 정규화 상품 **72,376개** 확보
- 3개 공급사 모두 100% 처리 완료
- 마켓플레이스 등록 및 API 서비스 준비 완료

## 다음 개발 단계

PLAN.md의 우선순위에 따라:

### 우선순위 1: 추가 공급사 연동 (높음)
- 4-5개 추가 도매 공급사 API/Excel 연동
- 공급사별 커넥터 개발
- 배치 수집 시스템 적용
- 목표: 10만개 이상 상품 확보

### 우선순위 2: 마켓플레이스 경쟁사 데이터 수집 강화 (높음)
- 쿠팡/네이버 실시간 데이터 수집 (418 오류 해결)
- 11번가, 옥션, G마켓 추가
- 대량 수집 시스템 안정화
- 가격 비교 및 경쟁력 분석

### 우선순위 3: 트랜잭션 시스템 구현 (중간)
- 재고 관리 시스템
- 자동 주문 처리
- 정산 및 결제 시스템

## 변경 이력
- 2025-10-07: **72,376개 상품 정규화 완료 및 세션 요약** [Cline]
  - 배치 수집 최적화: 10-20배 속도 향상
  - 대량 정규화: 3개 공급사 100% 처리
  - REST API 서버 및 웹 대시보드 완성
  - 상세: SESSION_SUMMARY_2025_10_07.md 참조
- 2025-10-07: **전체 정규화 완료** (72,376개 상품, 3개 공급사 100%) [Cline]
- 2025-10-07: 대량 데이터 정규화 완료 (67,535개 상품) [Cline]
- 2025-10-07: 배치 수집 최적화 완료 (오너클랜, 젠트레이드) [Cline]
- 2025-10-06: 초기 문서 생성 [Claude Code]
- 2025-10-06: MCP (Model Context Protocol) 통합 가이드 추가 [Claude Code]
- 2025-10-06: 멀티공급사/멀티계정 시스템으로 업데이트 [Claude Code]
- 2025-10-06: Phase 1 완료 및 실제 데이터 처리 성공 [Windsurf]
