#!/usr/bin/env python3
"""
트랜잭션 시스템 통합 테스트
"""

import asyncio
import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.database_service import DatabaseService
from src.services.advanced_order_processor import (
    AdvancedOrderProcessor, OrderItem, OrderRequest, ShippingAddress,
    PaymentMethod, OrderPriority
)
from src.services.inventory_manager import (
    InventoryManager, InventoryAction, InventoryStatus
)
from src.services.payment_shipping_automation import (
    PaymentShippingAutomation, PaymentRequest, ShippingRequest,
    ShippingMethod
)


class TransactionSystemIntegrationTest:
    """트랜잭션 시스템 통합 테스트"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.order_processor = AdvancedOrderProcessor(self.db_service)
        self.inventory_manager = InventoryManager(self.db_service)
        self.payment_shipping = PaymentShippingAutomation(self.db_service)
    
    async def run_comprehensive_test(self):
        """종합 테스트 실행"""
        logger.info("=== 트랜잭션 시스템 통합 테스트 시작 ===")
        
        try:
            # 1. 재고 관리 테스트
            await self.test_inventory_management()
            
            # 2. 주문 처리 테스트
            await self.test_order_processing()
            
            # 3. 결제 및 배송 테스트
            await self.test_payment_shipping()
            
            # 4. 전체 워크플로우 테스트
            await self.test_complete_workflow()
            
            logger.info("=== 트랜잭션 시스템 통합 테스트 완료 ===")
            
        except Exception as e:
            logger.error(f"통합 테스트 중 오류 발생: {e}")
            raise
    
    async def test_inventory_management(self):
        """재고 관리 테스트"""
        logger.info("\n--- 재고 관리 테스트 ---")
        
        try:
            # 1. 재고 상태 조회
            logger.info("1. 재고 상태 조회 테스트")
            inventory_items = await self.inventory_manager.get_inventory_status()
            logger.info(f"   총 재고 아이템 수: {len(inventory_items)}")
            
            # 2. 재고 동기화 테스트
            logger.info("2. 재고 동기화 테스트")
            sync_results = []
            for supplier in ["ownerclan", "domaemae_dome", "domaemae_supply", "zentrade"]:
                result = await self.inventory_manager.sync_supplier_inventory(supplier)
                sync_results.append(result)
                logger.info(f"   {supplier}: {'성공' if result.get('success') else '실패'}")
            
            # 3. 재고 알림 조회
            logger.info("3. 재고 알림 조회 테스트")
            alerts = await self.inventory_manager.get_stock_alerts()
            logger.info(f"   재고 알림 수: {len(alerts)}")
            
            logger.info("재고 관리 테스트 완료")
            
        except Exception as e:
            logger.error(f"재고 관리 테스트 실패: {e}")
            raise
    
    async def test_order_processing(self):
        """주문 처리 테스트"""
        logger.info("\n--- 주문 처리 테스트 ---")
        
        try:
            # 테스트 주문 아이템 생성
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
                notes="통합 테스트 주문"
            )
            
            # 주문 처리 실행
            logger.info("주문 처리 실행")
            result = await self.order_processor.process_order(order_request)
            
            logger.info(f"주문 처리 결과:")
            logger.info(f"   주문 ID: {result.order_id}")
            logger.info(f"   상태: {result.status}")
            logger.info(f"   총액: {result.total_amount:,.0f}원")
            logger.info(f"   공급사 주문 수: {len(result.supplier_orders)}")
            
            if result.errors:
                logger.warning(f"   오류: {result.errors}")
            
            logger.info("주문 처리 테스트 완료")
            
        except Exception as e:
            logger.error(f"주문 처리 테스트 실패: {e}")
            raise
    
    async def test_payment_shipping(self):
        """결제 및 배송 테스트"""
        logger.info("\n--- 결제 및 배송 테스트 ---")
        
        try:
            order_id = f"TEST_PAYMENT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 결제 요청 생성
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
            
            # 배송 요청 생성
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
            
            # 결제 및 배송 처리
            logger.info("결제 및 배송 처리 실행")
            result = await self.payment_shipping.process_order_complete(
                order_id, payment_request, shipping_request
            )
            
            logger.info(f"결제 및 배송 처리 결과:")
            logger.info(f"   성공: {result['success']}")
            logger.info(f"   주문 ID: {result.get('order_id', 'N/A')}")
            
            if result["success"]:
                payment_info = result["payment_info"]
                shipping_info = result["shipping_info"]
                
                logger.info(f"   결제 ID: {payment_info.payment_id}")
                logger.info(f"   결제 상태: {payment_info.status.value}")
                logger.info(f"   결제 금액: {payment_info.amount:,.0f}원")
                
                logger.info(f"   배송 ID: {shipping_info.shipping_id}")
                logger.info(f"   배송 상태: {shipping_info.status.value}")
                logger.info(f"   운송장 번호: {shipping_info.tracking_number}")
            else:
                logger.error(f"   오류: {result.get('error', 'Unknown error')}")
            
            logger.info("결제 및 배송 테스트 완료")
            
        except Exception as e:
            logger.error(f"결제 및 배송 테스트 실패: {e}")
            raise
    
    async def test_complete_workflow(self):
        """전체 워크플로우 테스트"""
        logger.info("\n--- 전체 워크플로우 테스트 ---")
        
        try:
            # 1. 재고 확인 및 동기화
            logger.info("1. 재고 확인 및 동기화")
            await self.inventory_manager.sync_supplier_inventory("ownerclan")
            
            # 2. 주문 생성 및 처리
            logger.info("2. 주문 생성 및 처리")
            test_items = [
                OrderItem(
                    product_id="PROD_WORKFLOW_001",
                    product_name="워크플로우 테스트 상품",
                    quantity=1,
                    unit_price=30000,
                    total_price=30000,
                    supplier_code="ownerclan",
                    supplier_product_id="WFK7323"
                )
            ]
            
            shipping_address = ShippingAddress(
                name="김철수",
                phone="010-9876-5432",
                address="부산시 해운대구 센텀로 456",
                detail_address="789호",
                postal_code="48099",
                city="부산시",
                province="해운대구"
            )
            
            order_request = OrderRequest(
                customer_id="CUST_WORKFLOW_001",
                items=test_items,
                shipping_address=shipping_address,
                payment_method=PaymentMethod.CARD,
                priority=OrderPriority.HIGH,
                notes="전체 워크플로우 테스트"
            )
            
            order_result = await self.order_processor.process_order(order_request)
            
            if order_result.status == "completed":
                # 3. 결제 및 배송 처리
                logger.info("3. 결제 및 배송 처리")
                
                payment_request = PaymentRequest(
                    order_id=order_result.order_id,
                    amount=order_result.total_amount,
                    payment_method=PaymentMethod.CARD,
                    customer_info={
                        "name": "김철수",
                        "email": "kim@example.com",
                        "phone": "010-9876-5432"
                    },
                    billing_address={
                        "address": "부산시 해운대구 센텀로 456",
                        "postal_code": "48099"
                    },
                    items=[{"product_id": item.product_id, "name": item.product_name, 
                           "quantity": item.quantity, "price": item.unit_price} 
                          for item in test_items]
                )
                
                shipping_request = ShippingRequest(
                    order_id=order_result.order_id,
                    items=payment_request.items,
                    shipping_address={
                        "name": "김철수",
                        "phone": "010-9876-5432",
                        "address": "부산시 해운대구 센텀로 456",
                        "detail_address": "789호",
                        "postal_code": "48099"
                    },
                    shipping_method=ShippingMethod.EXPRESS,
                    special_instructions="빠른 배송 요청"
                )
                
                payment_shipping_result = await self.payment_shipping.process_order_complete(
                    order_result.order_id, payment_request, shipping_request
                )
                
                if payment_shipping_result["success"]:
                    # 4. 재고 업데이트
                    logger.info("4. 재고 업데이트")
                    for item in test_items:
                        await self.inventory_manager.update_inventory(
                            item.product_id,
                            item.supplier_code,
                            InventoryAction.SALE,
                            item.quantity,
                            reference_id=order_result.order_id,
                            notes=f"주문 완료: {order_result.order_id}"
                        )
                    
                    logger.info("전체 워크플로우 테스트 성공!")
                    logger.info(f"   최종 주문 ID: {order_result.order_id}")
                    logger.info(f"   결제 ID: {payment_shipping_result['payment_info'].payment_id}")
                    logger.info(f"   배송 ID: {payment_shipping_result['shipping_info'].shipping_id}")
                else:
                    logger.error(f"결제 및 배송 처리 실패: {payment_shipping_result.get('error')}")
            else:
                logger.error(f"주문 처리 실패: {order_result.errors}")
            
            logger.info("전체 워크플로우 테스트 완료")
            
        except Exception as e:
            logger.error(f"전체 워크플로우 테스트 실패: {e}")
            raise
    
    async def generate_test_report(self):
        """테스트 리포트 생성"""
        logger.info("\n=== 테스트 리포트 생성 ===")
        
        try:
            # 데이터베이스에서 테스트 결과 조회
            orders = await self.db_service.select_data("orders", limit=10)
            payments = await self.db_service.select_data("payments", limit=10)
            shipping = await self.db_service.select_data("shipping", limit=10)
            inventory = await self.db_service.select_data("product_inventory", limit=10)
            
            logger.info(f"테스트 결과 요약:")
            logger.info(f"   주문 수: {len(orders)}")
            logger.info(f"   결제 수: {len(payments)}")
            logger.info(f"   배송 수: {len(shipping)}")
            logger.info(f"   재고 아이템 수: {len(inventory)}")
            
            # 최근 주문 상태 분석
            if orders:
                status_counts = {}
                for order in orders:
                    status = order.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                logger.info(f"   주문 상태 분포: {status_counts}")
            
            logger.info("테스트 리포트 생성 완료")
            
        except Exception as e:
            logger.error(f"테스트 리포트 생성 실패: {e}")


async def main():
    """메인 테스트 함수"""
    logger.info("트랜잭션 시스템 통합 테스트 시작")
    
    try:
        test_suite = TransactionSystemIntegrationTest()
        
        # 종합 테스트 실행
        await test_suite.run_comprehensive_test()
        
        # 테스트 리포트 생성
        await test_suite.generate_test_report()
        
        logger.info("모든 테스트가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        logger.error(f"테스트 실행 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
