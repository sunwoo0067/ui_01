#!/usr/bin/env python3
"""
젠트레이드 통합 테스트 스크립트
"""

import asyncio
import sys
import os
import time
from datetime import datetime, timedelta
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.services.zentrade_account_manager import ZentradeAccountManager
from src.services.zentrade_data_collector import ZentradeDataCollector, ZentradeDataStorage


async def test_zentrade_integration():
    """젠트레이드 통합 테스트"""
    try:
        logger.info("젠트레이드 통합 테스트 시작")
        
        # 서비스 초기화
        db_service = DatabaseService()
        account_manager = ZentradeAccountManager(db_service)
        collector = ZentradeDataCollector(db_service)
        storage = ZentradeDataStorage(db_service)
        
        # 테스트 계정명
        account_name = "test_account"
        
        # 1. 계정 생성 테스트
        logger.info("1. 젠트레이드 계정 생성 테스트")
        account_id = await account_manager.create_zentrade_account(
            account_name=account_name,
            id="b00679540",
            m_skey="5284c44b0fcf0f877e6791c5884d6ea9",
            description="젠트레이드 테스트 계정"
        )
        
        if account_id:
            logger.info(f"✅ 계정 생성 성공: {account_id}")
        else:
            logger.warning("⚠️ 계정 생성 실패 (이미 존재할 수 있음)")
        
        # 2. 계정 조회 테스트
        logger.info("2. 젠트레이드 계정 조회 테스트")
        account = await account_manager.get_zentrade_account(account_name)
        
        if account:
            logger.info(f"✅ 계정 조회 성공: {account['account_name']}")
        else:
            logger.error("❌ 계정 조회 실패")
            return
        
        # 3. 상품 데이터 수집 테스트
        logger.info("3. 젠트레이드 상품 데이터 수집 테스트")
        start_time = time.time()
        
        products = await collector.collect_products(account_name)
        
        collection_time = time.time() - start_time
        
        if products:
            logger.info(f"✅ 상품 데이터 수집 성공: {len(products)}개 (소요시간: {collection_time:.2f}초)")
            
            # 첫 번째 상품 정보 출력
            if products:
                first_product = products[0]
                logger.info(f"  - 첫 번째 상품: {first_product.get('title', 'N/A')}")
                logger.info(f"  - 가격: {first_product.get('price', 0)}원")
                logger.info(f"  - 카테고리: {first_product.get('category', 'N/A')}")
        else:
            logger.error("❌ 상품 데이터 수집 실패")
            return
        
        # 4. 상품 데이터 저장 테스트
        logger.info("4. 젠트레이드 상품 데이터 저장 테스트")
        saved_count = await storage.save_products(products)
        
        if saved_count > 0:
            logger.info(f"✅ 상품 데이터 저장 성공: {saved_count}개")
        else:
            logger.error("❌ 상품 데이터 저장 실패")
        
        # 5. 배치 수집 테스트
        logger.info("5. 젠트레이드 배치 수집 테스트")
        batch_start_time = time.time()
        
        batch_saved = await collector.collect_products_batch(
            account_name=account_name,
            batch_size=100,
            storage_service=storage
        )
        
        batch_time = time.time() - batch_start_time
        
        if batch_saved > 0:
            logger.info(f"✅ 배치 수집 성공: {batch_saved}개 (소요시간: {batch_time:.2f}초)")
        else:
            logger.warning("⚠️ 배치 수집 실패 또는 데이터 없음")
        
        # 6. 주문 데이터 수집 테스트 (샘플 주문번호로 테스트)
        logger.info("6. 젠트레이드 주문 데이터 수집 테스트")
        
        # 실제 주문번호가 없으므로 테스트용으로 빈 결과 확인
        orders = await collector.collect_orders(
            account_name=account_name,
            ordno="1234567890123"  # 테스트용 주문번호
        )
        
        if orders:
            logger.info(f"✅ 주문 데이터 수집 성공: {len(orders)}개")
        else:
            logger.info("ℹ️ 주문 데이터 없음 (정상 - 테스트 주문번호)")
        
        # 7. 성능 메트릭 계산
        logger.info("7. 성능 메트릭")
        if products and collection_time > 0:
            products_per_second = len(products) / collection_time
            logger.info(f"  - 상품 수집 속도: {products_per_second:.2f}개/초")
        
        if batch_saved > 0 and batch_time > 0:
            batch_per_second = batch_saved / batch_time
            logger.info(f"  - 배치 처리 속도: {batch_per_second:.2f}개/초")
        
        logger.info("✅ 젠트레이드 통합 테스트 완료")
        
    except Exception as e:
        logger.error(f"❌ 젠트레이드 통합 테스트 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_zentrade_integration())
