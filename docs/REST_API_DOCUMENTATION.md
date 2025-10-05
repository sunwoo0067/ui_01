# REST API 문서

## 개요

드롭쉬핑 자동화 시스템을 위한 포괄적인 REST API입니다. 이 API는 외부 시스템과의 연동을 위해 설계되었으며, 상품 검색, AI 가격 예측, 주문 관리, 공급사 관리 등의 기능을 제공합니다.

## 기본 정보

- **Base URL**: `http://localhost:8001`
- **API 버전**: `v2`
- **인증 방식**: Bearer Token
- **응답 형식**: JSON

## 인증

모든 API 요청에는 인증 토큰이 필요합니다.

```http
Authorization: Bearer dev_token_123
```

## 공통 응답 형식

모든 API 응답은 다음 형식을 따릅니다:

```json
{
  "success": true,
  "message": "작업이 성공적으로 완료되었습니다",
  "data": { ... },
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "optional-request-id"
}
```

## 엔드포인트

### 기본 엔드포인트

#### GET /
API 루트 엔드포인트

**응답 예시:**
```json
{
  "success": true,
  "message": "Dropshipping Automation REST API",
  "data": {
    "version": "2.0.0",
    "status": "running",
    "endpoints": {
      "products": "/api/v2/products",
      "search": "/api/v2/search",
      "ai": "/api/v2/ai",
      "orders": "/api/v2/orders",
      "suppliers": "/api/v2/suppliers",
      "analytics": "/api/v2/analytics"
    }
  }
}
```

#### GET /health
헬스 체크

**응답 예시:**
```json
{
  "success": true,
  "message": "API 서버가 정상적으로 작동 중입니다",
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "uptime": "running"
  }
}
```

### 상품 관련 API

#### GET /api/v2/products
상품 목록 조회

**쿼리 매개변수:**
- `limit` (int, 선택): 조회 개수 (기본값: 20, 최대: 100)
- `offset` (int, 선택): 오프셋 (기본값: 0)
- `category` (string, 선택): 카테고리 필터
- `platform` (string, 선택): 플랫폼 필터

**응답 예시:**
```json
{
  "success": true,
  "message": "20개의 상품을 조회했습니다",
  "data": {
    "products": [
      {
        "id": "product_001",
        "name": "스마트폰",
        "price": 50000,
        "platform": "coupang",
        "category": "electronics"
      }
    ],
    "total": 20,
    "limit": 20,
    "offset": 0
  }
}
```

#### GET /api/v2/products/{product_id}
특정 상품 조회

**경로 매개변수:**
- `product_id` (string, 필수): 상품 ID

**응답 예시:**
```json
{
  "success": true,
  "message": "상품 조회 성공",
  "data": {
    "id": "product_001",
    "name": "스마트폰",
    "price": 50000,
    "platform": "coupang",
    "category": "electronics",
    "seller": "테스트 셀러",
    "product_url": "https://example.com/product/001",
    "rating": 4.5,
    "review_count": 150
  }
}
```

### 검색 관련 API

#### POST /api/v2/search
상품 검색

**요청 본문:**
```json
{
  "keyword": "스마트폰",
  "page": 1,
  "platform": "coupang",
  "category": "electronics",
  "min_price": 10000,
  "max_price": 100000
}
```

**응답 예시:**
```json
{
  "success": true,
  "message": "'스마트폰' 검색 완료",
  "data": {
    "keyword": "스마트폰",
    "page": 1,
    "platform": "coupang",
    "results": {
      "coupang": [
        {
          "name": "스마트폰 A",
          "price": 50000,
          "platform": "coupang",
          "seller": "셀러 A"
        }
      ]
    },
    "total_results": 1
  }
}
```

#### GET /api/v2/search/suggestions
검색 제안

**쿼리 매개변수:**
- `q` (string, 필수): 검색어 (최소 2자)
- `limit` (int, 선택): 제안 개수 (기본값: 10, 최대: 20)

**응답 예시:**
```json
{
  "success": true,
  "message": "'스마트'에 대한 검색 제안",
  "data": {
    "query": "스마트",
    "suggestions": ["스마트폰", "스마트워치", "스마트TV"],
    "count": 3
  }
}
```

### AI 관련 API

#### POST /api/v2/ai/predict
AI 가격 예측

**요청 본문:**
```json
{
  "product_data": {
    "platform": "coupang",
    "category": "electronics",
    "price": 50000,
    "original_price": 60000,
    "rating": 4.5,
    "review_count": 150
  },
  "category": "electronics"
}
```

**응답 예시:**
```json
{
  "success": true,
  "message": "가격 예측 완료",
  "data": {
    "predictions": [
      {
        "model": "random_forest",
        "predicted_price": 52000,
        "confidence": 0.85,
        "features_used": ["platform", "category", "rating"]
      }
    ],
    "best_prediction": {
      "model": "random_forest",
      "price": 52000,
      "confidence": 0.85
    }
  }
}
```

#### POST /api/v2/ai/strategy
가격 전략 제안

**요청 본문:**
```json
{
  "product_data": {
    "platform": "coupang",
    "category": "electronics",
    "price": 50000,
    "original_price": 60000,
    "rating": 4.5,
    "review_count": 150
  },
  "category": "electronics"
}
```

**응답 예시:**
```json
{
  "success": true,
  "message": "가격 전략 분석 완료",
  "data": {
    "recommended_price": 52000,
    "strategy": "competitive",
    "confidence": 0.85,
    "reasoning": "시장 가격 상승 추세",
    "market_trend": {
      "direction": "up",
      "strength": 0.7,
      "volatility": 0.3,
      "competitor_count": 5
    }
  }
}
```

#### GET /api/v2/ai/trends
시장 트렌드 분석

**쿼리 매개변수:**
- `category` (string, 선택): 카테고리

**응답 예시:**
```json
{
  "success": true,
  "message": "시장 트렌드 분석 완료",
  "data": {
    "trend_direction": "up",
    "trend_strength": 0.7,
    "volatility": 0.3,
    "seasonal_pattern": "seasonal",
    "competitor_count": 5,
    "price_range": {
      "min": 30000,
      "max": 80000
    }
  }
}
```

### 주문 관련 API

#### POST /api/v2/orders
주문 생성

**요청 본문:**
```json
{
  "products": [
    {
      "item_key": "item_001",
      "quantity": 1,
      "option_attributes": [
        {"name": "색상", "value": "RED"}
      ]
    }
  ],
  "recipient": {
    "name": "홍길동",
    "phone": "010-1234-5678",
    "address": "서울시 강남구 테헤란로 123",
    "postal_code": "12345",
    "city": "서울시",
    "district": "강남구",
    "detail_address": "테헤란로 123"
  },
  "note": "빠른 배송 부탁드립니다",
  "seller_note": "재고 확인 필요",
  "orderer_note": "선물용 포장"
}
```

**응답 예시:**
```json
{
  "success": true,
  "message": "주문 생성 성공",
  "data": {
    "order_id": "order_12345",
    "status": "pending",
    "message": "주문이 성공적으로 생성되었습니다"
  }
}
```

#### GET /api/v2/orders
주문 목록 조회

**쿼리 매개변수:**
- `limit` (int, 선택): 조회 개수 (기본값: 20, 최대: 100)
- `offset` (int, 선택): 오프셋 (기본값: 0)
- `status` (string, 선택): 주문 상태

**응답 예시:**
```json
{
  "success": true,
  "message": "10개의 주문을 조회했습니다",
  "data": {
    "orders": [
      {
        "id": "order_12345",
        "status": "pending",
        "total_amount": 50000,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 10,
    "limit": 20,
    "offset": 0
  }
}
```

### 공급사 관련 API

#### GET /api/v2/suppliers
공급사 목록 조회

**응답 예시:**
```json
{
  "success": true,
  "message": "3개의 공급사를 조회했습니다",
  "data": {
    "suppliers": [
      {
        "id": "supplier_001",
        "supplier_code": "ownerclan",
        "account_name": "테스트 계정",
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "count": 3
  }
}
```

#### POST /api/v2/suppliers
공급사 계정 생성

**요청 본문:**
```json
{
  "supplier_code": "ownerclan",
  "account_name": "테스트 계정",
  "credentials": {
    "username": "test_user",
    "password": "test_password"
  },
  "is_active": true
}
```

**응답 예시:**
```json
{
  "success": true,
  "message": "공급사 계정 생성 성공",
  "data": {
    "supplier_code": "ownerclan"
  }
}
```

### 분석 관련 API

#### GET /api/v2/analytics/dashboard
대시보드 분석 데이터

**쿼리 매개변수:**
- `period` (string, 선택): 분석 기간 (1d, 7d, 30d, 기본값: 7d)

**응답 예시:**
```json
{
  "success": true,
  "message": "대시보드 분석 데이터 조회 완료",
  "data": {
    "period": "7d",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-08T00:00:00Z",
    "statistics": {
      "total_products": 1000,
      "total_orders": 50,
      "active_suppliers": 3,
      "platforms_monitored": 5
    },
    "trends": {
      "product_growth": 0.1,
      "order_growth": 0.2,
      "price_changes": 0.05
    }
  }
}
```

### 배치 작업 API

#### POST /api/v2/batch
배치 작업 실행

**요청 본문:**
```json
{
  "operation": "data_collection",
  "parameters": {
    "platforms": ["coupang", "naver"],
    "keywords": ["스마트폰", "노트북"]
  },
  "target_ids": ["product_001", "product_002"]
}
```

**지원하는 작업 유형:**
- `data_collection`: 데이터 수집
- `price_analysis`: 가격 분석
- `model_training`: 모델 훈련

**응답 예시:**
```json
{
  "success": true,
  "message": "데이터 수집 작업이 백그라운드에서 시작되었습니다",
  "data": {
    "operation": "data_collection",
    "status": "started",
    "parameters": {
      "platforms": ["coupang", "naver"],
      "keywords": ["스마트폰", "노트북"]
    }
  }
}
```

## 오류 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 |
| 401 | 인증 실패 |
| 403 | 권한 없음 |
| 404 | 리소스 없음 |
| 500 | 서버 오류 |

## 오류 응답 예시

```json
{
  "success": false,
  "message": "인증 토큰이 필요합니다",
  "data": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 사용 예시

### Python 클라이언트 예시

```python
import aiohttp
import asyncio

async def test_api():
    headers = {
        "Authorization": "Bearer dev_token_123",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        # 상품 검색
        search_data = {
            "keyword": "스마트폰",
            "page": 1,
            "platform": "coupang"
        }
        
        async with session.post(
            "http://localhost:8001/api/v2/search",
            headers=headers,
            json=search_data
        ) as response:
            data = await response.json()
            print(f"검색 결과: {data['data']['total_results']}개")

# 실행
asyncio.run(test_api())
```

### JavaScript 클라이언트 예시

```javascript
const API_BASE_URL = 'http://localhost:8001';
const AUTH_TOKEN = 'dev_token_123';

async function searchProducts(keyword) {
    const response = await fetch(`${API_BASE_URL}/api/v2/search`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${AUTH_TOKEN}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            keyword: keyword,
            page: 1
        })
    });
    
    const data = await response.json();
    return data.data;
}

// 사용 예시
searchProducts('스마트폰').then(result => {
    console.log(`검색 결과: ${result.total_results}개`);
});
```

## 제한 사항

- 요청 제한: 분당 1000회
- 응답 크기: 최대 10MB
- 타임아웃: 30초
- 동시 연결: 최대 100개

## 버전 관리

API 버전은 URL 경로에 포함됩니다 (`/api/v2/`). 새로운 버전이 출시될 때는 이전 버전과의 호환성을 유지합니다.

## 지원

API 사용 중 문제가 발생하면 다음을 확인해주세요:

1. 인증 토큰이 올바른지 확인
2. 요청 형식이 올바른지 확인
3. 서버 상태 확인 (`/health` 엔드포인트)
4. 로그 파일 확인
