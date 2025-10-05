"""
프록시 관리 및 웹 스크래핑 우회 테스트
"""

import asyncio
import json
from datetime import datetime, timezone
from loguru import logger

from src.services.advanced_web_scraper import AdvancedWebScraper, ProxyScraper
from src.services.coupang_search_service import CoupangSearchService
from src.services.naver_smartstore_search_service import NaverSmartStoreSearchService


class WebScrapingBypassTester:
    """웹 스크래핑 우회 테스트 클래스"""

    def __init__(self):
        self.scraper = AdvancedWebScraper()
        self.proxy_scraper = ProxyScraper()
        self.coupang_service = CoupangSearchService()
        self.naver_service = NaverSmartStoreSearchService()

    async def test_proxy_collection(self) -> bool:
        """프록시 수집 테스트"""
        try:
            logger.info("\n=== 프록시 수집 테스트 시작 ===")
            
            # 무료 프록시 수집
            proxies = await self.proxy_scraper.get_free_proxies()
            
            if proxies:
                logger.info(f"✅ 프록시 수집 성공: {len(proxies)}개")
                
                # 프록시 유효성 검증
                valid_proxies = await self.proxy_scraper.validate_proxies(proxies)
                
                if valid_proxies:
                    logger.info(f"✅ 유효한 프록시: {len(valid_proxies)}개")
                    
                    # 상위 5개 프록시를 스크래퍼에 추가
                    for proxy in valid_proxies[:5]:
                        self.scraper.add_proxy(proxy)
                        logger.info(f"프록시 추가: {proxy}")
                    
                    return True
                else:
                    logger.warning("⚠️ 유효한 프록시 없음")
                    return False
            else:
                logger.error("❌ 프록시 수집 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 프록시 수집 테스트 중 오류: {e}")
            return False

    async def test_advanced_scraping(self) -> bool:
        """고급 스크래핑 테스트"""
        try:
            logger.info("\n=== 고급 스크래핑 테스트 시작 ===")
            
            # 테스트 URL들
            test_urls = [
                "https://httpbin.org/user-agent",
                "https://httpbin.org/headers",
                "https://httpbin.org/ip",
            ]
            
            success_count = 0
            
            for url in test_urls:
                try:
                    logger.info(f"테스트 URL: {url}")
                    
                    # 페이지 내용 가져오기
                    content = await self.scraper.get_page_content(url)
                    
                    if content:
                        logger.info(f"✅ {url} - 성공")
                        success_count += 1
                        
                        # JSON 응답인 경우 파싱
                        if 'httpbin.org' in url:
                            try:
                                data = json.loads(content)
                                logger.info(f"  응답 데이터: {data}")
                            except:
                                logger.info(f"  응답 내용: {content[:100]}...")
                    else:
                        logger.warning(f"⚠️ {url} - 실패")
                        
                except Exception as e:
                    logger.error(f"❌ {url} - 오류: {e}")
                    continue
            
            logger.info(f"고급 스크래핑 테스트 결과: {success_count}/{len(test_urls)} 성공")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ 고급 스크래핑 테스트 중 오류: {e}")
            return False

    async def test_coupang_bypass(self) -> bool:
        """쿠팡 우회 테스트"""
        try:
            logger.info("\n=== 쿠팡 우회 테스트 시작 ===")
            
            # 쿠팡 상품 검색 테스트
            products = await self.coupang_service.search_products(
                keyword="무선 이어폰",
                page=1
            )
            
            if products:
                logger.info(f"✅ 쿠팡 우회 성공: {len(products)}개 상품")
                
                # 상품 정보 출력
                for i, product in enumerate(products[:3]):
                    logger.info(f"  {i+1}. {product.name}")
                    logger.info(f"     가격: {product.price:,}원")
                    logger.info(f"     판매자: {product.seller}")
                
                return True
            else:
                logger.warning("⚠️ 쿠팡 우회 실패 - 상품 없음")
                return False
                
        except Exception as e:
            logger.error(f"❌ 쿠팡 우회 테스트 중 오류: {e}")
            return False

    async def test_naver_bypass(self) -> bool:
        """네이버 우회 테스트"""
        try:
            logger.info("\n=== 네이버 우회 테스트 시작 ===")
            
            # 네이버 스마트스토어 상품 검색 테스트
            products = await self.naver_service.search_products(
                keyword="스마트워치",
                page=1
            )
            
            if products:
                logger.info(f"✅ 네이버 우회 성공: {len(products)}개 상품")
                
                # 상품 정보 출력
                for i, product in enumerate(products[:3]):
                    logger.info(f"  {i+1}. {product.name}")
                    logger.info(f"     가격: {product.price:,}원")
                    logger.info(f"     판매자: {product.seller}")
                
                return True
            else:
                logger.warning("⚠️ 네이버 우회 실패 - 상품 없음")
                return False
                
        except Exception as e:
            logger.error(f"❌ 네이버 우회 테스트 중 오류: {e}")
            return False

    async def test_rate_limit_handling(self) -> bool:
        """Rate Limit 처리 테스트"""
        try:
            logger.info("\n=== Rate Limit 처리 테스트 시작 ===")
            
            # 연속 요청으로 Rate Limit 유발 시도
            test_url = "https://httpbin.org/delay/1"
            
            success_count = 0
            total_requests = 5
            
            for i in range(total_requests):
                try:
                    logger.info(f"요청 {i+1}/{total_requests}")
                    
                    response = await self.scraper.make_request(test_url)
                    
                    if response:
                        logger.info(f"✅ 요청 {i+1} 성공")
                        success_count += 1
                    else:
                        logger.warning(f"⚠️ 요청 {i+1} 실패")
                        
                except Exception as e:
                    logger.error(f"❌ 요청 {i+1} 오류: {e}")
                    continue
            
            logger.info(f"Rate Limit 처리 테스트 결과: {success_count}/{total_requests} 성공")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Rate Limit 처리 테스트 중 오류: {e}")
            return False

    async def run_all_tests(self) -> bool:
        """모든 우회 테스트 실행"""
        try:
            logger.info("🚀 웹 스크래핑 우회 시스템 테스트 시작")
            
            test_results = []
            
            # 1. 프록시 수집 테스트
            test_results.append(await self.test_proxy_collection())
            
            # 2. 고급 스크래핑 테스트
            test_results.append(await self.test_advanced_scraping())
            
            # 3. 쿠팡 우회 테스트
            test_results.append(await self.test_coupang_bypass())
            
            # 4. 네이버 우회 테스트
            test_results.append(await self.test_naver_bypass())
            
            # 5. Rate Limit 처리 테스트
            test_results.append(await self.test_rate_limit_handling())
            
            # 결과 요약
            passed_tests = sum(test_results)
            total_tests = len(test_results)
            
            logger.info(f"\n📊 우회 테스트 결과 요약:")
            logger.info(f"  총 테스트: {total_tests}개")
            logger.info(f"  성공: {passed_tests}개")
            logger.info(f"  실패: {total_tests - passed_tests}개")
            logger.info(f"  성공률: {passed_tests/total_tests*100:.1f}%")
            
            if passed_tests == total_tests:
                logger.info("🎉 모든 우회 테스트 통과!")
                return True
            else:
                logger.warning("⚠️ 일부 테스트 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 우회 테스트 실행 중 오류: {e}")
            return False


async def main():
    """메인 함수"""
    tester = WebScrapingBypassTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("\n✅ 웹 스크래핑 우회 시스템 테스트 완료")
    else:
        logger.error("\n❌ 웹 스크래핑 우회 시스템 테스트 실패")


if __name__ == "__main__":
    asyncio.run(main())
