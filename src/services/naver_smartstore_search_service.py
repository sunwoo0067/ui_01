"""
네이버 스마트스토어 상품 검색 및 분석 시스템
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
import asyncio
import aiohttp
import json
import re
from urllib.parse import quote, urljoin
from loguru import logger
from bs4 import BeautifulSoup

from src.config.settings import settings
from src.utils.error_handler import ErrorHandler, BaseAPIError, DatabaseError
from src.services.database_service import DatabaseService


class NaverSmartStoreProduct:
    """네이버 스마트스토어 상품 정보 클래스"""
    
    def __init__(self, data: Dict[str, Any]):
        self.product_id = data.get('product_id', '')
        self.name = data.get('name', '')
        self.price = data.get('price', 0)
        self.original_price = data.get('original_price', 0)
        self.discount_rate = data.get('discount_rate', 0)
        self.seller = data.get('seller', '')
        self.shop_name = data.get('shop_name', '')
        self.rating = data.get('rating', 0.0)
        self.review_count = data.get('review_count', 0)
        self.image_url = data.get('image_url', '')
        self.product_url = data.get('product_url', '')
        self.category = data.get('category', '')
        self.brand = data.get('brand', '')
        self.collected_at = data.get('collected_at', datetime.now(timezone.utc).isoformat())


class NaverSmartStoreSearchService:
    """네이버 스마트스토어 상품 검색 서비스"""

    def __init__(self):
        self.settings = settings
        self.error_handler = ErrorHandler()
        self.db_service = DatabaseService()
        
        # 네이버 쇼핑 검색 URL
        self.search_base_url = "https://search.shopping.naver.com/search/all"
        
        # 헤더 설정
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 테이블명
        self.competitor_products_table = "competitor_products"
        self.price_history_table = "price_history"

    async def search_products(self, keyword: str, 
                            page: int = 1, 
                            sort: str = "rel",
                            min_price: Optional[int] = None,
                            max_price: Optional[int] = None) -> List[NaverSmartStoreProduct]:
        """
        네이버 스마트스토어에서 상품 검색
        
        Args:
            keyword: 검색 키워드
            page: 페이지 번호 (1부터 시작)
            sort: 정렬 방식 (rel, price, review, date)
            min_price: 최소 가격
            max_price: 최대 가격
            
        Returns:
            List[NaverSmartStoreProduct]: 검색된 상품 목록
        """
        try:
            logger.info(f"네이버 스마트스토어 상품 검색 시작: {keyword}, 페이지: {page}")
            
            # 검색 파라미터 구성
            params = {
                'query': keyword,
                'pagingIndex': page,
                'pagingSize': 40,  # 한 페이지당 상품 수
                'sort': sort,
            }
            
            if min_price:
                params['minPrice'] = min_price
            if max_price:
                params['maxPrice'] = max_price
            
            # URL 구성
            url = f"{self.search_base_url}?" + "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
            
            # HTTP 요청
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        products = await self._parse_search_results(html, keyword)
                        logger.info(f"네이버 스마트스토어 상품 검색 완료: {len(products)}개 상품")
                        return products
                    else:
                        logger.error(f"네이버 검색 요청 실패: {response.status}")
                        return []
                        
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "네이버 스마트스토어 상품 검색 실패",
                'keyword': keyword,
                'page': page
            })
            return []

    async def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        상품 상세 정보 조회
        
        Args:
            product_url: 상품 URL
            
        Returns:
            Dict: 상품 상세 정보
        """
        try:
            logger.info(f"네이버 스마트스토어 상품 상세 정보 조회: {product_url}")
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(product_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        details = await self._parse_product_details(html)
                        logger.info(f"네이버 스마트스토어 상품 상세 정보 조회 완료")
                        return details
                    else:
                        logger.error(f"네이버 상품 상세 조회 실패: {response.status}")
                        return None
                        
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "네이버 스마트스토어 상품 상세 조회 실패",
                'product_url': product_url
            })
            return None

    async def save_competitor_products(self, products: List[NaverSmartStoreProduct], 
                                     search_keyword: str) -> int:
        """
        경쟁사 상품 정보를 데이터베이스에 저장
        
        Args:
            products: 상품 목록
            search_keyword: 검색 키워드
            
        Returns:
            int: 저장된 상품 수
        """
        try:
            logger.info(f"네이버 스마트스토어 경쟁사 상품 정보 저장 시작: {len(products)}개")
            
            saved_count = 0
            for product in products:
                try:
                    # 상품 데이터 구성
                    product_data = {
                        "platform": "naver_smartstore",
                        "product_id": product.product_id,
                        "name": product.name,
                        "price": product.price,
                        "original_price": product.original_price,
                        "discount_rate": product.discount_rate,
                        "seller": product.seller,
                        "rating": product.rating,
                        "review_count": product.review_count,
                        "image_url": product.image_url,
                        "product_url": product.product_url,
                        "category": product.category,
                        "brand": product.brand,
                        "search_keyword": search_keyword,
                        "collected_at": product.collected_at,
                        "is_active": True
                    }
                    
                    # 기존 상품 확인
                    existing = await self.db_service.select_data(
                        self.competitor_products_table,
                        {"platform": "naver_smartstore", "product_id": product.product_id}
                    )
                    
                    if existing:
                        # 가격 변동 확인
                        old_price = existing[0]["price"]
                        if old_price != product.price:
                            # 가격 변동 로그 저장
                            await self._save_price_history(
                                product.product_id, 
                                old_price, 
                                product.price
                            )
                        
                        # 상품 정보 업데이트
                        await self.db_service.update_data(
                            self.competitor_products_table,
                            {"platform": "naver_smartstore", "product_id": product.product_id},
                            product_data
                        )
                        logger.debug(f"네이버 스마트스토어 경쟁사 상품 정보 업데이트: {product.product_id}")
                    else:
                        # 새 상품 삽입
                        await self.db_service.insert_data(
                            self.competitor_products_table, 
                            product_data
                        )
                        logger.debug(f"네이버 스마트스토어 경쟁사 상품 정보 삽입: {product.product_id}")
                    
                    saved_count += 1
                    
                except Exception as e:
                    self.error_handler.log_error(e, {
                        'operation': "네이버 스마트스토어 경쟁사 상품 저장 실패",
                        'product_id': product.product_id
                    })
                    continue
            
            logger.info(f"네이버 스마트스토어 경쟁사 상품 정보 저장 완료: {saved_count}개")
            return saved_count
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "네이버 스마트스토어 경쟁사 상품 정보 저장 실패"
            })
            return 0

    async def analyze_competitor_trends(self, keyword: str, days: int = 7) -> Dict[str, Any]:
        """
        경쟁사 동향 분석
        
        Args:
            keyword: 분석 키워드
            days: 분석 기간 (일)
            
        Returns:
            Dict: 분석 결과
        """
        try:
            logger.info(f"네이버 스마트스토어 경쟁사 동향 분석 시작: {keyword}")
            
            from datetime import timedelta
            
            # 분석 기간 설정
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # 해당 키워드의 상품들 조회
            products = await self.db_service.select_data(
                self.competitor_products_table,
                {
                    "platform": "naver_smartstore",
                    "search_keyword": keyword,
                    "collected_at__gte": start_date.isoformat(),
                    "is_active": True
                }
            )
            
            if not products:
                return {
                    "keyword": keyword,
                    "analysis_period": f"{days}일",
                    "total_products": 0,
                    "analysis_data": {}
                }
            
            # 분석 데이터 구성
            analysis_data = {
                "total_products": len(products),
                "price_statistics": self._calculate_price_statistics(products),
                "seller_analysis": self._analyze_sellers(products),
                "category_analysis": self._analyze_categories(products),
                "rating_analysis": self._analyze_ratings(products),
                "trend_analysis": await self._analyze_trends(products, keyword, days)
            }
            
            # 분석 결과 저장
            analysis_result = {
                "analysis_type": "market_trend",
                "target_keyword": keyword,
                "platform": "naver_smartstore",
                "analysis_data": analysis_data,
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db_service.insert_data("competitor_analysis", analysis_result)
            
            logger.info(f"네이버 스마트스토어 경쟁사 동향 분석 완료: {keyword}")
            
            return {
                "keyword": keyword,
                "analysis_period": f"{days}일",
                "total_products": len(products),
                "analysis_data": analysis_data
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "네이버 스마트스토어 경쟁사 동향 분석 실패",
                'keyword': keyword
            })
            return {}

    async def _parse_search_results(self, html: str, keyword: str) -> List[NaverSmartStoreProduct]:
        """검색 결과 HTML 파싱"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            products = []
            
            # 상품 리스트 찾기
            product_list = soup.find('div', class_='product_list')
            if not product_list:
                logger.warning("네이버 상품 리스트를 찾을 수 없음")
                return products
            
            # 각 상품 파싱
            for item in product_list.find_all('div', class_='product_item'):
                try:
                    product_data = await self._parse_single_product(item)
                    if product_data:
                        products.append(NaverSmartStoreProduct(product_data))
                except Exception as e:
                    logger.debug(f"네이버 상품 파싱 실패: {e}")
                    continue
            
            return products
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "네이버 검색 결과 파싱 실패",
                'keyword': keyword
            })
            return []

    async def _parse_single_product(self, item) -> Optional[Dict[str, Any]]:
        """단일 상품 정보 파싱"""
        try:
            # 상품 ID 추출
            product_id = ""
            product_link = item.find('a', class_='product_link')
            if product_link:
                href = product_link.get('href', '')
                product_id_match = re.search(r'product/(\d+)', href)
                if product_id_match:
                    product_id = product_id_match.group(1)
            
            # 상품명 추출
            name_element = item.find('span', class_='product_title')
            name = name_element.get_text(strip=True) if name_element else ""
            
            # 가격 추출
            price_element = item.find('span', class_='price')
            price = 0
            if price_element:
                price_text = price_element.get_text(strip=True).replace(',', '')
                price_match = re.search(r'(\d+)', price_text)
                if price_match:
                    price = int(price_match.group(1))
            
            # 원가 추출
            original_price_element = item.find('span', class_='original_price')
            original_price = price
            if original_price_element:
                original_price_text = original_price_element.get_text(strip=True).replace(',', '')
                original_price_match = re.search(r'(\d+)', original_price_text)
                if original_price_match:
                    original_price = int(original_price_match.group(1))
            
            # 할인율 계산
            discount_rate = 0
            if original_price > price:
                discount_rate = int((1 - price / original_price) * 100)
            
            # 판매자 정보 추출
            seller_element = item.find('span', class_='seller')
            seller = seller_element.get_text(strip=True) if seller_element else ""
            
            shop_element = item.find('span', class_='shop_name')
            shop_name = shop_element.get_text(strip=True) if shop_element else ""
            
            # 평점 추출
            rating_element = item.find('span', class_='rating')
            rating = 0.0
            if rating_element:
                rating_text = rating_element.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # 리뷰 수 추출
            review_element = item.find('span', class_='review_count')
            review_count = 0
            if review_element:
                review_text = review_element.get_text(strip=True)
                review_match = re.search(r'(\d+)', review_text)
                if review_match:
                    review_count = int(review_match.group(1))
            
            # 이미지 URL 추출
            image_element = item.find('img', class_='product_image')
            image_url = ""
            if image_element:
                image_url = image_element.get('src', '')
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
            
            # 상품 URL 구성
            product_url = ""
            if product_link:
                href = product_link.get('href', '')
                if href.startswith('/'):
                    product_url = f"https://shopping.naver.com{href}"
                else:
                    product_url = href
            
            return {
                'product_id': product_id,
                'name': name,
                'price': price,
                'original_price': original_price,
                'discount_rate': discount_rate,
                'seller': seller,
                'shop_name': shop_name,
                'rating': rating,
                'review_count': review_count,
                'image_url': image_url,
                'product_url': product_url,
                'category': '',
                'brand': '',
                'collected_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.debug(f"네이버 단일 상품 파싱 실패: {e}")
            return None

    async def _parse_product_details(self, html: str) -> Optional[Dict[str, Any]]:
        """상품 상세 정보 파싱"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 카테고리 추출
            category = ""
            breadcrumb = soup.find('nav', class_='breadcrumb')
            if breadcrumb:
                category_links = breadcrumb.find_all('a')
                if len(category_links) > 1:
                    category = category_links[-1].get_text(strip=True)
            
            # 브랜드 추출
            brand = ""
            brand_element = soup.find('span', class_='brand')
            if brand_element:
                brand = brand_element.get_text(strip=True)
            
            return {
                'category': category,
                'brand': brand
            }
            
        except Exception as e:
            logger.debug(f"네이버 상품 상세 정보 파싱 실패: {e}")
            return None

    def _calculate_price_statistics(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """가격 통계 계산"""
        prices = [p['price'] for p in products if p['price'] > 0]
        
        if not prices:
            return {}
        
        return {
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": sum(prices) / len(prices),
            "median_price": sorted(prices)[len(prices) // 2]
        }

    def _analyze_sellers(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """판매자 분석"""
        seller_counts = {}
        for product in products:
            seller = product.get('seller', 'Unknown')
            seller_counts[seller] = seller_counts.get(seller, 0) + 1
        
        # 상위 판매자
        top_sellers = sorted(seller_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_sellers": len(seller_counts),
            "top_sellers": top_sellers
        }

    def _analyze_categories(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """카테고리 분석"""
        category_counts = {}
        for product in products:
            category = product.get('category', 'Unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 상위 카테고리
        top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_categories": len(category_counts),
            "top_categories": top_categories
        }

    def _analyze_ratings(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """평점 분석"""
        ratings = [p['rating'] for p in products if p['rating'] > 0]
        
        if not ratings:
            return {}
        
        return {
            "avg_rating": sum(ratings) / len(ratings),
            "min_rating": min(ratings),
            "max_rating": max(ratings),
            "high_rated_products": len([r for r in ratings if r >= 4.0])
        }

    async def _analyze_trends(self, products: List[Dict[str, Any]], keyword: str, days: int) -> Dict[str, Any]:
        """동향 분석"""
        # 최근 가격 변동 분석
        recent_price_changes = await self.db_service.select_data(
            self.price_history_table,
            {
                "platform": "naver_smartstore",
                "timestamp__gte": (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            }
        )
        
        return {
            "price_changes_count": len(recent_price_changes) if recent_price_changes else 0,
            "trend_period": f"{days}일"
        }

    async def _save_price_history(self, product_id: str, old_price: int, new_price: int) -> None:
        """가격 변동 이력 저장"""
        try:
            price_history_data = {
                "product_id": product_id,
                "platform": "naver_smartstore",
                "old_price": old_price,
                "new_price": new_price,
                "price_change": new_price - old_price,
                "price_change_rate": ((new_price - old_price) / old_price * 100) if old_price > 0 else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db_service.insert_data(self.price_history_table, price_history_data)
            logger.debug(f"네이버 가격 변동 이력 저장: {product_id} - {old_price} → {new_price}")
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "네이버 가격 변동 이력 저장 실패",
                'product_id': product_id
            })


# 전역 인스턴스
naver_smartstore_search_service = NaverSmartStoreSearchService()
