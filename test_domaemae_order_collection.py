#!/usr/bin/env python3
"""
도매꾹 주문 데이터 수집 테스트 스크립트
"""

import asyncio
import sys
import os
from loguru import logger
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.services.domaemae_data_collector import DomaemaeDataCollector, DomaemaeDataStorage
from src.services.order_tracking_service import OrderTrackingService


async def test_domaemae_order_collection():
    """도매꾹 주문 데이터 수집 테스트"""
    try:
        logger.info("=== 도매꾹 주문 데이터 수집 테스트 시작 ===")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 도매꾹 데이터 수집기 초기화
        collector = DomaemaeDataCollector(db_service)
        storage = DomaemaeDataStorage(db_service)
        
        # 주문 추적 서비스 초기화
        tracking_service = OrderTrackingService(db_service)
        
        account_name = "test_account"
        
        # 1. 도매꾹 주문 데이터 수집 테스트
        logger.info("=== 도매꾹 주문 데이터 수집 테스트 ===")
        
        # 도매꾹 시장에서 주문 데이터 수집
        dome_orders = await collector.collect_orders(
            account_name=account_name,
            market="dome",  # 도매꾹 시장
            page=1,
            size=50
        )
        
        logger.info(f"도매꾹 주문 데이터 수집 완료: {len(dome_orders)}개")
        
        # 도매매 시장에서 주문 데이터 수집
        supply_orders = await collector.collect_orders(
            account_name=account_name,
            market="supply",  # 도매매 시장
            page=1,
            size=50
        )
        
        logger.info(f"도매매 주문 데이터 수집 완료: {len(supply_orders)}개")
        
        # 2. 주문 데이터 저장 테스트
        logger.info("=== 주문 데이터 저장 테스트 ===")
        
        all_orders = dome_orders + supply_orders
        
        if all_orders:
            saved_count = await storage.save_orders(all_orders)
            logger.info(f"주문 데이터 저장 완료: {saved_count}개")
            
            # 3. 주문 추적 시스템 테스트
            logger.info("=== 주문 추적 시스템 테스트 ===")
            
            for i, order in enumerate(all_orders[:5]):  # 처음 5개 주문만 테스트
                try:
                    # 주문 추적 생성
                    tracking_data = {
                        "order_id": f"domaemae_{order['order_id']}_{i}",
                        "supplier_id": "domaemae_dome" if order.get("market") == "dome" else "domaemae_supply",
                        "supplier_account_id": account_name,
                        "supplier_order_id": order["order_id"],
                        "customer_name": order.get("buyer_name", "Unknown"),
                        "total_amount": order.get("total_amount", 0),
                        "order_date": order.get("order_date", datetime.utcnow().isoformat())
                    }
                    
                    order_id = await tracking_service.create_order_tracking(tracking_data)
                    
                    if order_id:
                        logger.info(f"주문 추적 생성 성공: {order_id}")
                        
                        # 주문 상태 업데이트 시뮬레이션
                        await tracking_service.update_order_status(
                            order_id,
                            "confirmed",
                            "주문 확인됨"
                        )
                        
                        await tracking_service.update_order_status(
                            order_id,
                            "preparing",
                            "배송 준비중"
                        )
                        
                    else:
                        logger.error(f"주문 추적 생성 실패: {order['order_id']}")
                        
                except Exception as e:
                    logger.error(f"주문 추적 처리 실패: {e}")
                    continue
        
        # 4. 주문 상태 동기화 테스트
        logger.info("=== 주문 상태 동기화 테스트 ===")
        
        # 도매꾹 주문 상태 동기화
        dome_sync_result = await tracking_service.sync_order_status_from_supplier(
            "domaemae_dome", account_name
        )
        
        if dome_sync_result["success"]:
            logger.info(f"도매꾹 주문 상태 동기화 성공: {dome_sync_result['synced_count']}개")
        else:
            logger.error(f"도매꾹 주문 상태 동기화 실패: {dome_sync_result.get('error', 'Unknown error')}")
        
        # 도매매 주문 상태 동기화
        supply_sync_result = await tracking_service.sync_order_status_from_supplier(
            "domaemae_supply", account_name
        )
        
        if supply_sync_result["success"]:
            logger.info(f"도매매 주문 상태 동기화 성공: {supply_sync_result['synced_count']}개")
        else:
            logger.error(f"도매매 주문 상태 동기화 실패: {supply_sync_result.get('error', 'Unknown error')}")
        
        # 5. 주문 통계 조회 테스트
        logger.info("=== 주문 통계 조회 테스트 ===")
        
        # 전체 주문 통계
        all_stats = await tracking_service.get_order_statistics(days=30)
        logger.info(f"전체 주문 통계 (최근 30일):")
        logger.info(f"  - 총 주문 수: {all_stats['total_orders']}개")
        logger.info(f"  - 상태별 분포: {all_stats['status_distribution']}")
        
        # 도매꾹 주문 통계
        dome_stats = await tracking_service.get_order_statistics(
            supplier_id="domaemae_dome", days=30
        )
        logger.info(f"도매꾹 주문 통계: {dome_stats['total_orders']}개")
        
        # 도매매 주문 통계
        supply_stats = await tracking_service.get_order_statistics(
            supplier_id="domaemae_supply", days=30
        )
        logger.info(f"도매매 주문 통계: {supply_stats['total_orders']}개")
        
        # 6. 활성 주문 목록 조회 테스트
        logger.info("=== 활성 주문 목록 조회 테스트 ===")
        
        active_orders = await tracking_service.get_active_orders()
        logger.info(f"전체 활성 주문: {len(active_orders)}개")
        
        for order in active_orders:
            logger.info(f"  - 주문 ID: {order['order_id']}, 상태: {order['current_status']}")
        
        # 7. 배치 주문 수집 테스트
        logger.info("=== 배치 주문 수집 테스트 ===")
        
        # 도매꾹 배치 주문 수집
        dome_batch_orders = await collector.collect_orders_batch(
            account_name=account_name,
            market="dome",
            batch_size=100,
            max_pages=3
        )
        
        logger.info(f"도매꾹 배치 주문 수집 완료: {len(dome_batch_orders)}개")
        
        # 도매매 배치 주문 수집
        supply_batch_orders = await collector.collect_orders_batch(
            account_name=account_name,
            market="supply",
            batch_size=100,
            max_pages=3
        )
        
        logger.info(f"도매매 배치 주문 수집 완료: {len(supply_batch_orders)}개")
        
        # 배치 주문 데이터 저장
        all_batch_orders = dome_batch_orders + supply_batch_orders
        if all_batch_orders:
            batch_saved_count = await storage.save_orders(all_batch_orders)
            logger.info(f"배치 주문 데이터 저장 완료: {batch_saved_count}개")
        
        logger.info("=== 도매꾹 주문 데이터 수집 테스트 완료 ===")
        
    except Exception as e:
        logger.error(f"도매꾹 주문 데이터 수집 테스트 실패: {e}")
        raise


async def test_domaemae_order_api_integration():
    """도매꾹 주문 API 통합 테스트"""
    try:
        logger.info("=== 도매꾹 주문 API 통합 테스트 시작 ===")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 도매꾹 데이터 수집기 초기화
        collector = DomaemaeDataCollector(db_service)
        
        account_name = "test_account"
        
        # 1. API 파라미터 테스트
        logger.info("=== API 파라미터 테스트 ===")
        
        test_params = [
            {"market": "dome", "page": 1, "size": 10},
            {"market": "supply", "page": 1, "size": 10},
            {"market": "dome", "page": 2, "size": 20},
            {"market": "supply", "page": 2, "size": 20}
        ]
        
        for params in test_params:
            logger.info(f"API 파라미터 테스트: {params}")
            
            orders = await collector.collect_orders(
                account_name=account_name,
                **params
            )
            
            logger.info(f"  결과: {len(orders)}개 주문 수집")
            
            # API 호출 간격 조절
            await asyncio.sleep(1)
        
        # 2. 날짜 필터 테스트
        logger.info("=== 날짜 필터 테스트 ===")
        
        # 최근 7일 주문 조회
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        orders_with_date = await collector.collect_orders(
            account_name=account_name,
            market="dome",
            start_date=start_date,
            end_date=end_date,
            page=1,
            size=50
        )
        
        logger.info(f"날짜 필터 주문 조회 완료: {len(orders_with_date)}개")
        
        # 3. 주문 상태 필터 테스트
        logger.info("=== 주문 상태 필터 테스트 ===")
        
        order_statuses = ["주문대기", "주문확인", "배송준비중", "배송중", "배송완료"]
        
        for status in order_statuses:
            orders_with_status = await collector.collect_orders(
                account_name=account_name,
                market="dome",
                order_status=status,
                page=1,
                size=20
            )
            
            logger.info(f"  {status} 상태 주문: {len(orders_with_status)}개")
            
            # API 호출 간격 조절
            await asyncio.sleep(0.5)
        
        # 4. 판매자별 주문 조회 테스트
        logger.info("=== 판매자별 주문 조회 테스트 ===")
        
        # 특정 판매자 ID로 주문 조회 (테스트용)
        test_seller_ids = ["test_seller_1", "test_seller_2"]
        
        for seller_id in test_seller_ids:
            orders_by_seller = await collector.collect_orders(
                account_name=account_name,
                market="dome",
                seller_id=seller_id,
                page=1,
                size=20
            )
            
            logger.info(f"  {seller_id} 판매자 주문: {len(orders_by_seller)}개")
            
            # API 호출 간격 조절
            await asyncio.sleep(0.5)
        
        logger.info("=== 도매꾹 주문 API 통합 테스트 완료 ===")
        
    except Exception as e:
        logger.error(f"도매꾹 주문 API 통합 테스트 실패: {e}")
        raise


async def main():
    """메인 함수"""
    try:
        # 기본 주문 데이터 수집 테스트
        await test_domaemae_order_collection()
        
        # API 통합 테스트
        await test_domaemae_order_api_integration()
        
        logger.info("모든 테스트 완료!")
        
    except Exception as e:
        logger.error(f"테스트 실행 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
