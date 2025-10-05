"""
추가 마켓플레이스 통합 테스트
"""

import asyncio
from loguru import logger

from src.services.elevenstreet_search_service import ElevenStreetSearchService
from src.services.gmarket_search_service import GmarketSearchService
from src.services.auction_search_service import AuctionSearchService
from src.services.unified_marketplace_search_service import UnifiedMarketplaceSearchService


class AdditionalMarketplaceTester:
    """추가 마켓플레이스 테스트 클래스"""

    def __init__(self):
        self.elevenstreet_service = ElevenStreetSearchService()
        self.gmarket_service = GmarketSearchService()
        self.auction_service = AuctionSearchService()
        self.unified_service = UnifiedMarketplaceSearchService()

    async def test_elevenstreet_search(self) -> bool:
        """11번가 검색 테스트"""
        try:
            logger.info("\n=== 11번가 검색 테스트 ===")
            
            keyword = "무선 이어폰"
            products = await self.elevenstreet_service.search_products(keyword, page=1)
            
            if products:
                logger.info(f"✅ 11번가 검색 성공: {len(products)}개 상품")
                
                # 첫 번째 상품 정보 출력
                first_product = products[0]
                logger.info(f"  상품명: {first_product.name}")
                logger.info(f"  가격: {first_product.price:,}원")
                logger.info(f"  판매자: {first_product.seller}")
                logger.info(f"  플랫폼: {first_product.platform}")
                
                return True
            else:
                logger.warning("⚠️ 11번가 검색 결과 없음")
                return False
                
        except Exception as e:
            logger.error(f"❌ 11번가 검색 테스트 실패: {e}")
            return False

    async def test_gmarket_search(self) -> bool:
        """G마켓 검색 테스트"""
        try:
            logger.info("\n=== G마켓 검색 테스트 ===")
            
            keyword = "무선 이어폰"
            products = await self.gmarket_service.search_products(keyword, page=1)
            
            if products:
                logger.info(f"✅ G마켓 검색 성공: {len(products)}개 상품")
                
                # 첫 번째 상품 정보 출력
                first_product = products[0]
                logger.info(f"  상품명: {first_product.name}")
                logger.info(f"  가격: {first_product.price:,}원")
                logger.info(f"  판매자: {first_product.seller}")
                logger.info(f"  플랫폼: {first_product.platform}")
                
                return True
            else:
                logger.warning("⚠️ G마켓 검색 결과 없음")
                return False
                
        except Exception as e:
            logger.error(f"❌ G마켓 검색 테스트 실패: {e}")
            return False

    async def test_auction_search(self) -> bool:
        """옥션 검색 테스트"""
        try:
            logger.info("\n=== 옥션 검색 테스트 ===")
            
            keyword = "무선 이어폰"
            products = await self.auction_service.search_products(keyword, page=1)
            
            if products:
                logger.info(f"✅ 옥션 검색 성공: {len(products)}개 상품")
                
                # 첫 번째 상품 정보 출력
                first_product = products[0]
                logger.info(f"  상품명: {first_product.name}")
                logger.info(f"  가격: {first_product.price:,}원")
                logger.info(f"  판매자: {first_product.seller}")
                logger.info(f"  플랫폼: {first_product.platform}")
                
                return True
            else:
                logger.warning("⚠️ 옥션 검색 결과 없음")
                return False
                
        except Exception as e:
            logger.error(f"❌ 옥션 검색 테스트 실패: {e}")
            return False

    async def test_unified_search(self) -> bool:
        """통합 검색 테스트"""
        try:
            logger.info("\n=== 통합 마켓플레이스 검색 테스트 ===")
            
            keyword = "무선 이어폰"
            
            # 모든 플랫폼에서 검색
            results = await self.unified_service.search_all_platforms(keyword, page=1)
            
            if results:
                logger.info(f"✅ 통합 검색 성공")
                
                total_products = 0
                for platform, products in results.items():
                    logger.info(f"  {platform}: {len(products)}개 상품")
                    total_products += len(products)
                
                logger.info(f"  총 상품 수: {total_products}개")
                
                # 가격 비교 분석
                comparison = await self.unified_service.get_price_comparison(keyword)
                if comparison and comparison.get('overall_stats'):
                    stats = comparison['overall_stats']
                    logger.info(f"  최저가: {stats.get('min_price', 0):,}원")
                    logger.info(f"  최고가: {stats.get('max_price', 0):,}원")
                    logger.info(f"  평균가: {stats.get('avg_price', 0):,.0f}원")
                
                return True
            else:
                logger.warning("⚠️ 통합 검색 결과 없음")
                return False
                
        except Exception as e:
            logger.error(f"❌ 통합 검색 테스트 실패: {e}")
            return False

    async def test_platform_status(self) -> bool:
        """플랫폼 상태 확인 테스트"""
        try:
            logger.info("\n=== 플랫폼 상태 확인 테스트 ===")
            
            status = await self.unified_service.get_platform_status()
            
            if status:
                logger.info("✅ 플랫폼 상태 확인 성공")
                
                for platform, is_working in status.items():
                    status_text = "🟢 정상" if is_working else "🔴 오류"
                    logger.info(f"  {platform}: {status_text}")
                
                working_count = sum(1 for working in status.values() if working)
                total_count = len(status)
                
                logger.info(f"  정상 작동: {working_count}/{total_count}개 플랫폼")
                
                return working_count > 0
            else:
                logger.warning("⚠️ 플랫폼 상태 확인 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 플랫폼 상태 확인 테스트 실패: {e}")
            return False

    async def test_supported_platforms(self) -> bool:
        """지원 플랫폼 목록 테스트"""
        try:
            logger.info("\n=== 지원 플랫폼 목록 테스트 ===")
            
            platforms = self.unified_service.get_supported_platforms()
            
            if platforms:
                logger.info(f"✅ 지원 플랫폼 목록 조회 성공: {len(platforms)}개")
                
                for i, platform in enumerate(platforms, 1):
                    logger.info(f"  {i}. {platform}")
                
                return True
            else:
                logger.warning("⚠️ 지원 플랫폼 목록 없음")
                return False
                
        except Exception as e:
            logger.error(f"❌ 지원 플랫폼 목록 테스트 실패: {e}")
            return False

    async def run_all_tests(self) -> bool:
        """모든 테스트 실행"""
        try:
            logger.info("🚀 추가 마켓플레이스 통합 테스트 시작")
            
            test_results = []
            
            # 1. 지원 플랫폼 목록 테스트
            test_results.append(await self.test_supported_platforms())
            
            # 2. 플랫폼 상태 확인 테스트
            test_results.append(await self.test_platform_status())
            
            # 3. 개별 플랫폼 검색 테스트
            test_results.append(await self.test_elevenstreet_search())
            test_results.append(await self.test_gmarket_search())
            test_results.append(await self.test_auction_search())
            
            # 4. 통합 검색 테스트
            test_results.append(await self.test_unified_search())
            
            # 결과 요약
            passed_tests = sum(test_results)
            total_tests = len(test_results)
            
            logger.info(f"\n📊 추가 마켓플레이스 테스트 결과 요약:")
            logger.info(f"  총 테스트: {total_tests}개")
            logger.info(f"  성공: {passed_tests}개")
            logger.info(f"  실패: {total_tests - passed_tests}개")
            logger.info(f"  성공률: {passed_tests/total_tests*100:.1f}%")
            
            if passed_tests == total_tests:
                logger.info("🎉 모든 추가 마켓플레이스 테스트 통과!")
                return True
            else:
                logger.warning("⚠️ 일부 테스트 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 추가 마켓플레이스 테스트 실행 중 오류: {e}")
            return False


async def main():
    """메인 함수"""
    tester = AdditionalMarketplaceTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("\n✅ 추가 마켓플레이스 통합 테스트 완료")
        logger.info("🌐 지원 플랫폼: 쿠팡, 네이버 스마트스토어, 11번가, G마켓, 옥션")
    else:
        logger.error("\n❌ 추가 마켓플레이스 통합 테스트 실패")


if __name__ == "__main__":
    asyncio.run(main())
