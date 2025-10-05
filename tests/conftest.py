"""
테스트 설정 및 픽스처
pytest 설정 파일
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock
from uuid import uuid4

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@pytest.fixture(scope="session")
def event_loop():
    """비동기 테스트를 위한 이벤트 루프 픽스처"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase 클라이언트 픽스처"""
    mock_client = Mock()
    mock_client.table.return_value.select.return_value.execute.return_value.data = []
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [{"id": str(uuid4())}]
    mock_client.table.return_value.update.return_value.execute.return_value.data = [{"id": str(uuid4())}]
    return mock_client


@pytest.fixture
def sample_supplier_data():
    """테스트용 공급사 데이터"""
    return {
        "id": str(uuid4()),
        "name": "테스트 공급사",
        "code": "test_supplier",
        "type": "api",
        "is_active": True,
        "api_endpoint": "https://api.test.com",
        "credentials": {"api_key": "test_key"},
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_product_data():
    """테스트용 상품 데이터"""
    return {
        "id": str(uuid4()),
        "title": "테스트 상품",
        "description": "테스트 상품 설명",
        "price": 10000.0,
        "original_price": 12000.0,
        "currency": "KRW",
        "stock_quantity": 100,
        "category": "테스트 카테고리",
        "tags": ["테스트", "상품"],
        "images": [{"url": "https://example.com/image.jpg", "is_primary": True}],
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_raw_product_data():
    """테스트용 원본 상품 데이터"""
    return {
        "id": str(uuid4()),
        "supplier_id": str(uuid4()),
        "raw_data": {
            "product_id": "supplier_product_123",
            "name": "공급사 상품명",
            "price": 8000,
            "description": "공급사 상품 설명",
            "stock": 50,
            "category": "공급사 카테고리",
            "images": ["https://supplier.com/image1.jpg", "https://supplier.com/image2.jpg"]
        },
        "is_processed": False,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_normalized_product_data():
    """테스트용 정규화된 상품 데이터"""
    return {
        "id": str(uuid4()),
        "supplier_id": str(uuid4()),
        "supplier_product_id": "supplier_product_123",
        "title": "정규화된 상품명",
        "description": "정규화된 상품 설명",
        "price": 10000.0,
        "cost_price": 8000.0,
        "currency": "KRW",
        "category": "정규화된 카테고리",
        "brand": "테스트 브랜드",
        "stock_quantity": 50,
        "status": "active",
        "images": [
            {"url": "https://supplier.com/image1.jpg", "is_primary": True},
            {"url": "https://supplier.com/image2.jpg", "is_primary": False}
        ],
        "attributes": {
            "color": "빨강",
            "size": "M",
            "material": "면"
        },
        "metadata": {
            "supplier": "test_supplier",
            "updated_at": "2025-01-01T00:00:00Z"
        },
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_marketplace_data():
    """테스트용 마켓플레이스 데이터"""
    return {
        "id": str(uuid4()),
        "name": "테스트 마켓플레이스",
        "api_endpoint": "https://api.marketplace.com",
        "credentials": {
            "api_key": "marketplace_key",
            "secret": "marketplace_secret"
        },
        "is_active": True,
        "created_at": "2025-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_pricing_rule_data():
    """테스트용 가격 규칙 데이터"""
    return {
        "id": str(uuid4()),
        "supplier_id": str(uuid4()),
        "marketplace_id": str(uuid4()),
        "rule_name": "기본 30% 마진",
        "calculation_type": "percentage_margin",
        "calculation_value": 30.0,
        "round_to": 100,
        "conditions": {"category": "의류"},
        "priority": 1,
        "is_active": True,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_collection_job_data():
    """테스트용 수집 작업 데이터"""
    return {
        "id": str(uuid4()),
        "supplier_id": str(uuid4()),
        "account_id": str(uuid4()),
        "job_name": "테스트 수집 작업",
        "status": "running",
        "progress": 50.0,
        "total_count": 100,
        "success_count": 50,
        "failed_count": 0,
        "parameters": {
            "limit": 100,
            "category": "의류"
        },
        "started_at": "2025-01-01T00:00:00Z",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_api_response():
    """Mock API 응답 픽스처"""
    return {
        "status": 200,
        "data": {
            "products": [
                {
                    "id": "api_product_1",
                    "name": "API 상품 1",
                    "price": 15000,
                    "description": "API 상품 설명",
                    "stock": 25,
                    "category": "API 카테고리",
                    "images": ["https://api.com/image1.jpg"]
                },
                {
                    "id": "api_product_2",
                    "name": "API 상품 2",
                    "price": 25000,
                    "description": "API 상품 설명 2",
                    "stock": 15,
                    "category": "API 카테고리",
                    "images": ["https://api.com/image2.jpg"]
                }
            ],
            "total": 2,
            "page": 1,
            "per_page": 50
        }
    }


@pytest.fixture
def mock_excel_data():
    """Mock Excel 데이터 픽스처"""
    return [
        {
            "상품코드(번호)": "EXCEL_001",
            "상품명": "엑셀 상품 1",
            "가격": 12000,
            "카테고리": "엑셀 카테고리",
            "재고": 30,
            "이미지URL": "https://excel.com/image1.jpg,https://excel.com/image2.jpg",
            "_row_number": 2
        },
        {
            "상품코드(번호)": "EXCEL_002",
            "상품명": "엑셀 상품 2",
            "가격": 18000,
            "카테고리": "엑셀 카테고리",
            "재고": 20,
            "이미지URL": "https://excel.com/image3.jpg",
            "_row_number": 3
        }
    ]


@pytest.fixture
def mock_web_crawling_data():
    """Mock 웹 크롤링 데이터 픽스처"""
    return [
        {
            "url": "https://crawling-site.com/product/1",
            "title": "크롤링 상품 1",
            "price": 20000,
            "description": "크롤링 상품 설명",
            "images": ["https://crawling-site.com/img1.jpg"],
            "category": "크롤링 카테고리",
            "stock": 10
        },
        {
            "url": "https://crawling-site.com/product/2",
            "title": "크롤링 상품 2",
            "price": 30000,
            "description": "크롤링 상품 설명 2",
            "images": ["https://crawling-site.com/img2.jpg"],
            "category": "크롤링 카테고리",
            "stock": 5
        }
    ]


# 테스트 설정
def pytest_configure(config):
    """pytest 설정"""
    config.addinivalue_line(
        "markers", "asyncio: 비동기 테스트 마커"
    )
    config.addinivalue_line(
        "markers", "integration: 통합 테스트 마커"
    )
    config.addinivalue_line(
        "markers", "unit: 단위 테스트 마커"
    )


# 테스트 수집 시 경고 무시
def pytest_collection_modifyitems(config, items):
    """테스트 수집 시 설정"""
    for item in items:
        # 비동기 테스트에 asyncio 마커 추가
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
        
        # 통합 테스트에 integration 마커 추가
        if "integration" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        
        # 단위 테스트에 unit 마커 추가
        if "test_" in item.name and "integration" not in item.name.lower():
            item.add_marker(pytest.mark.unit)
