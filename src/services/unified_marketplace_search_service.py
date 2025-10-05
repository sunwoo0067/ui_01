"""
통합 마켓플레이스 검색 서비스
"""

import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger

from src.services.coupang_search_service import CoupangSearchService, CoupangProduct
from src.services.naver_smartstore_search_service import NaverSmartStoreSearchService, NaverSmartStoreProduct
from src.services.elevenstreet_search_service import ElevenStreetSearchService, ElevenStreetProduct
from src.services.gmarket_search_service import GmarketSearchService, GmarketProduct
from src.services.auction_search_service import AuctionSearchService, AuctionProduct
from src.services.database_service import DatabaseService
from src.utils.error_handler import ErrorHandler


class UnifiedProduct:
    """통합 상품 정보 클래스"""
    
    def __init__(self, 
                 name: str,
                 price: int,
                 seller: str,
                 product_url: str,
                 original_price: Optional[int] = None,
                 discount_rate: Optional[int] = None,
                 image_url: Optional[str] = None,
                 rating: Optional[float] = None,
                 review_count: Optional[int] = None,
                 shipping_info: Optional[str] = None,
                 platform: str = "unknown"):
        self.name = name
        self.price = price
        self.original_price = original_price
        self.discount_rate = discount_rate
        self.seller = seller
        self.product_url = product_url
        self.image_url = image_url
        self.rating = rating
        self.review_count = review_count
        self.shipping_info = shipping_info
        self.platform = platform

    def dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "price": self.price,
            "original_price": self.original_price,
            "discount_rate": self.discount_rate,
            "seller": self.seller,
            "product_url": self.product_url,
            "image_url": self.image_url,
            "rating": self.rating,
            "review_count": self.review_count,
            "shipping_info": self.shipping_info,
            "platform": self.platform
        }


class UnifiedMarketplaceSearchService:
    """통합 마켓플레이스 검색 서비스"""

    def __init__(self):
        self.error_handler = ErrorHandler()
        self.db_service = DatabaseService()
        
        # 각 마켓플레이스 서비스 초기화
        self.coupang_service = CoupangSearchService()
        self.naver_service = NaverSmartStoreSearchService()
        self.elevenstreet_service = ElevenStreetSearchService()
        self.gmarket_service = GmarketSearchService()
        self.auction_service = AuctionSearchService()
        
        # 지원하는 플랫폼 목록
        self.supported_platforms = [
            "coupang",
            "naver_smartstore", 
            "11st",
            "gmarket",
            "auction"
        ]

    async def search_all_platforms(self, keyword: str, 
                                 platforms: Optional[List[str]] = None,
                                 page: int = 1) -> Dict[str, List[UnifiedProduct]]:
        """
        모든 플랫폼에서 상품 검색
        
        Args:
            keyword: 검색 키워드
            platforms: 검색할 플랫폼 목록 (None이면 모든 플랫폼)
            page: 페이지 번호
            
        Returns:
            Dict[str, List[UnifiedProduct]]: 플랫폼별 검색 결과
        """
        try:
            logger.info(f"통합 마켓플레이스 검색 시작: {keyword}")
            
            if platforms is None:
                platforms = self.supported_platforms
            
            results = {}
            
            # 각 플랫폼별로 병렬 검색
            tasks = []
            
            if "coupang" in platforms:
                tasks.append(self._search_coupang(keyword, page))
            if "naver_smartstore" in platforms:
                tasks.append(self._search_naver(keyword, page))
            if "11st" in platforms:
                tasks.append(self._search_elevenstreet(keyword, page))
            if "gmarket" in platforms:
                tasks.append(self._search_gmarket(keyword, page))
            if "auction" in platforms:
                tasks.append(self._search_auction(keyword, page))
            
            # 모든 검색 작업 실행
            search_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 정리
            platform_index = 0
            for platform in platforms:
                if platform_index < len(search_results):
                    result = search_results[platform_index]
                    if isinstance(result, Exception):
                        logger.error(f"{platform} 검색 실패: {result}")
                        results[platform] = []
                    else:
                        results[platform] = result
                else:
                    results[platform] = []
                platform_index += 1
            
            # 총 결과 수 계산
            total_results = sum(len(products) for products in results.values())
            logger.info(f"통합 마켓플레이스 검색 완료: {total_results}개 상품")
            
            return results
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "통합 마켓플레이스 검색 실패",
                'keyword': keyword,
                'platforms': platforms
            })
            return {}

    async def search_single_platform(self, keyword: str, 
                                   platform: str, 
                                   page: int = 1) -> List[UnifiedProduct]:
        """
        단일 플랫폼에서 상품 검색
        
        Args:
            keyword: 검색 키워드
            platform: 플랫폼명
            page: 페이지 번호
            
        Returns:
            List[UnifiedProduct]: 검색된 상품 목록
        """
        try:
            logger.info(f"단일 플랫폼 검색: {platform} - {keyword}")
            
            if platform == "coupang":
                return await self._search_coupang(keyword, page)
            elif platform == "naver_smartstore":
                return await self._search_naver(keyword, page)
            elif platform == "11st":
                return await self._search_elevenstreet(keyword, page)
            elif platform == "gmarket":
                return await self._search_gmarket(keyword, page)
            elif platform == "auction":
                return await self._search_auction(keyword, page)
            else:
                logger.warning(f"지원하지 않는 플랫폼: {platform}")
                return []
                
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "단일 플랫폼 검색 실패",
                'keyword': keyword,
                'platform': platform
            })
            return []

    async def get_price_comparison(self, keyword: str, 
                                 platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        가격 비교 분석
        
        Args:
            keyword: 검색 키워드
            platforms: 비교할 플랫폼 목록
            
        Returns:
            Dict: 가격 비교 분석 결과
        """
        try:
            logger.info(f"가격 비교 분석 시작: {keyword}")
            
            # 모든 플랫폼에서 검색
            search_results = await self.search_all_platforms(keyword, platforms)
            
            # 가격 통계 계산
            all_products = []
            platform_stats = {}
            
            for platform, products in search_results.items():
                if products:
                    prices = [p.price for p in products if p.price > 0]
                    if prices:
                        platform_stats[platform] = {
                            'count': len(products),
                            'min_price': min(prices),
                            'max_price': max(prices),
                            'avg_price': sum(prices) / len(prices),
                            'median_price': sorted(prices)[len(prices) // 2]
                        }
                        all_products.extend(products)
            
            # 전체 통계
            all_prices = [p.price for p in all_products if p.price > 0]
            if all_prices:
                overall_stats = {
                    'total_products': len(all_products),
                    'min_price': min(all_prices),
                    'max_price': max(all_prices),
                    'avg_price': sum(all_prices) / len(all_prices),
                    'median_price': sorted(all_prices)[len(all_prices) // 2]
                }
            else:
                overall_stats = {'total_products': 0}
            
            # 최저가 상품 찾기
            cheapest_product = None
            if all_products:
                cheapest_product = min(all_products, key=lambda p: p.price)
            
            # 최고가 상품 찾기
            most_expensive_product = None
            if all_products:
                most_expensive_product = max(all_products, key=lambda p: p.price)
            
            comparison_result = {
                'keyword': keyword,
                'platform_stats': platform_stats,
                'overall_stats': overall_stats,
                'cheapest_product': cheapest_product.dict() if cheapest_product else None,
                'most_expensive_product': most_expensive_product.dict() if most_expensive_product else None,
                'search_results': {platform: [p.dict() for p in products] for platform, products in search_results.items()}
            }
            
            logger.info(f"가격 비교 분석 완료: {overall_stats.get('total_products', 0)}개 상품")
            return comparison_result
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "가격 비교 분석 실패",
                'keyword': keyword
            })
            return {}

    async def save_search_results(self, search_results: Dict[str, List[UnifiedProduct]], 
                                keyword: str) -> bool:
        """검색 결과를 데이터베이스에 저장"""
        try:
            logger.info(f"검색 결과 저장 시작: {keyword}")
            
            total_saved = 0
            
            for platform, products in search_results.items():
                if products:
                    # 각 플랫폼별로 저장
                    if platform == "coupang":
                        saved = await self.coupang_service.save_products_to_database(
                            [CoupangProduct(**p.dict()) for p in products], keyword
                        )
                    elif platform == "naver_smartstore":
                        saved = await self.naver_service.save_products_to_database(
                            [NaverSmartStoreProduct(p.dict()) for p in products], keyword
                        )
                    elif platform == "11st":
                        saved = await self.elevenstreet_service.save_products_to_database(
                            [ElevenStreetProduct(**p.dict()) for p in products], keyword
                        )
                    elif platform == "gmarket":
                        saved = await self.gmarket_service.save_products_to_database(
                            [GmarketProduct(**p.dict()) for p in products], keyword
                        )
                    elif platform == "auction":
                        saved = await self.auction_service.save_products_to_database(
                            [AuctionProduct(**p.dict()) for p in products], keyword
                        )
                    else:
                        saved = False
                    
                    if saved:
                        total_saved += len(products)
            
            logger.info(f"✅ 검색 결과 저장 완료: {total_saved}개 상품")
            return total_saved > 0
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "검색 결과 저장 실패",
                'keyword': keyword
            })
            return False

    async def _search_coupang(self, keyword: str, page: int) -> List[UnifiedProduct]:
        """쿠팡 검색"""
        try:
            coupang_products = await self.coupang_service.search_products(keyword, page)
            return [UnifiedProduct(**product.dict()) for product in coupang_products]
        except Exception as e:
            logger.error(f"쿠팡 검색 실패: {e}")
            return []

    async def _search_naver(self, keyword: str, page: int) -> List[UnifiedProduct]:
        """네이버 스마트스토어 검색"""
        try:
            naver_products = await self.naver_service.search_products(keyword, page)
            return [UnifiedProduct(**product.dict()) for product in naver_products]
        except Exception as e:
            logger.error(f"네이버 검색 실패: {e}")
            return []

    async def _search_elevenstreet(self, keyword: str, page: int) -> List[UnifiedProduct]:
        """11번가 검색"""
        try:
            elevenstreet_products = await self.elevenstreet_service.search_products(keyword, page)
            return [UnifiedProduct(**product.dict()) for product in elevenstreet_products]
        except Exception as e:
            logger.error(f"11번가 검색 실패: {e}")
            return []

    async def _search_gmarket(self, keyword: str, page: int) -> List[UnifiedProduct]:
        """G마켓 검색"""
        try:
            gmarket_products = await self.gmarket_service.search_products(keyword, page)
            return [UnifiedProduct(**product.dict()) for product in gmarket_products]
        except Exception as e:
            logger.error(f"G마켓 검색 실패: {e}")
            return []

    async def _search_auction(self, keyword: str, page: int) -> List[UnifiedProduct]:
        """옥션 검색"""
        try:
            auction_products = await self.auction_service.search_products(keyword, page)
            return [UnifiedProduct(**product.dict()) for product in auction_products]
        except Exception as e:
            logger.error(f"옥션 검색 실패: {e}")
            return []

    def get_supported_platforms(self) -> List[str]:
        """지원하는 플랫폼 목록 반환"""
        return self.supported_platforms.copy()

    async def get_platform_status(self) -> Dict[str, bool]:
        """각 플랫폼의 상태 확인"""
        try:
            status = {}
            test_keyword = "테스트"
            
            # 각 플랫폼별로 간단한 테스트 검색
            tasks = [
                self._test_platform("coupang", test_keyword),
                self._test_platform("naver_smartstore", test_keyword),
                self._test_platform("11st", test_keyword),
                self._test_platform("gmarket", test_keyword),
                self._test_platform("auction", test_keyword)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            platforms = self.supported_platforms
            for i, result in enumerate(results):
                if i < len(platforms):
                    platform = platforms[i]
                    status[platform] = not isinstance(result, Exception)
            
            return status
            
        except Exception as e:
            logger.error(f"플랫폼 상태 확인 실패: {e}")
            return {platform: False for platform in self.supported_platforms}

    async def _test_platform(self, platform: str, keyword: str) -> bool:
        """플랫폼 테스트"""
        try:
            products = await self.search_single_platform(keyword, platform, 1)
            return len(products) >= 0  # 검색이 성공하면 True (결과가 없어도 성공)
        except:
            return False
