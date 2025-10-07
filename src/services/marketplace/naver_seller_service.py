"""
네이버 스마트스토어 커머스 API 판매자 서비스
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


class NaverSellerService:
    """네이버 스마트스토어 커머스 API 판매자 서비스"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.error_handler = ErrorHandler()
        self.base_url = "https://api.commerce.naver.com"
        
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
                "operation": "get_naver_credentials",
                "sales_account_id": str(sales_account_id)
            })
            raise
    
    async def _get_access_token(self, credentials: Dict[str, str]) -> str:
        """OAuth 2.0 액세스 토큰 가져오기"""
        try:
            # 저장된 토큰이 있고 유효하면 사용
            access_token = credentials.get("access_token")
            token_expires_at = credentials.get("token_expires_at")
            
            if access_token and token_expires_at:
                expires_at = datetime.fromisoformat(token_expires_at)
                if expires_at > datetime.now(timezone.utc):
                    return access_token
            
            # 토큰이 없거나 만료되었으면 새로 발급
            client_id = credentials.get("client_id")
            client_secret = credentials.get("client_secret")
            
            if not all([client_id, client_secret]):
                raise ValueError("네이버 API 인증 정보가 누락되었습니다")
            
            # 토큰 발급 API 호출 (실제 구현 필요)
            # 여기서는 간단화를 위해 저장된 토큰 사용
            return access_token or credentials.get("client_secret")
            
        except Exception as e:
            logger.error(f"네이버 액세스 토큰 가져오기 실패: {e}")
            raise
    
    async def _make_api_call(
        self,
        sales_account_id: UUID,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """네이버 API 호출"""
        start_time = datetime.now()
        
        try:
            credentials = await self._get_credentials(sales_account_id)
            access_token = await self._get_access_token(credentials)
            
            url = f"{self.base_url}{endpoint}"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
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
                "operation": "naver_api_call",
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
            logger.info(f"네이버 상품 등록 시작: {product_data.get('title')}")
            
            # 네이버 상품 등록 API 형식으로 변환
            naver_product = {
                "originProduct": {
                    "statusType": "SALE",
                    "saleType": "NEW",
                    "leafCategoryId": product_data.get("category_id", ""),
                    "name": product_data.get("title"),
                    "images": [
                        {"url": img} for img in product_data.get("images", [])[:20]
                    ],
                    "salePrice": int(product_data.get("price", 0)),
                    "stockQuantity": product_data.get("stock_quantity", 999),
                    "deliveryInfo": {
                        "deliveryType": "DELIVERY",
                        "deliveryAttributeType": "NORMAL",
                        "deliveryCompany": product_data.get("delivery_company", "CJ대한통운"),
                        "deliveryBundleGroupUsable": True,
                        "deliveryFee": {
                            "deliveryFeeType": "FREE"
                        }
                    },
                    "detailContent": product_data.get("description", ""),
                    "customerBenefit": {
                        "immediateDiscountPolicy": {
                            "discountMethod": {
                                "value": 0,
                                "unitType": "WON"
                            }
                        }
                    }
                }
            }
            
            # API 호출
            result = await self._make_api_call(
                sales_account_id,
                "POST",
                "/external/v1/products/origin-products",
                naver_product
            )
            
            logger.info(f"✅ 네이버 상품 등록 성공: {result.get('data', {}).get('originProductNo')}")
            
            return {
                "success": True,
                "marketplace_product_id": str(result.get("data", {}).get("originProductNo")),
                "response": result.get("data")
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "create_naver_product",
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
            logger.info(f"네이버 상품 수정 시작: {marketplace_product_id}")
            
            # 네이버 상품 수정 API 형식으로 변환
            naver_product = {
                "originProduct": {
                    "name": product_data.get("title"),
                    "salePrice": int(product_data.get("price", 0)),
                    "stockQuantity": product_data.get("stock_quantity"),
                    # ... 필요한 필드만 포함
                }
            }
            
            result = await self._make_api_call(
                sales_account_id,
                "PUT",
                f"/external/v1/products/origin-products/{marketplace_product_id}",
                naver_product
            )
            
            logger.info(f"✅ 네이버 상품 수정 성공: {marketplace_product_id}")
            
            return {
                "success": True,
                "response": result.get("data")
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "update_naver_product",
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
            logger.info(f"네이버 재고 수정 시작: {marketplace_product_id} -> {quantity}")
            
            inventory_data = {
                "stockQuantity": quantity
            }
            
            result = await self._make_api_call(
                sales_account_id,
                "PUT",
                f"/external/v1/products/origin-products/{marketplace_product_id}/stockQuantity",
                inventory_data
            )
            
            logger.info(f"✅ 네이버 재고 수정 성공: {marketplace_product_id}")
            
            return {
                "success": True,
                "response": result.get("data")
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "update_naver_inventory",
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
            logger.info(f"네이버 주문 조회 시작")
            
            # 쿼리 파라미터 구성
            params = []
            if created_after:
                params.append(f"lastChangedFrom={created_after.strftime('%Y-%m-%d')}")
            if created_before:
                params.append(f"lastChangedTo={created_before.strftime('%Y-%m-%d')}")
            
            endpoint = "/external/v1/pay-order/seller/product-orders"
            if params:
                endpoint += "?" + "&".join(params)
            
            result = await self._make_api_call(
                sales_account_id,
                "GET",
                endpoint
            )
            
            orders = result.get("data", {}).get("data", [])
            logger.info(f"✅ 네이버 주문 조회 성공: {len(orders)}개")
            
            return {
                "success": True,
                "orders": orders,
                "total_count": len(orders)
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "get_naver_orders"
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
            logger.info(f"네이버 상품 판매중지 시작: {marketplace_product_id}")
            
            # 네이버는 삭제 대신 판매중지 사용
            status_data = {
                "originProduct": {
                    "statusType": "SUSPENSION"
                }
            }
            
            result = await self._make_api_call(
                sales_account_id,
                "PUT",
                f"/external/v1/products/origin-products/{marketplace_product_id}",
                status_data
            )
            
            logger.info(f"✅ 네이버 상품 판매중지 성공: {marketplace_product_id}")
            
            return {
                "success": True,
                "response": result.get("data")
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "delete_naver_product",
                "product_id": marketplace_product_id
            })
            return {
                "success": False,
                "error": str(e)
            }

