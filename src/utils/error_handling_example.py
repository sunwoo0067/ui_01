"""
에러 처리 패턴 적용 예시
기존 서비스에 통일된 에러 처리 적용
"""

import asyncio
from typing import Dict, Any, Optional, List
from uuid import UUID
from loguru import logger

from src.utils.error_handler import (
    BaseAPIError,
    APIConnectionError,
    APIAuthenticationError,
    DatabaseError,
    ValidationError,
    BusinessLogicError,
    ErrorHandler,
    safe_async_execute,
    validate_required_fields,
    validate_data_type
)


class ImprovedCollectionService:
    """개선된 수집 서비스 (에러 처리 강화)"""
    
    def __init__(self):
        self.connector_factory = None  # 실제 구현에서는 ConnectorFactory 사용
    
    async def collect_from_supplier_safe(
        self,
        supplier_id: UUID,
        account_id: Optional[UUID] = None,
        job_name: str = "Manual Collection",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        안전한 공급사 상품 수집 (에러 처리 강화)
        
        Args:
            supplier_id: 공급사 ID
            account_id: 공급사 계정 ID
            job_name: 작업 이름
            **kwargs: 수집 파라미터
            
        Returns:
            수집 결과 또는 에러 정보
        """
        context = {
            "supplier_id": str(supplier_id),
            "account_id": str(account_id) if account_id else None,
            "job_name": job_name,
            "kwargs": kwargs
        }
        
        try:
            # 1. 입력 검증
            validate_required_fields(
                {"supplier_id": supplier_id, "job_name": job_name},
                ["supplier_id", "job_name"],
                "수집 요청"
            )
            
            # 2. 공급사 정보 조회
            supplier = await self._get_supplier_safe(supplier_id, context)
            if isinstance(supplier, BaseAPIError):
                return {"status": "error", "error": supplier.to_dict()}
            
            # 3. 수집 작업 생성
            job_id = await self._create_collection_job_safe(
                supplier_id, account_id, supplier["type"], job_name, kwargs, context
            )
            if isinstance(job_id, BaseAPIError):
                return {"status": "error", "error": job_id.to_dict()}
            
            # 4. 커넥터 생성 및 상품 수집
            connector = self._create_connector_safe(supplier, account_id, context)
            if isinstance(connector, BaseAPIError):
                return {"status": "error", "error": connector.to_dict()}
            
            # 5. 상품 수집 실행
            products = await self._collect_products_safe(connector, context)
            if isinstance(products, BaseAPIError):
                return {"status": "error", "error": products.to_dict()}
            
            # 6. 성공 결과 반환
            return {
                "status": "success",
                "job_id": str(job_id),
                "products_collected": len(products),
                "supplier_name": supplier["name"]
            }
            
        except ValidationError as e:
            ErrorHandler.log_error(e, context)
            return {"status": "validation_error", "error": e.to_dict()}
        
        except Exception as e:
            ErrorHandler.log_error(e, context)
            return {
                "status": "unexpected_error",
                "error": {
                    "message": str(e),
                    "error_code": "UNKNOWN_ERROR",
                    "context": context
                }
            }
    
    async def _get_supplier_safe(
        self, 
        supplier_id: UUID, 
        context: Dict[str, Any]
    ) -> Union[Dict[str, Any], BaseAPIError]:
        """안전한 공급사 정보 조회"""
        try:
            # 실제 구현에서는 Supabase 클라이언트 사용
            # 여기서는 예시로 더미 데이터 반환
            return {
                "id": str(supplier_id),
                "name": "테스트 공급사",
                "type": "api",
                "is_active": True
            }
        except Exception as e:
            return ErrorHandler.handle_database_error(
                e, "공급사 정보 조회", context
            )
    
    async def _create_collection_job_safe(
        self,
        supplier_id: UUID,
        account_id: Optional[UUID],
        supplier_type: str,
        job_name: str,
        kwargs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Union[UUID, BaseAPIError]:
        """안전한 수집 작업 생성"""
        try:
            # 실제 구현에서는 데이터베이스에 작업 레코드 생성
            # 여기서는 예시로 더미 UUID 반환
            import uuid
            return uuid.uuid4()
        except Exception as e:
            return ErrorHandler.handle_database_error(
                e, "수집 작업 생성", context
            )
    
    def _create_connector_safe(
        self,
        supplier: Dict[str, Any],
        account_id: Optional[UUID],
        context: Dict[str, Any]
    ) -> Union[Any, BaseAPIError]:
        """안전한 커넥터 생성"""
        try:
            # 실제 구현에서는 ConnectorFactory 사용
            # 여기서는 예시로 더미 커넥터 반환
            return MockConnector()
        except Exception as e:
            return BaseAPIError(
                message="커넥터 생성 실패",
                details=context,
                original_error=e
            )
    
    async def _collect_products_safe(
        self,
        connector: Any,
        context: Dict[str, Any]
    ) -> Union[List[Dict[str, Any]], BaseAPIError]:
        """안전한 상품 수집"""
        try:
            # 실제 구현에서는 커넥터의 collect_products 메서드 호출
            # 여기서는 예시로 더미 데이터 반환
            return [
                {"id": "1", "title": "테스트 상품 1", "price": 10000},
                {"id": "2", "title": "테스트 상품 2", "price": 20000}
            ]
        except Exception as e:
            return ErrorHandler.handle_api_error(
                e, "상품 수집", context
            )


class MockConnector:
    """테스트용 더미 커넥터"""
    
    async def collect_products(self, **kwargs):
        """더미 상품 수집"""
        return [
            {"id": "1", "title": "더미 상품 1", "price": 10000},
            {"id": "2", "title": "더미 상품 2", "price": 20000}
        ]


class ImprovedProductPipeline:
    """개선된 상품 파이프라인 (에러 처리 강화)"""
    
    async def process_raw_data_safe(
        self, 
        raw_data_id: UUID, 
        auto_list: bool = False
    ) -> Dict[str, Any]:
        """
        안전한 원본 데이터 처리
        
        Args:
            raw_data_id: 원본 데이터 ID
            auto_list: 자동 등록 여부
            
        Returns:
            처리 결과 또는 에러 정보
        """
        context = {
            "raw_data_id": str(raw_data_id),
            "auto_list": auto_list
        }
        
        try:
            # 1. 입력 검증
            validate_data_type(raw_data_id, UUID, "raw_data_id")
            validate_data_type(auto_list, bool, "auto_list")
            
            # 2. 원본 데이터 조회
            raw_data_record = await self._get_raw_data_safe(raw_data_id, context)
            if isinstance(raw_data_record, BaseAPIError):
                return {"status": "error", "error": raw_data_record.to_dict()}
            
            # 3. 이미 처리된 데이터 확인
            if raw_data_record.get("is_processed"):
                logger.info(f"원본 데이터 이미 처리됨: {raw_data_id}")
                return {"status": "already_processed"}
            
            # 4. 공급사 정보 조회
            supplier = await self._get_supplier_safe(
                UUID(raw_data_record["supplier_id"]), context
            )
            if isinstance(supplier, BaseAPIError):
                return {"status": "error", "error": supplier.to_dict()}
            
            # 5. 데이터 변환
            normalized_data = await self._transform_data_safe(
                raw_data_record, supplier, context
            )
            if isinstance(normalized_data, BaseAPIError):
                return {"status": "error", "error": normalized_data.to_dict()}
            
            # 6. 정규화된 상품 저장
            normalized_product_id = await self._save_normalized_product_safe(
                raw_data_record, normalized_data, context
            )
            if isinstance(normalized_product_id, BaseAPIError):
                return {"status": "error", "error": normalized_product_id.to_dict()}
            
            # 7. 처리 완료 표시
            await self._mark_processed_safe(raw_data_id, context)
            
            # 8. 자동 등록 (요청된 경우)
            if auto_list:
                list_result = await self._auto_list_product_safe(
                    normalized_product_id, UUID(raw_data_record["supplier_id"]), context
                )
                if isinstance(list_result, BaseAPIError):
                    logger.warning(f"자동 등록 실패: {list_result.message}")
            
            return {
                "status": "success",
                "normalized_product_id": str(normalized_product_id),
                "auto_listed": auto_list
            }
            
        except ValidationError as e:
            ErrorHandler.log_error(e, context)
            return {"status": "validation_error", "error": e.to_dict()}
        
        except Exception as e:
            ErrorHandler.log_error(e, context)
            return {
                "status": "unexpected_error",
                "error": {
                    "message": str(e),
                    "error_code": "UNKNOWN_ERROR",
                    "context": context
                }
            }
    
    async def _get_raw_data_safe(
        self, 
        raw_data_id: UUID, 
        context: Dict[str, Any]
    ) -> Union[Dict[str, Any], BaseAPIError]:
        """안전한 원본 데이터 조회"""
        try:
            # 실제 구현에서는 Supabase 클라이언트 사용
            return {
                "id": str(raw_data_id),
                "supplier_id": "test-supplier-id",
                "raw_data": {"title": "테스트 상품", "price": 10000},
                "is_processed": False
            }
        except Exception as e:
            return ErrorHandler.handle_database_error(
                e, "원본 데이터 조회", context
            )
    
    async def _get_supplier_safe(
        self, 
        supplier_id: UUID, 
        context: Dict[str, Any]
    ) -> Union[Dict[str, Any], BaseAPIError]:
        """안전한 공급사 정보 조회"""
        try:
            # 실제 구현에서는 Supabase 클라이언트 사용
            return {
                "id": str(supplier_id),
                "name": "테스트 공급사",
                "type": "api"
            }
        except Exception as e:
            return ErrorHandler.handle_database_error(
                e, "공급사 정보 조회", context
            )
    
    async def _transform_data_safe(
        self,
        raw_data_record: Dict[str, Any],
        supplier: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Union[Dict[str, Any], BaseAPIError]:
        """안전한 데이터 변환"""
        try:
            # 실제 구현에서는 커넥터의 transform_product 메서드 사용
            return {
                "title": raw_data_record["raw_data"]["title"],
                "price": raw_data_record["raw_data"]["price"],
                "supplier_product_id": "test-product-id"
            }
        except Exception as e:
            return BaseAPIError(
                message="데이터 변환 실패",
                details=context,
                original_error=e
            )
    
    async def _save_normalized_product_safe(
        self,
        raw_data_record: Dict[str, Any],
        normalized_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Union[UUID, BaseAPIError]:
        """안전한 정규화된 상품 저장"""
        try:
            # 실제 구현에서는 Supabase 클라이언트 사용
            import uuid
            return uuid.uuid4()
        except Exception as e:
            return ErrorHandler.handle_database_error(
                e, "정규화된 상품 저장", context
            )
    
    async def _mark_processed_safe(
        self, 
        raw_data_id: UUID, 
        context: Dict[str, Any]
    ) -> Union[bool, BaseAPIError]:
        """안전한 처리 완료 표시"""
        try:
            # 실제 구현에서는 Supabase 클라이언트 사용
            return True
        except Exception as e:
            return ErrorHandler.handle_database_error(
                e, "처리 완료 표시", context
            )
    
    async def _auto_list_product_safe(
        self,
        normalized_product_id: UUID,
        supplier_id: UUID,
        context: Dict[str, Any]
    ) -> Union[bool, BaseAPIError]:
        """안전한 자동 상품 등록"""
        try:
            # 실제 구현에서는 마켓플레이스 등록 로직 사용
            return True
        except Exception as e:
            return BaseAPIError(
                message="자동 등록 실패",
                details=context,
                original_error=e
            )


# 사용 예시
async def example_usage():
    """에러 처리 패턴 사용 예시"""
    
    # 수집 서비스 테스트
    collection_service = ImprovedCollectionService()
    result = await collection_service.collect_from_supplier_safe(
        supplier_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        job_name="테스트 수집"
    )
    
    print("수집 결과:", result)
    
    # 파이프라인 테스트
    pipeline = ImprovedProductPipeline()
    result = await pipeline.process_raw_data_safe(
        raw_data_id=UUID("123e4567-e89b-12d3-a456-426614174001"),
        auto_list=True
    )
    
    print("파이프라인 결과:", result)


if __name__ == "__main__":
    asyncio.run(example_usage())
