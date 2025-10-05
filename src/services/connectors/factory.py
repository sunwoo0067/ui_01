"""
커넥터 팩토리
공급사별 커넥터 동적 생성
"""

from typing import Dict, Type
from uuid import UUID
from loguru import logger

from .base import SupplierConnector, CollectionMethod
from .examples.naver_smartstore import NaverSmartstoreConnector
from .examples.excel_generic import GenericExcelConnector
from .examples.web_generic import GenericWebCrawler


class ConnectorFactory:
    """공급사 커넥터 팩토리"""

    # 공급사 코드 → 커넥터 클래스 매핑
    _connectors: Dict[str, Type[SupplierConnector]] = {
        "naver_smartstore": NaverSmartstoreConnector,
        "excel_supplier": GenericExcelConnector,
        "taobao": GenericWebCrawler,
        # 여기에 새 공급사 추가
    }

    @classmethod
    def create(
        cls,
        supplier_code: str,
        supplier_id: UUID,
        supplier_type: CollectionMethod,
        credentials: Dict,
        config: Dict,
    ) -> SupplierConnector:
        """
        공급사 커넥터 생성

        Args:
            supplier_code: 공급사 코드
            supplier_id: 공급사 ID
            supplier_type: 수집 방법 (api, excel, web_crawling)
            credentials: 인증 정보
            config: 공급사 설정 (api_config, excel_config, crawl_config)

        Returns:
            커넥터 인스턴스
        """
        connector_class = cls._connectors.get(supplier_code)

        if not connector_class:
            logger.warning(
                f"No specific connector for '{supplier_code}', using generic connector"
            )

            # 제네릭 커넥터 사용
            from .examples.excel_generic import GenericExcelConnector
            from .examples.web_generic import GenericWebCrawler

            if supplier_type == CollectionMethod.EXCEL:
                connector_class = GenericExcelConnector
            elif supplier_type == CollectionMethod.WEB_CRAWLING:
                connector_class = GenericWebCrawler
            else:
                raise ValueError(
                    f"No connector available for '{supplier_code}' with type '{supplier_type}'"
                )

        # 커넥터 인스턴스 생성
        try:
            if supplier_type == CollectionMethod.API:
                return connector_class(supplier_id, credentials, config)
            elif supplier_type == CollectionMethod.EXCEL:
                return connector_class(supplier_id, credentials, config)
            elif supplier_type == CollectionMethod.WEB_CRAWLING:
                return connector_class(supplier_id, credentials, config)
            else:
                raise ValueError(f"Unsupported supplier type: {supplier_type}")

        except Exception as e:
            logger.error(f"Failed to create connector for '{supplier_code}': {e}")
            raise

    @classmethod
    def register(cls, supplier_code: str, connector_class: Type[SupplierConnector]):
        """
        새 공급사 커넥터 등록

        Args:
            supplier_code: 공급사 코드
            connector_class: 커넥터 클래스
        """
        cls._connectors[supplier_code] = connector_class
        logger.info(f"Registered connector for '{supplier_code}'")

    @classmethod
    def list_connectors(cls) -> list[str]:
        """등록된 커넥터 목록"""
        return list(cls._connectors.keys())
