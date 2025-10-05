#!/usr/bin/env python3
"""
OwnerClan 대량 데이터 수집 스크립트
"""

import asyncio
from datetime import datetime
from loguru import logger

from src.services.supplier_account_manager import OwnerClanAccountManager
from src.services.ownerclan_data_collector import ownerclan_data_collector
from src.services.ownerclan_data_storage import ownerclan_data_storage

async def collect_large_dataset():
    """대량 데이터 수집"""
    logger.info("=== OwnerClan 대량 데이터 수집 시작 ===")
    
    account_name = "test_account"
    username = "b00679540"
    password = "ehdgod1101*"
    
    account_manager = OwnerClanAccountManager()
    
    try:
        # 1. 계정 확인/생성
        logger.info("1. 계정 확인 중...")
        try:
            account_id = await account_manager.create_ownerclan_account(
                account_name, username, password
            )
            logger.info(f"계정 생성 완료: {account_id}")
        except Exception as e:
            if "duplicate key" in str(e):
                # 기존 계정 사용
                account = await account_manager.get_supplier_account('ownerclan', account_name)
                if account:
                    account_id = account['id']
                    logger.info(f"기존 계정 사용: {account_id}")
                else:
                    raise e
            else:
                raise e
        
        # 2. 대량 상품 데이터 수집 (제한 없이)
        logger.info("2. 대량 상품 데이터 수집 중...")
        products = await ownerclan_data_collector.collect_products(
            account_name=account_name,
            limit=None,  # 제한 없음
            min_price=1000,
            max_price=200000
        )
        logger.info(f"상품 데이터 수집 완료: {len(products)}개")
        
        # 3. 상품 데이터 저장
        logger.info("3. 상품 데이터 저장 중...")
        saved_count = await ownerclan_data_storage.save_products(products)
        logger.info(f"상품 데이터 저장 완료: {saved_count}개")
        
        # 4. 카테고리 데이터 수집
        logger.info("4. 카테고리 데이터 수집 중...")
        categories = await ownerclan_data_collector.collect_categories(account_name)
        logger.info(f"카테고리 데이터 수집 완료: {len(categories)}개")
        
        # 5. 최근 주문 데이터 수집
        logger.info("5. 최근 주문 데이터 수집 중...")
        orders = await ownerclan_data_collector.collect_orders(
            account_name=account_name,
            limit=50,  # 최근 50개 주문
            start_date=datetime.now().replace(day=1),  # 이번 달부터
            end_date=datetime.now()
        )
        logger.info(f"주문 데이터 수집 완료: {len(orders)}개")
        
        # 6. 수집 결과 요약
        logger.info("=== 수집 결과 요약 ===")
        logger.info(f"✅ 상품 데이터: {len(products)}개 수집, {saved_count}개 저장")
        logger.info(f"✅ 카테고리 데이터: {len(categories)}개 수집")
        logger.info(f"✅ 주문 데이터: {len(orders)}개 수집")
        
        # 7. 데이터 품질 확인
        if products:
            prices = [p.get('price', 0) for p in products if p.get('price')]
            if prices:
                logger.info(f"📊 가격 통계: 최저 {min(prices):,}원, 최고 {max(prices):,}원, 평균 {sum(prices)/len(prices):,.0f}원")
            
            # 상품명 길이 통계
            name_lengths = [len(p.get('name', '')) for p in products if p.get('name')]
            if name_lengths:
                logger.info(f"📝 상품명 길이: 평균 {sum(name_lengths)/len(name_lengths):.1f}자")
        
        logger.info("=== OwnerClan 대량 데이터 수집 완료 ===")
        
    except Exception as e:
        logger.error(f"데이터 수집 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(collect_large_dataset())
