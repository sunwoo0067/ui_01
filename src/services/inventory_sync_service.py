"""
재고 동기화 시스템 - 오너클랜 상품 재고 관리
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
import json
import asyncio
from loguru import logger

from src.config.settings import settings
from src.utils.error_handler import ErrorHandler, BaseAPIError, DatabaseError
from src.services.database_service import DatabaseService
from src.services.ownerclan_token_manager import OwnerClanTokenManager
from src.services.supplier_account_manager import SupplierAccountManager


class InventorySyncService:
    """재고 동기화 서비스 - 오너클랜 상품 재고 관리"""

    def __init__(self):
        self.settings = settings
        self.error_handler = ErrorHandler()
        self.db_service = DatabaseService()
        self.token_manager = OwnerClanTokenManager()
        self.account_manager = SupplierAccountManager()
        
        # API 엔드포인트
        self.api_endpoint = "https://api.ownerclan.com/v1/graphql"
        
        # 테이블명
        self.inventory_table = "inventory_sync_logs"
        self.product_inventory_table = "product_inventory"

    async def sync_all_products_inventory(self, account_name: str, 
                                        limit: int = 1000) -> Dict[str, Any]:
        """
        모든 상품의 재고 정보를 오너클랜에서 동기화
        
        Args:
            account_name: 계정 이름
            limit: 조회할 상품 수 (최대 1000)
            
        Returns:
            Dict: 동기화 결과
        """
        try:
            logger.info(f"전체 상품 재고 동기화 시작: {account_name}")
            
            # 1. 인증 토큰 획득
            token = await self.token_manager.get_auth_token(account_name)
            if not token:
                return {
                    "success": False,
                    "error": "인증 토큰 획득 실패",
                    "synced_count": 0
                }
            
            # 2. GraphQL 쿼리 구성
            query = """
            query GetAllItems($first: Int) {
                allItems(first: $first) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    edges {
                        cursor
                        node {
                            key
                            name
                            model
                            options {
                                price
                                quantity
                                optionAttributes {
                                    name
                                    value
                                }
                            }
                            metadata {
                                vendorKey
                            }
                        }
                    }
                }
            }
            """
            
            variables = {"first": min(limit, 1000)}
            
            # 3. GraphQL 쿼리 실행
            result = await self._execute_graphql_query(token, query, variables)
            
            if not result or "data" not in result or not result["data"]["allItems"]:
                return {
                    "success": False,
                    "error": "상품 데이터 조회 실패",
                    "synced_count": 0
                }
            
            items_data = result["data"]["allItems"]["edges"]
            synced_count = 0
            
            # 4. 각 상품의 재고 정보를 로컬 DB에 저장/업데이트
            for edge in items_data:
                item = edge["node"]
                try:
                    await self._sync_single_product_inventory(account_name, item)
                    synced_count += 1
                except Exception as e:
                    self.error_handler.log_error(e, {
                        'operation': "단일 상품 재고 동기화 실패",
                        'account_name': account_name,
                        'item_key': item.get("key")
                    })
                    continue
            
            # 5. 동기화 로그 저장
            await self._log_inventory_sync(
                account_name=account_name,
                sync_type="sync_all_products",
                success=True,
                synced_count=synced_count,
                sync_data={
                    "total_items": len(items_data),
                    "has_next_page": result["data"]["allItems"]["pageInfo"]["hasNextPage"],
                    "end_cursor": result["data"]["allItems"]["pageInfo"]["endCursor"]
                }
            )
            
            logger.info(f"전체 상품 재고 동기화 완료: {synced_count}개")
            
            return {
                "success": True,
                "synced_count": synced_count,
                "total_items": len(items_data),
                "has_next_page": result["data"]["allItems"]["pageInfo"]["hasNextPage"],
                "end_cursor": result["data"]["allItems"]["pageInfo"]["endCursor"]
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "전체 상품 재고 동기화 실패",
                'account_name': account_name
            })
            
            # 동기화 실패 로그 저장
            await self._log_inventory_sync(
                account_name=account_name,
                sync_type="sync_all_products",
                success=False,
                error_message=str(e)
            )
            
            return {
                "success": False,
                "error": f"재고 동기화 중 오류 발생: {str(e)}",
                "synced_count": 0
            }

    async def sync_single_product_inventory(self, account_name: str, item_key: str) -> Dict[str, Any]:
        """
        특정 상품의 재고 정보를 오너클랜에서 동기화
        
        Args:
            account_name: 계정 이름
            item_key: 상품 키
            
        Returns:
            Dict: 동기화 결과
        """
        try:
            logger.info(f"단일 상품 재고 동기화: {item_key}")
            
            # 1. 인증 토큰 획득
            token = await self.token_manager.get_auth_token(account_name)
            if not token:
                return {
                    "success": False,
                    "error": "인증 토큰 획득 실패"
                }
            
            # 2. GraphQL 쿼리 실행
            query = """
            query GetItem($key: ID!) {
                item(key: $key) {
                    key
                    name
                    model
                    options {
                        price
                        quantity
                        optionAttributes {
                            name
                            value
                        }
                    }
                    metadata {
                        vendorKey
                    }
                }
            }
            """
            
            variables = {"key": item_key}
            
            result = await self._execute_graphql_query(token, query, variables)
            
            if not result or "data" not in result or not result["data"]["item"]:
                return {
                    "success": False,
                    "error": "상품 데이터 조회 실패"
                }
            
            item_data = result["data"]["item"]
            
            # 3. 재고 정보 동기화
            await self._sync_single_product_inventory(account_name, item_data)
            
            # 4. 동기화 로그 저장
            await self._log_inventory_sync(
                account_name=account_name,
                sync_type="sync_single_product",
                item_key=item_key,
                success=True,
                sync_data=item_data
            )
            
            logger.info(f"단일 상품 재고 동기화 완료: {item_key}")
            
            return {
                "success": True,
                "item_key": item_key,
                "data": item_data
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "단일 상품 재고 동기화 실패",
                'account_name': account_name,
                'item_key': item_key
            })
            
            # 동기화 실패 로그 저장
            await self._log_inventory_sync(
                account_name=account_name,
                sync_type="sync_single_product",
                item_key=item_key,
                success=False,
                error_message=str(e)
            )
            
            return {
                "success": False,
                "error": f"재고 동기화 중 오류 발생: {str(e)}"
            }

    async def get_product_inventory(self, account_name: str, item_key: str) -> Optional[Dict[str, Any]]:
        """
        로컬 DB에서 특정 상품의 재고 정보 조회
        
        Args:
            account_name: 계정 이름
            item_key: 상품 키
            
        Returns:
            Dict: 재고 정보 또는 None
        """
        try:
            inventory = await self.db_service.select_data(
                self.product_inventory_table,
                {"account_name": account_name, "item_key": item_key}
            )
            
            if inventory:
                return inventory[0]
            else:
                return None
                
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "상품 재고 조회 실패",
                'account_name': account_name,
                'item_key': item_key
            })
            return None

    async def get_low_stock_products(self, account_name: str, threshold: int = 10) -> List[Dict[str, Any]]:
        """
        재고가 부족한 상품 목록 조회
        
        Args:
            account_name: 계정 이름
            threshold: 재고 부족 기준 (기본값: 10개)
            
        Returns:
            List[Dict]: 재고 부족 상품 목록
        """
        try:
            # 재고가 threshold 이하인 상품 조회
            low_stock_products = await self.db_service.select_data(
                self.product_inventory_table,
                {
                    "account_name": account_name,
                    "total_quantity__lte": threshold
                },
                order_by="total_quantity ASC"
            )
            
            return low_stock_products or []
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "재고 부족 상품 조회 실패",
                'account_name': account_name
            })
            return []

    async def update_product_inventory(self, account_name: str, item_key: str, 
                                     quantity_change: int, reason: str = "manual_update") -> bool:
        """
        상품 재고 수동 업데이트
        
        Args:
            account_name: 계정 이름
            item_key: 상품 키
            quantity_change: 재고 변경량 (양수: 증가, 음수: 감소)
            reason: 변경 사유
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            logger.info(f"상품 재고 수동 업데이트: {item_key}, 변경량: {quantity_change}")
            
            # 1. 현재 재고 정보 조회
            current_inventory = await self.get_product_inventory(account_name, item_key)
            if not current_inventory:
                logger.error(f"상품 재고 정보를 찾을 수 없음: {item_key}")
                return False
            
            # 2. 새로운 재고량 계산
            new_total_quantity = current_inventory["total_quantity"] + quantity_change
            if new_total_quantity < 0:
                logger.warning(f"재고가 음수가 될 수 없음: {item_key}")
                return False
            
            # 3. 재고 업데이트
            update_data = {
                "total_quantity": new_total_quantity,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "update_reason": reason
            }
            
            await self.db_service.update_data(
                self.product_inventory_table,
                {"account_name": account_name, "item_key": item_key},
                update_data
            )
            
            # 4. 재고 변경 로그 저장
            await self._log_inventory_sync(
                account_name=account_name,
                sync_type="manual_update",
                item_key=item_key,
                success=True,
                sync_data={
                    "previous_quantity": current_inventory["total_quantity"],
                    "quantity_change": quantity_change,
                    "new_quantity": new_total_quantity,
                    "reason": reason
                }
            )
            
            logger.info(f"상품 재고 업데이트 완료: {item_key} -> {new_total_quantity}")
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "상품 재고 수동 업데이트 실패",
                'account_name': account_name,
                'item_key': item_key
            })
            return False

    async def _sync_single_product_inventory(self, account_name: str, item_data: Dict[str, Any]) -> None:
        """단일 상품의 재고 정보를 로컬 DB에 동기화"""
        try:
            item_key = item_data["key"]
            
            # 총 재고량 계산
            total_quantity = sum(option["quantity"] for option in item_data["options"])
            
            # 옵션별 재고 정보 구성
            options_inventory = []
            for option in item_data["options"]:
                option_info = {
                    "price": option["price"],
                    "quantity": option["quantity"],
                    "option_attributes": option["optionAttributes"]
                }
                options_inventory.append(option_info)
            
            # 재고 데이터 구성
            inventory_record = {
                "account_name": account_name,
                "item_key": item_key,
                "item_name": item_data["name"],
                "item_model": item_data.get("model"),
                "vendor_key": item_data.get("metadata", {}).get("vendorKey"),
                "total_quantity": total_quantity,
                "options_inventory": json.dumps(options_inventory),
                "last_synced": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            # 기존 재고 정보 확인
            existing_inventory = await self.db_service.select_data(
                self.product_inventory_table,
                {"account_name": account_name, "item_key": item_key}
            )
            
            if existing_inventory:
                # 업데이트
                await self.db_service.update_data(
                    self.product_inventory_table,
                    {"account_name": account_name, "item_key": item_key},
                    inventory_record
                )
                logger.debug(f"재고 정보 업데이트: {item_key}")
            else:
                # 새로 삽입
                await self.db_service.insert_data(self.product_inventory_table, inventory_record)
                logger.debug(f"재고 정보 삽입: {item_key}")
                
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "단일 상품 재고 동기화 실패",
                'account_name': account_name,
                'item_key': item_data.get("key")
            })
            raise

    async def _execute_graphql_query(self, token: str, query: str, variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """GraphQL 쿼리 실행"""
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "variables": variables
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_endpoint,
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"GraphQL 쿼리 실패: {response.status} - {error_text}")
                    return None

    async def _log_inventory_sync(self, account_name: str, sync_type: str, 
                                item_key: Optional[str] = None, success: bool = True,
                                synced_count: int = 0, error_message: Optional[str] = None,
                                sync_data: Optional[Dict[str, Any]] = None) -> None:
        """재고 동기화 작업 로그 저장"""
        try:
            log_data = {
                "account_name": account_name,
                "sync_type": sync_type,
                "item_key": item_key,
                "success": success,
                "synced_count": synced_count,
                "error_message": error_message,
                "sync_data": json.dumps(sync_data) if sync_data else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db_service.insert_data(self.inventory_table, log_data)
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "재고 동기화 로그 저장 실패",
                'account_name': account_name,
                'sync_type': sync_type
            })


# 전역 인스턴스
inventory_sync_service = InventorySyncService()
