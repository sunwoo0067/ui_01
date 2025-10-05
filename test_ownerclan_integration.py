#!/usr/bin/env python3
"""
오너클랜 통합 테스트
"""

import asyncio
from datetime import datetime, timedelta
from loguru import logger

from src.services.supplier_account_manager import supplier_account_manager
from src.services.ownerclan_data_collector import ownerclan_data_collector
from src.services.ownerclan_data_storage import ownerclan_data_storage


async def test_ownerclan_integration():
    """오너클랜 통합 테스트"""
    logger.info("=== 오너클랜 통합 테스트 시작 ===")
    
    account_name = "test_account"
    username = "b00679540"
    password = "ehdgod1101*"
    
    try:
        # 1. 계정 생성
        logger.info("1. 오너클랜 계정 생성 중...")
        account_id = await supplier_account_manager.create_ownerclan_account(
            account_name, username, password
        )
        logger.info(f"계정 생성 완료: {account_id}")
        
        # 2. 상품 데이터 수집
        logger.info("2. 상품 데이터 수집 중...")
        products = await ownerclan_data_collector.collect_products(
            account_name=account_name,
            limit=10,  # 테스트용으로 10개만 수집
            min_price=1000,
            max_price=100000
        )
        logger.info(f"상품 데이터 수집 완료: {len(products)}개")
        
        # 3. 상품 데이터 저장
        logger.info("3. 상품 데이터 저장 중...")
        saved_count = await ownerclan_data_storage.save_products(products)
        logger.info(f"상품 데이터 저장 완료: {saved_count}개")
        
        # 4. 주문 데이터 수집
        logger.info("4. 주문 데이터 수집 중...")
        orders = await ownerclan_data_collector.collect_orders(
            account_name=account_name,
            limit=5,  # 테스트용으로 5개만 수집
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        logger.info(f"주문 데이터 수집 완료: {len(orders)}개")
        
        # 5. 주문 데이터 저장
        logger.info("5. 주문 데이터 저장 중...")
        saved_orders_count = await ownerclan_data_storage.save_orders(orders)
        logger.info(f"주문 데이터 저장 완료: {saved_orders_count}개")
        
        # 6. 카테고리 데이터 수집
        logger.info("6. 카테고리 데이터 수집 중...")
        categories = await ownerclan_data_collector.collect_categories(account_name)
        logger.info(f"카테고리 데이터 수집 완료: {len(categories)}개")
        
        # 7. 카테고리 데이터 저장
        logger.info("7. 카테고리 데이터 저장 중...")
        saved_categories_count = await ownerclan_data_storage.save_categories(categories)
        logger.info(f"카테고리 데이터 저장 완료: {saved_categories_count}개")
        
        logger.info("=== 오너클랜 통합 테스트 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"오너클랜 통합 테스트 실패: {e}")
        return False


async def test_ownerclan_products_only():
    """오너클랜 상품 데이터만 테스트"""
    logger.info("\n=== 오너클랜 상품 데이터 테스트 시작 ===")
    
    account_name = "test_account"
    
    try:
        # 상품 데이터 수집
        logger.info("상품 데이터 수집 중...")
        products = await ownerclan_data_collector.collect_products(
            account_name=account_name,
            limit=5,  # 테스트용으로 5개만 수집
            min_price=1000,
            max_price=100000
        )
        logger.info(f"상품 데이터 수집 완료: {len(products)}개")
        
        if products:
            # 첫 번째 상품 정보 출력
            first_product = products[0]
            logger.info(f"첫 번째 상품: {first_product.get('name', 'N/A')}")
            logger.info(f"가격: {first_product.get('price', 'N/A')}원")
            logger.info(f"재고: {first_product.get('stock', 'N/A')}개")
        
        # 상품 데이터 저장
        logger.info("상품 데이터 저장 중...")
        saved_count = await ownerclan_data_storage.save_products(products)
        logger.info(f"상품 데이터 저장 완료: {saved_count}개")
        
        logger.info("=== 오너클랜 상품 데이터 테스트 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"오너클랜 상품 데이터 테스트 실패: {e}")
        return False


async def test_ownerclan_auth_only():
    """오너클랜 인증만 테스트"""
    logger.info("\n=== 오너클랜 인증 테스트 시작 ===")
    
    account_name = "auth_test"
    username = "b00679540"
    password = "ehdgod1101*"
    
    try:
        # 계정 생성
        account_id = await supplier_account_manager.create_ownerclan_account(
            account_name, username, password
        )
        logger.info(f"계정 생성 완료: {account_id}")
        
        # 인증 정보 조회
        credentials = await supplier_account_manager.get_ownerclan_credentials(account_name)
        logger.info(f"인증 정보 조회 완료: {credentials is not None}")
        
        # 토큰 발급 테스트
        from src.services.ownerclan_token_manager import ownerclan_token_manager
        token = await ownerclan_token_manager.get_auth_token(account_name)
        logger.info(f"토큰 발급 완료: {token is not None}")
        
        if token:
            logger.info(f"토큰 길이: {len(token)}")
            logger.info(f"토큰 앞 20자: {token[:20]}...")
        
        logger.info("=== 오너클랜 인증 테스트 완료 ===")
        return {'success': True, 'token_received': token is not None}
        
    except Exception as e:
        logger.error(f"오너클랜 인증 테스트 실패: {e}")
        return {'success': False, 'error': str(e)}


async def main():
    """메인 테스트 함수"""
    logger.info("=== 오너클랜 통합 테스트 시작 ===")
    
    # 테스트 선택
    test_type = "products_only"  # "full", "products_only", "auth_only"
    
    if test_type == "full":
        success = await test_ownerclan_integration()
    elif test_type == "products_only":
        success = await test_ownerclan_products_only()
    elif test_type == "auth_only":
        result = await test_ownerclan_auth_only()
        success = result.get('success', False)
    else:
        logger.error(f"알 수 없는 테스트 타입: {test_type}")
        return
    
    if success:
        logger.info("=== 모든 테스트 성공 ===")
    else:
        logger.error("=== 테스트 실패 ===")


if __name__ == "__main__":
    asyncio.run(main())