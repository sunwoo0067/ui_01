"""
제네릭 웹 크롤러
"""

from typing import List, Dict, Optional
from uuid import UUID
from loguru import logger
import asyncio
import aiohttp
from bs4 import BeautifulSoup

from ..base import WebCrawlingConnector


class GenericWebCrawler(WebCrawlingConnector):
    """범용 웹 크롤러"""

    async def collect_products(
        self, account_id: Optional[UUID] = None, start_url: str = None, **kwargs
    ) -> List[Dict]:
        """웹 페이지에서 상품 수집"""
        url = start_url or self.base_url

        if not url:
            raise ValueError("Start URL is required for web crawling")

        max_pages = kwargs.get("max_pages", 10)
        products = []

        try:
            for page in range(1, max_pages + 1):
                page_url = self._build_page_url(url, page)
                logger.info(f"Crawling page {page}: {page_url}")

                page_products = await self._crawl_page(page_url)
                products.extend(page_products)

                # 다음 페이지 확인
                if not page_products or len(page_products) == 0:
                    break

                # Rate limiting
                await asyncio.sleep(1)

            logger.info(f"Collected {len(products)} products from web crawling")

            return products

        except Exception as e:
            logger.error(f"Failed to crawl {url}: {e}")
            return products

    async def _crawl_page(self, url: str) -> List[Dict]:
        """페이지 크롤링"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as resp:
                    html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")

            # 상품 목록 선택자
            product_selector = self.selectors.get("product_list", ".product-item")
            product_elements = soup.select(product_selector)

            products = []
            for elem in product_elements:
                raw_data = self._parse_product_element(elem)
                if raw_data:
                    products.append(raw_data)

            return products

        except Exception as e:
            logger.error(f"Failed to parse page {url}: {e}")
            return []

    def _parse_product_element(self, element) -> Optional[Dict]:
        """상품 요소 파싱"""
        try:
            selectors = self.selectors

            raw_data = {}

            # 제목
            title_selector = selectors.get("title", ".product-title")
            title_elem = element.select_one(title_selector)
            raw_data["title"] = title_elem.text.strip() if title_elem else ""

            # 가격
            price_selector = selectors.get("price", ".product-price")
            price_elem = element.select_one(price_selector)
            if price_elem:
                price_text = price_elem.text.strip().replace(",", "").replace("원", "")
                try:
                    raw_data["price"] = float(price_text)
                except:
                    raw_data["price"] = 0.0

            # 이미지
            image_selector = selectors.get("image", ".product-image img")
            image_elem = element.select_one(image_selector)
            if image_elem:
                raw_data["image_url"] = image_elem.get("src") or image_elem.get(
                    "data-src"
                )

            # 링크
            link_selector = selectors.get("link", "a")
            link_elem = element.select_one(link_selector)
            if link_elem:
                raw_data["product_url"] = link_elem.get("href")

            # 기타 필드 (설정에 따라)
            for field, selector in selectors.items():
                if field not in ["product_list", "title", "price", "image", "link"]:
                    field_elem = element.select_one(selector)
                    if field_elem:
                        raw_data[field] = field_elem.text.strip()

            return raw_data if raw_data.get("title") else None

        except Exception as e:
            logger.warning(f"Failed to parse product element: {e}")
            return None

    def _build_page_url(self, base_url: str, page: int) -> str:
        """페이지 URL 생성"""
        pagination = self.pagination

        if not pagination:
            return base_url

        page_param = pagination.get("param", "page")
        page_format = pagination.get("format", "query")  # 'query' or 'path'

        if page_format == "query":
            separator = "&" if "?" in base_url else "?"
            return f"{base_url}{separator}{page_param}={page}"
        elif page_format == "path":
            return f"{base_url}/{page}"
        else:
            return base_url

    def transform_product(self, raw_data: Dict) -> Dict:
        """웹 크롤링 데이터 → 정규화된 형식"""
        return {
            "title": raw_data.get("title", ""),
            "description": raw_data.get("description", ""),
            "price": raw_data.get("price", 0.0),
            "original_price": raw_data.get("original_price"),
            "images": (
                [{"url": raw_data["image_url"], "order": 0}]
                if raw_data.get("image_url")
                else []
            ),
            "attributes": {
                "source_url": raw_data.get("product_url"),
                "brand": raw_data.get("brand"),
                "category": raw_data.get("category"),
            },
        }

    def extract_images(self, raw_data: Dict) -> List[str]:
        """이미지 URL 추출"""
        image_url = raw_data.get("image_url")
        return [image_url] if image_url else []

    def calculate_cost_price(self, raw_data: Dict) -> float:
        """원가 계산 (판매가의 60%로 추정)"""
        price = raw_data.get("price", 0)
        try:
            return float(price) * 0.6
        except:
            return 0.0

    def validate_credentials(self) -> bool:
        """웹 크롤링은 인증 불필요"""
        return True
