#!/usr/bin/env python3
"""
도매꾹 주문 데이터 수집 테스트
"""

import asyncio
import sys
import os
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.services.domaemae_data_collector import DomaemaeDataCollector, DomaemaeDataStorage


async def test_domaemae_orders():
    """도매꾹 주문 데이터 수집 테스트"""
    try:
        logger.info("도매꾹 주문 데이터 수집 테스트 시작")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 도매꾹 데이터 수집기 및 저장 서비스 초기화
        collector = DomaemaeDataCollector(db_service)
        storage = DomaemaeDataStorage(db_service)
        
        account_name = "test_account"
        
        # 1. 도매꾹 주문 수집 테스트
        logger.info("=== 도매꾹 주문 수집 테스트 ===")
        
        dome_orders = await collector.collect_orders(
            account_name=account_name,
            market="dome",
            page=1,
            size=50
        )
        
        logger.info(f"도매꾹 주문 수집 결과: {len(dome_orders)}개")
        
        if dome_orders:
            sample_order = dome_orders[0]
            logger.info(f"도매꾹 샘플 주문:")
            logger.info(f"  - 주문번호: {sample_order.get('order_id', 'N/A')}")
            logger.info(f"  - 주문일: {sample_order.get('order_date', 'N/A')}")
            logger.info(f"  - 주문상태: {sample_order.get('order_status', 'N/A')}")
            logger.info(f"  - 총금액: {sample_order.get('total_amount', 0):,}원")
            logger.info(f"  - 구매자: {sample_order.get('buyer_name', 'N/A')}")
            logger.info(f"  - 판매자: {sample_order.get('seller_nick', 'N/A')}")
        
        # 2. 도매매 주문 수집 테스트
        logger.info("=== 도매매 주문 수집 테스트 ===")
        
        supply_orders = await collector.collect_orders(
            account_name=account_name,
            market="supply",
            page=1,
            size=50
        )
        
        logger.info(f"도매매 주문 수집 결과: {len(supply_orders)}개")
        
        if supply_orders:
            sample_order = supply_orders[0]
            logger.info(f"도매매 샘플 주문:")
            logger.info(f"  - 주문번호: {sample_order.get('order_id', 'N/A')}")
            logger.info(f"  - 주문일: {sample_order.get('order_date', 'N/A')}")
            logger.info(f"  - 주문상태: {sample_order.get('order_status', 'N/A')}")
            logger.info(f"  - 총금액: {sample_order.get('total_amount', 0):,}원")
            logger.info(f"  - 구매자: {sample_order.get('buyer_name', 'N/A')}")
            logger.info(f"  - 판매자: {sample_order.get('seller_nick', 'N/A')}")
        
        # 3. 주문 배치 수집 테스트
        logger.info("=== 주문 배치 수집 테스트 ===")
        
        # 도매꾹 주문 배치 수집
        dome_batch_orders = await collector.collect_orders_batch(
            account_name=account_name,
            market="dome",
            batch_size=50,
            max_pages=2
        )
        
        logger.info(f"도매꾹 주문 배치 수집 결과: {len(dome_batch_orders)}개")
        
        # 도매매 주문 배치 수집
        supply_batch_orders = await collector.collect_orders_batch(
            account_name=account_name,
            market="supply",
            batch_size=50,
            max_pages=2
        )
        
        logger.info(f"도매매 주문 배치 수집 결과: {len(supply_batch_orders)}개")
        
        # 4. 주문 데이터 저장 테스트
        logger.info("=== 주문 데이터 저장 테스트 ===")
        
        all_orders = dome_batch_orders + supply_batch_orders
        
        if all_orders:
            saved_count = await storage.save_orders(all_orders)
            logger.info(f"주문 데이터 저장 완료: {saved_count}개")
            
            # 저장 성공률 계산
            success_rate = (saved_count / len(all_orders)) * 100
            logger.info(f"저장 성공률: {success_rate:.1f}%")
        else:
            logger.info("저장할 주문 데이터가 없습니다")
        
        # 5. 시장별 주문 통계
        logger.info("=== 시장별 주문 통계 ===")
        
        dome_total_amount = sum(order.get("total_amount", 0) for order in dome_batch_orders)
        supply_total_amount = sum(order.get("total_amount", 0) for order in supply_batch_orders)
        
        logger.info(f"도매꾹 주문 통계:")
        logger.info(f"  - 주문 수: {len(dome_batch_orders)}개")
        logger.info(f"  - 총 금액: {dome_total_amount:,}원")
        logger.info(f"  - 평균 주문 금액: {dome_total_amount / len(dome_batch_orders):,.0f}원" if dome_batch_orders else "  - 평균 주문 금액: 0원")
        
        logger.info(f"도매매 주문 통계:")
        logger.info(f"  - 주문 수: {len(supply_batch_orders)}개")
        logger.info(f"  - 총 금액: {supply_total_amount:,}원")
        logger.info(f"  - 평균 주문 금액: {supply_total_amount / len(supply_batch_orders):,.0f}원" if supply_batch_orders else "  - 평균 주문 금액: 0원")
        
        # 6. 주문 상태별 분석
        logger.info("=== 주문 상태별 분석 ===")
        
        all_orders_for_analysis = dome_batch_orders + supply_batch_orders
        status_counts = {}
        
        for order in all_orders_for_analysis:
            status = order.get("order_status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            percentage = (count / len(all_orders_for_analysis)) * 100 if all_orders_for_analysis else 0
            logger.info(f"  - {status}: {count}개 ({percentage:.1f}%)")
        
        logger.info("도매꾹 주문 데이터 수집 테스트 완료")
        
    except Exception as e:
        logger.error(f"테스트 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_domaemae_orders())
