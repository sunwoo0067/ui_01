"""
통합 마켓플레이스 관리 서비스
여러 마켓플레이스에 대한 상품 등록, 재고 동기화, 주문 관리 통합
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from uuid import UUID
from loguru import logger

from src.services.database_service import DatabaseService
from src.utils.error_handler import ErrorHandler
from src.services.marketplace.coupang_seller_service import CoupangSellerService
from src.services.marketplace.naver_seller_service import NaverSellerService
from src.services.marketplace.elevenst_seller_service import ElevenStSellerService
from src.services.marketplace.gmarket_seller_service import GmarketSellerService
from src.services.marketplace.auction_seller_service import AuctionSellerService


class MarketplaceManager:
    """통합 마켓플레이스 관리 서비스"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.error_handler = ErrorHandler()
        
        # 마켓플레이스별 서비스 초기화
        self.services = {
            "coupang": CoupangSellerService(),
            "naver_smartstore": NaverSellerService(),
            "11st": ElevenStSellerService(),
            "gmarket": GmarketSellerService(),
            "auction": AuctionSellerService()
        }
    
    async def get_marketplace_service(self, marketplace_code: str):
        """마켓플레이스 코드로 서비스 가져오기"""
        service = self.services.get(marketplace_code)
        if not service:
            raise ValueError(f"지원하지 않는 마켓플레이스: {marketplace_code}")
        return service
    
    async def register_product(
        self,
        normalized_product_id: UUID,
        marketplace_id: UUID,
        sales_account_id: UUID,
        custom_title: Optional[str] = None,
        custom_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        상품을 마켓플레이스에 등록
        
        Args:
            normalized_product_id: 정규화된 상품 ID
            marketplace_id: 마켓플레이스 ID
            sales_account_id: 판매 계정 ID
            custom_title: 커스텀 제목 (선택)
            custom_price: 커스텀 가격 (선택)
        """
        try:
            logger.info(f"상품 등록 시작: {normalized_product_id} -> {marketplace_id}")
            
            # 1. 정규화된 상품 조회
            product = await self.db_service.select_data(
                "normalized_products",
                {"id": str(normalized_product_id)}
            )
            
            if not product or len(product) == 0:
                raise ValueError(f"상품을 찾을 수 없습니다: {normalized_product_id}")
            
            product_data = product[0]
            
            # 2. 마켓플레이스 정보 조회
            marketplace = await self.db_service.select_data(
                "sales_marketplaces",
                {"id": str(marketplace_id)}
            )
            
            if not marketplace or len(marketplace) == 0:
                raise ValueError(f"마켓플레이스를 찾을 수 없습니다: {marketplace_id}")
            
            marketplace_code = marketplace[0].get("code")
            
            # 3. 마켓플레이스 서비스 가져오기
            service = await self.get_marketplace_service(marketplace_code)
            
            # 4. 상품 데이터 준비
            marketplace_product_data = {
                "title": custom_title or product_data.get("title"),
                "description": product_data.get("description", ""),
                "price": custom_price or float(product_data.get("price", 0)),
                "original_price": float(product_data.get("original_price", 0)),
                "stock_quantity": product_data.get("stock_quantity", 0),
                "images": product_data.get("images", []),
                "category": product_data.get("category", ""),
                "brand": product_data.get("brand", ""),
                "tags": product_data.get("tags", [])
            }
            
            # 5. 마켓플레이스에 상품 등록
            result = await service.create_product(
                sales_account_id,
                marketplace_product_data
            )
            
            if not result.get("success"):
                raise Exception(f"상품 등록 실패: {result.get('error')}")
            
            # 6. listed_products 테이블에 저장
            listed_product_id = await self.db_service.insert_data(
                "listed_products",
                {
                    "normalized_product_id": str(normalized_product_id),
                    "marketplace_id": str(marketplace_id),
                    "sales_account_id": str(sales_account_id),
                    "marketplace_product_id": result.get("marketplace_product_id"),
                    "selling_price": custom_price or float(product_data.get("price", 0)),
                    "title": custom_title or product_data.get("title"),
                    "description": product_data.get("description", ""),
                    "images": product_data.get("images", []),
                    "status": "active",
                    "marketplace_status": "active",
                    "marketplace_response": result.get("response"),
                    "last_synced_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
            logger.info(f"✅ 상품 등록 완료: {listed_product_id}")
            
            return {
                "success": True,
                "listed_product_id": listed_product_id,
                "marketplace_product_id": result.get("marketplace_product_id"),
                "marketplace": marketplace_code
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "register_product",
                "normalized_product_id": str(normalized_product_id),
                "marketplace_id": str(marketplace_id)
            })
            return {
                "success": False,
                "error": str(e)
            }
    
    async def register_product_to_multiple_marketplaces(
        self,
        normalized_product_id: UUID,
        marketplace_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        여러 마켓플레이스에 동시 상품 등록
        
        Args:
            normalized_product_id: 정규화된 상품 ID
            marketplace_configs: 마켓플레이스 설정 리스트
                [{marketplace_id, sales_account_id, custom_title, custom_price}, ...]
        """
        try:
            logger.info(f"다중 마켓플레이스 등록 시작: {len(marketplace_configs)}개")
            
            # 병렬 처리
            tasks = []
            for config in marketplace_configs:
                task = self.register_product(
                    normalized_product_id,
                    UUID(config["marketplace_id"]),
                    UUID(config["sales_account_id"]),
                    config.get("custom_title"),
                    config.get("custom_price")
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 집계
            success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            failed_count = len(results) - success_count
            
            logger.info(f"✅ 다중 등록 완료: 성공 {success_count}개, 실패 {failed_count}개")
            
            return {
                "success": True,
                "total": len(results),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "register_product_to_multiple_marketplaces",
                "normalized_product_id": str(normalized_product_id)
            })
            return {
                "success": False,
                "error": str(e)
            }
    
    async def sync_inventory(
        self,
        listed_product_id: UUID,
        new_quantity: int
    ) -> Dict[str, Any]:
        """재고 동기화"""
        try:
            logger.info(f"재고 동기화 시작: {listed_product_id} -> {new_quantity}")
            
            # 1. listed_product 조회
            listed_product = await self.db_service.select_data(
                "listed_products",
                {"id": str(listed_product_id)}
            )
            
            if not listed_product or len(listed_product) == 0:
                raise ValueError(f"등록 상품을 찾을 수 없습니다: {listed_product_id}")
            
            product_data = listed_product[0]
            marketplace_id = product_data.get("marketplace_id")
            sales_account_id = product_data.get("sales_account_id")
            marketplace_product_id = product_data.get("marketplace_product_id")
            
            # 2. 마켓플레이스 정보 조회
            marketplace = await self.db_service.select_data(
                "sales_marketplaces",
                {"id": marketplace_id}
            )
            
            marketplace_code = marketplace[0].get("code")
            
            # 3. 마켓플레이스 서비스로 재고 업데이트
            service = await self.get_marketplace_service(marketplace_code)
            
            result = await service.update_inventory(
                UUID(sales_account_id),
                marketplace_product_id,
                new_quantity
            )
            
            # 4. 동기화 로그 저장
            await self.db_service.insert_data(
                "marketplace_inventory_sync_log",
                {
                    "marketplace_id": marketplace_id,
                    "sales_account_id": sales_account_id,
                    "listed_product_id": str(listed_product_id),
                    "sync_type": "manual",
                    "sync_action": "update",
                    "new_quantity": new_quantity,
                    "status": "success" if result.get("success") else "failed",
                    "error_message": result.get("error") if not result.get("success") else None
                }
            )
            
            logger.info(f"✅ 재고 동기화 완료: {listed_product_id}")
            
            return result
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "sync_inventory",
                "listed_product_id": str(listed_product_id)
            })
            return {
                "success": False,
                "error": str(e)
            }
    
    async def bulk_sync_inventory(
        self,
        inventory_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """대량 재고 동기화"""
        try:
            logger.info(f"대량 재고 동기화 시작: {len(inventory_updates)}개")
            
            # 병렬 처리
            tasks = []
            for update in inventory_updates:
                task = self.sync_inventory(
                    UUID(update["listed_product_id"]),
                    update["quantity"]
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 집계
            success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            failed_count = len(results) - success_count
            
            logger.info(f"✅ 대량 재고 동기화 완료: 성공 {success_count}개, 실패 {failed_count}개")
            
            return {
                "success": True,
                "total": len(results),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "bulk_sync_inventory"
            })
            return {
                "success": False,
                "error": str(e)
            }
    
    async def sync_orders(
        self,
        marketplace_id: UUID,
        sales_account_id: UUID,
        created_after: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """주문 동기화"""
        try:
            logger.info(f"주문 동기화 시작: {marketplace_id}")
            
            # 1. 마켓플레이스 정보 조회
            marketplace = await self.db_service.select_data(
                "sales_marketplaces",
                {"id": str(marketplace_id)}
            )
            
            if not marketplace or len(marketplace) == 0:
                raise ValueError(f"마켓플레이스를 찾을 수 없습니다: {marketplace_id}")
            
            marketplace_code = marketplace[0].get("code")
            
            # 2. 마켓플레이스 서비스로 주문 조회
            service = await self.get_marketplace_service(marketplace_code)
            
            result = await service.get_orders(
                sales_account_id,
                created_after=created_after
            )
            
            if not result.get("success"):
                raise Exception(f"주문 조회 실패: {result.get('error')}")
            
            orders = result.get("orders", [])
            
            # 3. 주문 데이터를 DB에 저장
            saved_count = 0
            for order in orders:
                try:
                    # 중복 체크
                    existing = await self.db_service.select_data(
                        "marketplace_orders",
                        {
                            "marketplace_id": str(marketplace_id),
                            "order_id": str(order.get("order_id", order.get("orderId", "")))
                        }
                    )
                    
                    if existing:
                        # 주문 업데이트
                        await self.db_service.update_data(
                            "marketplace_orders",
                            {"id": existing[0]["id"]},
                            {
                                "order_status": order.get("status", "pending"),
                                "marketplace_data": order,
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }
                        )
                    else:
                        # 새 주문 저장
                        await self.db_service.insert_data(
                            "marketplace_orders",
                            {
                                "marketplace_id": str(marketplace_id),
                                "sales_account_id": str(sales_account_id),
                                "order_id": str(order.get("order_id", order.get("orderId", ""))),
                                "order_status": order.get("status", "pending"),
                                "items": order.get("items", []),
                                "total_amount": float(order.get("total_amount", 0)),
                                "final_amount": float(order.get("final_amount", order.get("total_amount", 0))),
                                "marketplace_data": order,
                                "ordered_at": order.get("ordered_at", datetime.now(timezone.utc).isoformat())
                            }
                        )
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.warning(f"주문 저장 실패: {e}")
                    continue
            
            logger.info(f"✅ 주문 동기화 완료: {saved_count}개")
            
            return {
                "success": True,
                "total_orders": len(orders),
                "saved_count": saved_count
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "sync_orders",
                "marketplace_id": str(marketplace_id)
            })
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_marketplace_summary(self) -> Dict[str, Any]:
        """마켓플레이스별 요약 통계"""
        try:
            # marketplace_sales_summary 뷰 조회
            summary = await self.db_service.select_data("marketplace_sales_summary", {})
            
            return {
                "success": True,
                "summary": summary
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "operation": "get_marketplace_summary"
            })
            return {
                "success": False,
                "error": str(e),
                "summary": []
            }

