"""
쿠팡 상품 검색 및 가격 모니터링 시스템
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


class CoupangProduct:
    """쿠팡 상품 정보 클래스"""
    
    def __init__(self, data: Dict[str, Any]):
        self.product_id = data.get('product_id', '')
        self.name = data.get('name', '')
        self.price = data.get('price', 0)
        self.original_price = data.get('original_price', 0)
        self.discount_rate = data.get('discount_rate', 0)
        self.seller = data.get('seller', '')
        self.rating = data.get('rating', 0.0)
        self.review_count = data.get('review_count', 0)
        self.image_url = data.get('image_url', '')
        self.product_url = data.get('product_url', '')
        self.category = data.get('category', '')
        self.brand = data.get('brand', '')
        self.collected_at = data.get('collected_at', datetime.now(timezone.utc).isoformat())


class CoupangSearchService:
    """쿠팡 상품 검색 서비스"""

    def __init__(self):
        self.settings = settings
        self.error_handler = ErrorHandler()
        self.db_service = DatabaseService()
        
        # 쿠팡 검색 URL
        self.search_base_url = "https://www.coupang.com/np/search"
        
        # 헤더 설정 (봇 차단 방지)
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
                            sort: str = "scoreDesc",
                            min_price: Optional[int] = None,
                            max_price: Optional[int] = None) -> List[CoupangProduct]:
        """
        쿠팡에서 상품 검색
        
        Args:
            keyword: 검색 키워드
            page: 페이지 번호 (1부터 시작)
            sort: 정렬 방식 (scoreDesc, priceAsc, priceDesc, reviewDesc, saleDesc)
            min_price: 최소 가격
            max_price: 최대 가격
            
        Returns:
            List[CoupangProduct]: 검색된 상품 목록
        """
        try:
            logger.info(f"쿠팡 상품 검색 시작: {keyword}, 페이지: {page}")
            
            # 검색 파라미터 구성
            params = {
                'q': keyword,
                'page': page,
                'sort': sort,
                'listSize': 60,  # 한 페이지당 상품 수
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
                        logger.info(f"쿠팡 상품 검색 완료: {len(products)}개 상품")
                        return products
                    else:
                        logger.error(f"쿠팡 검색 요청 실패: {response.status}")
                        return []
                        
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "쿠팡 상품 검색 실패",
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
            logger.info(f"쿠팡 상품 상세 정보 조회: {product_url}")
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(product_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        details = await self._parse_product_details(html)
                        logger.info(f"쿠팡 상품 상세 정보 조회 완료")
                        return details
                    else:
                        logger.error(f"쿠팡 상품 상세 조회 실패: {response.status}")
                        return None
                        
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "쿠팡 상품 상세 조회 실패",
                'product_url': product_url
            })
            return None

    async def save_competitor_products(self, products: List[CoupangProduct], 
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
            logger.info(f"경쟁사 상품 정보 저장 시작: {len(products)}개")
            
            saved_count = 0
            for product in products:
                try:
                    # 상품 데이터 구성
                    product_data = {
                        "platform": "coupang",
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
                        {"platform": "coupang", "product_id": product.product_id}
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
                            {"platform": "coupang", "product_id": product.product_id},
                            product_data
                        )
                        logger.debug(f"경쟁사 상품 정보 업데이트: {product.product_id}")
                    else:
                        # 새 상품 삽입
                        await self.db_service.insert_data(
                            self.competitor_products_table, 
                            product_data
                        )
                        logger.debug(f"경쟁사 상품 정보 삽입: {product.product_id}")
                    
                    saved_count += 1
                    
                except Exception as e:
                    self.error_handler.log_error(e, {
                        'operation': "경쟁사 상품 저장 실패",
                        'product_id': product.product_id
                    })
                    continue
            
            logger.info(f"경쟁사 상품 정보 저장 완료: {saved_count}개")
            return saved_count
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "경쟁사 상품 정보 저장 실패"
            })
            return 0

    async def get_price_history(self, product_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        상품 가격 변동 이력 조회
        
        Args:
            product_id: 상품 ID
            days: 조회 기간 (일)
            
        Returns:
            List[Dict]: 가격 변동 이력
        """
        try:
            from datetime import timedelta
            
            # 조회 기간 설정
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            price_history = await self.db_service.select_data(
                self.price_history_table,
                {
                    "product_id": product_id,
                    "timestamp__gte": start_date.isoformat()
                },
                order_by="timestamp ASC"
            )
            
            return price_history or []
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "가격 변동 이력 조회 실패",
                'product_id': product_id
            })
            return []

    async def _parse_search_results(self, html: str, keyword: str) -> List[CoupangProduct]:
        """검색 결과 HTML 파싱"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            products = []
            
            # 상품 리스트 찾기
            product_list = soup.find('ul', class_='search-product-list')
            if not product_list:
                logger.warning("상품 리스트를 찾을 수 없음")
                return products
            
            # 각 상품 파싱
            for item in product_list.find_all('li', class_='search-product'):
                try:
                    product_data = await self._parse_single_product(item)
                    if product_data:
                        products.append(CoupangProduct(product_data))
                except Exception as e:
                    logger.debug(f"상품 파싱 실패: {e}")
                    continue
            
            return products
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "검색 결과 파싱 실패",
                'keyword': keyword
            })
            return []

    async def _parse_single_product(self, item) -> Optional[Dict[str, Any]]:
        """단일 상품 정보 파싱"""
        try:
            # 상품 ID 추출
            product_id = ""
            product_link = item.find('a', class_='search-product-link')
            if product_link:
                href = product_link.get('href', '')
                product_id_match = re.search(r'/products/(\d+)', href)
                if product_id_match:
                    product_id = product_id_match.group(1)
            
            # 상품명 추출
            name_element = item.find('div', class_='name')
            name = name_element.get_text(strip=True) if name_element else ""
            
            # 가격 추출
            price_element = item.find('strong', class_='price-value')
            price = 0
            if price_element:
                price_text = price_element.get_text(strip=True).replace(',', '')
                price_match = re.search(r'(\d+)', price_text)
                if price_match:
                    price = int(price_match.group(1))
            
            # 원가 추출
            original_price_element = item.find('span', class_='original-price')
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
            
            # 판매자 추출
            seller_element = item.find('span', class_='seller')
            seller = seller_element.get_text(strip=True) if seller_element else ""
            
            # 평점 추출
            rating_element = item.find('em', class_='rating')
            rating = 0.0
            if rating_element:
                rating_text = rating_element.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # 리뷰 수 추출
            review_element = item.find('span', class_='rating-total-count')
            review_count = 0
            if review_element:
                review_text = review_element.get_text(strip=True)
                review_match = re.search(r'(\d+)', review_text)
                if review_match:
                    review_count = int(review_match.group(1))
            
            # 이미지 URL 추출
            image_element = item.find('img', class_='search-product-wrap-img')
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
                    product_url = f"https://www.coupang.com{href}"
                else:
                    product_url = href
            
            return {
                'product_id': product_id,
                'name': name,
                'price': price,
                'original_price': original_price,
                'discount_rate': discount_rate,
                'seller': seller,
                'rating': rating,
                'review_count': review_count,
                'image_url': image_url,
                'product_url': product_url,
                'category': '',
                'brand': '',
                'collected_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.debug(f"단일 상품 파싱 실패: {e}")
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
            logger.debug(f"상품 상세 정보 파싱 실패: {e}")
            return None

    async def _save_price_history(self, product_id: str, old_price: int, new_price: int) -> None:
        """가격 변동 이력 저장"""
        try:
            price_history_data = {
                "product_id": product_id,
                "platform": "coupang",
                "old_price": old_price,
                "new_price": new_price,
                "price_change": new_price - old_price,
                "price_change_rate": ((new_price - old_price) / old_price * 100) if old_price > 0 else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db_service.insert_data(self.price_history_table, price_history_data)
            logger.debug(f"가격 변동 이력 저장: {product_id} - {old_price} → {new_price}")
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "가격 변동 이력 저장 실패",
                'product_id': product_id
            })


# 전역 인스턴스
coupang_search_service = CoupangSearchService()
