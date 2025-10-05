"""
G마켓 검색 서비스
"""

import asyncio
import re
from typing import List, Optional, Dict, Any
from urllib.parse import quote, urljoin
from loguru import logger
from bs4 import BeautifulSoup

from src.config.settings import settings
from src.utils.error_handler import ErrorHandler, BaseAPIError, DatabaseError
from src.services.database_service import DatabaseService
from src.services.advanced_web_scraper import AdvancedWebScraper


class GmarketProduct:
    """G마켓 상품 정보 클래스"""
    
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
                 platform: str = "gmarket"):
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


class GmarketSearchService:
    """G마켓 상품 검색 서비스"""

    def __init__(self):
        self.settings = settings
        self.error_handler = ErrorHandler()
        self.db_service = DatabaseService()
        self.scraper = AdvancedWebScraper()
        
        # G마켓 검색 URL
        self.search_base_url = "https://browse.gmarket.co.kr/search"
        
        # 딜레이 설정 (봇 차단 방지)
        self.scraper.set_delay_range(2.0, 5.0)
        
        # 테이블명
        self.competitor_products_table = "competitor_products"
        self.price_history_table = "price_history"

    async def search_products(self, keyword: str, 
                            page: int = 1, 
                            sort: str = "scoreDesc",
                            min_price: Optional[int] = None,
                            max_price: Optional[int] = None) -> List[GmarketProduct]:
        """
        G마켓 상품 검색
        
        Args:
            keyword: 검색 키워드
            page: 페이지 번호
            sort: 정렬 방식 (scoreDesc, priceAsc, priceDesc, dateDesc)
            min_price: 최소 가격
            max_price: 최대 가격
            
        Returns:
            List[GmarketProduct]: 검색된 상품 목록
        """
        try:
            logger.info(f"G마켓 상품 검색 시작: {keyword}, 페이지: {page}")
            
            # 검색 파라미터 구성
            params = {
                'keyword': keyword,
                'pagingIndex': page,
                'sortType': sort,
                'listSize': 60,  # 한 페이지당 상품 수
            }
            
            if min_price:
                params['minPrice'] = min_price
            if max_price:
                params['maxPrice'] = max_price
            
            # URL 구성
            url = f"{self.search_base_url}?" + "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
            
            # 고급 웹 스크래핑으로 요청
            html = await self.scraper.get_page_content(url)
            if html:
                products = await self._parse_search_results(html, keyword)
                logger.info(f"G마켓 상품 검색 완료: {len(products)}개 상품")
                return products
            else:
                logger.error(f"G마켓 검색 요청 실패")
                return []
                        
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "G마켓 상품 검색 실패",
                'keyword': keyword,
                'page': page
            })
            return []

    async def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        G마켓 상품 상세 정보 조회
        
        Args:
            product_url: 상품 URL
            
        Returns:
            Dict: 상품 상세 정보
        """
        try:
            logger.info(f"G마켓 상품 상세 정보 조회: {product_url}")
            
            html = await self.scraper.get_page_content(product_url)
            if html:
                details = await self._parse_product_details(html)
                logger.info(f"G마켓 상품 상세 정보 조회 완료")
                return details
            else:
                logger.error(f"G마켓 상품 상세 조회 실패")
                return None
                        
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "G마켓 상품 상세 조회 실패",
                'product_url': product_url
            })
            return None

    async def _parse_search_results(self, html: str, keyword: str) -> List[GmarketProduct]:
        """검색 결과 파싱"""
        products = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # G마켓 상품 리스트 선택자 (실제 구조에 따라 조정 필요)
            product_items = soup.select('.box__item, .item, .product_item')
            
            for item in product_items:
                try:
                    # 상품명
                    name_elem = item.select_one('.box__item-title, .item_title, .product_name')
                    if not name_elem:
                        continue
                    name = name_elem.get_text(strip=True)
                    
                    # 가격
                    price_elem = item.select_one('.box__item-price, .item_price, .product_price')
                    if not price_elem:
                        continue
                    
                    price_text = price_elem.get_text(strip=True)
                    price = self._extract_price(price_text)
                    
                    # 원가 (할인가가 있는 경우)
                    original_price_elem = item.select_one('.box__item-original-price, .item_original_price')
                    original_price = None
                    if original_price_elem:
                        original_price_text = original_price_elem.get_text(strip=True)
                        original_price = self._extract_price(original_price_text)
                    
                    # 할인율
                    discount_elem = item.select_one('.box__item-discount, .item_discount')
                    discount_rate = None
                    if discount_elem:
                        discount_text = discount_elem.get_text(strip=True)
                        discount_rate = self._extract_discount_rate(discount_text)
                    
                    # 판매자
                    seller_elem = item.select_one('.box__item-seller, .item_seller, .product_seller')
                    seller = seller_elem.get_text(strip=True) if seller_elem else "G마켓"
                    
                    # 상품 URL
                    link_elem = item.select_one('a')
                    product_url = ""
                    if link_elem:
                        href = link_elem.get('href', '')
                        if href:
                            product_url = urljoin("https://www.gmarket.co.kr", href)
                    
                    # 이미지 URL
                    img_elem = item.select_one('img')
                    image_url = None
                    if img_elem:
                        image_url = img_elem.get('src') or img_elem.get('data-src')
                        if image_url:
                            image_url = urljoin("https://www.gmarket.co.kr", image_url)
                    
                    # 평점
                    rating_elem = item.select_one('.box__item-rating, .item_rating, .product_rating')
                    rating = None
                    if rating_elem:
                        rating_text = rating_elem.get_text(strip=True)
                        rating = self._extract_rating(rating_text)
                    
                    # 리뷰 수
                    review_elem = item.select_one('.box__item-review-count, .item_review_count')
                    review_count = None
                    if review_elem:
                        review_text = review_elem.get_text(strip=True)
                        review_count = self._extract_review_count(review_text)
                    
                    # 배송 정보
                    shipping_elem = item.select_one('.box__item-shipping, .item_shipping')
                    shipping_info = None
                    if shipping_elem:
                        shipping_info = shipping_elem.get_text(strip=True)
                    
                    product = GmarketProduct(
                        name=name,
                        price=price,
                        original_price=original_price,
                        discount_rate=discount_rate,
                        seller=seller,
                        product_url=product_url,
                        image_url=image_url,
                        rating=rating,
                        review_count=review_count,
                        shipping_info=shipping_info
                    )
                    
                    products.append(product)
                    
                except Exception as e:
                    logger.warning(f"상품 파싱 중 오류: {e}")
                    continue
            
            logger.info(f"G마켓 검색 결과 파싱 완료: {len(products)}개 상품")
            return products
            
        except Exception as e:
            logger.error(f"G마켓 검색 결과 파싱 실패: {e}")
            return []

    async def _parse_product_details(self, html: str) -> Dict[str, Any]:
        """상품 상세 정보 파싱"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            details = {}
            
            # 상품명
            name_elem = soup.select_one('.product_title, .item_title')
            if name_elem:
                details['name'] = name_elem.get_text(strip=True)
            
            # 가격
            price_elem = soup.select_one('.price, .product_price')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                details['price'] = self._extract_price(price_text)
            
            # 상품 설명
            desc_elem = soup.select_one('.product_description, .item_description')
            if desc_elem:
                details['description'] = desc_elem.get_text(strip=True)
            
            # 상품 이미지들
            img_elements = soup.select('.product_image img, .item_image img')
            images = []
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src:
                    images.append(urljoin("https://www.gmarket.co.kr", src))
            details['images'] = images
            
            # 상품 옵션
            options_elem = soup.select_one('.product_options, .item_options')
            if options_elem:
                details['options'] = options_elem.get_text(strip=True)
            
            return details
            
        except Exception as e:
            logger.error(f"G마켓 상품 상세 정보 파싱 실패: {e}")
            return {}

    def _extract_price(self, price_text: str) -> int:
        """가격 텍스트에서 숫자 추출"""
        try:
            # 숫자와 콤마만 추출
            price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
            if price_match:
                return int(price_match.group().replace(',', ''))
            return 0
        except:
            return 0

    def _extract_discount_rate(self, discount_text: str) -> Optional[int]:
        """할인율 텍스트에서 숫자 추출"""
        try:
            discount_match = re.search(r'(\d+)%', discount_text)
            if discount_match:
                return int(discount_match.group(1))
            return None
        except:
            return None

    def _extract_rating(self, rating_text: str) -> Optional[float]:
        """평점 텍스트에서 숫자 추출"""
        try:
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                return float(rating_match.group(1))
            return None
        except:
            return None

    def _extract_review_count(self, review_text: str) -> Optional[int]:
        """리뷰 수 텍스트에서 숫자 추출"""
        try:
            review_match = re.search(r'(\d+)', review_text)
            if review_match:
                return int(review_match.group(1))
            return None
        except:
            return None

    async def save_products_to_database(self, products: List[GmarketProduct], keyword: str) -> bool:
        """상품 정보를 데이터베이스에 저장"""
        try:
            logger.info(f"G마켓 상품 {len(products)}개를 데이터베이스에 저장")
            
            for product in products:
                product_data = {
                    'platform': 'gmarket',
                    'search_keyword': keyword,
                    'product_name': product.name,
                    'price': product.price,
                    'original_price': product.original_price,
                    'discount_rate': product.discount_rate,
                    'seller': product.seller,
                    'product_url': product.product_url,
                    'image_url': product.image_url,
                    'rating': product.rating,
                    'review_count': product.review_count,
                    'shipping_info': product.shipping_info,
                    'is_active': True,
                    'collected_at': 'now()'
                }
                
                await self.db_service.insert_data(self.competitor_products_table, product_data)
            
            logger.info(f"✅ G마켓 상품 저장 완료: {len(products)}개")
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "G마켓 상품 데이터베이스 저장 실패",
                'keyword': keyword,
                'product_count': len(products)
            })
            return False
