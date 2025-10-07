#!/usr/bin/env python3
"""
오너클랜 데이터 저장 서비스
"""

import asyncio
import json
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
        """상품 데이터 배치 저장 (중복 사전 필터링 + bulk insert/update)"""
        try:
            if not products:
                logger.info("저장할 상품 데이터가 없습니다")
                return 0
            
            logger.info(f"상품 데이터 배치 저장 시작: {len(products)}개")
            
            # 공급사 ID와 계정 ID를 캐시 (모든 상품이 같은 계정)
            supplier_id = await self._get_supplier_id("ownerclan")
            if not supplier_id:
                logger.error("공급사 ID를 찾을 수 없습니다: ownerclan")
                return 0
            
            # 첫 상품의 account_name으로 계정 ID 조회
            account_name = products[0].get("account_name", "test_account")
            supplier_account_id = await self._get_supplier_account_id("ownerclan", account_name)
            
            # 1단계: 기존 상품 ID 목록 조회 (한 번의 쿼리)
            logger.info(f"기존 상품 ID 조회 중...")
            try:
                existing_products = await self.db_service.select_data(
                    "raw_product_data",
                    {"supplier_id": supplier_id}
                )
                existing_ids = set(p['supplier_product_id'] for p in existing_products)
                logger.info(f"기존 상품: {len(existing_ids)}개")
            except Exception as e:
                logger.warning(f"기존 상품 조회 실패 (전체 upsert로 진행): {e}")
                existing_ids = set()
            
            # 2단계: 신규/업데이트 상품 분리
            logger.info(f"신규/업데이트 상품 분류 중...")
            new_products = []
            update_products = []
            
            for product in products:
                try:
                    supplier_product_id = product["supplier_key"]
                    
                    raw_data = {
                        "supplier_id": supplier_id,
                        "supplier_account_id": supplier_account_id,
                        "raw_data": json.dumps(product, ensure_ascii=False),
                        "collection_method": "api",
                        "collection_source": "https://api.ownerclan.com/v1/graphql",
                        "supplier_product_id": supplier_product_id,
                        "is_processed": False,
                        "data_hash": self._calculate_hash(product),
                        "metadata": json.dumps({
                            "collected_at": product.get("collected_at"),
                            "account_name": product.get("account_name")
                        }, ensure_ascii=False)
                    }
                    
                    # 신규/업데이트 분류
                    if supplier_product_id in existing_ids:
                        update_products.append(raw_data)
                    else:
                        new_products.append(raw_data)
                    
                except Exception as e:
                    logger.warning(f"상품 데이터 준비 실패: {product.get('supplier_key', 'Unknown')}, {e}")
                    continue
            
            logger.info(f"신규: {len(new_products)}개, 업데이트: {len(update_products)}개")
            
            total_saved = 0
            batch_size = 5000
            
            # 3단계: 신규 상품만 bulk insert (빠름)
            if new_products:
                logger.info(f"신규 상품 저장 중: {len(new_products)}개")
                total_batches = (len(new_products) + batch_size - 1) // batch_size
                
                for i in range(0, len(new_products), batch_size):
                    chunk = new_products[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    
                    try:
                        saved_count = await self.db_service.bulk_insert("raw_product_data", chunk)
                        total_saved += saved_count
                        progress = (batch_num / total_batches) * 100
                        logger.info(f"신규 배치 {batch_num}/{total_batches}: {saved_count}개 ({progress:.1f}%)")
                    except Exception as e:
                        logger.error(f"신규 배치 {batch_num} 실패: {e}")
                        # 실패시 upsert로 재시도
                        try:
                            saved_count = await self.db_service.bulk_upsert("raw_product_data", chunk)
                            total_saved += saved_count
                        except:
                            pass
            
            # 4단계: 업데이트 상품 bulk upsert
            if update_products:
                logger.info(f"업데이트 상품 저장 중: {len(update_products)}개")
                total_batches = (len(update_products) + batch_size - 1) // batch_size
                
                for i in range(0, len(update_products), batch_size):
                    chunk = update_products[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    
                    try:
                        saved_count = await self.db_service.bulk_upsert("raw_product_data", chunk)
                        total_saved += saved_count
                        progress = (batch_num / total_batches) * 100
                        logger.info(f"업데이트 배치 {batch_num}/{total_batches}: {saved_count}개 ({progress:.1f}%)")
                    except Exception as e:
                        logger.error(f"업데이트 배치 {batch_num} 실패: {e}")
            
            logger.info(f"상품 데이터 배치 저장 완료: 총 {total_saved}개 (신규: {len(new_products)}, 업데이트: {len(update_products)})")
            return total_saved
            
        except Exception as e:
            self.error_handler.log_error(e, "상품 데이터 배치 저장 실패")
            return 0
    
    async def save_orders(self, orders: List[Dict[str, Any]]) -> int:
        """주문 데이터 배치 저장 (bulk upsert)"""
        try:
            if not orders:
                logger.info("저장할 주문 데이터가 없습니다")
                return 0
            
            logger.info(f"주문 데이터 배치 저장 시작: {len(orders)}개")
            
            # 배치 데이터 준비
            batch_data = []
            for order in orders:
                try:
                    order_data = {
                        "supplier_code": "ownerclan",
                        "supplier_key": order["supplier_key"],
                        "supplier_id": order["supplier_id"],
                        "status": order["status"],
                        "created_at": order["created_at"],
                        "updated_at": order["updated_at"],
                        "note": order.get("note", ""),
                        "orderer_note": order.get("orderer_note", ""),
                        "seller_note": order.get("seller_note", ""),
                        "collected_at": order["collected_at"],
                        "account_name": order["account_name"]
                    }
                    batch_data.append(order_data)
                    
                except Exception as e:
                    logger.warning(f"주문 데이터 준비 실패: {order.get('supplier_key', 'Unknown')}, {e}")
                    continue
            
            if not batch_data:
                logger.warning("준비된 배치 데이터가 없습니다")
                return 0
            
            # 배치 크기로 분할하여 저장 (5000개씩)
            batch_size = 5000
            total_saved = 0
            total_batches = (len(batch_data) + batch_size - 1) // batch_size
            
            logger.info(f"총 {total_batches}개 배치로 저장 시작 (배치 크기: {batch_size})")
            
            for i in range(0, len(batch_data), batch_size):
                chunk = batch_data[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                try:
                    saved_count = await self.db_service.bulk_upsert("supplier_orders", chunk)
                    total_saved += saved_count
                    progress = (batch_num / total_batches) * 100
                    logger.info(f"배치 {batch_num}/{total_batches} 저장 완료: {saved_count}개 (진행률: {progress:.1f}%, 누적: {total_saved}개)")
                except Exception as e:
                    logger.error(f"배치 {batch_num} 저장 실패: {e}")
                    # 실패한 배치는 작은 배치로 재시도
                    logger.info(f"작은 배치(100개씩)로 재시도 중...")
                    small_batch_size = 100
                    for j in range(0, len(chunk), small_batch_size):
                        small_chunk = chunk[j:j + small_batch_size]
                        try:
                            saved_count = await self.db_service.bulk_upsert("supplier_orders", small_chunk)
                            total_saved += saved_count
                        except:
                            # 최후의 수단: 개별 저장
                            for item in small_chunk:
                                try:
                                    await self.db_service.insert_data("supplier_orders", item)
                                    total_saved += 1
                                except Exception as e2:
                                    logger.warning(f"개별 저장 실패: {item.get('supplier_key')}, {e2}")
                                    continue
            
            logger.info(f"주문 데이터 배치 저장 완료: 총 {total_saved}개")
            return total_saved
            
        except Exception as e:
            self.error_handler.log_error(e, "주문 데이터 배치 저장 실패")
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