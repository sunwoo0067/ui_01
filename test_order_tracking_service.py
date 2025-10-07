#!/usr/bin/env python3
"""
주문 상태 추적 및 동기화 서비스 테스트
"""

import asyncio
import sys
import os
from loguru import logger
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.services.order_tracking_service import OrderTrackingService, OrderStatus


async def test_order_tracking_service():
    """주문 상태 추적 서비스 테스트"""
    try:
        logger.info("주문 상태 추적 서비스 테스트 시작")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 주문 추적 서비스 초기화
        tracking_service = OrderTrackingService(db_service)
        
        # 1. 주문 추적 생성 테스트
        logger.info("=== 주문 추적 생성 테스트 ===")
        
        test_order_data = {
            "order_id": f"test_order_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "supplier_id": "domaemae_dome",
            "supplier_account_id": "test_account",
            "supplier_order_id": "dome_test_001",
            "customer_name": "테스트 고객",
            "total_amount": 50000,
            "order_date": datetime.utcnow().isoformat()
        }
        
        order_id = await tracking_service.create_order_tracking(test_order_data)
        
        if order_id:
            logger.info(f"주문 추적 생성 성공: {order_id}")
        else:
            logger.error("주문 추적 생성 실패")
            return
        
        # 2. 주문 상태 업데이트 테스트
        logger.info("=== 주문 상태 업데이트 테스트 ===")
        
        status_updates = [
            (OrderStatus.CONFIRMED.value, "주문 확인됨"),
            (OrderStatus.PREPARING.value, "배송 준비중"),
            (OrderStatus.SHIPPED.value, "배송중"),
            (OrderStatus.DELIVERED.value, "배송 완료")
        ]
        
        for status, note in status_updates:
            success = await tracking_service.update_order_status(order_id, status, note)
            if success:
                logger.info(f"주문 상태 업데이트 성공: {status}")
            else:
                logger.error(f"주문 상태 업데이트 실패: {status}")
            
            # 상태 업데이트 간격
            await asyncio.sleep(0.5)
        
        # 3. 주문 상태 조회 테스트
        logger.info("=== 주문 상태 조회 테스트 ===")
        
        order_status = await tracking_service.get_order_status(order_id)
        if order_status:
            logger.info(f"주문 상태 조회 성공:")
            logger.info(f"  - 주문 ID: {order_status['order_id']}")
            logger.info(f"  - 현재 상태: {order_status['current_status']}")
            logger.info(f"  - 마지막 업데이트: {order_status['last_updated']}")
            logger.info(f"  - 상태 히스토리: {len(order_status['status_history'])}개")
        else:
            logger.error("주문 상태 조회 실패")
        
        # 4. 활성 주문 목록 조회 테스트
        logger.info("=== 활성 주문 목록 조회 테스트 ===")
        
        active_orders = await tracking_service.get_active_orders()
        logger.info(f"활성 주문 수: {len(active_orders)}개")
        
        for order in active_orders:
            logger.info(f"  - 주문 ID: {order['order_id']}, 상태: {order['current_status']}")
        
        # 5. 공급사별 주문 상태 동기화 테스트
        logger.info("=== 공급사별 주문 상태 동기화 테스트 ===")
        
        suppliers = ["domaemae_dome", "ownerclan", "zentrade"]
        
        for supplier_id in suppliers:
            logger.info(f"{supplier_id} 주문 상태 동기화 테스트...")
            
            sync_result = await tracking_service.sync_order_status_from_supplier(
                supplier_id, "test_account"
            )
            
            if sync_result["success"]:
                logger.info(f"{supplier_id} 동기화 성공: {sync_result['synced_count']}개")
            else:
                logger.error(f"{supplier_id} 동기화 실패: {sync_result.get('error', 'Unknown error')}")
        
        # 6. 주문 통계 조회 테스트
        logger.info("=== 주문 통계 조회 테스트 ===")
        
        statistics = await tracking_service.get_order_statistics(days=30)
        
        logger.info(f"주문 통계 (최근 30일):")
        logger.info(f"  - 총 주문 수: {statistics['total_orders']}개")
        logger.info(f"  - 상태별 분포:")
        
        for status, count in statistics["status_distribution"].items():
            logger.info(f"    - {status}: {count}개")
        
        # 7. 추가 주문 생성 및 테스트
        logger.info("=== 추가 주문 생성 및 테스트 ===")
        
        additional_orders = [
            {
                "order_id": f"test_order_2_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "supplier_id": "ownerclan",
                "supplier_account_id": "test_account",
                "supplier_order_id": "ownerclan_test_001",
                "customer_name": "테스트 고객 2",
                "total_amount": 75000,
                "order_date": datetime.utcnow().isoformat()
            },
            {
                "order_id": f"test_order_3_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "supplier_id": "zentrade",
                "supplier_account_id": "test_account",
                "supplier_order_id": "zentrade_test_001",
                "customer_name": "테스트 고객 3",
                "total_amount": 30000,
                "order_date": datetime.utcnow().isoformat()
            }
        ]
        
        for order_data in additional_orders:
            order_id = await tracking_service.create_order_tracking(order_data)
            if order_id:
                logger.info(f"추가 주문 생성 성공: {order_id}")
                
                # 상태 업데이트
                await tracking_service.update_order_status(
                    order_id, 
                    OrderStatus.CONFIRMED.value,
                    "추가 주문 확인"
                )
            else:
                logger.error(f"추가 주문 생성 실패: {order_data['order_id']}")
        
        # 8. 공급사별 활성 주문 조회
        logger.info("=== 공급사별 활성 주문 조회 테스트 ===")
        
        for supplier_id in suppliers:
            supplier_orders = await tracking_service.get_active_orders(supplier_id=supplier_id)
            logger.info(f"{supplier_id} 활성 주문: {len(supplier_orders)}개")
        
        # 9. 상태별 주문 조회
        logger.info("=== 상태별 주문 조회 테스트 ===")
        
        for status in [OrderStatus.PENDING.value, OrderStatus.CONFIRMED.value, OrderStatus.DELIVERED.value]:
            status_orders = await tracking_service.get_active_orders(status=status)
            logger.info(f"{status} 상태 주문: {len(status_orders)}개")
        
        logger.info("주문 상태 추적 서비스 테스트 완료")
        
    except Exception as e:
        logger.error(f"테스트 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_order_tracking_service())
