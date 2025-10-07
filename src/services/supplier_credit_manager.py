import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from loguru import logger
from dataclasses import dataclass, field
from enum import Enum

from src.services.database_service import DatabaseService
from src.utils.error_handler import ErrorHandler, DatabaseError, BaseAPIError

class CreditTransactionType(Enum):
    """적립금 거래 유형"""
    DEPOSIT = "deposit"  # 입금
    WITHDRAWAL = "withdrawal"  # 출금 (주문 시 차감)
    REFUND = "refund"  # 환불
    ADJUSTMENT = "adjustment"  # 조정

class CreditTransactionStatus(Enum):
    """적립금 거래 상태"""
    PENDING = "pending"  # 대기
    COMPLETED = "completed"  # 완료
    FAILED = "failed"  # 실패
    CANCELLED = "cancelled"  # 취소

@dataclass
class SupplierCredit:
    """공급사 적립금 정보"""
    supplier_id: str
    account_name: str
    current_balance: float
    reserved_balance: float = 0.0  # 예약된 금액 (주문 진행 중)
    available_balance: float = field(init=False)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        self.available_balance = self.current_balance - self.reserved_balance

@dataclass
class CreditTransaction:
    """적립금 거래 내역"""
    transaction_id: str
    supplier_id: str
    account_name: str
    transaction_type: CreditTransactionType
    amount: float
    status: CreditTransactionStatus
    description: str
    order_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

class SupplierCreditManager:
    """
    공급사 적립금 관리 시스템:
    - 적립금 잔액 조회 및 관리
    - 주문 시 적립금 차감
    - 적립금 입금 및 조정
    - 거래 내역 관리
    """
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
        logger.info("SupplierCreditManager 초기화 완료")

    async def get_supplier_credit(self, supplier_id: str, account_name: str) -> Optional[SupplierCredit]:
        """공급사 적립금 잔액 조회"""
        try:
            logger.info(f"공급사 적립금 조회: {supplier_id}, {account_name}")
            
            # 데이터베이스에서 적립금 정보 조회
            credit_data = await self.db_service.select_data(
                table_name="supplier_credits",
                conditions={"supplier_id": supplier_id, "account_name": account_name}
            )
            
            if credit_data:
                data = credit_data[0]
                return SupplierCredit(
                    supplier_id=data["supplier_id"],
                    account_name=data["account_name"],
                    current_balance=data["current_balance"],
                    reserved_balance=data.get("reserved_balance", 0.0),
                    last_updated=datetime.fromisoformat(data["last_updated"])
                )
            else:
                logger.warning(f"공급사 적립금 정보를 찾을 수 없습니다: {supplier_id}, {account_name}")
                return None
                
        except Exception as e:
            self.error_handler.log_error(e, f"공급사 적립금 조회 실패: {supplier_id}, {account_name}")
            return None

    async def check_sufficient_credit(self, supplier_id: str, account_name: str, required_amount: float) -> bool:
        """적립금 충분 여부 확인"""
        try:
            credit = await self.get_supplier_credit(supplier_id, account_name)
            if not credit:
                logger.warning(f"공급사 적립금 정보 없음: {supplier_id}, {account_name}")
                return False
            
            if credit.available_balance >= required_amount:
                logger.info(f"적립금 충분: {supplier_id}, {account_name}, 필요: {required_amount}, 사용가능: {credit.available_balance}")
                return True
            else:
                logger.warning(f"적립금 부족: {supplier_id}, {account_name}, 필요: {required_amount}, 사용가능: {credit.available_balance}")
                return False
                
        except Exception as e:
            self.error_handler.log_error(e, f"적립금 충분 여부 확인 실패: {supplier_id}, {account_name}")
            return False

    async def reserve_credit(self, supplier_id: str, account_name: str, amount: float, order_id: str) -> bool:
        """주문 시 적립금 예약 (차감 준비)"""
        try:
            logger.info(f"적립금 예약 시작: {supplier_id}, {account_name}, 금액: {amount}, 주문: {order_id}")
            
            # 충분한 적립금이 있는지 확인
            if not await self.check_sufficient_credit(supplier_id, account_name, amount):
                logger.error(f"적립금 부족으로 예약 실패: {supplier_id}, {account_name}, 필요: {amount}")
                return False
            
            # 예약된 금액 업데이트
            update_data = {
                "reserved_balance": amount,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            result = await self.db_service.update_data(
                table_name="supplier_credits",
                filters={"supplier_id": supplier_id, "account_name": account_name},
                data=update_data
            )
            
            if result:
                # 거래 내역 기록
                await self._record_transaction(
                    supplier_id=supplier_id,
                    account_name=account_name,
                    transaction_type=CreditTransactionType.WITHDRAWAL,
                    amount=amount,
                    status=CreditTransactionStatus.PENDING,
                    description=f"주문 예약: {order_id}",
                    order_id=order_id
                )
                
                logger.info(f"적립금 예약 성공: {supplier_id}, {account_name}, 금액: {amount}")
                return True
            else:
                logger.error(f"적립금 예약 실패: {supplier_id}, {account_name}")
                return False
                
        except Exception as e:
            self.error_handler.log_error(e, f"적립금 예약 실패: {supplier_id}, {account_name}")
            return False

    async def confirm_credit_deduction(self, supplier_id: str, account_name: str, amount: float, order_id: str) -> bool:
        """주문 확정 시 적립금 실제 차감"""
        try:
            logger.info(f"적립금 차감 확정: {supplier_id}, {account_name}, 금액: {amount}, 주문: {order_id}")
            
            # 현재 적립금 정보 조회
            credit_data = await self.db_service.select_data(
                table_name="supplier_credits",
                conditions={"supplier_id": supplier_id, "account_name": account_name}
            )
            
            if not credit_data:
                logger.error(f"공급사 적립금 정보 없음: {supplier_id}, {account_name}")
                return False
            
            current_data = credit_data[0]
            new_balance = current_data["current_balance"] - amount
            new_reserved = max(0, current_data.get("reserved_balance", 0) - amount)
            
            # 적립금 차감 및 예약 금액 해제
            update_data = {
                "current_balance": new_balance,
                "reserved_balance": new_reserved,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            result = await self.db_service.update_data(
                table_name="supplier_credits",
                filters={"supplier_id": supplier_id, "account_name": account_name},
                data=update_data
            )
            
            if result:
                # 거래 내역 업데이트 (완료 상태로)
                await self._update_transaction_status(
                    order_id=order_id,
                    status=CreditTransactionStatus.COMPLETED,
                    completed_at=datetime.now(timezone.utc)
                )
                
                logger.info(f"적립금 차감 확정 성공: {supplier_id}, {account_name}, 새 잔액: {new_balance}")
                return True
            else:
                logger.error(f"적립금 차감 확정 실패: {supplier_id}, {account_name}")
                return False
                
        except Exception as e:
            self.error_handler.log_error(e, f"적립금 차감 확정 실패: {supplier_id}, {account_name}")
            return False

    async def cancel_credit_reservation(self, supplier_id: str, account_name: str, amount: float, order_id: str) -> bool:
        """주문 취소 시 적립금 예약 해제"""
        try:
            logger.info(f"적립금 예약 해제: {supplier_id}, {account_name}, 금액: {amount}, 주문: {order_id}")
            
            # 예약된 금액 해제
            credit_data = await self.db_service.select_data(
                table_name="supplier_credits",
                conditions={"supplier_id": supplier_id, "account_name": account_name}
            )
            
            if credit_data:
                current_data = credit_data[0]
                new_reserved = max(0, current_data.get("reserved_balance", 0) - amount)
                
                update_data = {
                    "reserved_balance": new_reserved,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                
                await self.db_service.update_data(
                    table_name="supplier_credits",
                    filters={"supplier_id": supplier_id, "account_name": account_name},
                    data=update_data
                )
            
            # 거래 내역 취소 상태로 업데이트
            await self._update_transaction_status(
                order_id=order_id,
                status=CreditTransactionStatus.CANCELLED,
                completed_at=datetime.now(timezone.utc)
            )
            
            logger.info(f"적립금 예약 해제 성공: {supplier_id}, {account_name}")
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, f"적립금 예약 해제 실패: {supplier_id}, {account_name}")
            return False

    async def deposit_credit(self, supplier_id: str, account_name: str, amount: float, description: str = "수동 입금") -> bool:
        """적립금 입금 (수동)"""
        try:
            logger.info(f"적립금 입금: {supplier_id}, {account_name}, 금액: {amount}")
            
            # 기존 적립금 정보 조회
            credit_data = await self.db_service.select_data(
                table_name="supplier_credits",
                conditions={"supplier_id": supplier_id, "account_name": account_name}
            )
            
            if credit_data:
                # 기존 적립금 업데이트
                current_data = credit_data[0]
                new_balance = current_data["current_balance"] + amount
                
                update_data = {
                    "current_balance": new_balance,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                
                result = await self.db_service.update_data(
                    table_name="supplier_credits",
                    filters={"supplier_id": supplier_id, "account_name": account_name},
                    data=update_data
                )
            else:
                # 새 적립금 계정 생성
                insert_data = {
                    "supplier_id": supplier_id,
                    "account_name": account_name,
                    "current_balance": amount,
                    "reserved_balance": 0.0,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                result = await self.db_service.insert_data(
                    table_name="supplier_credits",
                    data=insert_data
                )
            
            if result:
                # 거래 내역 기록
                await self._record_transaction(
                    supplier_id=supplier_id,
                    account_name=account_name,
                    transaction_type=CreditTransactionType.DEPOSIT,
                    amount=amount,
                    status=CreditTransactionStatus.COMPLETED,
                    description=description,
                    completed_at=datetime.now(timezone.utc)
                )
                
                logger.info(f"적립금 입금 성공: {supplier_id}, {account_name}, 금액: {amount}")
                return True
            else:
                logger.error(f"적립금 입금 실패: {supplier_id}, {account_name}")
                return False
                
        except Exception as e:
            self.error_handler.log_error(e, f"적립금 입금 실패: {supplier_id}, {account_name}")
            return False

    async def get_credit_transactions(self, supplier_id: str, account_name: str, limit: int = 50) -> List[CreditTransaction]:
        """적립금 거래 내역 조회"""
        try:
            logger.info(f"적립금 거래 내역 조회: {supplier_id}, {account_name}")
            
            transactions_data = await self.db_service.select_data(
                table_name="credit_transactions",
                conditions={"supplier_id": supplier_id, "account_name": account_name},
                limit=limit
            )
            
            transactions = []
            for data in transactions_data:
                transaction = CreditTransaction(
                    transaction_id=data["transaction_id"],
                    supplier_id=data["supplier_id"],
                    account_name=data["account_name"],
                    transaction_type=CreditTransactionType(data["transaction_type"]),
                    amount=data["amount"],
                    status=CreditTransactionStatus(data["status"]),
                    description=data["description"],
                    order_id=data.get("order_id"),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
                    failure_reason=data.get("failure_reason")
                )
                transactions.append(transaction)
            
            logger.info(f"적립금 거래 내역 조회 완료: {len(transactions)}건")
            return transactions
            
        except Exception as e:
            self.error_handler.log_error(e, f"적립금 거래 내역 조회 실패: {supplier_id}, {account_name}")
            return []

    async def _record_transaction(self, supplier_id: str, account_name: str, transaction_type: CreditTransactionType,
                                amount: float, status: CreditTransactionStatus, description: str,
                                order_id: Optional[str] = None, completed_at: Optional[datetime] = None) -> None:
        """거래 내역 기록"""
        try:
            transaction_id = f"TXN_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{supplier_id}_{account_name}"
            
            transaction_data = {
                "transaction_id": transaction_id,
                "supplier_id": supplier_id,
                "account_name": account_name,
                "transaction_type": transaction_type.value,
                "amount": amount,
                "status": status.value,
                "description": description,
                "order_id": order_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": completed_at.isoformat() if completed_at else None,
                "failure_reason": None
            }
            
            await self.db_service.insert_data("credit_transactions", transaction_data)
            logger.debug(f"거래 내역 기록 완료: {transaction_id}")
            
        except Exception as e:
            self.error_handler.log_error(e, f"거래 내역 기록 실패: {supplier_id}, {account_name}")

    async def _update_transaction_status(self, order_id: str, status: CreditTransactionStatus, 
                                       completed_at: Optional[datetime] = None) -> None:
        """거래 내역 상태 업데이트"""
        try:
            update_data = {
                "status": status.value,
                "completed_at": completed_at.isoformat() if completed_at else None
            }
            
            await self.db_service.update_data(
                table_name="credit_transactions",
                filters={"order_id": order_id},
                data=update_data
            )
            
            logger.debug(f"거래 내역 상태 업데이트 완료: {order_id} -> {status.value}")
            
        except Exception as e:
            self.error_handler.log_error(e, f"거래 내역 상태 업데이트 실패: {order_id}")

    async def get_all_supplier_credits(self) -> List[SupplierCredit]:
        """모든 공급사 적립금 정보 조회"""
        try:
            logger.info("모든 공급사 적립금 정보 조회")
            
            credits_data = await self.db_service.select_data(
                table_name="supplier_credits",
                conditions=None
            )
            
            credits = []
            for data in credits_data:
                credit = SupplierCredit(
                    supplier_id=data["supplier_id"],
                    account_name=data["account_name"],
                    current_balance=data["current_balance"],
                    reserved_balance=data.get("reserved_balance", 0.0),
                    last_updated=datetime.fromisoformat(data["last_updated"])
                )
                credits.append(credit)
            
            logger.info(f"모든 공급사 적립금 정보 조회 완료: {len(credits)}개")
            return credits
            
        except Exception as e:
            self.error_handler.log_error(e, "모든 공급사 적립금 정보 조회 실패")
            return []
