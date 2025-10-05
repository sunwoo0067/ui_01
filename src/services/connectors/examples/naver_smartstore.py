"""
네이버 스마트스토어 API 커넥터 예시
"""

import aiohttp
from typing import List, Dict, Optional
from uuid import UUID
from loguru import logger

from ..base import APIConnector


class NaverSmartstoreConnector(APIConnector):
    """네이버 스마트스토어 API 커넥터"""

    def __init__(self, supplier_id: UUID, credentials: Dict, api_config: Dict):
        super().__init__(supplier_id, credentials, api_config)

        # 네이버 API 인증
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")

    async def _make_api_request(
        self, endpoint: str, method: str = "GET", params: Dict = None
    ) -> Dict:
        """네이버 API 요청"""
        url = f"{self.api_endpoint}{endpoint}"
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, headers=headers, params=params) as resp:
                    return await resp.json()
            elif method == "POST":
                async with session.post(url, headers=headers, json=params) as resp:
                    return await resp.json()

    async def collect_products(
        self, account_id: Optional[UUID] = None, **kwargs
    ) -> List[Dict]:
        """네이버 스마트스토어 상품 수집"""
        category_id = kwargs.get("category_id")
        page = kwargs.get("page", 1)
        size = kwargs.get("size", 100)

        params = {"categoryId": category_id, "page": page, "size": size}

        try:
            response = await self._make_api_request("/products", params=params)

            products = response.get("products", [])
            logger.info(f"Collected {len(products)} products from Naver Smartstore")

            return products

        except Exception as e:
            logger.error(f"Failed to collect products from Naver: {e}")
            return []

    def transform_product(self, raw_data: Dict) -> Dict:
        """네이버 데이터 → 정규화된 형식"""
        return {
            "title": raw_data.get("name"),
            "description": raw_data.get("description"),
            "price": float(raw_data.get("salePrice", 0)),
            "original_price": float(raw_data.get("originalPrice", 0)),
            "stock_quantity": int(raw_data.get("stockQuantity", 0)),
            "category": raw_data.get("categoryName"),
            "brand": raw_data.get("brandName"),
            "images": [
                {"url": img.get("url"), "order": idx}
                for idx, img in enumerate(raw_data.get("images", []))
            ],
            "attributes": {
                "sku": raw_data.get("productCode"),
                "barcode": raw_data.get("barcode"),
                "manufacturer": raw_data.get("manufacturer"),
            },
        }

    def extract_images(self, raw_data: Dict) -> List[str]:
        """이미지 URL 추출"""
        images = raw_data.get("images", [])
        return [img.get("url") for img in images if img.get("url")]

    def calculate_cost_price(self, raw_data: Dict) -> float:
        """원가 계산 (API에서 제공하는 경우)"""
        return float(raw_data.get("supplyPrice", raw_data.get("salePrice", 0)))

    def validate_credentials(self) -> bool:
        """인증 정보 검증"""
        if not self.client_id or not self.client_secret:
            return False

        try:
            # 테스트 API 호출
            import asyncio

            response = asyncio.run(self._make_api_request("/test"))
            return response.get("status") == "ok"
        except:
            return False
