#!/usr/bin/env python3
"""
오너클랜 데이터 저장 서비스
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

from src.config.settings import settings
from src.utils.error_handler import ErrorHandler
from src.services.database_service import database_service


class OwnerClanDataStorage:
    """오너클랜 데이터 저장 서비스"""
    
    def __init__(self):
        self.settings = settings
        self.error_handler = ErrorHandler()
        self.db_service = database_service
    
    async def save_products(self, products: List[Dict[str, Any]]) -> int:
        """상품 데이터 저장"""
        try:
            if not products:
                logger.info("저장할 상품 데이터가 없습니다")
                return 0
            
            logger.info(f"상품 데이터 저장 시작: {len(products)}개")
            
            saved_count = 0
            for product in products:
                try:
                    # 원본 데이터 저장 (raw_product_data 테이블)
                    raw_data = {
                        "supplier_id": await self._get_supplier_id("ownerclan"),
                        "supplier_account_id": await self._get_supplier_account_id("ownerclan", product["account_name"]),
                        "raw_data": product,
                        "collection_method": "api",
                        "collection_source": "https://api.ownerclan.com/v1/graphql",
                        "supplier_product_id": product["supplier_key"],
                        "is_processed": False,
                        "data_hash": self._calculate_hash(product),
                        "metadata": {
                            "collected_at": product["collected_at"],
                            "account_name": product["account_name"]
                        }
                    }
                    
                    # 기존 데이터 확인
                    existing = await self.db_service.select_data(
                        "raw_product_data",
                        {"supplier_product_id": product["supplier_key"]}
                    )
                    
                    if existing:
                        # 업데이트
                        await self.db_service.update_data(
                            "raw_product_data",
                            {"supplier_product_id": product["supplier_key"]},
                            raw_data
                        )
                        logger.debug(f"원본 상품 데이터 업데이트: {product['supplier_key']}")
                    else:
                        # 새로 삽입
                        await self.db_service.insert_data("raw_product_data", raw_data)
                        logger.debug(f"원본 상품 데이터 삽입: {product['supplier_key']}")
                    
                    saved_count += 1
                    
                except Exception as e:
                    self.error_handler.log_error(e, f"상품 저장 실패: {product.get('supplier_key', 'Unknown')}")
                    continue
            
            logger.info(f"상품 데이터 저장 완료: {saved_count}개")
            return saved_count
            
        except Exception as e:
            self.error_handler.log_error(e, "상품 데이터 저장 실패")
            return 0
    
    async def save_orders(self, orders: List[Dict[str, Any]]) -> int:
        """주문 데이터 저장"""
        try:
            if not orders:
                logger.info("저장할 주문 데이터가 없습니다")
                return 0
            
            logger.info(f"주문 데이터 저장 시작: {len(orders)}개")
            
            saved_count = 0
            for order in orders:
                try:
                    # 주문 기본 정보 저장
                    order_data = {
                        "supplier_code": "ownerclan",
                        "supplier_key": order["supplier_key"],
                        "supplier_id": order["supplier_id"],
                        "status": order["status"],
                        "created_at": order["created_at"],
                        "updated_at": order["updated_at"],
                        "note": order["note"],
                        "orderer_note": order["orderer_note"],
                        "seller_note": order["seller_note"],
                        "collected_at": order["collected_at"],
                        "account_name": order["account_name"]
                    }
                    
                    # 기존 주문 확인
                    existing = await self.db_service.select_data(
                        "supplier_orders",
                        {"supplier_code": "ownerclan", "supplier_key": order["supplier_key"]}
                    )
                    
                    if existing:
                        # 업데이트
                        await self.db_service.update_data(
                            "supplier_orders",
                            {"supplier_key": order["supplier_key"]},
                            order_data
                        )
                        logger.debug(f"주문 업데이트: {order['supplier_key']}")
                    else:
                        # 새로 삽입
                        await self.db_service.insert_data("supplier_orders", order_data)
                        logger.debug(f"주문 삽입: {order['supplier_key']}")
                    
                    saved_count += 1
                    
                except Exception as e:
                    self.error_handler.log_error(e, f"주문 저장 실패: {order.get('supplier_key', 'Unknown')}")
                    continue
            
            logger.info(f"주문 데이터 저장 완료: {saved_count}개")
            return saved_count
            
        except Exception as e:
            self.error_handler.log_error(e, "주문 데이터 저장 실패")
            return 0
    
    async def save_categories(self, categories: List[Dict[str, Any]]) -> int:
        """카테고리 데이터 저장"""
        try:
            if not categories:
                logger.info("저장할 카테고리 데이터가 없습니다")
                return 0
            
            logger.info(f"카테고리 데이터 저장 시작: {len(categories)}개")
            
            saved_count = 0
            for category in categories:
                try:
                    # 카테고리 기본 정보 저장
                    category_data = {
                        "supplier_code": "ownerclan",
                        "supplier_key": category["supplier_key"],
                        "name": category["name"],
                        "parent_key": category["parent_key"],
                        "parent_name": category["parent_name"],
                        "collected_at": category["collected_at"],
                        "account_name": category["account_name"]
                    }
                    
                    # 기존 카테고리 확인
                    existing = await self.db_service.select_data(
                        "supplier_categories",
                        {"supplier_code": "ownerclan", "supplier_key": category["supplier_key"]}
                    )
                    
                    if existing:
                        # 업데이트
                        await self.db_service.update_data(
                            "supplier_categories",
                            {"supplier_key": category["supplier_key"]},
                            category_data
                        )
                        logger.debug(f"카테고리 업데이트: {category['supplier_key']}")
                    else:
                        # 새로 삽입
                        await self.db_service.insert_data("supplier_categories", category_data)
                        logger.debug(f"카테고리 삽입: {category['supplier_key']}")
                    
                    saved_count += 1
                    
                except Exception as e:
                    self.error_handler.log_error(e, f"카테고리 저장 실패: {category.get('supplier_key', 'Unknown')}")
                    continue
            
            logger.info(f"카테고리 데이터 저장 완료: {saved_count}개")
            return saved_count
            
        except Exception as e:
            self.error_handler.log_error(e, "카테고리 데이터 저장 실패")
            return 0
    
    async def _get_supplier_id(self, supplier_code: str) -> str:
        """공급사 ID 조회"""
        try:
            result = await self.db_service.select_data(
                "suppliers",
                {"code": supplier_code}
            )
            if result:
                return result[0]["id"]
            return None
        except Exception as e:
            self.error_handler.log_error(e, f"공급사 ID 조회 실패: {supplier_code}")
            return None
    
    async def _get_supplier_account_id(self, supplier_code: str, account_name: str) -> str:
        """공급사 계정 ID 조회"""
        try:
            # 먼저 공급사 ID 조회
            supplier_id = await self._get_supplier_id(supplier_code)
            if not supplier_id:
                return None
            
            result = await self.db_service.select_data(
                "supplier_accounts",
                {"supplier_id": supplier_id, "account_name": account_name}
            )
            if result:
                return result[0]["id"]
            return None
        except Exception as e:
            self.error_handler.log_error(e, f"공급사 계정 ID 조회 실패: {supplier_code}, {account_name}")
            return None
    
    def _calculate_hash(self, data: Dict[str, Any]) -> str:
        """데이터 해시 계산"""
        import hashlib
        import json
        
        # JSON 직렬화하여 해시 계산
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()


# 전역 인스턴스
ownerclan_data_storage = OwnerClanDataStorage()