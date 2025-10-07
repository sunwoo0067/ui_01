#!/usr/bin/env python3
"""
마켓플레이스 경쟁사 데이터 수집 시스템 모의 테스트
웹 스크래핑 차단 문제를 우회하여 데이터베이스 및 분석 기능 테스트
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.services.marketplace_competitor_service import MarketplaceCompetitorService


async def create_mock_competitor_data() -> Dict[str, List[Dict[str, Any]]]:
    """모의 경쟁사 데이터 생성"""
    mock_data = {
        "coupang": [
            {
                "product_id": "mock_coupang_001",
                "name": "무선 이어폰 블루투스 5.0",
                "price": 45000,
                "original_price": 60000,
                "discount_rate": 25,
                "seller": "쿠팡",
                "rating": 4.5,
                "review_count": 1250,
                "image_url": "https://example.com/image1.jpg",
                "product_url": "https://coupang.com/products/mock_coupang_001",
                "category": "전자제품",
                "brand": "MockBrand",
                "marketplace_code": "coupang",
                "marketplace_name": "쿠팡",
                "market_share": 0.35,
                "avg_delivery_days": 1.5,
                "free_shipping_threshold": 30000,
                "collected_at": datetime.utcnow().isoformat()
            },
            {
                "product_id": "mock_coupang_002",
                "name": "스마트워치 GPS 심박측정",
                "price": 89000,
                "original_price": 120000,
                "discount_rate": 26,
                "seller": "쿠팡",
                "rating": 4.3,
                "review_count": 890,
                "image_url": "https://example.com/image2.jpg",
                "product_url": "https://coupang.com/products/mock_coupang_002",
                "category": "전자제품",
                "brand": "SmartTech",
                "marketplace_code": "coupang",
                "marketplace_name": "쿠팡",
                "market_share": 0.35,
                "avg_delivery_days": 1.5,
                "free_shipping_threshold": 30000,
                "collected_at": datetime.utcnow().isoformat()
            },
            {
                "product_id": "mock_coupang_003",
                "name": "블루투스 스피커 휴대용",
                "price": 32000,
                "original_price": 45000,
                "discount_rate": 29,
                "seller": "쿠팡",
                "rating": 4.2,
                "review_count": 567,
                "image_url": "https://example.com/image3.jpg",
                "product_url": "https://coupang.com/products/mock_coupang_003",
                "category": "전자제품",
                "brand": "SoundMax",
                "marketplace_code": "coupang",
                "marketplace_name": "쿠팡",
                "market_share": 0.35,
                "avg_delivery_days": 1.5,
                "free_shipping_threshold": 30000,
                "collected_at": datetime.utcnow().isoformat()
            }
        ],
        "naver_smartstore": [
            {
                "product_id": "mock_naver_001",
                "name": "무선 이어폰 블루투스 5.0",
                "price": 42000,
                "original_price": 55000,
                "discount_rate": 24,
                "seller": "스마트스토어",
                "rating": 4.4,
                "review_count": 980,
                "image_url": "https://example.com/image4.jpg",
                "product_url": "https://smartstore.naver.com/products/mock_naver_001",
                "category": "전자제품",
                "brand": "MockBrand",
                "marketplace_code": "naver_smartstore",
                "marketplace_name": "네이버 스마트스토어",
                "market_share": 0.25,
                "avg_delivery_days": 2.0,
                "free_shipping_threshold": 20000,
                "collected_at": datetime.utcnow().isoformat()
            },
            {
                "product_id": "mock_naver_002",
                "name": "스마트워치 GPS 심박측정",
                "price": 95000,
                "original_price": 130000,
                "discount_rate": 27,
                "seller": "스마트스토어",
                "rating": 4.1,
                "review_count": 445,
                "image_url": "https://example.com/image5.jpg",
                "product_url": "https://smartstore.naver.com/products/mock_naver_002",
                "category": "전자제품",
                "brand": "SmartTech",
                "marketplace_code": "naver_smartstore",
                "marketplace_name": "네이버 스마트스토어",
                "market_share": 0.25,
                "avg_delivery_days": 2.0,
                "free_shipping_threshold": 20000,
                "collected_at": datetime.utcnow().isoformat()
            },
            {
                "product_id": "mock_naver_003",
                "name": "블루투스 스피커 휴대용",
                "price": 35000,
                "original_price": 48000,
                "discount_rate": 27,
                "seller": "스마트스토어",
                "rating": 4.0,
                "review_count": 234,
                "image_url": "https://example.com/image6.jpg",
                "product_url": "https://smartstore.naver.com/products/mock_naver_003",
                "category": "전자제품",
                "brand": "SoundMax",
                "marketplace_code": "naver_smartstore",
                "marketplace_name": "네이버 스마트스토어",
                "market_share": 0.25,
                "avg_delivery_days": 2.0,
                "free_shipping_threshold": 20000,
                "collected_at": datetime.utcnow().isoformat()
            }
        ]
    }
    
    return mock_data


async def test_competitor_data_storage():
    """경쟁사 데이터 저장 테스트"""
    try:
        logger.info("=== 경쟁사 데이터 저장 테스트 시작 ===")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 경쟁사 서비스 초기화
        competitor_service = MarketplaceCompetitorService(db_service)
        
        # 모의 데이터 생성
        mock_data = await create_mock_competitor_data()
        
        # 데이터 저장
        saved_count = await competitor_service.save_competitor_data(mock_data)
        
        if saved_count > 0:
            logger.info(f"✅ 경쟁사 데이터 저장 성공: {saved_count}개")
            
            # 저장된 데이터 확인
            stored_products = await db_service.select_data(
                "competitor_products",
                {"is_active": True},
                limit=10
            )
            
            logger.info(f"저장된 상품 수: {len(stored_products)}개")
            for product in stored_products[:3]:
                logger.info(f"  - {product['name']}: {product['price']:,}원 ({product['platform']})")
            
            return True
        else:
            logger.error("❌ 경쟁사 데이터 저장 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 경쟁사 데이터 저장 테스트 실패: {e}")
        return False


async def test_price_competition_analysis():
    """가격 경쟁 분석 테스트"""
    try:
        logger.info("\n=== 가격 경쟁 분석 테스트 시작 ===")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 경쟁사 서비스 초기화
        competitor_service = MarketplaceCompetitorService(db_service)
        
        # 가격 경쟁 분석
        analysis_result = await competitor_service.analyze_price_competition(
            keyword="무선 이어폰",
            our_price=50000,
            marketplaces=["coupang", "naver_smartstore"]
        )
        
        if analysis_result and analysis_result.get("competitor_count", 0) > 0:
            logger.info("✅ 가격 경쟁 분석 성공")
            
            # 분석 결과 출력
            logger.info(f"  경쟁사 수: {analysis_result['competitor_count']}개")
            logger.info(f"  우리 가격: {analysis_result['our_price']:,}원")
            
            overall_stats = analysis_result.get("overall_stats", {})
            logger.info(f"  시장 평균가: {overall_stats.get('avg_competitor_price', 0):,.0f}원")
            logger.info(f"  최저가: {overall_stats.get('min_competitor_price', 0):,.0f}원")
            logger.info(f"  최고가: {overall_stats.get('max_competitor_price', 0):,.0f}원")
            
            competitiveness = analysis_result.get("competitiveness", {})
            logger.info(f"  경쟁력: {competitiveness.get('level', 'N/A')} ({competitiveness.get('score', 0)}점)")
            
            price_position = analysis_result.get("price_position", {})
            logger.info(f"  가격 포지션: {price_position.get('position', 'N/A')}")
            logger.info(f"  순위: {price_position.get('rank', 0)}/{price_position.get('total_competitors', 0)}")
            
            # 추천사항 출력
            recommendations = analysis_result.get("recommendations", [])
            if recommendations:
                logger.info("  추천사항:")
                for i, rec in enumerate(recommendations[:3]):
                    logger.info(f"    {i+1}. {rec}")
            
            return True
        else:
            logger.error("❌ 가격 경쟁 분석 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 가격 경쟁 분석 테스트 실패: {e}")
        return False


async def test_price_history():
    """가격 변동 이력 테스트"""
    try:
        logger.info("\n=== 가격 변동 이력 테스트 시작 ===")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 모의 가격 변동 이력 생성
        price_history_data = [
            {
                "product_id": "mock_coupang_001",
                "platform": "coupang",
                "old_price": 48000,
                "new_price": 45000,
                "price_change": -3000,
                "price_change_rate": -6.25,
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat()
            },
            {
                "product_id": "mock_naver_001",
                "platform": "naver_smartstore",
                "old_price": 45000,
                "new_price": 42000,
                "price_change": -3000,
                "price_change_rate": -6.67,
                "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat()
            }
        ]
        
        # 가격 변동 이력 저장
        saved_count = 0
        for history in price_history_data:
            try:
                await db_service.insert_data("price_history", history)
                saved_count += 1
                logger.info(f"가격 변동 이력 저장: {history['product_id']} - {history['old_price']:,}원 → {history['new_price']:,}원")
            except Exception as e:
                logger.error(f"가격 변동 이력 저장 실패: {e}")
        
        if saved_count > 0:
            logger.info(f"✅ 가격 변동 이력 저장 성공: {saved_count}개")
            
            # 저장된 가격 변동 이력 조회
            stored_history = await db_service.select_data(
                "price_history",
                {},
                order_by="timestamp DESC",
                limit=5
            )
            
            logger.info(f"저장된 가격 변동 이력: {len(stored_history)}개")
            for history in stored_history:
                logger.info(f"  - {history['product_id']}: {history['old_price']:,}원 → {history['new_price']:,}원 ({history['price_change_rate']:.1f}%)")
            
            return True
        else:
            logger.error("❌ 가격 변동 이력 저장 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 가격 변동 이력 테스트 실패: {e}")
        return False


async def test_marketplace_statistics():
    """마켓플레이스 통계 테스트"""
    try:
        logger.info("\n=== 마켓플레이스 통계 테스트 시작 ===")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 플랫폼별 상품 수 통계
        platforms = ["coupang", "naver_smartstore"]
        platform_stats = {}
        
        for platform in platforms:
            products = await db_service.select_data(
                "competitor_products",
                {"platform": platform, "is_active": True}
            )
            
            if products:
                prices = [p["price"] for p in products if p["price"] > 0]
                platform_stats[platform] = {
                    "product_count": len(products),
                    "avg_price": sum(prices) / len(prices) if prices else 0,
                    "min_price": min(prices) if prices else 0,
                    "max_price": max(prices) if prices else 0
                }
                
                logger.info(f"{platform} 통계:")
                logger.info(f"  상품 수: {len(products)}개")
                logger.info(f"  평균 가격: {platform_stats[platform]['avg_price']:,.0f}원")
                logger.info(f"  가격 범위: {platform_stats[platform]['min_price']:,.0f}원 ~ {platform_stats[platform]['max_price']:,.0f}원")
        
        if platform_stats:
            logger.info("✅ 마켓플레이스 통계 조회 성공")
            return True
        else:
            logger.error("❌ 마켓플레이스 통계 조회 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 마켓플레이스 통계 테스트 실패: {e}")
        return False


async def run_all_mock_tests():
    """모든 모의 테스트 실행"""
    try:
        logger.info("🚀 마켓플레이스 경쟁사 데이터 수집 시스템 모의 테스트 시작")
        
        test_results = []
        
        # 1. 경쟁사 데이터 저장 테스트
        test_results.append(await test_competitor_data_storage())
        
        # 2. 가격 경쟁 분석 테스트
        test_results.append(await test_price_competition_analysis())
        
        # 3. 가격 변동 이력 테스트
        test_results.append(await test_price_history())
        
        # 4. 마켓플레이스 통계 테스트
        test_results.append(await test_marketplace_statistics())
        
        # 결과 요약
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        logger.info(f"\n📊 모의 테스트 결과 요약:")
        logger.info(f"  총 테스트: {total_tests}개")
        logger.info(f"  성공: {passed_tests}개")
        logger.info(f"  실패: {total_tests - passed_tests}개")
        logger.info(f"  성공률: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 모든 모의 테스트 통과!")
            return True
        else:
            logger.warning("⚠️ 일부 모의 테스트 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 모의 테스트 실행 중 오류: {e}")
        return False


async def main():
    """메인 함수"""
    success = await run_all_mock_tests()
    
    if success:
        logger.info("\n✅ 마켓플레이스 경쟁사 데이터 수집 시스템 모의 테스트 완료")
    else:
        logger.error("\n❌ 마켓플레이스 경쟁사 데이터 수집 시스템 모의 테스트 실패")


if __name__ == "__main__":
    asyncio.run(main())
