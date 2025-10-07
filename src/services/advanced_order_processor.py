#!/usr/bin/env python3
"""
고급 주문 처리 시스템 - 다중 공급사 지원
"""

import asyncio
import sys
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import json
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.settings import settings
from src.utils.error_handler import ErrorHandler, BaseAPIError, DatabaseError
from src.services.database_service import DatabaseService
from src.services.ownerclan_token_manager import OwnerClanTokenManager
from src.services.supplier_account_manager import SupplierAccountManager
from src.services.domaemae_optimal_order_service import DomaemaeOptimalOrderService


class OrderPriority(Enum):
    """주문 우선순위"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class PaymentMethod(Enum):
    """결제 방법"""
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    VIRTUAL_ACCOUNT = "virtual_account"
    MOBILE_PAYMENT = "mobile_payment"


@dataclass
class OrderItem:
    """주문 아이템"""
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    supplier_code: str
    supplier_product_id: str
    options: Optional[Dict[str, str]] = None
    notes: Optional[str] = None


@dataclass
class ShippingAddress:
    """배송 주소"""
    name: str
    phone: str
    address: str
    detail_address: str
    postal_code: str
    city: str
    province: str
    country: str = "KR"


@dataclass
class OrderRequest:
    """주문 요청"""
    customer_id: str
    items: List[OrderItem]
    shipping_address: ShippingAddress
    payment_method: PaymentMethod
    priority: OrderPriority = OrderPriority.NORMAL
    notes: Optional[str] = None
    requested_delivery_date: Optional[datetime] = None


@dataclass
class OrderResult:
    """주문 결과"""
    order_id: str
    status: str
    total_amount: float
    supplier_orders: List[Dict[str, Any]]
    estimated_delivery_date: Optional[datetime] = None
    tracking_numbers: List[str] = None
    errors: List[str] = None


class AdvancedOrderProcessor:
    """고급 주문 처리 시스템"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
        self.supplier_manager = SupplierAccountManager()
        self.optimal_order_service = DomaemaeOptimalOrderService(self.db_service)
        
        # 공급사별 주문 처리기
        self.order_processors = {
            "ownerclan": self._process_ownerclan_order,
            "domaemae_dome": self._process_domaemae_order,
            "domaemae_supply": self._process_domaemae_order,
            "zentrade": self._process_zentrade_order
        }
    
    async def process_order(self, order_request: OrderRequest) -> OrderResult:
        """주문 처리 메인 함수"""
        try:
            logger.info(f"주문 처리 시작: 고객 {order_request.customer_id}")
            
            # 1. 재고 확인
            inventory_check = await self._check_inventory(order_request.items)
            if not inventory_check["available"]:
                return OrderResult(
                    order_id="",
                    status="failed",
                    total_amount=0,
                    supplier_orders=[],
                    errors=inventory_check["errors"]
                )
            
            # 2. 최적 공급사 선택
            optimized_items = await self._optimize_supplier_selection(order_request.items)
            
            # 3. 공급사별 주문 그룹화
            supplier_groups = self._group_items_by_supplier(optimized_items)
            
            # 4. 공급사별 주문 처리
            supplier_orders = []
            total_amount = 0
            all_errors = []
            
            for supplier_code, items in supplier_groups.items():
                try:
                    supplier_order = await self._process_supplier_order(
                        supplier_code, items, order_request
                    )
                    supplier_orders.append(supplier_order)
                    total_amount += supplier_order.get("total_amount", 0)
                except Exception as e:
                    error_msg = f"{supplier_code} 주문 처리 실패: {str(e)}"
                    logger.error(error_msg)
                    all_errors.append(error_msg)
            
            # 5. 주문 결과 생성
            order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{order_request.customer_id}"
            
            result = OrderResult(
                order_id=order_id,
                status="completed" if not all_errors else "partial",
                total_amount=total_amount,
                supplier_orders=supplier_orders,
                errors=all_errors
            )
            
            # 6. 주문 정보 저장
            await self._save_order_to_database(order_request, result)
            
            logger.info(f"주문 처리 완료: {order_id}, 총액: {total_amount:,.0f}원")
            return result
            
        except Exception as e:
            self.error_handler.log_error(e, "주문 처리 중 오류 발생")
            return OrderResult(
                order_id="",
                status="failed",
                total_amount=0,
                supplier_orders=[],
                errors=[f"주문 처리 실패: {str(e)}"]
            )
    
    async def _check_inventory(self, items: List[OrderItem]) -> Dict[str, Any]:
        """재고 확인"""
        try:
            logger.info("재고 확인 시작")
            
            unavailable_items = []
            errors = []
            
            for item in items:
                # 데이터베이스에서 재고 확인
                inventory_data = await self.db_service.select_data(
                    table_name="product_inventory",
                    conditions={"supplier_product_id": item.supplier_product_id}
                )
                
                if not inventory_data:
                    unavailable_items.append(item.product_name)
                    errors.append(f"{item.product_name}: 재고 정보 없음")
                    continue
                
                available_quantity = inventory_data[0].get("available_quantity", 0)
                if available_quantity < item.quantity:
                    unavailable_items.append(item.product_name)
                    errors.append(f"{item.product_name}: 재고 부족 (요청: {item.quantity}, 가용: {available_quantity})")
            
            return {
                "available": len(unavailable_items) == 0,
                "unavailable_items": unavailable_items,
                "errors": errors
            }
            
        except Exception as e:
            self.error_handler.log_error(e, "재고 확인 중 오류")
            return {
                "available": False,
                "unavailable_items": [],
                "errors": [f"재고 확인 실패: {str(e)}"]
            }
    
    async def _optimize_supplier_selection(self, items: List[OrderItem]) -> List[OrderItem]:
        """최적 공급사 선택"""
        try:
            logger.info("최적 공급사 선택 시작")
            
            optimized_items = []
            
            for item in items:
                # 도매매/도매꾹 최적화
                if item.supplier_code in ["domaemae_dome", "domaemae_supply"]:
                    optimization_result = await self.optimal_order_service.analyze_order_requirements(
                        item.quantity, item.unit_price
                    )
                    
                    # 최적 공급사로 변경
                    if optimization_result["recommended_market"] != item.supplier_code:
                        item.supplier_code = optimization_result["recommended_market"]
                        logger.info(f"{item.product_name}: {optimization_result['recommended_market']}로 최적화")
                
                optimized_items.append(item)
            
            return optimized_items
            
        except Exception as e:
            self.error_handler.log_error(e, "공급사 최적화 중 오류")
            return items
    
    def _group_items_by_supplier(self, items: List[OrderItem]) -> Dict[str, List[OrderItem]]:
        """공급사별 아이템 그룹화"""
        groups = {}
        
        for item in items:
            if item.supplier_code not in groups:
                groups[item.supplier_code] = []
            groups[item.supplier_code].append(item)
        
        return groups
    
    async def _process_supplier_order(self, supplier_code: str, items: List[OrderItem], 
                                    order_request: OrderRequest) -> Dict[str, Any]:
        """공급사별 주문 처리"""
        try:
            logger.info(f"{supplier_code} 주문 처리 시작")
            
            if supplier_code not in self.order_processors:
                raise ValueError(f"지원하지 않는 공급사: {supplier_code}")
            
            processor = self.order_processors[supplier_code]
            result = await processor(items, order_request)
            
            logger.info(f"{supplier_code} 주문 처리 완료")
            return result
            
        except Exception as e:
            self.error_handler.log_error(e, f"{supplier_code} 주문 처리 실패")
            raise
    
    async def _process_ownerclan_order(self, items: List[OrderItem], 
                                     order_request: OrderRequest) -> Dict[str, Any]:
        """오너클랜 주문 처리"""
        try:
            # 오너클랜 주문 처리 로직
            from src.services.transaction_system import TransactionSystem
            
            transaction_system = TransactionSystem(self.db_service)
            
            # 오너클랜 주문 형식으로 변환
            order_input = self._convert_to_ownerclan_format(items, order_request)
            
            # 주문 생성
            result = await transaction_system.create_order(order_input)
            
            return {
                "supplier_code": "ownerclan",
                "order_id": result.get("order_id", ""),
                "status": result.get("status", "unknown"),
                "total_amount": sum(item.total_price for item in items),
                "items_count": len(items)
            }
            
        except Exception as e:
            logger.error(f"오너클랜 주문 처리 실패: {e}")
            raise
    
    async def _process_domaemae_order(self, items: List[OrderItem], 
                                    order_request: OrderRequest) -> Dict[str, Any]:
        """도매매/도매꾹 주문 처리"""
        try:
            # 도매매 주문 처리 로직 (시뮬레이션)
            logger.info("도매매 주문 처리 (시뮬레이션)")
            
            return {
                "supplier_code": items[0].supplier_code,
                "order_id": f"DOMA_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "status": "pending",
                "total_amount": sum(item.total_price for item in items),
                "items_count": len(items)
            }
            
        except Exception as e:
            logger.error(f"도매매 주문 처리 실패: {e}")
            raise
    
    async def _process_zentrade_order(self, items: List[OrderItem], 
                                    order_request: OrderRequest) -> Dict[str, Any]:
        """젠트레이드 주문 처리"""
        try:
            # 젠트레이드 주문 처리 로직 (시뮬레이션)
            logger.info("젠트레이드 주문 처리 (시뮬레이션)")
            
            return {
                "supplier_code": "zentrade",
                "order_id": f"ZEN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "status": "pending",
                "total_amount": sum(item.total_price for item in items),
                "items_count": len(items)
            }
            
        except Exception as e:
            logger.error(f"젠트레이드 주문 처리 실패: {e}")
            raise
    
    def _convert_to_ownerclan_format(self, items: List[OrderItem], 
                                   order_request: OrderRequest) -> Dict[str, Any]:
        """오너클랜 주문 형식으로 변환"""
        from src.services.transaction_system import OrderProduct, OrderRecipient
        
        # 상품 변환
        products = []
        for item in items:
            products.append(OrderProduct(
                item_key=item.supplier_product_id,
                quantity=item.quantity,
                option_attributes=[f"{k}:{v}" for k, v in (item.options or {}).items()]
            ))
        
        # 수령자 정보 변환
        recipient = OrderRecipient(
            name=order_request.shipping_address.name,
            phone=order_request.shipping_address.phone,
            address=order_request.shipping_address.address,
            detail_address=order_request.shipping_address.detail_address,
            postal_code=order_request.shipping_address.postal_code
        )
        
        return {
            "products": products,
            "recipient": recipient,
            "notes": order_request.notes
        }
    
    async def _save_order_to_database(self, order_request: OrderRequest, 
                                     result: OrderResult) -> None:
        """주문 정보를 데이터베이스에 저장"""
        try:
            logger.info("주문 정보 데이터베이스 저장")
            
            # 주문 메인 정보
            order_data = {
                "order_id": result.order_id,
                "customer_id": order_request.customer_id,
                "status": result.status,
                "total_amount": result.total_amount,
                "payment_method": order_request.payment_method.value,
                "priority": order_request.priority.value,
                "shipping_address": asdict(order_request.shipping_address),
                "notes": order_request.notes,
                "supplier_orders": result.supplier_orders,
                "errors": result.errors,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # 데이터베이스에 저장
            await self.db_service.insert_data("orders", order_data)
            
            # 주문 아이템 저장
            for item in order_request.items:
                item_data = {
                    "order_id": result.order_id,
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "supplier_code": item.supplier_code,
                    "supplier_product_id": item.supplier_product_id,
                    "options": item.options,
                    "notes": item.notes,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await self.db_service.insert_data("order_items", item_data)
            
            logger.info(f"주문 정보 저장 완료: {result.order_id}")
            
        except Exception as e:
            self.error_handler.log_error(e, "주문 정보 저장 실패")
            raise


async def test_advanced_order_processor():
    """고급 주문 처리 시스템 테스트"""
    logger.info("고급 주문 처리 시스템 테스트 시작")
    
    try:
        # 서비스 초기화
        db_service = DatabaseService()
        processor = AdvancedOrderProcessor(db_service)
        
        # 테스트 주문 요청 생성
        test_items = [
            OrderItem(
                product_id="PROD_001",
                product_name="테스트 상품 1",
                quantity=2,
                unit_price=25000,
                total_price=50000,
                supplier_code="ownerclan",
                supplier_product_id="WFK7323",
                options={"색상": "빨강", "사이즈": "L"}
            ),
            OrderItem(
                product_id="PROD_002",
                product_name="테스트 상품 2",
                quantity=1,
                unit_price=15000,
                total_price=15000,
                supplier_code="domaemae_supply",
                supplier_product_id="dome_12345"
            )
        ]
        
        shipping_address = ShippingAddress(
            name="홍길동",
            phone="010-1234-5678",
            address="서울시 강남구 테헤란로 123",
            detail_address="456호",
            postal_code="06292",
            city="서울시",
            province="강남구"
        )
        
        order_request = OrderRequest(
            customer_id="CUST_001",
            items=test_items,
            shipping_address=shipping_address,
            payment_method=PaymentMethod.CARD,
            priority=OrderPriority.NORMAL,
            notes="테스트 주문입니다."
        )
        
        # 주문 처리 실행
        result = await processor.process_order(order_request)
        
        # 결과 출력
        logger.info(f"주문 처리 결과:")
        logger.info(f"- 주문 ID: {result.order_id}")
        logger.info(f"- 상태: {result.status}")
        logger.info(f"- 총액: {result.total_amount:,.0f}원")
        logger.info(f"- 공급사 주문 수: {len(result.supplier_orders)}")
        
        if result.errors:
            logger.warning(f"오류: {result.errors}")
        
        logger.info("고급 주문 처리 시스템 테스트 완료")
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_advanced_order_processor())
