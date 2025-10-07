#!/usr/bin/env python3
"""
마켓플레이스 경쟁사 서비스 통합 테스트
"""

import sys
import os
import asyncio
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.marketplace_competitor_service import MarketplaceCompetitorService
from src.services.database_service import DatabaseService


async def test_marketplace_competitor_service():
    """마켓플레이스 경쟁사 서비스 통합 테스트"""
    logger.info("마켓플레이스 경쟁사 서비스 통합 테스트 시작")
    
    try:
        # 서비스 초기화
        db_service = DatabaseService()
        service = MarketplaceCompetitorService(db_service)
        
        # 테스트 키워드들
        test_keywords = ["가방", "노트북", "스마트폰"]
        
        for keyword in test_keywords:
            logger.info(f"\n=== '{keyword}' 경쟁사 분석 ===")
            
            # 경쟁사 상품 수집
            competitor_data = await service.search_competitors(keyword)
            
            # 결과 출력
            coupang_count = len(competitor_data.get('coupang', []))
            naver_count = len(competitor_data.get('naver_smartstore', []))
            elevenstreet_count = len(competitor_data.get('elevenstreet', []))
            gmarket_count = len(competitor_data.get('gmarket', []))
            auction_count = len(competitor_data.get('auction', []))
            
            logger.info(f"쿠팡: {coupang_count}개 상품")
            logger.info(f"네이버 스마트스토어: {naver_count}개 상품")
            logger.info(f"11번가: {elevenstreet_count}개 상품")
            logger.info(f"G마켓: {gmarket_count}개 상품")
            logger.info(f"옥션: {auction_count}개 상품")
            
            # 가격 경쟁 분석
            analysis = await service.analyze_price_competition(keyword, 50000)  # 우리 가격 50,000원
            logger.info(f"가격 경쟁 분석 결과: {analysis}")
            
            # 경쟁사 데이터 저장
            saved_count = await service.save_competitor_data(competitor_data)
            logger.info(f"저장된 경쟁사 데이터: {saved_count}개")
        
        logger.info("\n마켓플레이스 경쟁사 서비스 통합 테스트 완료")
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_marketplace_competitor_service())
