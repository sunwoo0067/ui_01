"""
젠트레이드 (Zentrade) API 커넥터
B2B 도매 플랫폼 젠트레이드와 연동하는 커넥터
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
from loguru import logger

from ..base import APIConnector


class ZentradeConnector(APIConnector):
    """젠트레이드 API 커넥터"""

    def __init__(self, supplier_id: str, credentials: Dict[str, Any], api_config: Dict[str, Any], **kwargs):
        """
        젠트레이드 커넥터 초기화
        
        Args:
            supplier_id: 공급사 ID
            credentials: 인증 정보 (api_key, api_secret)
            api_config: API 설정 (base_url, timeout 등)
        """
        super().__init__(supplier_id, credentials, api_config)
        self.api_key = credentials.get('api_key', '')
        self.api_secret = credentials.get('api_secret', '')
        self.base_url = api_config.get('base_url', 'https://api.zentrade.com/api/v1')
        self.timeout = api_config.get('timeout', 30)

    async def validate_credentials(self) -> bool:
        """
        API 인증 정보 검증
        
        Returns:
            bool: 인증 성공 여부
        """
        try:
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/user/profile",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        logger.info("젠트레이드 API 인증 성공")
                        return True
                    else:
                        logger.error(f"젠트레이드 API 인증 실패: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"젠트레이드 API 인증 오류: {e}")
            return False

    async def collect_products(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        젠트레이드에서 상품 목록 수집
        
        Args:
            limit: 수집할 상품 개수 (None = 전체)
            offset: 시작 위치
            filters: 필터 조건
            
        Returns:
            List[Dict]: 수집된 상품 목록
        """
        try:
            logger.info(f"젠트레이드 상품 수집 시작 (limit={limit}, offset={offset})")
            
            products = []
            page_size = 50  # 젠트레이드는 50개씩 페이징
            current_offset = offset
            collected = 0
            
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                while True:
                    # API 요청 파라미터
                    params = {
                        'limit': page_size,
                        'offset': current_offset
                    }
                    
                    # 필터 적용
                    if filters:
                        if 'category_id' in filters:
                            params['category_id'] = filters['category_id']
                        if 'min_price' in filters:
                            params['min_price'] = filters['min_price']
                        if 'max_price' in filters:
                            params['max_price'] = filters['max_price']
                        if 'in_stock' in filters:
                            params['in_stock'] = filters['in_stock']
                    
                    # API 호출
                    async with session.get(
                        f"{self.base_url}/products",
                        headers=headers,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status != 200:
                            logger.error(f"젠트레이드 API 오류: {response.status}")
                            break
                        
                        data = await response.json()
                        page_products = data.get('data', [])
                        
                        if not page_products:
                            break
                        
                        # 상품 수집
                        for product in page_products:
                            if limit and collected >= limit:
                                break
                            
                            products.append(product)
                            collected += 1
                        
                        logger.info(f"젠트레이드 offset {current_offset} 수집: {len(page_products)}개 (누적: {collected}개)")
                        
                        # 제한 도달 확인
                        if limit and collected >= limit:
                            break
                        
                        # 마지막 페이지 확인
                        if len(page_products) < page_size:
                            break
                        
                        current_offset += page_size
            
            logger.info(f"젠트레이드 상품 수집 완료: 총 {len(products)}개")
            return products
            
        except Exception as e:
            logger.error(f"젠트레이드 상품 수집 오류: {e}")
            raise

    async def transform_product(self, raw_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        젠트레이드 상품 데이터를 시스템 형식으로 변환
        
        Args:
            raw_product: 원본 상품 데이터
            
        Returns:
            Dict: 변환된 상품 데이터
        """
        try:
            # 젠트레이드 API 응답 형식에 맞춰 변환
            transformed = {
                'supplier_product_id': str(raw_product.get('product_id', '')),
                'title': raw_product.get('product_name', ''),
                'description': raw_product.get('description', ''),
                'price': float(raw_product.get('retail_price', 0)),
                'cost_price': float(raw_product.get('supply_price', 0)),
                'currency': 'KRW',
                'category': raw_product.get('category_name', ''),
                'brand': raw_product.get('brand_name', ''),
                'stock_quantity': int(raw_product.get('stock_quantity', 0)),
                'status': 'active' if raw_product.get('is_available', False) else 'inactive',
                'images': [img['url'] for img in raw_product.get('images', [])],
                'attributes': {
                    'model': raw_product.get('model_number'),
                    'manufacturer': raw_product.get('manufacturer'),
                    'origin': raw_product.get('origin_country'),
                    'specifications': raw_product.get('specifications', {})
                },
                'metadata': {
                    'supplier': 'zentrade',
                    'updated_at': raw_product.get('updated_date'),
                    'product_code': raw_product.get('product_code'),
                    'minimum_order_quantity': raw_product.get('moq', 1)
                }
            }
            
            return transformed
            
        except Exception as e:
            logger.error(f"젠트레이드 상품 변환 오류: {e}")
            raise

    async def _make_api_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        API 요청 실행
        
        Args:
            method: HTTP 메서드 (GET, POST, PUT, DELETE)
            endpoint: API 엔드포인트
            **kwargs: 추가 요청 파라미터
            
        Returns:
            Dict: API 응답 데이터
        """
        try:
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    **kwargs
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"젠트레이드 API 요청 실패: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"젠트레이드 API 요청 오류: {e}")
            return {}

    def _get_headers(self) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        return {
            'X-API-Key': self.api_key,
            'X-API-Secret': self.api_secret,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    async def get_product_detail(self, product_id: str) -> Dict[str, Any]:
        """
        상품 상세 정보 조회
        
        Args:
            product_id: 상품 ID
            
        Returns:
            Dict: 상품 상세 정보
        """
        try:
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/products/{product_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {})
                    else:
                        logger.error(f"젠트레이드 상품 조회 실패: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"젠트레이드 상품 조회 오류: {e}")
            return {}

    async def check_stock(self, product_id: str) -> int:
        """
        재고 수량 확인
        
        Args:
            product_id: 상품 ID
            
        Returns:
            int: 재고 수량
        """
        try:
            product = await self.get_product_detail(product_id)
            return int(product.get('stock_quantity', 0))
        except Exception as e:
            logger.error(f"젠트레이드 재고 확인 오류: {e}")
            return 0

    async def get_categories(self) -> List[Dict[str, Any]]:
        """
        카테고리 목록 조회
        
        Returns:
            List[Dict]: 카테고리 목록
        """
        try:
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/categories",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', [])
                    else:
                        logger.error(f"젠트레이드 카테고리 조회 실패: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"젠트레이드 카테고리 조회 오류: {e}")
            return []
