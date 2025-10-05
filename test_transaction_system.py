"""
트랜잭션 시스템 통합 테스트
"""

import asyncio
import json
from datetime import datetime, timezone
from loguru import logger

from src.services.transaction_system import (
    TransactionSystem, OrderInput, OrderProduct, OrderRecipient, 
    TransactionType, OrderStatus
)
from src.services.order_management_service import OrderManagementService
from src.services.inventory_sync_service import InventorySyncService
from src.services.database_service import DatabaseService


class TransactionSystemTester:
    """트랜잭션 시스템 테스트 클래스"""

    def __init__(self):
        self.transaction_system = TransactionSystem()
        self.order_management = OrderManagementService()
        self.inventory_sync = InventorySyncService()
        self.db_service = DatabaseService()
        
        # 테스트 계정
        self.test_account = "test_account"

    async def test_order_simulation(self) -> bool:
        """주문 시뮬레이션 테스트"""
        try:
            logger.info("\n=== 주문 시뮬레이션 테스트 시작 ===")
            
            # 테스트 주문 데이터 구성
            test_order = OrderInput(
                products=[
                    OrderProduct(
                        item_key="WFK71WC",  # 실제 존재하는 상품 키 사용
                        quantity=2,
                        option_attributes=[
                            {"name": "색상", "value": "RED"},
                            {"name": "사이즈", "value": "95"}
                        ]
                    )
                ],
                recipient=OrderRecipient(
                    name="테스트 수령자",
                    phone="010-1234-5678",
                    address="서울특별시 강남구 테헤란로 123",
                    postal_code="12345",
                    city="서울특별시",
                    district="강남구",
                    detail_address="테헤란로 123, 456호"
                ),
                note="테스트 주문",
                seller_note="시뮬레이션 테스트",
                orderer_note="배송 시 문 앞에 놓아주세요"
            )
            
            # 주문 시뮬레이션 실행
            result = await self.transaction_system.simulate_order(
                self.test_account, 
                test_order
            )
            
            if result.success:
                logger.info("✅ 주문 시뮬레이션 성공!")
                logger.info(f"예상 상품 금액: {result.data}")
                return True
            else:
                logger.error(f"❌ 주문 시뮬레이션 실패: {result.error}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 주문 시뮬레이션 테스트 중 오류: {e}")
            return False

    async def test_order_creation(self) -> bool:
        """주문 생성 테스트 (실제 주문 생성)"""
        try:
            logger.info("\n=== 주문 생성 테스트 시작 ===")
            
            # 테스트 주문 데이터 구성
            test_order = OrderInput(
                products=[
                    OrderProduct(
                        item_key="WFK71WC",  # 실제 존재하는 상품 키 사용
                        quantity=1,
                        option_attributes=[
                            {"name": "색상", "value": "BLUE"},
                            {"name": "사이즈", "value": "100"}
                        ]
                    )
                ],
                recipient=OrderRecipient(
                    name="테스트 구매자",
                    phone="010-9876-5432",
                    address="서울특별시 서초구 서초대로 456",
                    postal_code="54321",
                    city="서울특별시",
                    district="서초구",
                    detail_address="서초대로 456, 789호"
                ),
                note="테스트 주문 생성",
                seller_note="트랜잭션 테스트",
                orderer_note="안전하게 배송해주세요"
            )
            
            # 주문 생성 실행
            result = await self.transaction_system.create_order(
                self.test_account, 
                test_order
            )
            
            if result.success:
                logger.info("✅ 주문 생성 성공!")
                logger.info(f"주문 키: {result.order_key}")
                logger.info(f"트랜잭션 ID: {result.transaction_id}")
                return True
            else:
                logger.error(f"❌ 주문 생성 실패: {result.error}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 주문 생성 테스트 중 오류: {e}")
            return False

    async def test_order_status_sync(self) -> bool:
        """주문 상태 동기화 테스트"""
        try:
            logger.info("\n=== 주문 상태 동기화 테스트 시작 ===")
            
            # 최근 주문 목록 조회
            orders_result = await self.order_management.pull_orders_from_ownerclan(
                self.test_account,
                limit=5
            )
            
            if not orders_result["success"]:
                logger.error(f"❌ 주문 목록 조회 실패: {orders_result['error']}")
                return False
            
            logger.info(f"✅ 주문 목록 조회 성공: {orders_result['synced_count']}개")
            
            # 로컬 주문 목록 조회
            local_orders = await self.order_management.get_local_orders(
                self.test_account,
                limit=5
            )
            
            if local_orders:
                logger.info(f"✅ 로컬 주문 목록 조회 성공: {len(local_orders)}개")
                
                # 첫 번째 주문의 상태 동기화 테스트
                first_order = local_orders[0]
                order_key = first_order["ownerclan_order_key"]
                
                sync_result = await self.order_management.sync_order_status(
                    self.test_account,
                    order_key
                )
                
                if sync_result:
                    logger.info(f"✅ 주문 상태 동기화 성공: {order_key}")
                    return True
                else:
                    logger.error(f"❌ 주문 상태 동기화 실패: {order_key}")
                    return False
            else:
                logger.warning("⚠️ 로컬 주문이 없어서 상태 동기화 테스트를 건너뜀")
                return True
                
        except Exception as e:
            logger.error(f"❌ 주문 상태 동기화 테스트 중 오류: {e}")
            return False

    async def test_inventory_sync(self) -> bool:
        """재고 동기화 테스트"""
        try:
            logger.info("\n=== 재고 동기화 테스트 시작 ===")
            
            # 전체 상품 재고 동기화
            inventory_result = await self.inventory_sync.sync_all_products_inventory(
                self.test_account,
                limit=10
            )
            
            if not inventory_result["success"]:
                logger.error(f"❌ 재고 동기화 실패: {inventory_result['error']}")
                return False
            
            logger.info(f"✅ 재고 동기화 성공: {inventory_result['synced_count']}개")
            
            # 재고 부족 상품 조회
            low_stock_products = await self.inventory_sync.get_low_stock_products(
                self.test_account,
                threshold=50
            )
            
            if low_stock_products:
                logger.info(f"✅ 재고 부족 상품 조회 성공: {len(low_stock_products)}개")
                for product in low_stock_products[:3]:  # 상위 3개만 출력
                    logger.info(f"  - {product['item_name']}: {product['total_quantity']}개")
            else:
                logger.info("✅ 재고 부족 상품 없음")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 재고 동기화 테스트 중 오류: {e}")
            return False

    async def test_transaction_logs(self) -> bool:
        """트랜잭션 로그 조회 테스트"""
        try:
            logger.info("\n=== 트랜잭션 로그 조회 테스트 시작 ===")
            
            # 트랜잭션 로그 조회
            transaction_logs = await self.db_service.select_data(
                "transaction_logs",
                {"account_name": self.test_account}
            )
            
            if transaction_logs:
                logger.info(f"✅ 트랜잭션 로그 조회 성공: {len(transaction_logs)}개")
                
                # 최근 트랜잭션 로그 출력
                for log in transaction_logs[:3]:
                    logger.info(f"  - {log['transaction_type']}: {log['success']} ({log['timestamp']})")
                
                return True
            else:
                logger.warning("⚠️ 트랜잭션 로그가 없음")
                return True
                
        except Exception as e:
            logger.error(f"❌ 트랜잭션 로그 조회 테스트 중 오류: {e}")
            return False

    async def run_all_tests(self) -> bool:
        """모든 테스트 실행"""
        try:
            logger.info("🚀 트랜잭션 시스템 통합 테스트 시작")
            
            test_results = []
            
            # 1. 주문 시뮬레이션 테스트
            test_results.append(await self.test_order_simulation())
            
            # 2. 주문 생성 테스트 (실제 주문 생성)
            test_results.append(await self.test_order_creation())
            
            # 3. 주문 상태 동기화 테스트
            test_results.append(await self.test_order_status_sync())
            
            # 4. 재고 동기화 테스트
            test_results.append(await self.test_inventory_sync())
            
            # 5. 트랜잭션 로그 조회 테스트
            test_results.append(await self.test_transaction_logs())
            
            # 결과 요약
            passed_tests = sum(test_results)
            total_tests = len(test_results)
            
            logger.info(f"\n📊 테스트 결과 요약:")
            logger.info(f"  총 테스트: {total_tests}개")
            logger.info(f"  성공: {passed_tests}개")
            logger.info(f"  실패: {total_tests - passed_tests}개")
            logger.info(f"  성공률: {passed_tests/total_tests*100:.1f}%")
            
            if passed_tests == total_tests:
                logger.info("🎉 모든 테스트 통과!")
                return True
            else:
                logger.warning("⚠️ 일부 테스트 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 테스트 실행 중 오류: {e}")
            return False


async def main():
    """메인 함수"""
    tester = TransactionSystemTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("\n✅ 트랜잭션 시스템 통합 테스트 완료")
    else:
        logger.error("\n❌ 트랜잭션 시스템 통합 테스트 실패")


if __name__ == "__main__":
    asyncio.run(main())
