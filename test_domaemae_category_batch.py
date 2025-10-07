#!/usr/bin/env python3
"""
도매꾹 카테고리 기반 배치 수집 테스트
"""

import asyncio
import sys
import os
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.services.domaemae_data_collector import DomaemaeDataCollector, DomaemaeDataStorage


async def test_category_batch_collection():
    """카테고리 기반 배치 수집 테스트"""
    try:
        logger.info("도매꾹 카테고리 기반 배치 수집 테스트 시작")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 도매꾹 데이터 수집기 및 저장 서비스 초기화
        collector = DomaemaeDataCollector(db_service)
        storage = DomaemaeDataStorage(db_service)
        
        # 테스트 카테고리 목록 (실제 도매꾹 카테고리 코드)
        test_categories = [
            "01_01_00_00_00",  # 의류/잡화 > 여성의류
            "01_02_00_00_00",  # 의류/잡화 > 남성의류
            "02_01_00_00_00",  # 뷰티/헬스 > 화장품
            "03_01_00_00_00",  # 식품/건강 > 건강식품
        ]
        
        account_name = "test_account"
        
        # 1. 카테고리별 수집 테스트 (도매꾹/도매매 모두)
        logger.info("=== 카테고리별 수집 테스트 (도매꾹/도매매 모두) ===")
        
        results = await collector.collect_products_by_category(
            account_name=account_name,
            categories=test_categories,
            batch_size=200,
            max_pages_per_category=2,  # 카테고리당 최대 2페이지
            markets=["dome", "supply"]  # 두 시장 모두
        )
        
        # 결과 분석
        total_collected = 0
        for market, products in results.items():
            market_name = "도매꾹" if market == "dome" else "도매매"
            logger.info(f"{market_name} 수집 결과: {len(products)}개 상품")
            total_collected += len(products)
            
            # 샘플 상품 정보 출력
            if products:
                sample = products[0]
                logger.info(f"{market_name} 샘플 상품:")
                logger.info(f"  - 상품명: {sample.get('title', 'N/A')}")
                logger.info(f"  - 가격: {sample.get('price', 0):,}원")
                logger.info(f"  - 판매자: {sample.get('seller_nick', 'N/A')}")
                logger.info(f"  - 시장 타입: {sample.get('market_type', 'N/A')}")
                logger.info(f"  - 최소 주문 타입: {sample.get('min_order_type', 'N/A')}")
        
        logger.info(f"카테고리별 수집 완료: 총 {total_collected}개 상품")
        
        # 2. 데이터베이스 저장 테스트
        logger.info("=== 데이터베이스 저장 테스트 ===")
        
        saved_count = 0
        for market, products in results.items():
            if products:
                market_name = "도매꾹" if market == "dome" else "도매매"
                logger.info(f"{market_name} 상품 저장 시작: {len(products)}개")
                
                count = await storage.save_products(products)
                saved_count += count
                
                logger.info(f"{market_name} 상품 저장 완료: {count}개")
        
        logger.info(f"전체 저장 완료: {saved_count}개 상품")
        
        # 3. 단일 시장 배치 수집 테스트
        logger.info("=== 단일 시장 배치 수집 테스트 ===")
        
        # 도매꾹만 테스트
        dome_products = await collector.collect_products_batch(
            account_name=account_name,
            batch_size=200,
            max_pages=2,
            market="dome",
            keyword="가방"
        )
        
        logger.info(f"도매꾹 단일 시장 수집 결과: {len(dome_products)}개 상품")
        
        # 도매매만 테스트
        supply_products = await collector.collect_products_batch(
            account_name=account_name,
            batch_size=200,
            max_pages=2,
            market="supply",
            keyword="가방"
        )
        
        logger.info(f"도매매 단일 시장 수집 결과: {len(supply_products)}개 상품")
        
        # 4. 모든 시장 배치 수집 테스트
        logger.info("=== 모든 시장 배치 수집 테스트 ===")
        
        all_markets_results = await collector.collect_all_markets_batch(
            account_name=account_name,
            batch_size=200,
            max_pages=1,
            keyword="가방"
        )
        
        for market, products in all_markets_results.items():
            market_name = "도매꾹" if market == "dome" else "도매매"
            logger.info(f"{market_name} 모든 시장 수집 결과: {len(products)}개 상품")
        
        # 5. 성능 분석
        logger.info("=== 성능 분석 ===")
        
        total_products = sum(len(products) for products in results.values())
        if total_products > 0:
            logger.info(f"총 수집 상품: {total_products}개")
            logger.info(f"저장 성공률: {(saved_count / total_products) * 100:.1f}%")
        
        # 시장별 통계
        dome_count = len(results.get("dome", []))
        supply_count = len(results.get("supply", []))
        
        logger.info(f"도매꾹 상품: {dome_count}개")
        logger.info(f"도매매 상품: {supply_count}개")
        
        if total_products > 0:
            logger.info(f"도매꾹 비율: {(dome_count / total_products) * 100:.1f}%")
            logger.info(f"도매매 비율: {(supply_count / total_products) * 100:.1f}%")
        else:
            logger.info("카테고리 검색 결과가 없습니다. 키워드 검색을 사용해보세요.")
        
        logger.info("도매꾹 카테고리 기반 배치 수집 테스트 완료")
        
    except Exception as e:
        logger.error(f"테스트 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_category_batch_collection())
