"""
트랜잭션 시스템 - 오너클랜 주문 관리
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import json
import asyncio
from loguru import logger

from src.config.settings import settings
from src.utils.error_handler import ErrorHandler, BaseAPIError, DatabaseError
from src.services.database_service import DatabaseService
from src.services.ownerclan_token_manager import OwnerClanTokenManager
from src.services.supplier_account_manager import SupplierAccountManager


class OrderStatus(Enum):
    """주문 상태 열거형"""
    PENDING = "pending"           # 대기중
    PAID = "paid"                # 결제완료
    PREPARING = "preparing"       # 배송준비중
    SHIPPED = "shipped"          # 배송중
    DELIVERED = "delivered"       # 배송완료
    CANCELLED = "cancelled"       # 취소됨
    REFUNDED = "refunded"         # 환불됨


class TransactionType(Enum):
    """트랜잭션 타입"""
    CREATE_ORDER = "create_order"
    UPDATE_ORDER = "update_order"
    CANCEL_ORDER = "cancel_order"
    REQUEST_CANCELLATION = "request_cancellation"
    SIMULATE_ORDER = "simulate_order"


@dataclass
class OrderProduct:
    """주문 상품 정보"""
    item_key: str
    quantity: int
    option_attributes: List[Dict[str, str]]


@dataclass
class OrderRecipient:
    """주문 수령자 정보"""
    name: str
    phone: str
    address: str
    postal_code: str
    city: str
    district: str
    detail_address: str


@dataclass
class OrderInput:
    """주문 입력 데이터"""
    products: List[OrderProduct]
    recipient: OrderRecipient
    note: Optional[str] = None
    seller_note: Optional[str] = None
    orderer_note: Optional[str] = None


@dataclass
class TransactionResult:
    """트랜잭션 결과"""
    success: bool
    transaction_id: Optional[str] = None
    order_key: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class TransactionSystem:
    """트랜잭션 시스템 - 오너클랜 주문 관리"""

    def __init__(self):
        self.settings = settings
        self.error_handler = ErrorHandler()
        self.db_service = DatabaseService()
        self.token_manager = OwnerClanTokenManager()
        self.account_manager = SupplierAccountManager()
        
        # API 엔드포인트
        self.api_endpoint = "https://api.ownerclan.com/v1/graphql"
        
        # 트랜잭션 로그 저장을 위한 테이블명
        self.transaction_log_table = "transaction_logs"

    async def create_order(self, account_name: str, order_input: OrderInput) -> TransactionResult:
        """
        새 주문 생성
        
        Args:
            account_name: 계정 이름
            order_input: 주문 입력 데이터
            
        Returns:
            TransactionResult: 트랜잭션 결과
        """
        try:
            logger.info(f"주문 생성 시작: {account_name}")
            
            # 1. 인증 토큰 획득
            token = await self.token_manager.get_auth_token(account_name)
            if not token:
                return TransactionResult(
                    success=False,
                    error="인증 토큰 획득 실패"
                )
            
            # 2. 주문 데이터 변환
            order_data = self._convert_order_input_to_graphql(order_input)
            
            # 3. GraphQL 쿼리 실행
            query = """
            mutation CreateOrder($input: OrderInput!) {
                createOrder(input: $input) {
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
                    createdAt
                    updatedAt
                    note
                    ordererNote
                    sellerNote
                }
            }
            """
            
            variables = {"input": order_data}
            
            result = await self._execute_graphql_query(token, query, variables)
            
            if result and "data" in result and result["data"]["createOrder"]:
                order_info = result["data"]["createOrder"]
                
                # 4. 트랜잭션 로그 저장
                transaction_id = await self._log_transaction(
                    account_name=account_name,
                    transaction_type=TransactionType.CREATE_ORDER,
                    order_key=order_info["key"],
                    data=order_info,
                    success=True
                )
                
                logger.info(f"주문 생성 성공: {order_info['key']}")
                
                return TransactionResult(
                    success=True,
                    transaction_id=transaction_id,
                    order_key=order_info["key"],
                    data=order_info
                )
            else:
                error_msg = "알 수 없는 오류"
                if result and "errors" in result:
                    error_msg = result["errors"][0]["message"]
                return TransactionResult(
                    success=False,
                    error=f"주문 생성 실패: {error_msg}"
                )
                
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "주문 생성 실패",
                'account_name': account_name
            })
            return TransactionResult(
                success=False,
                error=f"주문 생성 중 오류 발생: {str(e)}"
            )

    async def simulate_order(self, account_name: str, order_input: OrderInput) -> TransactionResult:
        """
        주문 시뮬레이션 (실제 주문 생성 없이 예상 금액 확인)
        
        Args:
            account_name: 계정 이름
            order_input: 주문 입력 데이터
            
        Returns:
            TransactionResult: 시뮬레이션 결과
        """
        try:
            logger.info(f"주문 시뮬레이션 시작: {account_name}")
            
            # 1. 인증 토큰 획득
            token = await self.token_manager.get_auth_token(account_name)
            if not token:
                return TransactionResult(
                    success=False,
                    error="인증 토큰 획득 실패"
                )
            
            # 2. 주문 데이터 변환
            order_data = self._convert_order_input_to_graphql(order_input)
            
            # 3. GraphQL 쿼리 실행
            query = """
            mutation SimulateCreateOrder($input: OrderInput!) {
                simulateCreateOrder(input: $input) {
                    itemAmounts {
                        amount
                        itemKey
                    }
                    shippingAmount
                    extraShippingFeeExists
                }
            }
            """
            
            variables = {"input": order_data}
            
            result = await self._execute_graphql_query(token, query, variables)
            
            if result and "data" in result and result["data"]["simulateCreateOrder"]:
                simulation_data = result["data"]["simulateCreateOrder"]
                
                # 4. 트랜잭션 로그 저장
                transaction_id = await self._log_transaction(
                    account_name=account_name,
                    transaction_type=TransactionType.SIMULATE_ORDER,
                    data=simulation_data,
                    success=True
                )
                
                logger.info(f"주문 시뮬레이션 성공")
                
                return TransactionResult(
                    success=True,
                    transaction_id=transaction_id,
                    data=simulation_data
                )
            else:
                error_msg = "알 수 없는 오류"
                if result and "errors" in result:
                    error_msg = result["errors"][0]["message"]
                return TransactionResult(
                    success=False,
                    error=f"주문 시뮬레이션 실패: {error_msg}"
                )
                
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "주문 시뮬레이션 실패",
                'account_name': account_name
            })
            return TransactionResult(
                success=False,
                error=f"주문 시뮬레이션 중 오류 발생: {str(e)}"
            )

    async def cancel_order(self, account_name: str, order_key: str) -> TransactionResult:
        """
        주문 취소 (결제완료 상태만 가능)
        
        Args:
            account_name: 계정 이름
            order_key: 주문 키
            
        Returns:
            TransactionResult: 취소 결과
        """
        try:
            logger.info(f"주문 취소 시작: {order_key}")
            
            # 1. 인증 토큰 획득
            token = await self.token_manager.get_auth_token(account_name)
            if not token:
                return TransactionResult(
                    success=False,
                    error="인증 토큰 획득 실패"
                )
            
            # 2. GraphQL 쿼리 실행
            query = """
            mutation CancelOrder($key: ID!) {
                cancelOrder(key: $key) {
                    key
                    id
                    status
                    updatedAt
                }
            }
            """
            
            variables = {"key": order_key}
            
            result = await self._execute_graphql_query(token, query, variables)
            
            if result and "data" in result and result["data"]["cancelOrder"]:
                cancel_data = result["data"]["cancelOrder"]
                
                # 3. 트랜잭션 로그 저장
                transaction_id = await self._log_transaction(
                    account_name=account_name,
                    transaction_type=TransactionType.CANCEL_ORDER,
                    order_key=order_key,
                    data=cancel_data,
                    success=True
                )
                
                logger.info(f"주문 취소 성공: {order_key}")
                
                return TransactionResult(
                    success=True,
                    transaction_id=transaction_id,
                    order_key=order_key,
                    data=cancel_data
                )
            else:
                error_msg = result.get("errors", [{"message": "알 수 없는 오류"}])[0]["message"]
                return TransactionResult(
                    success=False,
                    error=f"주문 취소 실패: {error_msg}"
                )
                
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "주문 취소 실패",
                'account_name': account_name,
                'order_key': order_key
            })
            return TransactionResult(
                success=False,
                error=f"주문 취소 중 오류 발생: {str(e)}"
            )

    async def request_order_cancellation(self, account_name: str, order_key: str, cancel_reason: str) -> TransactionResult:
        """
        주문 취소 요청 (배송준비중 상태만 가능)
        
        Args:
            account_name: 계정 이름
            order_key: 주문 키
            cancel_reason: 취소 사유
            
        Returns:
            TransactionResult: 취소 요청 결과
        """
        try:
            logger.info(f"주문 취소 요청 시작: {order_key}")
            
            # 1. 인증 토큰 획득
            token = await self.token_manager.get_auth_token(account_name)
            if not token:
                return TransactionResult(
                    success=False,
                    error="인증 토큰 획득 실패"
                )
            
            # 2. GraphQL 쿼리 실행
            query = """
            mutation RequestOrderCancellation($key: ID!, $input: RequestOrderCancellationInput!) {
                requestOrderCancellation(key: $key, input: $input) {
                    key
                    id
                    status
                    updatedAt
                }
            }
            """
            
            variables = {
                "key": order_key,
                "input": {
                    "cancelReason": cancel_reason
                }
            }
            
            result = await self._execute_graphql_query(token, query, variables)
            
            if result and "data" in result and result["data"]["requestOrderCancellation"]:
                cancellation_data = result["data"]["requestOrderCancellation"]
                
                # 3. 트랜잭션 로그 저장
                transaction_id = await self._log_transaction(
                    account_name=account_name,
                    transaction_type=TransactionType.REQUEST_CANCELLATION,
                    order_key=order_key,
                    data=cancellation_data,
                    success=True
                )
                
                logger.info(f"주문 취소 요청 성공: {order_key}")
                
                return TransactionResult(
                    success=True,
                    transaction_id=transaction_id,
                    order_key=order_key,
                    data=cancellation_data
                )
            else:
                error_msg = result.get("errors", [{"message": "알 수 없는 오류"}])[0]["message"]
                return TransactionResult(
                    success=False,
                    error=f"주문 취소 요청 실패: {error_msg}"
                )
                
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "주문 취소 요청 실패",
                'account_name': account_name,
                'order_key': order_key
            })
            return TransactionResult(
                success=False,
                error=f"주문 취소 요청 중 오류 발생: {str(e)}"
            )

    async def update_order_notes(self, account_name: str, order_key: str, note: Optional[str] = None, seller_note: Optional[str] = None) -> TransactionResult:
        """
        주문 메모 업데이트
        
        Args:
            account_name: 계정 이름
            order_key: 주문 키
            note: 원장주문코드
            seller_note: 주문관리메모
            
        Returns:
            TransactionResult: 업데이트 결과
        """
        try:
            logger.info(f"주문 메모 업데이트 시작: {order_key}")
            
            # 1. 인증 토큰 획득
            token = await self.token_manager.get_auth_token(account_name)
            if not token:
                return TransactionResult(
                    success=False,
                    error="인증 토큰 획득 실패"
                )
            
            # 2. 업데이트 데이터 구성
            update_input = {}
            if note is not None:
                update_input["note"] = note
            if seller_note is not None:
                update_input["sellerNote"] = seller_note
            
            # 3. GraphQL 쿼리 실행
            query = """
            mutation UpdateOrderNotes($key: ID!, $input: OrderUpdateNotesInput!) {
                updateOrderNotes(key: $key, input: $input) {
                    key
                    id
                    note
                    sellerNote
                    updatedAt
                }
            }
            """
            
            variables = {
                "key": order_key,
                "input": update_input
            }
            
            result = await self._execute_graphql_query(token, query, variables)
            
            if result and "data" in result and result["data"]["updateOrderNotes"]:
                update_data = result["data"]["updateOrderNotes"]
                
                # 4. 트랜잭션 로그 저장
                transaction_id = await self._log_transaction(
                    account_name=account_name,
                    transaction_type=TransactionType.UPDATE_ORDER,
                    order_key=order_key,
                    data=update_data,
                    success=True
                )
                
                logger.info(f"주문 메모 업데이트 성공: {order_key}")
                
                return TransactionResult(
                    success=True,
                    transaction_id=transaction_id,
                    order_key=order_key,
                    data=update_data
                )
            else:
                error_msg = result.get("errors", [{"message": "알 수 없는 오류"}])[0]["message"]
                return TransactionResult(
                    success=False,
                    error=f"주문 메모 업데이트 실패: {error_msg}"
                )
                
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "주문 메모 업데이트 실패",
                'account_name': account_name,
                'order_key': order_key
            })
            return TransactionResult(
                success=False,
                error=f"주문 메모 업데이트 중 오류 발생: {str(e)}"
            )

    def _convert_order_input_to_graphql(self, order_input: OrderInput) -> Dict[str, Any]:
        """OrderInput을 GraphQL 형식으로 변환"""
        return {
            "products": [
                {
                    "itemKey": product.item_key,
                    "quantity": product.quantity,
                    "optionAttributes": [
                        f"{attr['name']}:{attr['value']}" 
                        for attr in product.option_attributes
                    ]
                }
                for product in order_input.products
            ],
            "recipient": {
                "name": order_input.recipient.name,
                "phoneNumber": order_input.recipient.phone,
                "destinationAddress": {
                    "address": order_input.recipient.address,
                    "postalCode": order_input.recipient.postal_code,
                    "city": order_input.recipient.city,
                    "district": order_input.recipient.district,
                    "detailAddress": order_input.recipient.detail_address
                }
            },
            "note": order_input.note,
            "sellerNote": order_input.seller_note,
            "ordererNote": order_input.orderer_note
        }

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

    async def _log_transaction(self, account_name: str, transaction_type: TransactionType, 
                             order_key: Optional[str] = None, data: Optional[Dict[str, Any]] = None, 
                             success: bool = True) -> str:
        """트랜잭션 로그 저장"""
        try:
            # 트랜잭션 로그 데이터 구성
            log_data = {
                "account_name": account_name,
                "transaction_type": transaction_type.value,
                "order_key": order_key,
                "success": success,
                "data": json.dumps(data) if data else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # 데이터베이스에 저장
            result = await self.db_service.insert_data(self.transaction_log_table, log_data)
            return result["id"]
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "트랜잭션 로그 저장 실패",
                'account_name': account_name,
                'transaction_type': transaction_type.value
            })
            return "unknown"


# 전역 인스턴스
transaction_system = TransactionSystem()
