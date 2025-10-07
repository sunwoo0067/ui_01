"""
11번가 OpenAPI 판매자 서비스
상품 등록/수정/삭제, 재고 관리, 주문 조회
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from uuid import UUID
import aiohttp
from loguru import logger

from src.services.database_service import DatabaseService
from src.utils.error_handler import ErrorHandler


class ElevenStSellerService:
    """11번가 OpenAPI 판매자 서비스"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.error_handler = ErrorHandler()
        self.base_url = "https://openapi.11st.co.kr"
        
    async def _get_credentials(self, sales_account_id: UUID) -> Dict[str, str]:
        """판매 계정의 API 인증 정보 조회"""
        try:
            account = await self.db_service.select_data(
                "sales_accounts",
                {"id": str(sales_account_id)}
            )
            
            if not account or len(account) == 0:
                raise ValueError(f"Sales account not found: {sales_account_id}")
            
            credentials = account[0].get("account_credentials", {})
            if isinstance(credentials, str):
                credentials = json.loads(credentials)
                
            return credentials
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "get_11st_credentials",
                "sales_account_id": str(sales_account_id)
            })
            raise
    
    async def _make_api_call(
        self,
        sales_account_id: UUID,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """11번가 API 호출"""
        start_time = datetime.now()
        
        try:
            credentials = await self._get_credentials(sales_account_id)
            api_key = credentials.get("api_key")
            
            if not api_key:
                raise ValueError("11번가 API 키가 누락되었습니다")
            
            url = f"{self.base_url}{endpoint}"
            
            headers = {
                "Content-Type": "application/json",
                "openapikey": api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response_body = await response.json() if response.status != 204 else {}
                    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    # API 로그 저장
                    await self._log_api_call(
                        sales_account_id,
                        method,
                        endpoint,
                        headers,
                        data,
                        response.status,
                        dict(response.headers),
                        response_body,
                        duration_ms,
                        "success" if response.status < 400 else "failed"
                    )
                    
                    if response.status >= 400:
                        raise Exception(f"API 호출 실패: {response.status} - {response_body}")
                    
                    return {
                        "success": True,
                        "status_code": response.status,
                        "data": response_body
                    }
                    
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            await self._log_api_call(
                sales_account_id,
                method,
                endpoint,
                {},
                data,
                0,
                {},
                {},
                duration_ms,
                "error",
                str(e)
            )
            
            self.error_handler.log_error(e, {
                "operation": "11st_api_call",
                "method": method,
                "endpoint": endpoint
            })
            raise
    
    async def _log_api_call(
        self,
        sales_account_id: UUID,
        method: str,
        endpoint: str,
        request_headers: Dict,
        request_body: Optional[Dict],
        response_status: int,
        response_headers: Dict,
        response_body: Dict,
        duration_ms: int,
        status: str,
        error_message: Optional[str] = None
    ):
        """API 호출 로그 저장"""
        try:
            # marketplace_id 조회
            account = await self.db_service.select_data(
                "sales_accounts",
                {"id": str(sales_account_id)}
            )
            marketplace_id = account[0].get("marketplace_id") if account else None
            
            await self.db_service.insert_data(
                "marketplace_api_logs",
                {
                    "marketplace_id": marketplace_id,
                    "sales_account_id": str(sales_account_id),
                    "api_method": method,
                    "api_endpoint": endpoint,
                    "request_headers": request_headers,
                    "request_body": request_body,
                    "response_status": response_status,
                    "response_headers": response_headers,
                    "response_body": response_body,
                    "duration_ms": duration_ms,
                    "status": status,
                    "error_message": error_message
                }
            )
        except Exception as e:
            logger.warning(f"API 로그 저장 실패: {e}")
    
    async def create_product(
        self,
        sales_account_id: UUID,
        product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """상품 등록"""
        try:
            logger.info(f"11번가 상품 등록 시작: {product_data.get('title')}")
            
            # 11번가 상품 등록 API 형식으로 변환
            elevenst_product = {
                "action": "InsertProduct",
                "prdNo": "",
                "prdNm": product_data.get("title"),
                "prdSelTypCd": "01",  # 일반상품
                "prdStatCd": "01",  # 판매중
                "selPrc": int(product_data.get("price", 0)),
                "prdImage01": product_data.get("images", [""])[0] if product_data.get("images") else "",
                "prdDtlDesc": product_data.get("description", ""),
                "dispCtgrNo": product_data.get("category_no", ""),
                "dealerCd": product_data.get("dealer_cd", ""),
                "stdCtgrNo": product_data.get("std_category_no", ""),
                # ... 기타 필수 필드
            }
            
            # API 호출
            result = await self._make_api_call(
                sales_account_id,
                "POST",
                "/openapi/OpenApiService.tmall",
                elevenst_product
            )
            
            product_no = result.get("data", {}).get("prdNo", "")
            logger.info(f"✅ 11번가 상품 등록 성공: {product_no}")
            
            return {
                "success": True,
                "marketplace_product_id": product_no,
                "response": result.get("data")
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "create_11st_product",
                "product_title": product_data.get("title")
            })
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_product(
        self,
        sales_account_id: UUID,
        marketplace_product_id: str,
        product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """상품 수정"""
        try:
            logger.info(f"11번가 상품 수정 시작: {marketplace_product_id}")
            
            # 11번가 상품 수정 API 형식으로 변환
            elevenst_product = {
                "action": "ModifyProduct",
                "prdNo": marketplace_product_id,
                "prdNm": product_data.get("title"),
                "selPrc": int(product_data.get("price", 0)),
                # ... 필요한 필드만 포함
            }
            
            result = await self._make_api_call(
                sales_account_id,
                "POST",
                "/openapi/OpenApiService.tmall",
                elevenst_product
            )
            
            logger.info(f"✅ 11번가 상품 수정 성공: {marketplace_product_id}")
            
            return {
                "success": True,
                "response": result.get("data")
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "update_11st_product",
                "product_id": marketplace_product_id
            })
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_inventory(
        self,
        sales_account_id: UUID,
        marketplace_product_id: str,
        quantity: int
    ) -> Dict[str, Any]:
        """재고 수정"""
        try:
            logger.info(f"11번가 재고 수정 시작: {marketplace_product_id} -> {quantity}")
            
            inventory_data = {
                "action": "ModifyStock",
                "prdNo": marketplace_product_id,
                "stockQty": quantity
            }
            
            result = await self._make_api_call(
                sales_account_id,
                "POST",
                "/openapi/OpenApiService.tmall",
                inventory_data
            )
            
            logger.info(f"✅ 11번가 재고 수정 성공: {marketplace_product_id}")
            
            return {
                "success": True,
                "response": result.get("data")
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "update_11st_inventory",
                "product_id": marketplace_product_id,
                "quantity": quantity
            })
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_orders(
        self,
        sales_account_id: UUID,
        status: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """주문 조회"""
        try:
            logger.info(f"11번가 주문 조회 시작")
            
            # 주문 조회 요청
            order_request = {
                "action": "GetOrderList",
                "startDate": created_after.strftime("%Y%m%d") if created_after else "",
                "endDate": created_before.strftime("%Y%m%d") if created_before else ""
            }
            
            result = await self._make_api_call(
                sales_account_id,
                "GET",
                "/openapi/OpenApiService.tmall",
                order_request
            )
            
            orders = result.get("data", {}).get("orderList", [])
            logger.info(f"✅ 11번가 주문 조회 성공: {len(orders)}개")
            
            return {
                "success": True,
                "orders": orders,
                "total_count": len(orders)
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "get_11st_orders"
            })
            return {
                "success": False,
                "error": str(e),
                "orders": []
            }
    
    async def delete_product(
        self,
        sales_account_id: UUID,
        marketplace_product_id: str
    ) -> Dict[str, Any]:
        """상품 삭제 (판매중지)"""
        try:
            logger.info(f"11번가 상품 판매중지 시작: {marketplace_product_id}")
            
            # 11번가는 상태를 '판매중지'로 변경
            status_data = {
                "action": "ModifyProduct",
                "prdNo": marketplace_product_id,
                "prdStatCd": "02"  # 판매중지
            }
            
            result = await self._make_api_call(
                sales_account_id,
                "POST",
                "/openapi/OpenApiService.tmall",
                status_data
            )
            
            logger.info(f"✅ 11번가 상품 판매중지 성공: {marketplace_product_id}")
            
            return {
                "success": True,
                "response": result.get("data")
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "delete_11st_product",
                "product_id": marketplace_product_id
            })
            return {
                "success": False,
                "error": str(e)
            }

