#!/usr/bin/env python3
"""
간단한 경쟁사 데이터 저장 테스트
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService


async def test_simple_competitor_data():
    """간단한 경쟁사 데이터 저장 테스트"""
    try:
        logger.info("=== 간단한 경쟁사 데이터 저장 테스트 시작 ===")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 테스트 데이터 생성
        test_data = {
            "platform": "coupang",
            "product_id": "test_product_001",
            "name": "테스트 무선 이어폰",
            "price": 45000,
            "original_price": 60000,
            "discount_rate": 25,
            "seller": "테스트 셀러",
            "rating": 4.5,
            "review_count": 1250,
            "image_url": "https://example.com/test.jpg",
            "product_url": "https://coupang.com/test",
            "category": "전자제품",
            "brand": "TestBrand",
            "search_keyword": "무선 이어폰",
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True,
            "marketplace_code": "coupang",
            "marketplace_name": "쿠팡",
            "market_share": 0.35,
            "avg_delivery_days": 1.5,
            "free_shipping_threshold": 30000,
            "raw_data": {"test": "data"}
        }
        
        # 데이터 저장
        await db_service.insert_data("competitor_products", test_data)
        logger.info("✅ 경쟁사 데이터 저장 성공")
        
        # 저장된 데이터 조회
        stored_data = await db_service.select_data(
            "competitor_products",
            {"product_id": "test_product_001"}
        )
        
        if stored_data:
            logger.info(f"✅ 저장된 데이터 조회 성공: {len(stored_data)}개")
            product = stored_data[0]
            logger.info(f"  상품명: {product['name']}")
            logger.info(f"  가격: {product['price']:,}원")
            logger.info(f"  플랫폼: {product['platform']}")
            return True
        else:
            logger.error("❌ 저장된 데이터 조회 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 테스트 실패: {e}")
        return False


async def test_price_history():
    """가격 변동 이력 테스트"""
    try:
        logger.info("\n=== 가격 변동 이력 테스트 시작 ===")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 테스트 데이터 생성
        price_history_data = {
            "product_id": "test_product_001",
            "platform": "coupang",
            "old_price": 48000,
            "new_price": 45000,
            "price_change": -3000,
            "price_change_rate": -6.25,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # 데이터 저장
        await db_service.insert_data("price_history", price_history_data)
        logger.info("✅ 가격 변동 이력 저장 성공")
        
        # 저장된 데이터 조회
        stored_history = await db_service.select_data(
            "price_history",
            {"product_id": "test_product_001"}
        )
        
        if stored_history:
            logger.info(f"✅ 가격 변동 이력 조회 성공: {len(stored_history)}개")
            history = stored_history[0]
            logger.info(f"  상품 ID: {history['product_id']}")
            logger.info(f"  가격 변동: {history['old_price']:,}원 → {history['new_price']:,}원")
            logger.info(f"  변동률: {history['price_change_rate']:.1f}%")
            return True
        else:
            logger.error("❌ 가격 변동 이력 조회 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 가격 변동 이력 테스트 실패: {e}")
        return False


async def test_competitor_analysis():
    """경쟁사 분석 결과 테스트"""
    try:
        logger.info("\n=== 경쟁사 분석 결과 테스트 시작 ===")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 테스트 데이터 생성
        analysis_data = {
            "analysis_type": "market_trend",
            "target_keyword": "무선 이어폰",
            "platform": "coupang",
            "analysis_data": {
                "total_products": 10,
                "avg_price": 45000,
                "price_trend": "하락",
                "competitor_count": 5
            },
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "analysis_period_days": 7
        }
        
        # 데이터 저장
        await db_service.insert_data("competitor_analysis", analysis_data)
        logger.info("✅ 경쟁사 분석 결과 저장 성공")
        
        # 저장된 데이터 조회
        stored_analysis = await db_service.select_data(
            "competitor_analysis",
            {"target_keyword": "무선 이어폰"}
        )
        
        if stored_analysis:
            logger.info(f"✅ 경쟁사 분석 결과 조회 성공: {len(stored_analysis)}개")
            analysis = stored_analysis[0]
            logger.info(f"  분석 유형: {analysis['analysis_type']}")
            logger.info(f"  대상 키워드: {analysis['target_keyword']}")
            logger.info(f"  플랫폼: {analysis['platform']}")
            return True
        else:
            logger.error("❌ 경쟁사 분석 결과 조회 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 경쟁사 분석 결과 테스트 실패: {e}")
        return False


async def main():
    """메인 함수"""
    try:
        logger.info("🚀 간단한 경쟁사 데이터 테스트 시작")
        
        test_results = []
        
        # 1. 경쟁사 데이터 저장 테스트
        test_results.append(await test_simple_competitor_data())
        
        # 2. 가격 변동 이력 테스트
        test_results.append(await test_price_history())
        
        # 3. 경쟁사 분석 결과 테스트
        test_results.append(await test_competitor_analysis())
        
        # 결과 요약
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        logger.info(f"\n📊 테스트 결과 요약:")
        logger.info(f"  총 테스트: {total_tests}개")
        logger.info(f"  성공: {passed_tests}개")
        logger.info(f"  실패: {total_tests - passed_tests}개")
        logger.info(f"  성공률: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 모든 테스트 통과!")
        else:
            logger.warning("⚠️ 일부 테스트 실패")
            
    except Exception as e:
        logger.error(f"❌ 테스트 실행 중 오류: {e}")


if __name__ == "__main__":
    asyncio.run(main())
