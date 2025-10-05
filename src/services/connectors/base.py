"""
공급사 커넥터 추상 베이스 클래스
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from uuid import UUID
from enum import Enum


class CollectionMethod(str, Enum):
    """수집 방법"""

    API = "api"
    EXCEL = "excel"
    WEB_CRAWLING = "web_crawling"


class SupplierConnector(ABC):
    """공급사 커넥터 추상 클래스"""

    def __init__(self, supplier_id: UUID, credentials: Dict[str, Any]):
        self.supplier_id = supplier_id
        self.credentials = credentials

    @abstractmethod
    async def collect_products(
        self, account_id: Optional[UUID] = None, **kwargs
    ) -> List[Dict]:
        """
        상품 수집

        Args:
            account_id: 공급사 계정 ID (멀티 계정용)
            **kwargs: 추가 파라미터 (카테고리, 페이지 등)

        Returns:
            원본 데이터 리스트 (JSONB 형식)
        """
        pass

    @abstractmethod
    def transform_product(self, raw_data: Dict) -> Dict:
        """
        원본 데이터를 정규화된 형식으로 변환

        Args:
            raw_data: 공급사의 원본 데이터

        Returns:
            정규화된 상품 데이터
        """
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        인증 정보 검증

        Returns:
            유효성 여부
        """
        pass

    def extract_images(self, raw_data: Dict) -> List[str]:
        """
        원본 데이터에서 이미지 URL 추출

        Args:
            raw_data: 원본 데이터

        Returns:
            이미지 URL 리스트
        """
        # 공급사별로 오버라이드
        return []

    def calculate_cost_price(self, raw_data: Dict) -> float:
        """
        원가 계산

        Args:
            raw_data: 원본 데이터

        Returns:
            원가
        """
        # 공급사별로 오버라이드
        return 0.0


class APIConnector(SupplierConnector):
    """API 기반 공급사 커넥터"""

    def __init__(
        self, supplier_id: UUID, credentials: Dict[str, Any], api_config: Dict
    ):
        super().__init__(supplier_id, credentials)
        self.api_endpoint = api_config.get("api_endpoint")
        self.api_version = api_config.get("api_version")
        self.auth_type = api_config.get("auth_type", "api_key")

    @abstractmethod
    async def _make_api_request(
        self, endpoint: str, method: str = "GET", params: Dict = None
    ) -> Dict:
        """API 요청"""
        pass

    async def collect_products(
        self, account_id: Optional[UUID] = None, **kwargs
    ) -> List[Dict]:
        """API를 통한 상품 수집"""
        pass


class ExcelConnector(SupplierConnector):
    """엑셀 기반 공급사 커넥터"""

    def __init__(
        self, supplier_id: UUID, credentials: Dict[str, Any], excel_config: Dict
    ):
        super().__init__(supplier_id, credentials)
        self.column_mapping = excel_config.get("column_mapping", {})
        self.sheet_name = excel_config.get("sheet_name", 0)

    async def collect_products(
        self, account_id: Optional[UUID] = None, file_path: str = None, **kwargs
    ) -> List[Dict]:
        """엑셀 파일에서 상품 수집"""
        import pandas as pd

        if not file_path:
            raise ValueError("Excel file path is required")

        df = pd.read_excel(file_path, sheet_name=self.sheet_name)

        products = []
        for _, row in df.iterrows():
            raw_data = row.to_dict()
            products.append(raw_data)

        return products

    def transform_product(self, raw_data: Dict) -> Dict:
        """엑셀 데이터 변환"""
        transformed = {}

        for excel_col, our_field in self.column_mapping.items():
            if excel_col in raw_data:
                transformed[our_field] = raw_data[excel_col]

        return transformed

    def validate_credentials(self) -> bool:
        """엑셀은 인증 불필요"""
        return True


class WebCrawlingConnector(SupplierConnector):
    """웹 크롤링 기반 공급사 커넥터"""

    def __init__(
        self, supplier_id: UUID, credentials: Dict[str, Any], crawl_config: Dict
    ):
        super().__init__(supplier_id, credentials)
        self.base_url = crawl_config.get("base_url")
        self.selectors = crawl_config.get("selectors", {})
        self.pagination = crawl_config.get("pagination", {})

    async def collect_products(
        self, account_id: Optional[UUID] = None, start_url: str = None, **kwargs
    ) -> List[Dict]:
        """웹 크롤링으로 상품 수집"""
        pass

    @abstractmethod
    async def _crawl_page(self, url: str) -> Dict:
        """페이지 크롤링"""
        pass

    def validate_credentials(self) -> bool:
        """웹 크롤링은 인증 불필요 (또는 쿠키 체크)"""
        return True
