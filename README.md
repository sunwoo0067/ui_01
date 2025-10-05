# 드롭쉬핑 멀티공급사/멀티계정 자동화 시스템

Supabase 기반 개인용 드롭쉬핑 자동화 프로그램 (배포 없음)

## 프로젝트 개요

- **개발 환경**: Python 3.12.10
- **데이터베이스**: Supabase (PostgreSQL + pgvector)
- **목적**: 개인 사용자용 멀티공급사/멀티계정 드롭쉬핑 자동화

## 핵심 기능

### 🔄 멀티공급사 지원
- **공급사별 수집 방법**: API, 엑셀, 웹 크롤링
- **원본 데이터 저장**: JSONB 형식으로 공급사별 데이터 원본 보관
- **멀티 계정**: 공급사당 여러 계정 관리
- **커넥터 추상화**: 공급사별 API 형식 차이 자동 처리

### 📊 3가지 상품 수집 방식

#### 1. API 수집
```python
from src.services import CollectionService

service = CollectionService()

# API로 상품 수집
await service.collect_from_api(
    supplier_id=supplier_id,
    account_id=account_id,
    category_id='fashion'
)
```

#### 2. 엑셀 수집
```python
# 엑셀 파일에서 수집
await service.collect_from_excel(
    supplier_id=supplier_id,
    file_path='products.xlsx'
)
```

#### 3. 웹 크롤링
```python
# 웹 페이지 크롤링
await service.collect_from_web(
    supplier_id=supplier_id,
    start_url='https://supplier.com/products',
    max_pages=10
)
```

### 🛒 멀티마켓플레이스 등록
- **판매 플랫폼**: 네이버, 쿠팡, 11번가 등
- **멀티 계정**: 마켓플레이스당 여러 판매 계정
- **자동 가격 계산**: 공급사/마켓플레이스별 가격 규칙
- **일괄 등록**: 한 번에 여러 마켓플레이스 등록

### 🔍 고급 기능
- **중복 감지**: 데이터 해시 기반 중복 상품 자동 감지
- **시맨틱 검색**: pgvector로 유사 상품 찾기
- **가격 규칙**: 조건별 마진율/고정가 자동 계산
- **실시간 모니터링**: 수집 진행 상황 Realtime 구독

## 설치 및 설정

### 1. Python 환경 설정

```bash
# Python 3.12.10 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일 수정:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
```

### 3. Supabase 데이터베이스 설정

Supabase Dashboard → SQL Editor:

```sql
-- 001_initial_schema.sql 실행
-- 002_multi_supplier_schema.sql 실행
```

## 프로젝트 구조

```
ui_01/
├── src/
│   ├── config/                    # 설정
│   ├── models/                    # 데이터 모델 (Pydantic)
│   └── services/
│       ├── connectors/            # 공급사 커넥터
│       │   ├── base.py           # 추상 베이스
│       │   ├── factory.py        # 팩토리
│       │   └── examples/         # 공급사별 구현체
│       ├── collection_service.py  # 수집 서비스
│       ├── product_pipeline.py    # 변환 파이프라인
│       └── supabase_client.py     # DB 클라이언트
├── database/
│   └── migrations/                # SQL 스키마
│       ├── 001_initial_schema.sql
│       └── 002_multi_supplier_schema.sql
├── .ai/                           # AI 에디터 문서
└── requirements.txt
```

## 데이터 흐름

```
1. 수집 (Collection)
   ├── API: NaverSmartstoreConnector
   ├── Excel: GenericExcelConnector
   └── Web: GenericWebCrawler

2. 원본 저장 (Raw Data)
   └── raw_product_data 테이블 (JSONB)

3. 변환 (Transformation)
   └── ProductPipeline.process_raw_data()

4. 정규화 (Normalization)
   └── normalized_products 테이블

5. 가격 계산 (Pricing)
   └── apply_pricing_rule() 함수

6. 등록 (Listing)
   └── listed_products 테이블
```

## 사용 예시

### 공급사 등록

```python
# 네이버 스마트스토어 (API)
supplier_data = {
    'name': '네이버 스마트스토어',
    'code': 'naver_smartstore',
    'type': 'api',
    'api_endpoint': 'https://api.smartstore.naver.com',
    'credentials': {
        'client_id': 'YOUR_CLIENT_ID',
        'client_secret': 'YOUR_SECRET'
    }
}

# 엑셀 공급사
supplier_data = {
    'name': '엑셀 공급사 A',
    'code': 'excel_supplier_a',
    'type': 'excel',
    'excel_config': {
        'column_mapping': {
            '상품명': 'title',
            '판매가': 'price',
            '원가': 'cost_price',
            '재고': 'stock_quantity'
        }
    }
}

# 웹 크롤링 공급사
supplier_data = {
    'name': '타오바오',
    'code': 'taobao',
    'type': 'web_crawling',
    'crawl_config': {
        'base_url': 'https://taobao.com',
        'selectors': {
            'product_list': '.product-item',
            'title': '.product-title',
            'price': '.product-price',
            'image': '.product-image img'
        },
        'pagination': {
            'param': 'page',
            'format': 'query'
        }
    }
}
```

### 상품 수집 → 변환 → 등록

```python
import asyncio
from uuid import UUID
from src.services import CollectionService, ProductPipeline

async def main():
    # 1. 수집 서비스 초기화
    collection = CollectionService()
    pipeline = ProductPipeline()

    # 2. 엑셀에서 상품 수집
    result = await collection.collect_from_excel(
        supplier_id=UUID('supplier-uuid'),
        file_path='products.xlsx'
    )

    print(f"✅ 수집 완료: {result['saved']}개 상품")

    # 3. 미처리 데이터 변환
    process_result = await pipeline.process_all_unprocessed(
        supplier_id=UUID('supplier-uuid')
    )

    print(f"✅ 변환 완료: {process_result['success']}개 상품")

    # 4. 특정 상품 등록
    listed_id = await pipeline.list_product(
        normalized_product_id=UUID('product-uuid'),
        marketplace_id=UUID('marketplace-uuid')
    )

    print(f"✅ 등록 완료: {listed_id}")

asyncio.run(main())
```

### 가격 규칙 설정

```python
# 카테고리별 마진율 규칙
pricing_rule = {
    'supplier_id': 'supplier-uuid',
    'marketplace_id': 'marketplace-uuid',
    'rule_name': '의류 30% 마진',
    'priority': 10,
    'conditions': {
        'category': '의류'
    },
    'calculation_type': 'percentage_margin',
    'calculation_value': 30.0,  # 30% 마진
    'round_to': 100  # 100원 단위 반올림
}
```

## 공급사 커넥터 추가

새 공급사를 추가하려면:

1. `src/services/connectors/examples/` 에 새 파일 생성
2. `APIConnector`, `ExcelConnector`, 또는 `WebCrawlingConnector` 상속
3. 필수 메서드 구현:
   - `collect_products()`: 상품 수집
   - `transform_product()`: 데이터 변환
   - `validate_credentials()`: 인증 검증

```python
from src.services.connectors import APIConnector

class MySupplierConnector(APIConnector):
    async def collect_products(self, **kwargs):
        # API 호출 로직
        pass

    def transform_product(self, raw_data):
        # 데이터 변환 로직
        return {
            'title': raw_data.get('product_name'),
            'price': float(raw_data.get('price'))
        }

    def validate_credentials(self):
        # 인증 검증
        return True
```

4. 팩토리에 등록:

```python
from src.services.connectors import ConnectorFactory
from .my_supplier import MySupplierConnector

ConnectorFactory.register('my_supplier', MySupplierConnector)
```

## 주요 테이블 구조

### raw_product_data
- **목적**: 공급사별 원본 데이터 저장 (JSONB)
- **특징**: 데이터 해시로 중복 방지

### normalized_products
- **목적**: 정규화된 상품 데이터
- **특징**: pgvector 임베딩, 시맨틱 검색

### listed_products
- **목적**: 마켓플레이스별 등록 상품
- **특징**: 가격 규칙 적용, 동기화 상태

### pricing_rules
- **목적**: 공급사/마켓플레이스별 가격 규칙
- **특징**: 조건부 마진율, 우선순위

## 개발 가이드

### AI 에디터 사용

이 프로젝트는 멀티 AI 에디터 환경을 지원합니다:
- **Claude Code**, **Cursor**, **Windsurf**, **Codex/Cline**

작업 전 반드시 읽어주세요:
- [.ai/DEVELOPMENT.md](.ai/DEVELOPMENT.md) - 개발 가이드
- [.ai/ARCHITECTURE.md](.ai/ARCHITECTURE.md) - 아키텍처
- [.ai/CODING_RULES.md](.ai/CODING_RULES.md) - 코딩 규칙
- [.ai/SUPABASE_GUIDE.md](.ai/SUPABASE_GUIDE.md) - Supabase 가이드

### 테스트

```bash
pytest tests/ -v
```

## 라이선스

MIT License

## 문의

프로젝트 관련 문의는 이슈를 등록해주세요.
