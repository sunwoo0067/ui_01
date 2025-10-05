"""커넥터 예시 모듈"""

from .naver_smartstore import NaverSmartstoreConnector
from .excel_generic import GenericExcelConnector
from .web_generic import GenericWebCrawler

__all__ = [
    "NaverSmartstoreConnector",
    "GenericExcelConnector",
    "GenericWebCrawler",
]
