"""
오너클랜 (OwnerClan) API 커넥터
드롭쉬핑 공급사 오너클랜과 연동하는 커넥터
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
from loguru import logger

from ..base import APIConnector


class OwnerClanConnector(APIConnector):
    """오너클랜 API 커넥터"""

    def __init__(self, supplier_id: str, credentials: Dict[str, Any], api_config: Dict[str, Any], **kwargs):
        """
        오너클랜 커넥터 초기화
        
        Args:
            supplier_id: 공급사 ID
            credentials: 인증 정보 (api_key, api_secret)
            api_config: API 설정 (base_url, timeout 등)
        """
        super().__init__(supplier_id, credentials, api_config)
        self.api_key = credentials.get('api_key', '')
        self.api_secret = credentials.get('api_secret', '')
        self.base_url = api_config.get('base_url', 'https://api.ownerclan.com/v1')
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
                    f"{self.base_url}/auth/validate",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        logger.info("오너클랜 API 인증 성공")
                        return True
                    else:
                        logger.error(f"오너클랜 API 인증 실패: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"오너클랜 API 인증 오류: {e}")
            return False

    async def collect_products(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        오너클랜에서 상품 목록 수집
        
        Args:
            limit: 수집할 상품 개수 (None = 전체)
            offset: 시작 위치
            filters: 필터 조건 (category, price_min, price_max 등)
            
        Returns:
            List[Dict]: 수집된 상품 목록
        """
        try:
            logger.info(f"오너클랜 상품 수집 시작 (limit={limit}, offset={offset})")
            
            products = []
            page = offset // 100 + 1  # 100개씩 페이징
            collected = 0
            
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                while True:
                    # API 요청 파라미터
                    params = {
                        'page': page,
                        'per_page': 100
                    }
                    
                    # 필터 적용
                    if filters:
                        if 'category' in filters:
                            params['category'] = filters['category']
                        if 'price_min' in filters:
                            params['price_min'] = filters['price_min']
                        if 'price_max' in filters:
                            params['price_max'] = filters['price_max']
                    
                    # API 호출
                    async with session.get(
                        f"{self.base_url}/products",
                        headers=headers,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status != 200:
                            logger.error(f"오너클랜 API 오류: {response.status}")
                            break
                        
                        data = await response.json()
                        page_products = data.get('products', [])
                        
                        if not page_products:
                            break
                        
                        # 상품 수집
                        for product in page_products:
                            if limit and collected >= limit:
                                break
                            
                            products.append(product)
                            collected += 1
                        
                        logger.info(f"오너클랜 페이지 {page} 수집: {len(page_products)}개 (누적: {collected}개)")
                        
                        # 제한 도달 확인
                        if limit and collected >= limit:
                            break
                        
                        # 마지막 페이지 확인
                        if len(page_products) < 100:
                            break
                        
                        page += 1
            
            logger.info(f"오너클랜 상품 수집 완료: 총 {len(products)}개")
            return products
            
        except Exception as e:
            logger.error(f"오너클랜 상품 수집 오류: {e}")
            raise

    async def transform_product(self, raw_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        오너클랜 상품 데이터를 시스템 형식으로 변환
        
        Args:
            raw_product: 원본 상품 데이터
            
        Returns:
            Dict: 변환된 상품 데이터
        """
        try:
            # 실제 수집된 오너클랜 데이터 구조에 맞춰 변환
            # 필드명: supplier_key, name, price, status, category_name, etc.
            
            # 가격 계산 (옵션이 있으면 첫 번째 옵션 가격 사용)
            price = float(raw_product.get('price', 0))
            options = raw_product.get('options', [])
            if options and len(options) > 0:
                option_price = options[0].get('price', price)
                price = float(option_price)
            
            transformed = {
                'supplier_product_id': str(raw_product.get('supplier_key', '')),
                'title': raw_product.get('name', ''),
                'description': raw_product.get('model', ''),  # model을 description으로
                'price': price,
                'cost_price': price,  # 도매가 = 판매가 (오너클랜 특성)
                'currency': 'KRW',
                'category': raw_product.get('category_name', ''),
                'brand': '',  # 오너클랜 데이터에 브랜드 정보 없음
                'stock_quantity': 9999,  # 기본 재고 (실제 재고 정보 없음)
                'status': 'active' if raw_product.get('status') == 'available' else 'inactive',
                'images': raw_product.get('images', []),
                'attributes': {
                    'supplier_key': raw_product.get('supplier_key'),
                    'model': raw_product.get('model'),
                    'category_key': raw_product.get('category_key'),
                    'box_quantity': raw_product.get('box_quantity'),
                    'options': options,
                    'created_at': raw_product.get('created_at'),
                    'updated_at': raw_product.get('updated_at'),
                    'account_name': raw_product.get('account_name')
                }
            }
            
            return transformed
            
        except Exception as e:
            logger.error(f"오너클랜 상품 변환 오류: {e}")
            logger.error(f"문제 데이터: {raw_product}")
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
                        logger.error(f"오너클랜 API 요청 실패: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"오너클랜 API 요청 오류: {e}")
            return {}

    def _get_headers(self) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'X-API-Secret': self.api_secret,
            'Content-Type': 'application/json',
            'User-Agent': 'DropshippingSystem/1.0'
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
                        return await response.json()
                    else:
                        logger.error(f"오너클랜 상품 조회 실패: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"오너클랜 상품 조회 오류: {e}")
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
            return int(product.get('stock', 0))
        except Exception as e:
            logger.error(f"오너클랜 재고 확인 오류: {e}")
            return 0
