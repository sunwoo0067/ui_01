"""
도매매 (DomaeMae) API 커넥터
도매 전문 플랫폼 도매매와 연동하는 커넥터
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
from loguru import logger

from ..base import APIConnector


class DomaeMaeConnector(APIConnector):
    """도매매 API 커넥터"""

    def __init__(self, supplier_id: str, credentials: Dict[str, Any], api_config: Dict[str, Any], **kwargs):
        """
        도매매 커넥터 초기화
        
        Args:
            supplier_id: 공급사 ID
            credentials: 인증 정보 (api_key, api_secret, seller_id)
            api_config: API 설정 (base_url, timeout 등)
        """
        super().__init__(supplier_id, credentials, api_config)
        self.api_key = credentials.get('api_key', '')
        self.seller_id = credentials.get('seller_id', '')
        self.base_url = api_config.get('base_url', 'https://api.dodomall.com/v2')
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
                    f"{self.base_url}/seller/info",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        logger.info("도매매 API 인증 성공")
                        return True
                    else:
                        logger.error(f"도매매 API 인증 실패: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"도매매 API 인증 오류: {e}")
            return False

    async def collect_products(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        도매매에서 상품 목록 수집
        
        Args:
            limit: 수집할 상품 개수 (None = 전체)
            offset: 시작 위치
            filters: 필터 조건
            
        Returns:
            List[Dict]: 수집된 상품 목록
        """
        try:
            logger.info(f"도매매 상품 수집 시작 (limit={limit}, offset={offset})")
            
            products = []
            page = offset // 200 + 1  # 200개씩 페이징
            collected = 0
            
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                while True:
                    # API 요청 파라미터
                    params = {
                        'page': page,
                        'size': 200,
                        'seller_id': self.seller_id
                    }
                    
                    # 필터 적용
                    if filters:
                        if 'category_code' in filters:
                            params['category_code'] = filters['category_code']
                        if 'price_from' in filters:
                            params['price_from'] = filters['price_from']
                        if 'price_to' in filters:
                            params['price_to'] = filters['price_to']
                        if 'stock_available' in filters:
                            params['stock_available'] = filters['stock_available']
                    
                    # API 호출
                    async with session.get(
                        f"{self.base_url}/products/list",
                        headers=headers,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status != 200:
                            logger.error(f"도매매 API 오류: {response.status}")
                            break
                        
                        data = await response.json()
                        
                        if data.get('code') != '200':
                            logger.error(f"도매매 API 응답 오류: {data.get('message')}")
                            break
                        
                        page_products = data.get('result', {}).get('items', [])
                        
                        if not page_products:
                            break
                        
                        # 상품 수집
                        for product in page_products:
                            if limit and collected >= limit:
                                break
                            
                            products.append(product)
                            collected += 1
                        
                        logger.info(f"도매매 페이지 {page} 수집: {len(page_products)}개 (누적: {collected}개)")
                        
                        # 제한 도달 확인
                        if limit and collected >= limit:
                            break
                        
                        # 마지막 페이지 확인
                        total_count = data.get('result', {}).get('total_count', 0)
                        if collected >= total_count:
                            break
                        
                        page += 1
            
            logger.info(f"도매매 상품 수집 완료: 총 {len(products)}개")
            return products
            
        except Exception as e:
            logger.error(f"도매매 상품 수집 오류: {e}")
            raise

    async def transform_product(self, raw_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        도매매 상품 데이터를 시스템 형식으로 변환
        
        Args:
            raw_product: 원본 상품 데이터
            
        Returns:
            Dict: 변환된 상품 데이터
        """
        try:
            # 도매매 API 응답 형식에 맞춰 변환
            transformed = {
                'supplier_product_id': str(raw_product.get('goods_no', '')),
                'title': raw_product.get('goods_name', ''),
                'description': raw_product.get('goods_desc', ''),
                'price': float(raw_product.get('sale_price', 0)),
                'cost_price': float(raw_product.get('supply_price', 0)),
                'currency': 'KRW',
                'category': raw_product.get('category_name', ''),
                'brand': raw_product.get('brand', ''),
                'stock_quantity': int(raw_product.get('stock_qty', 0)),
                'status': 'active' if raw_product.get('sale_status') == 'Y' else 'inactive',
                'images': self._parse_images(raw_product.get('image_url', '')),
                'attributes': {
                    'options': raw_product.get('options', []),
                    'delivery_fee': raw_product.get('delivery_fee', 0),
                    'delivery_type': raw_product.get('delivery_type'),
                    'min_order_qty': raw_product.get('min_order_qty', 1)
                },
                'metadata': {
                    'supplier': 'domaemae',
                    'updated_at': raw_product.get('update_dt'),
                    'goods_code': raw_product.get('goods_code'),
                    'seller_code': raw_product.get('seller_code')
                }
            }
            
            return transformed
            
        except Exception as e:
            logger.error(f"도매매 상품 변환 오류: {e}")
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
                        logger.error(f"도매매 API 요청 실패: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"도매매 API 요청 오류: {e}")
            return {}

    def _get_headers(self) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'X-Seller-Id': self.seller_id,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def _parse_images(self, image_url: str) -> List[str]:
        """
        이미지 URL 파싱
        
        Args:
            image_url: 이미지 URL 문자열 (콤마로 구분된 경우)
            
        Returns:
            List[str]: 이미지 URL 리스트
        """
        if not image_url:
            return []
        
        if ',' in image_url:
            return [url.strip() for url in image_url.split(',') if url.strip()]
        else:
            return [image_url.strip()]

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
                    params={'seller_id': self.seller_id},
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == '200':
                            return data.get('result', {})
                        else:
                            logger.error(f"도매매 상품 조회 실패: {data.get('message')}")
                            return {}
                    else:
                        logger.error(f"도매매 상품 조회 실패: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"도매매 상품 조회 오류: {e}")
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
            return int(product.get('stock_qty', 0))
        except Exception as e:
            logger.error(f"도매매 재고 확인 오류: {e}")
            return 0

    async def update_stock(self, product_id: str, quantity: int) -> bool:
        """
        재고 수량 업데이트 (실시간 재고 동기화)
        
        Args:
            product_id: 상품 ID
            quantity: 재고 수량
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            headers = self._get_headers()
            payload = {
                'goods_no': product_id,
                'stock_qty': quantity,
                'seller_id': self.seller_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{self.base_url}/products/stock",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == '200':
                            logger.info(f"도매매 재고 업데이트 성공: {product_id} -> {quantity}")
                            return True
                        else:
                            logger.error(f"도매매 재고 업데이트 실패: {data.get('message')}")
                            return False
                    else:
                        logger.error(f"도매매 재고 업데이트 실패: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"도매매 재고 업데이트 오류: {e}")
            return False
