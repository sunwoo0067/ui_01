"""
주문 관리 서비스 - 오너클랜 주문 동기화 및 관리
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
from src.services.transaction_system import TransactionSystem, OrderStatus, OrderInput, OrderProduct, OrderRecipient


class OrderManagementService:
    """주문 관리 서비스 - 오너클랜 주문 동기화 및 관리"""

    def __init__(self):
        self.settings = settings
        self.error_handler = ErrorHandler()
        self.db_service = DatabaseService()
        self.token_manager = OwnerClanTokenManager()
        self.account_manager = SupplierAccountManager()
        self.transaction_system = TransactionSystem()
        
        # API 엔드포인트
        self.api_endpoint = "https://api.ownerclan.com/v1/graphql"
        
        # 테이블명
        self.local_orders_table = "local_orders"
        self.order_sync_logs_table = "order_sync_logs"

    async def pull_orders_from_ownerclan(self, account_name: str, 
                                       date_from: Optional[datetime] = None,
                                       date_to: Optional[datetime] = None,
                                       status: Optional[OrderStatus] = None,
                                       limit: int = 100) -> Dict[str, Any]:
        """
        오너클랜에서 주문 데이터를 가져와서 로컬 DB에 동기화
        
        Args:
            account_name: 계정 이름
            date_from: 조회 시작 날짜 (기본값: 90일 전)
            date_to: 조회 종료 날짜 (기본값: 현재)
            status: 주문 상태 필터
            limit: 조회할 주문 수 (최대 1000)
            
        Returns:
            Dict: 동기화 결과
        """
        try:
            logger.info(f"오너클랜 주문 동기화 시작: {account_name}")
            
            # 1. 인증 토큰 획득
            token = await self.token_manager.get_auth_token(account_name)
            if not token:
                return {
                    "success": False,
                    "error": "인증 토큰 획득 실패",
                    "synced_count": 0
                }
            
            # 2. 날짜 범위 설정
            if date_from is None:
                date_from = datetime.now(timezone.utc) - timedelta(days=90)
            if date_to is None:
                date_to = datetime.now(timezone.utc)
            
            # 3. GraphQL 쿼리 구성
            query = """
            query GetAllOrders($first: Int, $dateFrom: Timestamp, $dateTo: Timestamp, $status: OrderStatus) {
                allOrders(first: $first, dateFrom: $dateFrom, dateTo: $dateTo, status: $status) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    edges {
                        cursor
                        node {
                            key
                            id
                            products {
                                quantity
                                price
                                itemKey
                                itemOptionInfo {
                                    optionAttributes {
                                        name
                                        value
                                    }
                                }
                            }
                            status
                            shippingInfo {
                                sender {
                                    name
                                    phone
                                }
                                recipient {
                                    name
                                    phone
                                }
                                destinationAddress {
                                    address
                                    postalCode
                                    city
                                    district
                                    detailAddress
                                }
                                shippingFee
                            }
                            createdAt
                            updatedAt
                            note
                            ordererNote
                            sellerNote
                        }
                    }
                }
            }
            """
            
            variables = {
                "first": min(limit, 1000),
                "dateFrom": int(date_from.timestamp()),
                "dateTo": int(date_to.timestamp())
            }
            
            if status:
                variables["status"] = status.value.upper()
            
            # 4. GraphQL 쿼리 실행
            result = await self._execute_graphql_query(token, query, variables)
            
            if not result or "data" not in result or not result["data"]["allOrders"]:
                return {
                    "success": False,
                    "error": "주문 데이터 조회 실패",
                    "synced_count": 0
                }
            
            orders_data = result["data"]["allOrders"]["edges"]
            synced_count = 0
            
            # 5. 각 주문을 로컬 DB에 저장/업데이트
            for edge in orders_data:
                order = edge["node"]
                try:
                    await self._sync_single_order(account_name, order)
                    synced_count += 1
                except Exception as e:
                    self.error_handler.log_error(e, {
                        'operation': "단일 주문 동기화 실패",
                        'account_name': account_name,
                        'order_key': order.get("key")
                    })
                    continue
            
            # 6. 동기화 로그 저장
            await self._log_sync_operation(
                account_name=account_name,
                sync_type="pull_orders",
                success=True,
                synced_count=synced_count,
                sync_data={
                    "date_from": date_from.isoformat(),
                    "date_to": date_to.isoformat(),
                    "status": status.value if status else None,
                    "total_orders": len(orders_data)
                }
            )
            
            logger.info(f"오너클랜 주문 동기화 완료: {synced_count}개")
            
            return {
                "success": True,
                "synced_count": synced_count,
                "total_orders": len(orders_data),
                "has_next_page": result["data"]["allOrders"]["pageInfo"]["hasNextPage"],
                "end_cursor": result["data"]["allOrders"]["pageInfo"]["endCursor"]
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "오너클랜 주문 동기화 실패",
                'account_name': account_name
            })
            
            # 동기화 실패 로그 저장
            await self._log_sync_operation(
                account_name=account_name,
                sync_type="pull_orders",
                success=False,
                error_message=str(e)
            )
            
            return {
                "success": False,
                "error": f"주문 동기화 중 오류 발생: {str(e)}",
                "synced_count": 0
            }

    async def get_order_status(self, account_name: str, order_key: str) -> Optional[Dict[str, Any]]:
        """
        특정 주문의 상태 조회
        
        Args:
            account_name: 계정 이름
            order_key: 주문 키
            
        Returns:
            Dict: 주문 상태 정보 또는 None
        """
        try:
            logger.info(f"주문 상태 조회: {order_key}")
            
            # 1. 인증 토큰 획득
            token = await self.token_manager.get_auth_token(account_name)
            if not token:
                return None
            
            # 2. GraphQL 쿼리 실행
            query = """
            query GetOrder($key: ID!) {
                order(key: $key) {
                    key
                    id
                    status
                    products {
                        quantity
                        price
                        itemKey
                    }
                    createdAt
                    updatedAt
                    note
                    ordererNote
                    sellerNote
                }
            }
            """
            
            variables = {"key": order_key}
            
            result = await self._execute_graphql_query(token, query, variables)
            
            if result and "data" in result and result["data"]["order"]:
                return result["data"]["order"]
            else:
                return None
                
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "주문 상태 조회 실패",
                'account_name': account_name,
                'order_key': order_key
            })
            return None

    async def sync_order_status(self, account_name: str, order_key: str) -> bool:
        """
        특정 주문의 상태를 오너클랜에서 동기화
        
        Args:
            account_name: 계정 이름
            order_key: 주문 키
            
        Returns:
            bool: 동기화 성공 여부
        """
        try:
            logger.info(f"주문 상태 동기화: {order_key}")
            
            # 1. 오너클랜에서 주문 상태 조회
            order_data = await self.get_order_status(account_name, order_key)
            if not order_data:
                return False
            
            # 2. 로컬 DB에서 해당 주문 조회
            local_order = await self.db_service.select_data(
                self.local_orders_table,
                {"ownerclan_order_key": order_key, "account_name": account_name}
            )
            
            if local_order:
                # 3. 상태 업데이트
                update_data = {
                    "status": order_data["status"].lower(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                await self.db_service.update_data(
                    self.local_orders_table,
                    {"ownerclan_order_key": order_key, "account_name": account_name},
                    update_data
                )
                
                logger.info(f"주문 상태 동기화 완료: {order_key} -> {order_data['status']}")
                
                # 4. 동기화 로그 저장
                await self._log_sync_operation(
                    account_name=account_name,
                    sync_type="sync_status",
                    order_key=order_key,
                    success=True,
                    sync_data=order_data
                )
                
                return True
            else:
                logger.warning(f"로컬 주문을 찾을 수 없음: {order_key}")
                return False
                
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "주문 상태 동기화 실패",
                'account_name': account_name,
                'order_key': order_key
            })
            
            # 동기화 실패 로그 저장
            await self._log_sync_operation(
                account_name=account_name,
                sync_type="sync_status",
                order_key=order_key,
                success=False,
                error_message=str(e)
            )
            
            return False

    async def get_local_orders(self, account_name: str, 
                             status: Optional[OrderStatus] = None,
                             limit: int = 100,
                             offset: int = 0) -> List[Dict[str, Any]]:
        """
        로컬 DB에서 주문 목록 조회
        
        Args:
            account_name: 계정 이름
            status: 주문 상태 필터
            limit: 조회할 주문 수
            offset: 오프셋
            
        Returns:
            List[Dict]: 주문 목록
        """
        try:
            # 쿼리 조건 구성
            conditions = {"account_name": account_name}
            if status:
                conditions["status"] = status.value
            
            # 주문 조회
            orders = await self.db_service.select_data(
                self.local_orders_table,
                conditions,
                limit=limit,
                offset=offset,
                order_by="created_at DESC"
            )
            
            return orders or []
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "로컬 주문 조회 실패",
                'account_name': account_name
            })
            return []

    async def _sync_single_order(self, account_name: str, order_data: Dict[str, Any]) -> None:
        """단일 주문을 로컬 DB에 동기화"""
        try:
            order_key = order_data["key"]
            
            # 기존 주문 확인
            existing_order = await self.db_service.select_data(
                self.local_orders_table,
                {"ownerclan_order_key": order_key, "account_name": account_name}
            )
            
            # 주문 데이터 구성
            order_record = {
                "ownerclan_order_key": order_key,
                "ownerclan_order_id": order_data.get("id"),
                "account_name": account_name,
                "status": order_data["status"].lower(),
                "products": json.dumps(order_data["products"]),
                "recipient": json.dumps(order_data["shippingInfo"]["recipient"]),
                "note": order_data.get("note"),
                "seller_note": order_data.get("sellerNote"),
                "orderer_note": order_data.get("ordererNote"),
                "total_amount": sum(p["quantity"] * p["price"] for p in order_data["products"]),
                "shipping_amount": order_data["shippingInfo"]["shippingFee"],
                "created_at": datetime.fromtimestamp(order_data["createdAt"], tz=timezone.utc).isoformat(),
                "updated_at": datetime.fromtimestamp(order_data["updatedAt"], tz=timezone.utc).isoformat()
            }
            
            if existing_order:
                # 업데이트
                await self.db_service.update_data(
                    self.local_orders_table,
                    {"ownerclan_order_key": order_key, "account_name": account_name},
                    order_record
                )
                logger.debug(f"주문 업데이트: {order_key}")
            else:
                # 새로 삽입
                await self.db_service.insert_data(self.local_orders_table, order_record)
                logger.debug(f"주문 삽입: {order_key}")
                
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "단일 주문 동기화 실패",
                'account_name': account_name,
                'order_key': order_data.get("key")
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

    async def _log_sync_operation(self, account_name: str, sync_type: str, 
                                 order_key: Optional[str] = None, success: bool = True,
                                 synced_count: int = 0, error_message: Optional[str] = None,
                                 sync_data: Optional[Dict[str, Any]] = None) -> None:
        """동기화 작업 로그 저장"""
        try:
            log_data = {
                "account_name": account_name,
                "sync_type": sync_type,
                "order_key": order_key,
                "success": success,
                "synced_count": synced_count,
                "error_message": error_message,
                "sync_data": json.dumps(sync_data) if sync_data else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db_service.insert_data(self.order_sync_logs_table, log_data)
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "동기화 로그 저장 실패",
                'account_name': account_name,
                'sync_type': sync_type
            })


# 전역 인스턴스
order_management_service = OrderManagementService()
