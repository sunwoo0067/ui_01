#!/usr/bin/env python3
"""
도매꾹 통합 테스트 스크립트
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


async def test_domaemae_integration():
    """도매꾹 통합 테스트"""
    try:
        logger.info("도매꾹 통합 테스트 시작")
        
        # 서비스 초기화
        db_service = DatabaseService()
        account_manager = DomaemaeAccountManager(db_service)
        collector = DomaemaeDataCollector(db_service)
        storage = DomaemaeDataStorage(db_service)
        
        # 테스트 계정명
        account_name = "test_account"
        
        # 1. 계정 생성 테스트
        logger.info("1. 도매꾹 계정 생성 테스트")
        account_id = await account_manager.create_domaemae_account(
            account_name=account_name,
            api_key="96ef1110327e9ce5be389e5eaa612f4a",
            version="4.1",
            description="도매꾹 테스트 계정"
        )
        
        if account_id:
            logger.info(f"✅ 계정 생성 성공: {account_id}")
        else:
            logger.warning("⚠️ 계정 생성 실패 (이미 존재할 수 있음)")
        
        # 2. 계정 조회 테스트
        logger.info("2. 도매꾹 계정 조회 테스트")
        account = await account_manager.get_domaemae_account(account_name)
        
        if account:
            logger.info(f"✅ 계정 조회 성공: {account['account_name']}")
        else:
            logger.error("❌ 계정 조회 실패")
            return
        
        # 3. 상품 데이터 수집 테스트
        logger.info("3. 도매꾹 상품 데이터 수집 테스트")
        start_time = time.time()
        
        products = await collector.collect_products(
            account_name=account_name,
            market="dome",  # 도매꾹
            size=20,  # 테스트용으로 적은 수량
            page=1,
            sort="rd"  # 랭킹순
        )
        
        collection_time = time.time() - start_time
        
        if products:
            logger.info(f"✅ 상품 데이터 수집 성공: {len(products)}개 (소요시간: {collection_time:.2f}초)")
            
            # 첫 번째 상품 정보 출력
            if products:
                first_product = products[0]
                logger.info(f"  - 첫 번째 상품: {first_product.get('title', 'N/A')}")
                logger.info(f"  - 가격: {first_product.get('price', 0)}원")
                logger.info(f"  - 판매자: {first_product.get('seller_id', 'N/A')}")
                logger.info(f"  - 상품번호: {first_product.get('supplier_key', 'N/A')}")
        else:
            logger.error("❌ 상품 데이터 수집 실패")
            return
        
        # 4. 상품 데이터 저장 테스트
        logger.info("4. 도매꾹 상품 데이터 저장 테스트")
        saved_count = await storage.save_products(products)
        
        if saved_count > 0:
            logger.info(f"✅ 상품 데이터 저장 성공: {saved_count}개")
        else:
            logger.error("❌ 상품 데이터 저장 실패")
        
        # 5. 배치 수집 테스트
        logger.info("5. 도매꾹 배치 수집 테스트")
        batch_start_time = time.time()
        
        batch_products = await collector.collect_products_batch(
            account_name=account_name,
            batch_size=20,
            max_pages=3,
            market="dome"
        )
        
        batch_time = time.time() - batch_start_time
        
        if batch_products:
            logger.info(f"✅ 배치 수집 성공: {len(batch_products)}개 (소요시간: {batch_time:.2f}초)")
            
            # 배치 데이터 저장
            batch_saved = await storage.save_products(batch_products)
            logger.info(f"✅ 배치 데이터 저장: {batch_saved}개")
        else:
            logger.warning("⚠️ 배치 수집 실패 또는 데이터 없음")
        
        # 6. 성능 메트릭 계산
        logger.info("6. 성능 메트릭")
        if products and collection_time > 0:
            products_per_second = len(products) / collection_time
            logger.info(f"  - 상품 수집 속도: {products_per_second:.2f}개/초")
        
        if batch_products and batch_time > 0:
            batch_per_second = len(batch_products) / batch_time
            logger.info(f"  - 배치 처리 속도: {batch_per_second:.2f}개/초")
        
        # 7. 도매매 시장 테스트
        logger.info("7. 도매매 시장 테스트")
        supply_products = await collector.collect_products(
            account_name=account_name,
            market="supply",  # 도매매
            size=10,
            page=1
        )
        
        if supply_products:
            logger.info(f"✅ 도매매 상품 수집 성공: {len(supply_products)}개")
        else:
            logger.warning("⚠️ 도매매 상품 수집 실패 또는 데이터 없음")
        
        logger.info("✅ 도매꾹 통합 테스트 완료")
        
    except Exception as e:
        logger.error(f"❌ 도매꾹 통합 테스트 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_domaemae_integration())
