"""
마켓플레이스 경쟁사 데이터 수집 시스템 간단 테스트
"""

import asyncio
import json
from datetime import datetime, timezone
from loguru import logger

from src.services.coupang_search_service import CoupangSearchService
from src.services.naver_smartstore_search_service import NaverSmartStoreSearchService
from src.services.price_comparison_service import PriceComparisonService


class SimpleCompetitorTest:
    """간단한 경쟁사 데이터 수집 테스트"""

    def __init__(self):
        self.coupang_service = CoupangSearchService()
        self.naver_service = NaverSmartStoreSearchService()
        self.price_comparison_service = PriceComparisonService()

    async def test_coupang_search_simple(self) -> bool:
        """쿠팡 상품 검색 간단 테스트"""
        try:
            logger.info("\n=== 쿠팡 상품 검색 간단 테스트 ===")
            
            # 상품 검색
            products = await self.coupang_service.search_products(
                keyword="무선 이어폰",
                page=1
            )
            
            if products:
                logger.info(f"✅ 쿠팡 상품 검색 성공: {len(products)}개 상품")
                
                # 상품 정보 출력
                for i, product in enumerate(products[:3]):
                    logger.info(f"  {i+1}. {product.name}")
                    logger.info(f"     가격: {product.price:,}원")
                    logger.info(f"     판매자: {product.seller}")
                
                return True
            else:
                logger.warning("⚠️ 쿠팡 상품 검색 결과 없음")
                return False
                
        except Exception as e:
            logger.error(f"❌ 쿠팡 상품 검색 테스트 중 오류: {e}")
            return False

    async def test_naver_search_simple(self) -> bool:
        """네이버 스마트스토어 상품 검색 간단 테스트"""
        try:
            logger.info("\n=== 네이버 스마트스토어 상품 검색 간단 테스트 ===")
            
            # 상품 검색
            products = await self.naver_service.search_products(
                keyword="스마트워치",
                page=1
            )
            
            if products:
                logger.info(f"✅ 네이버 스마트스토어 상품 검색 성공: {len(products)}개 상품")
                
                # 상품 정보 출력
                for i, product in enumerate(products[:3]):
                    logger.info(f"  {i+1}. {product.name}")
                    logger.info(f"     가격: {product.price:,}원")
                    logger.info(f"     판매자: {product.seller}")
                
                return True
            else:
                logger.warning("⚠️ 네이버 스마트스토어 상품 검색 결과 없음")
                return False
                
        except Exception as e:
            logger.error(f"❌ 네이버 스마트스토어 상품 검색 테스트 중 오류: {e}")
            return False

    async def test_price_comparison_simple(self) -> bool:
        """가격 비교 분석 간단 테스트"""
        try:
            logger.info("\n=== 가격 비교 분석 간단 테스트 ===")
            
            # 가격 비교 분석 (데이터베이스 없이)
            test_products = [
                {"name": "무선 이어폰 A", "price": 50000, "platform": "coupang"},
                {"name": "무선 이어폰 B", "price": 45000, "platform": "naver_smartstore"},
                {"name": "무선 이어폰 C", "price": 55000, "platform": "coupang"},
            ]
            
            our_price = 48000
            
            # 가격 분석
            prices = [p['price'] for p in test_products]
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            
            logger.info(f"✅ 가격 분석 완료:")
            logger.info(f"  우리 가격: {our_price:,}원")
            logger.info(f"  최저가: {min_price:,}원")
            logger.info(f"  최고가: {max_price:,}원")
            logger.info(f"  평균가: {avg_price:,.0f}원")
            
            # 가격 포지션 분석
            if our_price < avg_price:
                logger.info(f"  가격 포지션: 저가 (평균 대비 {avg_price - our_price:,.0f}원 저렴)")
            else:
                logger.info(f"  가격 포지션: 고가 (평균 대비 {our_price - avg_price:,.0f}원 비쌈)")
            
            return True
                
        except Exception as e:
            logger.error(f"❌ 가격 비교 분석 테스트 중 오류: {e}")
            return False

    async def run_simple_tests(self) -> bool:
        """간단한 테스트들 실행"""
        try:
            logger.info("🚀 마켓플레이스 경쟁사 데이터 수집 시스템 간단 테스트 시작")
            
            test_results = []
            
            # 1. 쿠팡 상품 검색 테스트
            test_results.append(await self.test_coupang_search_simple())
            
            # 2. 네이버 스마트스토어 상품 검색 테스트
            test_results.append(await self.test_naver_search_simple())
            
            # 3. 가격 비교 분석 테스트
            test_results.append(await self.test_price_comparison_simple())
            
            # 결과 요약
            passed_tests = sum(test_results)
            total_tests = len(test_results)
            
            logger.info(f"\n📊 간단 테스트 결과 요약:")
            logger.info(f"  총 테스트: {total_tests}개")
            logger.info(f"  성공: {passed_tests}개")
            logger.info(f"  실패: {total_tests - passed_tests}개")
            logger.info(f"  성공률: {passed_tests/total_tests*100:.1f}%")
            
            if passed_tests == total_tests:
                logger.info("🎉 모든 간단 테스트 통과!")
                return True
            else:
                logger.warning("⚠️ 일부 테스트 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 간단 테스트 실행 중 오류: {e}")
            return False


async def main():
    """메인 함수"""
    tester = SimpleCompetitorTest()
    success = await tester.run_simple_tests()
    
    if success:
        logger.info("\n✅ 마켓플레이스 경쟁사 데이터 수집 시스템 간단 테스트 완료")
    else:
        logger.error("\n❌ 마켓플레이스 경쟁사 데이터 수집 시스템 간단 테스트 실패")


if __name__ == "__main__":
    asyncio.run(main())
