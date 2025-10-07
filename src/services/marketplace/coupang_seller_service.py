"""
쿠팡 Wing API 판매자 서비스
상품 등록/수정/삭제, 재고 관리, 주문 조회
"""

import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from uuid import UUID
import aiohttp
from loguru import logger

from src.services.database_service import DatabaseService
from src.utils.error_handler import ErrorHandler


class CoupangSellerService:
    """쿠팡 Wing API 판매자 서비스"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.error_handler = ErrorHandler()
        self.base_url = "https://api-gateway.coupang.com"
        
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
                "operation": "get_coupang_credentials",
                "sales_account_id": str(sales_account_id)
            })
            raise
    
    def _generate_hmac_signature(self, method: str, url: str, access_key: str, secret_key: str) -> str:
        """HMAC SHA256 서명 생성"""
        try:
            datetime_str = datetime.now(timezone.utc).strftime('%y%m%d') + 'T' + \
                          datetime.now(timezone.utc).strftime('%H%M%S') + 'Z'
            
            message = f"{datetime_str}{method}{url}"
            signature = hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_str}, signature={signature}"
            
        except Exception as e:
            logger.error(f"HMAC 서명 생성 실패: {e}")
            raise
    
    async def _make_api_call(
        self,
        sales_account_id: UUID,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """쿠팡 API 호출"""
        start_time = datetime.now()
        
        try:
            credentials = await self._get_credentials(sales_account_id)
            access_key = credentials.get("access_key")
            secret_key = credentials.get("secret_key")
            vendor_id = credentials.get("vendor_id")
            
            if not all([access_key, secret_key]):
                raise ValueError("쿠팡 API 인증 정보가 누락되었습니다")
            
            url = f"{self.base_url}{endpoint}"
            auth_signature = self._generate_hmac_signature(method, endpoint, access_key, secret_key)
            
            headers = {
                "Content-Type": "application/json;charset=UTF-8",
                "Authorization": auth_signature,
                "X-EXTENDED-TIMEOUT": "90000"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=90)
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
                "operation": "coupang_api_call",
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
            logger.info(f"쿠팡 상품 등록 시작: {product_data.get('title')}")
            
            # 쿠팡 상품 등록 API 형식으로 변환
            coupang_product = {
                "sellerProductName": product_data.get("title"),
                "displayCategoryCode": product_data.get("category_code", ""),
                "salePrice": int(product_data.get("price", 0)),
                "originalPrice": int(product_data.get("original_price", product_data.get("price", 0))),
                "maximumBuyCount": product_data.get("max_buy_count", 999),
                "outboundShippingTimeDay": product_data.get("shipping_days", 3),
                "brand": product_data.get("brand", ""),
                "manufacturerName": product_data.get("manufacturer", ""),
                "taxType": "TAX",
                "certificationTargetExcludeContent": {
                    "childCertifiedProductExclusionYn": "Y",
                    "kcCertifiedProductExclusionYn": "Y"
                },
                "searchTags": product_data.get("tags", []),
                "images": [{"imageUrl": img} for img in product_data.get("images", [])[:10]],
                "notice": product_data.get("notice", {}),
                "saleStartedAt": datetime.now(timezone.utc).isoformat(),
                "saleEndedAt": product_data.get("sale_end_date", ""),
                "displayable": True,
                "items": product_data.get("items", [])
            }
            
            # API 호출
            result = await self._make_api_call(
                sales_account_id,
                "POST",
                "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products",
                coupang_product
            )
            
            logger.info(f"✅ 쿠팡 상품 등록 성공: {result.get('data', {}).get('sellerProductId')}")
            
            return {
                "success": True,
                "marketplace_product_id": result.get("data", {}).get("sellerProductId"),
                "response": result.get("data")
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "create_coupang_product",
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
            logger.info(f"쿠팡 상품 수정 시작: {marketplace_product_id}")
            
            # 쿠팡 상품 수정 API 형식으로 변환
            coupang_product = {
                "sellerProductName": product_data.get("title"),
                "salePrice": int(product_data.get("price", 0)),
                "originalPrice": int(product_data.get("original_price", product_data.get("price", 0))),
                # ... 필요한 필드만 포함
            }
            
            result = await self._make_api_call(
                sales_account_id,
                "PUT",
                f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{marketplace_product_id}",
                coupang_product
            )
            
            logger.info(f"✅ 쿠팡 상품 수정 성공: {marketplace_product_id}")
            
            return {
                "success": True,
                "response": result.get("data")
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "update_coupang_product",
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
            logger.info(f"쿠팡 재고 수정 시작: {marketplace_product_id} -> {quantity}")
            
            inventory_data = {
                "vendorItemId": marketplace_product_id,
                "quantity": quantity
            }
            
            result = await self._make_api_call(
                sales_account_id,
                "PUT",
                "/v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/inventories",
                inventory_data
            )
            
            logger.info(f"✅ 쿠팡 재고 수정 성공: {marketplace_product_id}")
            
            return {
                "success": True,
                "response": result.get("data")
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "update_coupang_inventory",
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
            logger.info(f"쿠팡 주문 조회 시작")
            
            # 쿼리 파라미터 구성
            params = []
            if created_after:
                params.append(f"createdAfterAt={created_after.isoformat()}")
            if created_before:
                params.append(f"createdBeforeAt={created_before.isoformat()}")
            if status:
                params.append(f"status={status}")
            
            endpoint = "/v2/providers/seller_api/apis/api/v1/marketplace/orders"
            if params:
                endpoint += "?" + "&".join(params)
            
            result = await self._make_api_call(
                sales_account_id,
                "GET",
                endpoint
            )
            
            orders = result.get("data", {}).get("data", [])
            logger.info(f"✅ 쿠팡 주문 조회 성공: {len(orders)}개")
            
            return {
                "success": True,
                "orders": orders,
                "total_count": len(orders)
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "get_coupang_orders"
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
        """상품 삭제"""
        try:
            logger.info(f"쿠팡 상품 삭제 시작: {marketplace_product_id}")
            
            result = await self._make_api_call(
                sales_account_id,
                "DELETE",
                f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{marketplace_product_id}"
            )
            
            logger.info(f"✅ 쿠팡 상품 삭제 성공: {marketplace_product_id}")
            
            return {
                "success": True,
                "response": result.get("data")
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "delete_coupang_product",
                "product_id": marketplace_product_id
            })
            return {
                "success": False,
                "error": str(e)
            }

