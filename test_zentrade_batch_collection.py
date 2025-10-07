#!/usr/bin/env python3
"""
젠트레이드 배치 수집 테스트 스크립트
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


async def test_zentrade_batch_collection():
    """젠트레이드 배치 수집 테스트"""
    try:
        logger.info("젠트레이드 배치 수집 테스트 시작")
        
        # 서비스 초기화
        db_service = DatabaseService()
        account_manager = ZentradeAccountManager(db_service)
        collector = ZentradeDataCollector(db_service)
        storage = ZentradeDataStorage(db_service)
        
        # 테스트 계정명
        account_name = "test_account"
        
        # 계정 확인
        account = await account_manager.get_zentrade_account(account_name)
        if not account:
            logger.error(f"젠트레이드 계정을 찾을 수 없습니다: {account_name}")
            return
        
        logger.info(f"테스트 계정 확인: {account['account_name']}")
        
        # 배치 크기 설정
        batch_size = 1000
        
        # 전체 시작 시간
        total_start_time = time.time()
        
        # 1. 상품 데이터 배치 수집
        logger.info(f"1. 젠트레이드 상품 데이터 배치 수집 (배치 크기: {batch_size})")
        
        products_saved = await collector.collect_products_batch(
            account_name=account_name,
            batch_size=batch_size,
            storage_service=storage
        )
        
        products_time = time.time() - total_start_time
        
        logger.info(f"상품 데이터 배치 수집 완료: {products_saved}개 저장됨 (소요시간: {products_time:.2f}초)")
        
        # 2. 성능 메트릭 계산
        logger.info("2. 성능 메트릭")
        
        if products_saved > 0 and products_time > 0:
            products_per_second = products_saved / products_time
            logger.info(f"  - 상품 처리 속도: {products_per_second:.2f}개/초")
        
        # 3. 데이터베이스 확인
        logger.info("3. 데이터베이스 저장 확인")
        
        # 저장된 상품 데이터 확인
        raw_products = await db_service.select_data(
            "raw_product_data",
            {"supplier_id": await storage._get_supplier_id("zentrade")}
        )
        
        logger.info(f"  - DB에 저장된 젠트레이드 상품 데이터: {len(raw_products)}개")
        
        # 4. 샘플 데이터 출력
        if raw_products:
            sample_product = raw_products[0]
            logger.info("4. 샘플 상품 데이터")
            logger.info(f"  - 상품 ID: {sample_product.get('supplier_product_id', 'N/A')}")
            logger.info(f"  - 수집 시간: {sample_product.get('created_at', 'N/A')}")
            logger.info(f"  - 처리 상태: {'처리됨' if sample_product.get('is_processed') else '미처리'}")
        
        # 전체 실행 시간
        total_time = time.time() - total_start_time
        logger.info(f"전체 실행 시간: {total_time:.2f}초")
        
        logger.info("✅ 젠트레이드 배치 수집 테스트 완료")
        
    except Exception as e:
        logger.error(f"❌ 젠트레이드 배치 수집 테스트 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_zentrade_batch_collection())
