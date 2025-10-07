#!/usr/bin/env python3
"""
도매꾹 배치 수집 테스트 스크립트
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
from src.services.domaemae_account_manager import DomaemaeAccountManager
from src.services.domaemae_data_collector import DomaemaeDataCollector, DomaemaeDataStorage


async def test_domaemae_batch_collection():
    """도매꾹 배치 수집 테스트"""
    try:
        logger.info("도매꾹 배치 수집 테스트 시작")
        
        # 서비스 초기화
        db_service = DatabaseService()
        account_manager = DomaemaeAccountManager(db_service)
        collector = DomaemaeDataCollector(db_service)
        storage = DomaemaeDataStorage(db_service)
        
        # 테스트 계정명
        account_name = "test_account"
        
        # 계정 확인
        account = await account_manager.get_domaemae_account(account_name)
        if not account:
            logger.error(f"도매꾹 계정을 찾을 수 없습니다: {account_name}")
            return
        
        logger.info(f"테스트 계정 확인: {account['account_name']}")
        
        # 전체 시작 시간
        total_start_time = time.time()
        
        # 1. 도매꾹 상품 데이터 배치 수집
        logger.info("1. 도매꾹 상품 데이터 배치 수집")
        
        dome_products = await collector.collect_products_batch(
            account_name=account_name,
            batch_size=200,
            max_pages=5,
            market="dome"  # 도매꾹
        )
        
        dome_time = time.time() - total_start_time
        
        logger.info(f"도매꾹 상품 데이터 수집 완료: {len(dome_products)}개 (소요시간: {dome_time:.2f}초)")
        
        # 2. 도매매 상품 데이터 배치 수집
        logger.info("2. 도매매 상품 데이터 배치 수집")
        
        supply_start_time = time.time()
        supply_products = await collector.collect_products_batch(
            account_name=account_name,
            batch_size=200,
            max_pages=5,
            market="supply"  # 도매매
        )
        
        supply_time = time.time() - supply_start_time
        
        logger.info(f"도매매 상품 데이터 수집 완료: {len(supply_products)}개 (소요시간: {supply_time:.2f}초)")
        
        # 3. 데이터 저장
        logger.info("3. 데이터베이스 저장")
        
        dome_saved = await storage.save_products(dome_products)
        supply_saved = await storage.save_products(supply_products)
        
        logger.info(f"도매꾹 데이터 저장: {dome_saved}개")
        logger.info(f"도매매 데이터 저장: {supply_saved}개")
        
        # 4. 성능 메트릭 계산
        logger.info("4. 성능 메트릭")
        
        if dome_products and dome_time > 0:
            dome_per_second = len(dome_products) / dome_time
            logger.info(f"  - 도매꾹 처리 속도: {dome_per_second:.2f}개/초")
        
        if supply_products and supply_time > 0:
            supply_per_second = len(supply_products) / supply_time
            logger.info(f"  - 도매매 처리 속도: {supply_per_second:.2f}개/초")
        
        # 5. 데이터베이스 확인
        logger.info("5. 데이터베이스 저장 확인")
        
        # 저장된 상품 데이터 확인
        raw_products = await db_service.select_data(
            "raw_product_data",
            {"supplier_id": await storage._get_supplier_id("domaemae")}
        )
        
        logger.info(f"  - DB에 저장된 도매꾹 상품 데이터: {len(raw_products)}개")
        
        # 6. 샘플 데이터 출력
        if raw_products:
            sample_product = raw_products[0]
            logger.info("6. 샘플 상품 데이터")
            logger.info(f"  - 상품 ID: {sample_product.get('supplier_product_id', 'N/A')}")
            logger.info(f"  - 수집 시간: {sample_product.get('created_at', 'N/A')}")
            logger.info(f"  - 처리 상태: {'처리됨' if sample_product.get('is_processed') else '미처리'}")
        
        # 전체 실행 시간
        total_time = time.time() - total_start_time
        logger.info(f"전체 실행 시간: {total_time:.2f}초")
        
        # 7. 요약
        logger.info("7. 수집 요약")
        logger.info(f"  - 도매꾹 상품: {len(dome_products)}개 수집, {dome_saved}개 저장")
        logger.info(f"  - 도매매 상품: {len(supply_products)}개 수집, {supply_saved}개 저장")
        logger.info(f"  - 총 상품: {len(dome_products) + len(supply_products)}개 수집")
        logger.info(f"  - 총 저장: {dome_saved + supply_saved}개 저장")
        
        logger.info("✅ 도매꾹 배치 수집 테스트 완료")
        
    except Exception as e:
        logger.error(f"❌ 도매꾹 배치 수집 테스트 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_domaemae_batch_collection())
