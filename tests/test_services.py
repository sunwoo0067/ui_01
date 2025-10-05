"""
핵심 서비스 단위 테스트
pytest 기반 테스트 코드 작성
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4, UUID
from typing import Dict, Any, List

from src.services.collection_service import CollectionService
from src.services.product_pipeline import ProductPipeline
from src.services.supabase_client import SupabaseClient
from src.utils.error_handler import (
    ValidationError,
    DatabaseError,
    APIConnectionError,
    validate_required_fields,
    validate_data_type
)


class TestCollectionService:
    """CollectionService 테스트 클래스"""
    
    def setup_method(self):
        """각 테스트 전 실행"""
        self.collection_service = CollectionService()
        self.supplier_id = uuid4()
        self.account_id = uuid4()
    
    @pytest.mark.asyncio
    async def test_collect_from_supplier_success(self):
        """공급사로부터 상품 수집 성공 테스트"""
        # Arrange
        mock_supplier = {
            "id": str(self.supplier_id),
            "name": "테스트 공급사",
            "type": "api",
            "is_active": True
        }
        
        mock_products = [
            {"id": "1", "title": "테스트 상품 1", "price": 10000},
            {"id": "2", "title": "테스트 상품 2", "price": 20000}
        ]
        
        # Mock 설정
        with patch.object(self.collection_service, '_get_supplier') as mock_get_supplier, \
             patch.object(self.collection_service, '_create_collection_job') as mock_create_job, \
             patch.object(self.collection_service, '_create_connector') as mock_create_connector, \
             patch.object(self.collection_service, '_collect_products') as mock_collect:
            
            mock_get_supplier.return_value = mock_supplier
            mock_create_job.return_value = uuid4()
            mock_connector = Mock()
            mock_connector.collect_products = AsyncMock(return_value=mock_products)
            mock_create_connector.return_value = mock_connector
            mock_collect.return_value = mock_products
            
            # Act
            result = await self.collection_service.collect_from_supplier(
                supplier_id=self.supplier_id,
                account_id=self.account_id,
                job_name="테스트 수집"
            )
            
            # Assert
            assert result["status"] == "success"
            assert result["products_collected"] == len(mock_products)
            mock_get_supplier.assert_called_once_with(self.supplier_id)
            mock_create_job.assert_called_once()
            mock_create_connector.assert_called_once()
            mock_collect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_collect_from_supplier_not_found(self):
        """공급사를 찾을 수 없는 경우 테스트"""
        # Arrange
        with patch.object(self.collection_service, '_get_supplier') as mock_get_supplier:
            mock_get_supplier.return_value = None
            
            # Act & Assert
            with pytest.raises(ValueError, match="Supplier not found"):
                await self.collection_service.collect_from_supplier(
                    supplier_id=self.supplier_id,
                    job_name="테스트 수집"
                )
    
    @pytest.mark.asyncio
    async def test_collect_from_supplier_with_filters(self):
        """필터 조건과 함께 상품 수집 테스트"""
        # Arrange
        mock_supplier = {
            "id": str(self.supplier_id),
            "name": "테스트 공급사",
            "type": "api",
            "is_active": True
        }
        
        filters = {"category": "의류", "price_min": 10000}
        
        with patch.object(self.collection_service, '_get_supplier') as mock_get_supplier, \
             patch.object(self.collection_service, '_create_collection_job') as mock_create_job, \
             patch.object(self.collection_service, '_create_connector') as mock_create_connector, \
             patch.object(self.collection_service, '_collect_products') as mock_collect:
            
            mock_get_supplier.return_value = mock_supplier
            mock_create_job.return_value = uuid4()
            mock_connector = Mock()
            mock_connector.collect_products = AsyncMock(return_value=[])
            mock_create_connector.return_value = mock_connector
            mock_collect.return_value = []
            
            # Act
            result = await self.collection_service.collect_from_supplier(
                supplier_id=self.supplier_id,
                job_name="필터 테스트",
                **filters
            )
            
            # Assert
            assert result["status"] == "success"
            mock_collect.assert_called_once()


class TestProductPipeline:
    """ProductPipeline 테스트 클래스"""
    
    def setup_method(self):
        """각 테스트 전 실행"""
        self.pipeline = ProductPipeline()
        self.raw_data_id = uuid4()
        self.supplier_id = uuid4()
    
    @pytest.mark.asyncio
    async def test_process_raw_data_success(self):
        """원본 데이터 처리 성공 테스트"""
        # Arrange
        mock_raw_data = {
            "id": str(self.raw_data_id),
            "supplier_id": str(self.supplier_id),
            "raw_data": {"title": "테스트 상품", "price": 10000},
            "is_processed": False
        }
        
        mock_supplier = {
            "id": str(self.supplier_id),
            "name": "테스트 공급사",
            "type": "api"
        }
        
        mock_normalized_data = {
            "title": "테스트 상품",
            "price": 10000,
            "supplier_product_id": "test-product-id"
        }
        
        # Mock 설정
        with patch.object(self.pipeline, '_get_raw_data') as mock_get_raw_data, \
             patch.object(self.pipeline, '_get_supplier') as mock_get_supplier, \
             patch.object(self.pipeline, '_create_connector') as mock_create_connector, \
             patch.object(self.pipeline, '_save_normalized_product') as mock_save_product, \
             patch.object(self.pipeline, '_mark_processed') as mock_mark_processed:
            
            mock_get_raw_data.return_value = mock_raw_data
            mock_get_supplier.return_value = mock_supplier
            mock_connector = Mock()
            mock_connector.transform_product.return_value = mock_normalized_data
            mock_create_connector.return_value = mock_connector
            mock_save_product.return_value = uuid4()
            mock_mark_processed.return_value = True
            
            # Act
            result = await self.pipeline.process_raw_data(
                raw_data_id=self.raw_data_id,
                auto_list=False
            )
            
            # Assert
            assert result["status"] == "success"
            assert "normalized_product_id" in result
            assert result["auto_listed"] is False
            mock_get_raw_data.assert_called_once_with(self.raw_data_id)
            mock_get_supplier.assert_called_once()
            mock_create_connector.assert_called_once()
            mock_save_product.assert_called_once()
            mock_mark_processed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_raw_data_already_processed(self):
        """이미 처리된 데이터 테스트"""
        # Arrange
        mock_raw_data = {
            "id": str(self.raw_data_id),
            "supplier_id": str(self.supplier_id),
            "raw_data": {"title": "테스트 상품", "price": 10000},
            "is_processed": True
        }
        
        with patch.object(self.pipeline, '_get_raw_data') as mock_get_raw_data:
            mock_get_raw_data.return_value = mock_raw_data
            
            # Act
            result = await self.pipeline.process_raw_data(
                raw_data_id=self.raw_data_id
            )
            
            # Assert
            assert result["status"] == "already_processed"
            mock_get_raw_data.assert_called_once_with(self.raw_data_id)
    
    @pytest.mark.asyncio
    async def test_process_raw_data_not_found(self):
        """원본 데이터를 찾을 수 없는 경우 테스트"""
        # Arrange
        with patch.object(self.pipeline, '_get_raw_data') as mock_get_raw_data:
            mock_get_raw_data.return_value = None
            
            # Act & Assert
            with pytest.raises(ValueError, match="Raw data not found"):
                await self.pipeline.process_raw_data(
                    raw_data_id=self.raw_data_id
                )
    
    @pytest.mark.asyncio
    async def test_process_all_unprocessed(self):
        """미처리 데이터 일괄 처리 테스트"""
        # Arrange
        mock_raw_data_list = [
            {"id": str(uuid4()), "supplier_id": str(self.supplier_id), "is_processed": False},
            {"id": str(uuid4()), "supplier_id": str(self.supplier_id), "is_processed": False}
        ]
        
        with patch.object(self.pipeline, '_get_unprocessed_raw_data') as mock_get_unprocessed, \
             patch.object(self.pipeline, 'process_raw_data') as mock_process:
            
            mock_get_unprocessed.return_value = mock_raw_data_list
            mock_process.return_value = {"status": "success"}
            
            # Act
            result = await self.pipeline.process_all_unprocessed(
                supplier_id=self.supplier_id,
                limit=10
            )
            
            # Assert
            assert result["status"] == "success"
            assert result["processed_count"] == len(mock_raw_data_list)
            mock_get_unprocessed.assert_called_once()
            assert mock_process.call_count == len(mock_raw_data_list)


class TestSupabaseClient:
    """SupabaseClient 테스트 클래스"""
    
    def setup_method(self):
        """각 테스트 전 실행"""
        self.client = SupabaseClient()
    
    def test_singleton_pattern(self):
        """싱글톤 패턴 테스트"""
        # Arrange & Act
        client1 = SupabaseClient()
        client2 = SupabaseClient()
        
        # Assert
        assert client1 is client2
        assert id(client1) == id(client2)
    
    @patch('src.services.supabase_client.create_client')
    def test_client_initialization(self, mock_create_client):
        """클라이언트 초기화 테스트"""
        # Arrange
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Act
        client = SupabaseClient()
        
        # Assert
        assert client.client is not None
        mock_create_client.assert_called()
    
    def test_get_table(self):
        """테이블 접근 테스트"""
        # Arrange
        table_name = "test_table"
        
        # Act
        table = self.client.get_table(table_name)
        
        # Assert
        assert table is not None
    
    def test_get_storage(self):
        """Storage 접근 테스트"""
        # Act
        storage = self.client.get_storage()
        
        # Assert
        assert storage is not None


class TestErrorHandler:
    """에러 처리 유틸리티 테스트 클래스"""
    
    def test_validate_required_fields_success(self):
        """필수 필드 검증 성공 테스트"""
        # Arrange
        data = {"name": "테스트", "email": "test@example.com"}
        required_fields = ["name", "email"]
        
        # Act & Assert (예외가 발생하지 않아야 함)
        validate_required_fields(data, required_fields)
    
    def test_validate_required_fields_missing(self):
        """필수 필드 누락 테스트"""
        # Arrange
        data = {"name": "테스트"}
        required_fields = ["name", "email"]
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_required_fields(data, required_fields)
        
        assert "email" in exc_info.value.message
        assert "missing_fields" in exc_info.value.details
    
    def test_validate_data_type_success(self):
        """데이터 타입 검증 성공 테스트"""
        # Arrange
        value = "테스트 문자열"
        expected_type = str
        
        # Act & Assert (예외가 발생하지 않아야 함)
        validate_data_type(value, expected_type, "test_field")
    
    def test_validate_data_type_failure(self):
        """데이터 타입 검증 실패 테스트"""
        # Arrange
        value = "테스트 문자열"
        expected_type = int
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_data_type(value, expected_type, "test_field")
        
        assert "타입이 올바르지 않음" in exc_info.value.message
        assert exc_info.value.details["expected_type"] == "int"
        assert exc_info.value.details["actual_type"] == "str"


class TestAPIConnectors:
    """API 커넥터 테스트 클래스"""
    
    def test_ownerclan_connector_initialization(self):
        """오너클랜 커넥터 초기화 테스트"""
        # Arrange
        api_key = "test_api_key"
        api_secret = "test_api_secret"
        
        # Act
        from src.services.connectors.examples.ownerclan import OwnerClanConnector
        connector = OwnerClanConnector(api_key=api_key, api_secret=api_secret)
        
        # Assert
        assert connector.api_key == api_key
        assert connector.api_secret == api_secret
        assert connector.base_url == "https://api.ownerclan.com/v1"
    
    def test_zentrade_connector_initialization(self):
        """젠트레이드 커넥터 초기화 테스트"""
        # Arrange
        api_key = "test_api_key"
        api_secret = "test_api_secret"
        
        # Act
        from src.services.connectors.examples.zentrade import ZentradeConnector
        connector = ZentradeConnector(api_key=api_key, api_secret=api_secret)
        
        # Assert
        assert connector.api_key == api_key
        assert connector.api_secret == api_secret
        assert connector.base_url == "https://api.zentrade.com/api/v1"
    
    def test_domaemae_connector_initialization(self):
        """도매매 커넥터 초기화 테스트"""
        # Arrange
        api_key = "test_api_key"
        seller_id = "test_seller_id"
        
        # Act
        from src.services.connectors.examples.domaemae import DomaeMaeConnector
        connector = DomaeMaeConnector(api_key=api_key, seller_id=seller_id)
        
        # Assert
        assert connector.api_key == api_key
        assert connector.seller_id == seller_id
        assert connector.base_url == "https://api.dodomall.com/v2"


# 테스트 실행을 위한 픽스처
@pytest.fixture
def sample_supplier_data():
    """테스트용 공급사 데이터"""
    return {
        "id": str(uuid4()),
        "name": "테스트 공급사",
        "code": "test_supplier",
        "type": "api",
        "is_active": True
    }


@pytest.fixture
def sample_product_data():
    """테스트용 상품 데이터"""
    return {
        "id": str(uuid4()),
        "title": "테스트 상품",
        "price": 10000,
        "description": "테스트 상품 설명",
        "stock_quantity": 100
    }


# 통합 테스트
class TestIntegration:
    """통합 테스트 클래스"""
    
    @pytest.mark.asyncio
    async def test_full_collection_pipeline(self, sample_supplier_data, sample_product_data):
        """전체 수집 파이프라인 통합 테스트"""
        # Arrange
        collection_service = CollectionService()
        pipeline = ProductPipeline()
        
        supplier_id = UUID(sample_supplier_data["id"])
        
        # Mock 설정
        with patch.object(collection_service, '_get_supplier') as mock_get_supplier, \
             patch.object(collection_service, '_create_collection_job') as mock_create_job, \
             patch.object(collection_service, '_create_connector') as mock_create_connector, \
             patch.object(collection_service, '_collect_products') as mock_collect, \
             patch.object(pipeline, '_get_raw_data') as mock_get_raw_data, \
             patch.object(pipeline, '_get_supplier') as mock_get_supplier_pipeline, \
             patch.object(pipeline, '_create_connector') as mock_create_connector_pipeline, \
             patch.object(pipeline, '_save_normalized_product') as mock_save_product, \
             patch.object(pipeline, '_mark_processed') as mock_mark_processed:
            
            # 수집 서비스 Mock
            mock_get_supplier.return_value = sample_supplier_data
            mock_create_job.return_value = uuid4()
            mock_connector = Mock()
            mock_connector.collect_products = AsyncMock(return_value=[sample_product_data])
            mock_create_connector.return_value = mock_connector
            mock_collect.return_value = [sample_product_data]
            
            # 파이프라인 Mock
            mock_get_raw_data.return_value = {
                "id": str(uuid4()),
                "supplier_id": str(supplier_id),
                "raw_data": sample_product_data,
                "is_processed": False
            }
            mock_get_supplier_pipeline.return_value = sample_supplier_data
            mock_connector_pipeline = Mock()
            mock_connector_pipeline.transform_product.return_value = sample_product_data
            mock_create_connector_pipeline.return_value = mock_connector_pipeline
            mock_save_product.return_value = uuid4()
            mock_mark_processed.return_value = True
            
            # Act
            collection_result = await collection_service.collect_from_supplier(
                supplier_id=supplier_id,
                job_name="통합 테스트"
            )
            
            pipeline_result = await pipeline.process_raw_data(
                raw_data_id=uuid4(),
                auto_list=False
            )
            
            # Assert
            assert collection_result["status"] == "success"
            assert pipeline_result["status"] == "success"


if __name__ == "__main__":
    # 테스트 실행
    pytest.main([__file__, "-v"])
