"""
마켓플레이스 경쟁사 데이터 수집 시스템 통합 테스트
"""

import asyncio
import json
from datetime import datetime, timezone
from loguru import logger

from src.services.coupang_search_service import CoupangSearchService
from src.services.naver_smartstore_search_service import NaverSmartStoreSearchService
from src.services.price_comparison_service import PriceComparisonService
from src.services.database_service import DatabaseService


class CompetitorDataCollectionTester:
    """경쟁사 데이터 수집 시스템 테스트 클래스"""

    def __init__(self):
        self.coupang_service = CoupangSearchService()
        self.naver_service = NaverSmartStoreSearchService()
        self.price_comparison_service = PriceComparisonService()
        self.db_service = DatabaseService()
        
        # 테스트 키워드
        self.test_keywords = [
            "무선 이어폰",
            "스마트워치",
            "블루투스 스피커",
            "무선 충전기",
            "USB 케이블"
        ]

    async def test_coupang_search(self) -> bool:
        """쿠팡 상품 검색 테스트"""
        try:
            logger.info("\n=== 쿠팡 상품 검색 테스트 시작 ===")
            
            test_keyword = self.test_keywords[0]
            
                    # 상품 검색
                    products = await self.coupang_service.search_products(
                        keyword=test_keyword,
                        page=1
                    )
            
            if products:
                logger.info(f"✅ 쿠팡 상품 검색 성공: {len(products)}개 상품")
                
                # 상품 정보 출력
                for i, product in enumerate(products[:3]):
                    logger.info(f"  {i+1}. {product.name}")
                    logger.info(f"     가격: {product.price:,}원")
                    logger.info(f"     판매자: {product.seller}")
                    logger.info(f"     평점: {product.rating}")
                
                # 데이터베이스 저장 테스트
                saved_count = await self.coupang_service.save_competitor_products(
                    products, 
                    test_keyword
                )
                
                if saved_count > 0:
                    logger.info(f"✅ 쿠팡 상품 데이터 저장 성공: {saved_count}개")
                    return True
                else:
                    logger.error("❌ 쿠팡 상품 데이터 저장 실패")
                    return False
            else:
                logger.error("❌ 쿠팡 상품 검색 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 쿠팡 상품 검색 테스트 중 오류: {e}")
            return False

    async def test_naver_smartstore_search(self) -> bool:
        """네이버 스마트스토어 상품 검색 테스트"""
        try:
            logger.info("\n=== 네이버 스마트스토어 상품 검색 테스트 시작 ===")
            
            test_keyword = self.test_keywords[1]
            
                    # 상품 검색
                    products = await self.naver_service.search_products(
                        keyword=test_keyword,
                        page=1
                    )
            
            if products:
                logger.info(f"✅ 네이버 스마트스토어 상품 검색 성공: {len(products)}개 상품")
                
                # 상품 정보 출력
                for i, product in enumerate(products[:3]):
                    logger.info(f"  {i+1}. {product.name}")
                    logger.info(f"     가격: {product.price:,}원")
                    logger.info(f"     판매자: {product.seller}")
                    logger.info(f"     평점: {product.rating}")
                
                # 데이터베이스 저장 테스트
                saved_count = await self.naver_service.save_competitor_products(
                    products, 
                    test_keyword
                )
                
                if saved_count > 0:
                    logger.info(f"✅ 네이버 스마트스토어 상품 데이터 저장 성공: {saved_count}개")
                    return True
                else:
                    logger.error("❌ 네이버 스마트스토어 상품 데이터 저장 실패")
                    return False
            else:
                logger.error("❌ 네이버 스마트스토어 상품 검색 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 네이버 스마트스토어 상품 검색 테스트 중 오류: {e}")
            return False

    async def test_price_comparison(self) -> bool:
        """가격 비교 분석 테스트"""
        try:
            logger.info("\n=== 가격 비교 분석 테스트 시작 ===")
            
            test_keyword = self.test_keywords[2]
            our_product_id = "test_product_001"
            our_price = 50000
            
            # 가격 비교 분석
            comparison_result = await self.price_comparison_service.compare_prices(
                keyword=test_keyword,
                our_product_id=our_product_id,
                our_price=our_price,
                platforms=['coupang', 'naver_smartstore']
            )
            
            if comparison_result.price_analysis:
                logger.info("✅ 가격 비교 분석 성공")
                
                # 분석 결과 출력
                market_stats = comparison_result.price_analysis.get('market_statistics', {})
                our_analysis = comparison_result.price_analysis.get('our_price_analysis', {})
                
                logger.info(f"  시장 통계:")
                logger.info(f"    최저가: {market_stats.get('min_price', 0):,}원")
                logger.info(f"    최고가: {market_stats.get('max_price', 0):,}원")
                logger.info(f"    평균가: {market_stats.get('avg_price', 0):,}원")
                logger.info(f"    중간가: {market_stats.get('median_price', 0):,}원")
                
                logger.info(f"  우리 상품 분석:")
                logger.info(f"    우리 가격: {our_analysis.get('our_price', 0):,}원")
                logger.info(f"    가격 포지션: {our_analysis.get('price_position', 'N/A')}")
                logger.info(f"    평균가 대비: {our_analysis.get('vs_avg_price', 0):,}원")
                
                # 추천사항 출력
                if comparison_result.recommendations:
                    logger.info(f"  추천사항:")
                    for i, rec in enumerate(comparison_result.recommendations[:3]):
                        logger.info(f"    {i+1}. {rec}")
                
                return True
            else:
                logger.error("❌ 가격 비교 분석 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 가격 비교 분석 테스트 중 오류: {e}")
            return False

    async def test_market_insights(self) -> bool:
        """시장 인사이트 분석 테스트"""
        try:
            logger.info("\n=== 시장 인사이트 분석 테스트 시작 ===")
            
            test_keyword = self.test_keywords[3]
            
            # 시장 인사이트 분석
            insights = await self.price_comparison_service.get_market_insights(
                keyword=test_keyword,
                days=7
            )
            
            if insights and insights.get('insights'):
                logger.info("✅ 시장 인사이트 분석 성공")
                
                # 인사이트 결과 출력
                insights_data = insights['insights']
                
                market_overview = insights_data.get('market_overview', {})
                logger.info(f"  시장 개요:")
                logger.info(f"    총 상품 수: {market_overview.get('total_products', 0)}개")
                logger.info(f"    플랫폼 분포: {market_overview.get('platform_distribution', {})}")
                
                price_trends = insights_data.get('price_trends', {})
                logger.info(f"  가격 동향:")
                logger.info(f"    트렌드: {price_trends.get('trend', 'N/A')}")
                logger.info(f"    변동 횟수: {price_trends.get('changes_count', 0)}회")
                
                opportunities = insights_data.get('opportunities', [])
                if opportunities:
                    logger.info(f"  기회 요소:")
                    for i, opp in enumerate(opportunities[:3]):
                        logger.info(f"    {i+1}. {opp}")
                
                return True
            else:
                logger.error("❌ 시장 인사이트 분석 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 시장 인사이트 분석 테스트 중 오류: {e}")
            return False

    async def test_price_monitoring(self) -> bool:
        """가격 모니터링 테스트"""
        try:
            logger.info("\n=== 가격 모니터링 테스트 시작 ===")
            
            test_keyword = self.test_keywords[4]
            
            # 가격 변동 모니터링
            alerts = await self.price_comparison_service.monitor_price_changes(
                keyword=test_keyword,
                alert_threshold=5.0
            )
            
            if alerts:
                logger.info(f"✅ 가격 변동 모니터링 성공: {len(alerts)}개 알림")
                
                # 알림 정보 출력
                for i, alert in enumerate(alerts[:3]):
                    logger.info(f"  {i+1}. 상품 ID: {alert['product_id']}")
                    logger.info(f"     플랫폼: {alert['platform']}")
                    logger.info(f"     가격 변동: {alert['old_price']:,}원 → {alert['new_price']:,}원")
                    logger.info(f"     변동률: {alert['price_change_rate']:.1f}%")
                    logger.info(f"     심각도: {alert['severity']}")
            else:
                logger.info("✅ 가격 변동 모니터링 성공: 알림 없음")
            
            return True
                
        except Exception as e:
            logger.error(f"❌ 가격 모니터링 테스트 중 오류: {e}")
            return False

    async def test_database_operations(self) -> bool:
        """데이터베이스 작업 테스트"""
        try:
            logger.info("\n=== 데이터베이스 작업 테스트 시작 ===")
            
            # 경쟁사 상품 데이터 조회
            competitor_products = await self.db_service.select_data(
                "competitor_products",
                {"is_active": True},
                limit=5
            )
            
            if competitor_products:
                logger.info(f"✅ 경쟁사 상품 데이터 조회 성공: {len(competitor_products)}개")
                
                # 가격 변동 이력 조회
                price_history = await self.db_service.select_data(
                    "price_history",
                    {},
                    limit=5
                )
                
                if price_history:
                    logger.info(f"✅ 가격 변동 이력 조회 성공: {len(price_history)}개")
                else:
                    logger.info("✅ 가격 변동 이력 조회 성공: 데이터 없음")
                
                # 경쟁사 분석 결과 조회
                analysis_results = await self.db_service.select_data(
                    "competitor_analysis",
                    {},
                    limit=3
                )
                
                if analysis_results:
                    logger.info(f"✅ 경쟁사 분석 결과 조회 성공: {len(analysis_results)}개")
                else:
                    logger.info("✅ 경쟁사 분석 결과 조회 성공: 데이터 없음")
                
                return True
            else:
                logger.warning("⚠️ 경쟁사 상품 데이터가 없어서 DB 테스트를 건너뜀")
                return True
                
        except Exception as e:
            logger.error(f"❌ 데이터베이스 작업 테스트 중 오류: {e}")
            return False

    async def run_all_tests(self) -> bool:
        """모든 테스트 실행"""
        try:
            logger.info("🚀 마켓플레이스 경쟁사 데이터 수집 시스템 통합 테스트 시작")
            
            test_results = []
            
            # 1. 쿠팡 상품 검색 테스트
            test_results.append(await self.test_coupang_search())
            
            # 2. 네이버 스마트스토어 상품 검색 테스트
            test_results.append(await self.test_naver_smartstore_search())
            
            # 3. 가격 비교 분석 테스트
            test_results.append(await self.test_price_comparison())
            
            # 4. 시장 인사이트 분석 테스트
            test_results.append(await self.test_market_insights())
            
            # 5. 가격 모니터링 테스트
            test_results.append(await self.test_price_monitoring())
            
            # 6. 데이터베이스 작업 테스트
            test_results.append(await self.test_database_operations())
            
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
                return True
            else:
                logger.warning("⚠️ 일부 테스트 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 테스트 실행 중 오류: {e}")
            return False


async def main():
    """메인 함수"""
    tester = CompetitorDataCollectionTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("\n✅ 마켓플레이스 경쟁사 데이터 수집 시스템 통합 테스트 완료")
    else:
        logger.error("\n❌ 마켓플레이스 경쟁사 데이터 수집 시스템 통합 테스트 실패")


if __name__ == "__main__":
    asyncio.run(main())
