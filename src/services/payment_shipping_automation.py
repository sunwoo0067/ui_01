#!/usr/bin/env python3
"""
결제 및 배송 프로세스 자동화 시스템
"""

import asyncio
import sys
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.supplier_credit_manager import SupplierCreditManager, CreditTransactionType, CreditTransactionStatus
from src.services.database_service import DatabaseService
from src.utils.error_handler import ErrorHandler


class PaymentStatus(Enum):
    """결제 상태"""
    PENDING = "pending"             # 결제 대기
    PROCESSING = "processing"       # 결제 처리 중
    COMPLETED = "completed"         # 결제 완료
    FAILED = "failed"               # 결제 실패
    CANCELLED = "cancelled"         # 결제 취소
    REFUNDED = "refunded"           # 환불 완료
    PARTIAL_REFUND = "partial_refund"  # 부분 환불


class PaymentMethod(Enum):
    """결제 방법"""
    CREDIT = "credit"  # 공급사 적립금
    COUPON = "coupon"               # 쿠폰


class ShippingStatus(Enum):
    """배송 상태"""
    PENDING = "pending"             # 배송 대기
    PREPARING = "preparing"         # 배송 준비
    SHIPPED = "shipped"             # 배송 중
    IN_TRANSIT = "in_transit"        # 운송 중
    OUT_FOR_DELIVERY = "out_for_delivery"  # 배송 출발
    DELIVERED = "delivered"          # 배송 완료
    FAILED_DELIVERY = "failed_delivery"    # 배송 실패
    RETURNED = "returned"           # 반품


class ShippingMethod(Enum):
    """배송 방법"""
    STANDARD = "standard"           # 일반 배송
    EXPRESS = "express"             # 당일 배송
    NEXT_DAY = "next_day"           # 다음날 배송
    PICKUP = "pickup"               # 픽업
    COURIER = "courier"             # 택배


@dataclass
class PaymentInfo:
    """결제 정보"""
    payment_id: str
    order_id: str
    amount: float
    payment_method: PaymentMethod
    status: PaymentStatus
    transaction_id: Optional[str]
    payment_gateway: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None


@dataclass
class ShippingInfo:
    """배송 정보"""
    shipping_id: str
    order_id: str
    tracking_number: Optional[str]
    shipping_method: ShippingMethod
    status: ShippingStatus
    carrier: str
    created_at: datetime
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    shipping_address: Optional[Dict[str, str]] = None


@dataclass
class PaymentRequest:
    """결제 요청"""
    order_id: str
    amount: float
    payment_method: PaymentMethod
    customer_info: Dict[str, str]
    billing_address: Dict[str, str]
    items: List[Dict[str, Any]]


@dataclass
class ShippingRequest:
    """배송 요청"""
    order_id: str
    items: List[Dict[str, Any]]
    shipping_address: Dict[str, str]
    shipping_method: ShippingMethod
    special_instructions: Optional[str] = None


class PaymentProcessor:
    """결제 처리 시스템"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
        self.credit_manager = SupplierCreditManager(db_service)
        
        # 공급사별 결제 게이트웨이 매핑 (적립금 방식)
        self.payment_gateways = {
            PaymentMethod.CREDIT: "supplier_credit",  # 공급사 적립금
        }
        
        logger.info("PaymentShippingAutomation 초기화 완료 (공급사 적립금 결제 방식)")
    
    async def process_payment(self, payment_request: PaymentRequest) -> PaymentInfo:
        """결제 처리"""
        try:
            logger.info(f"결제 처리 시작: 주문 {payment_request.order_id}, 금액 {payment_request.amount:,.0f}원")
            
            payment_id = f"PAY_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # 결제 정보 생성
            payment_info = PaymentInfo(
                payment_id=payment_id,
                order_id=payment_request.order_id,
                amount=payment_request.amount,
                payment_method=payment_request.payment_method,
                status=PaymentStatus.PROCESSING,
                transaction_id=None,
                payment_gateway=self.payment_gateways.get(payment_request.payment_method, "unknown"),
                created_at=datetime.now(timezone.utc)
            )
            
            # 공급사 적립금 결제 처리
            if payment_request.payment_method == PaymentMethod.CREDIT:
                result = await self._process_credit_payment(payment_request)
            else:
                raise ValueError(f"지원하지 않는 결제 방법: {payment_request.payment_method}")
            
            # 결제 결과 처리
            if result["success"]:
                payment_info.status = PaymentStatus.COMPLETED
                payment_info.transaction_id = result["transaction_id"]
                payment_info.completed_at = datetime.now(timezone.utc)
            else:
                payment_info.status = PaymentStatus.FAILED
                payment_info.failure_reason = result["error"]
            
            # 결제 정보 저장
            await self._save_payment_info(payment_info)
            
            logger.info(f"결제 처리 완료: {payment_id}, 상태: {payment_info.status.value}")
            return payment_info
            
        except Exception as e:
            self.error_handler.log_error(e, "결제 처리 실패")
            
            # 실패한 결제 정보 저장
            payment_info = PaymentInfo(
                payment_id=f"PAY_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
                order_id=payment_request.order_id,
                amount=payment_request.amount,
                payment_method=payment_request.payment_method,
                status=PaymentStatus.FAILED,
                transaction_id=None,
                payment_gateway=self.payment_gateways.get(payment_request.payment_method, "unknown"),
                created_at=datetime.now(timezone.utc),
                failure_reason=str(e)
            )
            
            await self._save_payment_info(payment_info)
            return payment_info
    
    async def _process_card_payment(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """신용카드 결제 처리"""
        try:
            logger.info("신용카드 결제 처리 (시뮬레이션)")
            
            # 실제로는 Stripe, PayPal 등의 결제 게이트웨이 API 호출
            # 시뮬레이션: 90% 성공률
            import random
            success = random.random() < 0.9
            
            if success:
                return {
                    "success": True,
                    "transaction_id": f"TXN_{uuid.uuid4().hex[:12].upper()}",
                    "gateway_response": "Payment successful"
                }
            else:
                return {
                    "success": False,
                    "error": "카드 승인 실패"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _process_bank_transfer(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """계좌이체 결제 처리"""
        try:
            logger.info("계좌이체 결제 처리 (시뮬레이션)")
            
            # 계좌이체는 즉시 처리
            return {
                "success": True,
                "transaction_id": f"BT_{uuid.uuid4().hex[:12].upper()}",
                "gateway_response": "Bank transfer initiated"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _process_virtual_account(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """가상계좌 결제 처리"""
        try:
            logger.info("가상계좌 결제 처리 (시뮬레이션)")
            
            # 가상계좌 생성 및 입금 대기
            virtual_account = f"1234-5678-{uuid.uuid4().hex[:4].upper()}"
            
            return {
                "success": True,
                "transaction_id": f"VA_{uuid.uuid4().hex[:12].upper()}",
                "gateway_response": f"Virtual account created: {virtual_account}",
                "virtual_account": virtual_account
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _process_mobile_payment(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """모바일 결제 처리"""
        try:
            logger.info("모바일 결제 처리 (시뮬레이션)")
            
            # 모바일 결제 시뮬레이션
            import random
            success = random.random() < 0.95
            
            if success:
                return {
                    "success": True,
                    "transaction_id": f"MP_{uuid.uuid4().hex[:12].upper()}",
                    "gateway_response": "Mobile payment successful"
                }
            else:
                return {
                    "success": False,
                    "error": "모바일 결제 실패"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _save_payment_info(self, payment_info: PaymentInfo) -> None:
        """결제 정보 저장"""
        try:
            payment_data = asdict(payment_info)
            payment_data["created_at"] = payment_info.created_at.isoformat()
            if payment_info.completed_at:
                payment_data["completed_at"] = payment_info.completed_at.isoformat()
            
            # enum을 문자열로 변환
            if "payment_method" in payment_data and hasattr(payment_data["payment_method"], 'value'):
                payment_data["payment_method"] = payment_data["payment_method"].value
            if "status" in payment_data and hasattr(payment_data["status"], 'value'):
                payment_data["status"] = payment_data["status"].value
            
            await self.db_service.insert_data("payments", payment_data)
            
        except Exception as e:
            self.error_handler.log_error(e, "결제 정보 저장 실패")
    
    async def process_refund(self, payment_id: str, amount: Optional[float] = None, 
                           reason: Optional[str] = None) -> bool:
        """환불 처리"""
        try:
            logger.info(f"환불 처리 시작: {payment_id}")
            
            # 결제 정보 조회
            payment_data = await self.db_service.select_data(
                table="payments",
                filters={"payment_id": payment_id}
            )
            
            if not payment_data:
                logger.error(f"결제 정보를 찾을 수 없음: {payment_id}")
                return False
            
            payment = payment_data[0]
            
            # 환불 금액 결정
            refund_amount = amount or payment.get("amount", 0)
            
            # 환불 처리 (시뮬레이션)
            logger.info(f"환불 처리: {refund_amount:,.0f}원")
            
            # 결제 상태 업데이트
            update_data = {
                "status": PaymentStatus.PARTIAL_REFUND.value if amount and amount < payment.get("amount", 0) else PaymentStatus.REFUNDED.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db_service.update_data(
                table="payments",
                filters={"payment_id": payment_id},
                data=update_data
            )
            
            logger.info(f"환불 처리 완료: {payment_id}")
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, "환불 처리 실패")
            return False


class ShippingProcessor:
    """배송 처리 시스템"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
        
        # 배송업체 설정
        self.shipping_carriers = {
            ShippingMethod.STANDARD: "cj_logistics",
            ShippingMethod.EXPRESS: "hanjin",
            ShippingMethod.NEXT_DAY: "lotte",
            ShippingMethod.PICKUP: "pickup",
            ShippingMethod.COURIER: "courier"
        }
    
    async def process_shipping(self, shipping_request: ShippingRequest) -> ShippingInfo:
        """배송 처리"""
        try:
            logger.info(f"배송 처리 시작: 주문 {shipping_request.order_id}")
            
            shipping_id = f"SHIP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # 배송 정보 생성
            shipping_info = ShippingInfo(
                shipping_id=shipping_id,
                order_id=shipping_request.order_id,
                tracking_number=None,
                shipping_method=shipping_request.shipping_method,
                status=ShippingStatus.PREPARING,
                carrier=self.shipping_carriers.get(shipping_request.shipping_method, "unknown"),
                estimated_delivery=self._calculate_estimated_delivery(shipping_request.shipping_method),
                shipping_address=shipping_request.shipping_address,
                created_at=datetime.now(timezone.utc)
            )
            
            # 배송 처리
            await self._process_shipping_request(shipping_info, shipping_request)
            
            # 배송 정보 저장
            await self._save_shipping_info(shipping_info)
            
            logger.info(f"배송 처리 완료: {shipping_id}")
            return shipping_info
            
        except Exception as e:
            self.error_handler.log_error(e, "배송 처리 실패")
            raise
    
    def _calculate_estimated_delivery(self, shipping_method: ShippingMethod) -> datetime:
        """예상 배송일 계산"""
        now = datetime.now(timezone.utc)
        
        if shipping_method == ShippingMethod.EXPRESS:
            return now + timedelta(hours=6)  # 당일 배송
        elif shipping_method == ShippingMethod.NEXT_DAY:
            return now + timedelta(days=1)   # 다음날 배송
        elif shipping_method == ShippingMethod.STANDARD:
            return now + timedelta(days=2)   # 일반 배송
        else:
            return now + timedelta(days=3)   # 기본 배송
    
    async def _process_shipping_request(self, shipping_info: ShippingInfo, 
                                     shipping_request: ShippingRequest) -> None:
        """배송 요청 처리"""
        try:
            logger.info(f"배송 요청 처리: {shipping_info.carrier}")
            
            # 배송업체별 처리
            if shipping_info.carrier == "cj_logistics":
                await self._process_cj_logistics(shipping_info)
            elif shipping_info.carrier == "hanjin":
                await self._process_hanjin(shipping_info)
            elif shipping_info.carrier == "lotte":
                await self._process_lotte(shipping_info)
            else:
                await self._process_generic_carrier(shipping_info)
            
        except Exception as e:
            logger.error(f"배송 요청 처리 실패: {e}")
            raise
    
    async def _process_cj_logistics(self, shipping_info: ShippingInfo) -> None:
        """CJ대한통운 배송 처리"""
        try:
            logger.info("CJ대한통운 배송 처리 (시뮬레이션)")
            
            # 운송장 번호 생성
            shipping_info.tracking_number = f"CJ{uuid.uuid4().hex[:10].upper()}"
            shipping_info.status = ShippingStatus.SHIPPED
            
        except Exception as e:
            logger.error(f"CJ대한통운 배송 처리 실패: {e}")
            raise
    
    async def _process_hanjin(self, shipping_info: ShippingInfo) -> None:
        """한진택배 배송 처리"""
        try:
            logger.info("한진택배 배송 처리 (시뮬레이션)")
            
            # 운송장 번호 생성
            shipping_info.tracking_number = f"HJ{uuid.uuid4().hex[:10].upper()}"
            shipping_info.status = ShippingStatus.SHIPPED
            
        except Exception as e:
            logger.error(f"한진택배 배송 처리 실패: {e}")
            raise
    
    async def _process_lotte(self, shipping_info: ShippingInfo) -> None:
        """롯데택배 배송 처리"""
        try:
            logger.info("롯데택배 배송 처리 (시뮬레이션)")
            
            # 운송장 번호 생성
            shipping_info.tracking_number = f"LT{uuid.uuid4().hex[:10].upper()}"
            shipping_info.status = ShippingStatus.SHIPPED
            
        except Exception as e:
            logger.error(f"롯데택배 배송 처리 실패: {e}")
            raise
    
    async def _process_generic_carrier(self, shipping_info: ShippingInfo) -> None:
        """일반 배송업체 처리"""
        try:
            logger.info("일반 배송업체 처리 (시뮬레이션)")
            
            # 운송장 번호 생성
            shipping_info.tracking_number = f"GC{uuid.uuid4().hex[:10].upper()}"
            shipping_info.status = ShippingStatus.SHIPPED
            
        except Exception as e:
            logger.error(f"일반 배송업체 처리 실패: {e}")
            raise
    
    async def _save_shipping_info(self, shipping_info: ShippingInfo) -> None:
        """배송 정보 저장"""
        try:
            shipping_data = asdict(shipping_info)
            shipping_data["created_at"] = shipping_info.created_at.isoformat()
            if shipping_info.estimated_delivery:
                shipping_data["estimated_delivery"] = shipping_info.estimated_delivery.isoformat()
            if shipping_info.actual_delivery:
                shipping_data["actual_delivery"] = shipping_info.actual_delivery.isoformat()
            
            await self.db_service.insert_data("shipping", shipping_data)
            
        except Exception as e:
            self.error_handler.log_error(e, "배송 정보 저장 실패")
    
    async def update_shipping_status(self, shipping_id: str, status: ShippingStatus,
                                   tracking_number: Optional[str] = None) -> bool:
        """배송 상태 업데이트"""
        try:
            logger.info(f"배송 상태 업데이트: {shipping_id} -> {status.value}")
            
            update_data = {
                "status": status.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if tracking_number:
                update_data["tracking_number"] = tracking_number
            
            if status == ShippingStatus.DELIVERED:
                update_data["actual_delivery"] = datetime.now(timezone.utc).isoformat()
            
            await self.db_service.update_data(
                table="shipping",
                filters={"shipping_id": shipping_id},
                data=update_data
            )
            
            logger.info(f"배송 상태 업데이트 완료: {shipping_id}")
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, "배송 상태 업데이트 실패")
            return False


class PaymentShippingAutomation:
    """결제 및 배송 자동화 시스템"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.payment_processor = PaymentProcessor(db_service)
        self.shipping_processor = ShippingProcessor(db_service)
        self.error_handler = ErrorHandler()
    
    async def process_order_complete(self, order_id: str, 
                                   payment_request: PaymentRequest,
                                   shipping_request: ShippingRequest) -> Dict[str, Any]:
        """주문 완료 처리 (결제 + 배송)"""
        try:
            logger.info(f"주문 완료 처리 시작: {order_id}")
            
            # 1. 결제 처리
            payment_info = await self.payment_processor.process_payment(payment_request)
            
            if payment_info.status != PaymentStatus.COMPLETED:
                return {
                    "success": False,
                    "error": f"결제 실패: {payment_info.failure_reason}",
                    "payment_info": payment_info,
                    "shipping_info": None
                }
            
            # 2. 배송 처리
            shipping_info = await self.shipping_processor.process_shipping(shipping_request)
            
            # 3. 주문 상태 업데이트
            await self._update_order_status(order_id, "processing")
            
            result = {
                "success": True,
                "order_id": order_id,
                "payment_info": payment_info,
                "shipping_info": shipping_info,
                "message": "주문 완료 처리 성공"
            }
            
            logger.info(f"주문 완료 처리 성공: {order_id}")
            return result
            
        except Exception as e:
            self.error_handler.log_error(e, "주문 완료 처리 실패")
            return {
                "success": False,
                "error": str(e),
                "order_id": order_id
            }
    
    async def _update_order_status(self, order_id: str, status: str) -> None:
        """주문 상태 업데이트"""
        try:
            await self.db_service.update_data(
                table="orders",
                filters={"order_id": order_id},
                data={
                    "status": status,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            self.error_handler.log_error(e, "주문 상태 업데이트 실패")


async def test_payment_shipping_automation():
    """결제 및 배송 자동화 시스템 테스트"""
    logger.info("결제 및 배송 자동화 시스템 테스트 시작")
    
    try:
        # 서비스 초기화
        db_service = DatabaseService()
        automation = PaymentShippingAutomation(db_service)
        
        # 테스트 데이터 생성
        order_id = f"TEST_ORDER_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        payment_request = PaymentRequest(
            order_id=order_id,
            amount=75000.0,
            payment_method=PaymentMethod.CARD,
            customer_info={
                "name": "홍길동",
                "email": "hong@example.com",
                "phone": "010-1234-5678"
            },
            billing_address={
                "address": "서울시 강남구 테헤란로 123",
                "postal_code": "06292"
            },
            items=[
                {"product_id": "PROD_001", "name": "테스트 상품 1", "quantity": 2, "price": 25000},
                {"product_id": "PROD_002", "name": "테스트 상품 2", "quantity": 1, "price": 25000}
            ]
        )
        
        shipping_request = ShippingRequest(
            order_id=order_id,
            items=payment_request.items,
            shipping_address={
                "name": "홍길동",
                "phone": "010-1234-5678",
                "address": "서울시 강남구 테헤란로 123",
                "detail_address": "456호",
                "postal_code": "06292"
            },
            shipping_method=ShippingMethod.STANDARD,
            special_instructions="문 앞에 놓아주세요"
        )
        
        # 주문 완료 처리 실행
        result = await automation.process_order_complete(order_id, payment_request, shipping_request)
        
        # 결과 출력
        logger.info(f"주문 완료 처리 결과:")
        logger.info(f"- 성공: {result['success']}")
        logger.info(f"- 주문 ID: {result.get('order_id', 'N/A')}")
        
        if result["success"]:
            payment_info = result["payment_info"]
            shipping_info = result["shipping_info"]
            
            logger.info(f"- 결제 ID: {payment_info.payment_id}")
            logger.info(f"- 결제 상태: {payment_info.status.value}")
            logger.info(f"- 결제 금액: {payment_info.amount:,.0f}원")
            
            logger.info(f"- 배송 ID: {shipping_info.shipping_id}")
            logger.info(f"- 배송 상태: {shipping_info.status.value}")
            logger.info(f"- 운송장 번호: {shipping_info.tracking_number}")
            logger.info(f"- 예상 배송일: {shipping_info.estimated_delivery}")
        else:
            logger.error(f"- 오류: {result.get('error', 'Unknown error')}")
        
        logger.info("결제 및 배송 자동화 시스템 테스트 완료")
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        raise


    async def _process_credit_payment(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """공급사 적립금 결제 처리"""
        try:
            logger.info(f"공급사 적립금 결제 처리: 주문 {payment_request.order_id}, 금액 {payment_request.amount:,.0f}원")
            
            # 주문 정보에서 공급사 정보 조회
            order_data = await self.db_service.select_data(
                table_name="local_orders",
                conditions={"order_id": payment_request.order_id}
            )
            
            if not order_data:
                return {"success": False, "error": "주문 정보를 찾을 수 없습니다"}
            
            order_info = order_data[0]
            supplier_id = order_info.get("supplier_id")
            account_name = order_info.get("account_name")
            
            if not supplier_id or not account_name:
                return {"success": False, "error": "공급사 정보가 없습니다"}
            
            # 적립금 충분 여부 확인
            if not await self.credit_manager.check_sufficient_credit(supplier_id, account_name, payment_request.amount):
                return {"success": False, "error": "적립금이 부족합니다"}
            
            # 적립금 예약 (차감 준비)
            if not await self.credit_manager.reserve_credit(supplier_id, account_name, payment_request.amount, payment_request.order_id):
                return {"success": False, "error": "적립금 예약 실패"}
            
            # 결제 완료 처리
            transaction_id = f"CREDIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{payment_request.order_id}"
            
            logger.info(f"공급사 적립금 결제 성공: {supplier_id}, {account_name}, 금액: {payment_request.amount:,.0f}원")
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "payment_method": "supplier_credit",
                "supplier_id": supplier_id,
                "account_name": account_name
            }
            
        except Exception as e:
            self.error_handler.log_error(e, f"공급사 적립금 결제 처리 실패: {payment_request.order_id}")
            return {"success": False, "error": str(e)}

    async def confirm_credit_payment(self, order_id: str) -> bool:
        """주문 확정 시 적립금 실제 차감"""
        try:
            logger.info(f"적립금 차감 확정: 주문 {order_id}")
            
            # 주문 정보 조회
            order_data = await self.db_service.select_data(
                table_name="local_orders",
                conditions={"order_id": order_id}
            )
            
            if not order_data:
                logger.error(f"주문 정보를 찾을 수 없습니다: {order_id}")
                return False
            
            order_info = order_data[0]
            supplier_id = order_info.get("supplier_id")
            account_name = order_info.get("account_name")
            payment_amount = order_info.get("payment_amount", 0)
            
            if not supplier_id or not account_name:
                logger.error(f"공급사 정보가 없습니다: {order_id}")
                return False
            
            # 적립금 실제 차감
            if await self.credit_manager.confirm_credit_deduction(supplier_id, account_name, payment_amount, order_id):
                logger.info(f"적립금 차감 확정 성공: {order_id}")
                return True
            else:
                logger.error(f"적립금 차감 확정 실패: {order_id}")
                return False
                
        except Exception as e:
            self.error_handler.log_error(e, f"적립금 차감 확정 실패: {order_id}")
            return False

    async def cancel_credit_payment(self, order_id: str) -> bool:
        """주문 취소 시 적립금 예약 해제"""
        try:
            logger.info(f"적립금 예약 해제: 주문 {order_id}")
            
            # 주문 정보 조회
            order_data = await self.db_service.select_data(
                table_name="local_orders",
                conditions={"order_id": order_id}
            )
            
            if not order_data:
                logger.error(f"주문 정보를 찾을 수 없습니다: {order_id}")
                return False
            
            order_info = order_data[0]
            supplier_id = order_info.get("supplier_id")
            account_name = order_info.get("account_name")
            payment_amount = order_info.get("payment_amount", 0)
            
            if not supplier_id or not account_name:
                logger.error(f"공급사 정보가 없습니다: {order_id}")
                return False
            
            # 적립금 예약 해제
            if await self.credit_manager.cancel_credit_reservation(supplier_id, account_name, payment_amount, order_id):
                logger.info(f"적립금 예약 해제 성공: {order_id}")
                return True
            else:
                logger.error(f"적립금 예약 해제 실패: {order_id}")
                return False
                
        except Exception as e:
            self.error_handler.log_error(e, f"적립금 예약 해제 실패: {order_id}")
            return False
