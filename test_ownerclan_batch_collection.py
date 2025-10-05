#!/usr/bin/env python3
"""
OwnerClan 배치 데이터 수집 테스트
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.ownerclan_data_collector import OwnerClanDataCollector
from src.services.ownerclan_data_storage import OwnerClanDataStorage
from src.services.supplier_account_manager import OwnerClanAccountManager
from src.utils.error_handler import ErrorHandler

async def test_batch_product_collection():
    """배치 상품 수집 테스트"""
    try:
        logger.info("=== OwnerClan 배치 상품 수집 테스트 시작 ===")
        
        # 서비스 초기화
        error_handler = ErrorHandler()
        account_manager = OwnerClanAccountManager()
        collector = OwnerClanDataCollector()
        storage = OwnerClanDataStorage()
        
        # 테스트 계정 확인
        account_name = "test_account"
        account = await account_manager.get_supplier_account("ownerclan", account_name)
        if not account:
            logger.error(f"테스트 계정이 없습니다: {account_name}")
            return
        
        logger.info(f"테스트 계정 사용: {account_name}")
        
        # 배치 크기 설정
        batch_size = 1000
        
        # 배치 상품 수집 실행
        logger.info(f"배치 크기: {batch_size}개로 상품 수집 시작")
        
        total_saved = await collector.collect_products_batch(
            account_name=account_name,
            batch_size=batch_size,
            storage_service=storage
        )
        
        logger.info(f"배치 상품 수집 완료: 총 {total_saved}개 상품 저장됨")
        
        return total_saved
        
    except Exception as e:
        logger.error(f"배치 상품 수집 테스트 실패: {e}")
        error_handler.log_error(e, "배치 상품 수집 테스트 실패")
        return 0

async def test_batch_order_collection():
    """배치 주문 수집 테스트"""
    try:
        logger.info("\n=== OwnerClan 배치 주문 수집 테스트 시작 ===")
        
        # 서비스 초기화
        error_handler = ErrorHandler()
        account_manager = OwnerClanAccountManager()
        collector = OwnerClanDataCollector()
        storage = OwnerClanDataStorage()
        
        # 테스트 계정 확인
        account_name = "test_account"
        account = await account_manager.get_supplier_account("ownerclan", account_name)
        if not account:
            logger.error(f"테스트 계정이 없습니다: {account_name}")
            return
        
        logger.info(f"테스트 계정 사용: {account_name}")
        
        # 배치 크기 설정
        batch_size = 1000
        
        # 다양한 날짜 범위로 테스트
        test_cases = [
            {
                "name": "최근 7일",
                "start_date": datetime.now() - timedelta(days=7),
                "end_date": datetime.now()
            },
            {
                "name": "최근 30일",
                "start_date": datetime.now() - timedelta(days=30),
                "end_date": datetime.now()
            }
        ]
        
        total_orders_saved = 0
        
        for test_case in test_cases:
            logger.info(f"\n--- {test_case['name']} 주문 배치 수집 ---")
            
            try:
                # 배치 주문 수집 실행
                orders_saved = await collector.collect_orders_batch(
                    account_name=account_name,
                    batch_size=batch_size,
                    start_date=test_case['start_date'],
                    end_date=test_case['end_date'],
                    storage_service=storage
                )
                
                total_orders_saved += orders_saved
                logger.info(f"{test_case['name']} 주문 배치 수집 완료: {orders_saved}개 저장됨")
                
            except Exception as e:
                logger.error(f"{test_case['name']} 주문 배치 수집 실패: {e}")
                error_handler.log_error(e, f"주문 배치 수집 실패: {test_case['name']}")
        
        logger.info(f"전체 배치 주문 수집 완료: 총 {total_orders_saved}개 주문 저장됨")
        
        return total_orders_saved
        
    except Exception as e:
        logger.error(f"배치 주문 수집 테스트 실패: {e}")
        error_handler.log_error(e, "배치 주문 수집 테스트 실패")
        return 0

async def test_comprehensive_batch_collection():
    """종합 배치 수집 테스트"""
    try:
        logger.info("\n=== OwnerClan 종합 배치 수집 테스트 시작 ===")
        
        # 서비스 초기화
        error_handler = ErrorHandler()
        account_manager = OwnerClanAccountManager()
        collector = OwnerClanDataCollector()
        storage = OwnerClanDataStorage()
        
        # 테스트 계정 확인
        account_name = "test_account"
        account = await account_manager.get_supplier_account("ownerclan", account_name)
        if not account:
            logger.error(f"테스트 계정이 없습니다: {account_name}")
            return
        
        logger.info(f"테스트 계정 사용: {account_name}")
        
        # 배치 크기 설정
        batch_size = 1000
        
        # 1. 상품 데이터 배치 수집
        logger.info("1단계: 상품 데이터 배치 수집")
        products_saved = await collector.collect_products_batch(
            account_name=account_name,
            batch_size=batch_size,
            storage_service=storage
        )
        
        # 2. 주문 데이터 배치 수집 (최근 30일)
        logger.info("2단계: 주문 데이터 배치 수집 (최근 30일)")
        orders_saved = await collector.collect_orders_batch(
            account_name=account_name,
            batch_size=batch_size,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            storage_service=storage
        )
        
        # 결과 요약
        logger.info(f"\n=== 배치 수집 결과 요약 ===")
        logger.info(f"상품 데이터: {products_saved}개 저장됨")
        logger.info(f"주문 데이터: {orders_saved}개 저장됨")
        logger.info(f"총 저장된 데이터: {products_saved + orders_saved}개")
        
        return products_saved + orders_saved
        
    except Exception as e:
        logger.error(f"종합 배치 수집 테스트 실패: {e}")
        error_handler.log_error(e, "종합 배치 수집 테스트 실패")
        return 0

async def test_batch_performance():
    """배치 성능 테스트"""
    try:
        logger.info("\n=== 배치 성능 테스트 시작 ===")
        
        # 서비스 초기화
        error_handler = ErrorHandler()
        collector = OwnerClanDataCollector()
        storage = OwnerClanDataStorage()
        
        account_name = "test_account"
        
        # 다양한 배치 크기로 성능 테스트
        batch_sizes = [100, 500, 1000, 2000]
        
        for batch_size in batch_sizes:
            logger.info(f"\n--- 배치 크기 {batch_size}개 테스트 ---")
            
            start_time = datetime.now()
            
            try:
                # 상품 수집 성능 테스트
                products_saved = await collector.collect_products_batch(
                    account_name=account_name,
                    batch_size=batch_size,
                    storage_service=storage
                )
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(f"배치 크기 {batch_size}: {products_saved}개 저장, {duration:.2f}초 소요")
                
                if products_saved > 0:
                    throughput = products_saved / duration
                    logger.info(f"처리량: {throughput:.2f}개/초")
                
            except Exception as e:
                logger.error(f"배치 크기 {batch_size} 테스트 실패: {e}")
                error_handler.log_error(e, f"배치 성능 테스트 실패: {batch_size}")
        
        logger.info("배치 성능 테스트 완료")
        
    except Exception as e:
        logger.error(f"배치 성능 테스트 실패: {e}")
        error_handler.log_error(e, "배치 성능 테스트 실패")

if __name__ == "__main__":
    # 로거 설정
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # 테스트 실행
    async def main():
        # 1. 배치 상품 수집 테스트
        await test_batch_product_collection()
        
        # 2. 배치 주문 수집 테스트
        await test_batch_order_collection()
        
        # 3. 종합 배치 수집 테스트
        await test_comprehensive_batch_collection()
        
        # 4. 배치 성능 테스트
        await test_batch_performance()
        
        logger.info("\n=== 모든 배치 테스트 완료 ===")
    
    asyncio.run(main())
