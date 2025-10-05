"""
제네릭 엑셀 커넥터
"""

from typing import List, Dict, Optional
from uuid import UUID
from loguru import logger
import pandas as pd

from ..base import ExcelConnector


class GenericExcelConnector(ExcelConnector):
    """범용 엑셀 커넥터"""

    async def collect_products(
        self, account_id: Optional[UUID] = None, file_path: str = None, **kwargs
    ) -> List[Dict]:
        """엑셀 파일에서 상품 수집"""
        if not file_path:
            raise ValueError("Excel file path is required")

        try:
            # 엑셀 읽기
            df = pd.read_excel(file_path, sheet_name=self.sheet_name)

            # 빈 행 제거
            df = df.dropna(how="all")

            products = []
            for idx, row in df.iterrows():
                # NaN 값을 None으로 변환
                raw_data = row.where(pd.notna(row), None).to_dict()

                # 행 번호 추가
                raw_data["_row_number"] = idx + 2  # Excel은 1부터, 헤더 포함

                products.append(raw_data)

            logger.info(
                f"Collected {len(products)} products from Excel: {file_path}"
            )

            return products

        except Exception as e:
            logger.error(f"Failed to read Excel file {file_path}: {e}")
            raise

    def transform_product(self, raw_data: Dict) -> Dict:
        """엑셀 데이터 → 정규화된 형식"""
        transformed = {}

        # 컬럼 매핑 적용
        for excel_col, our_field in self.column_mapping.items():
            value = raw_data.get(excel_col)

            # 타입 변환
            if value is not None:
                if our_field in ["price", "original_price", "cost_price"]:
                    try:
                        value = float(value)
                    except:
                        value = 0.0
                elif our_field == "stock_quantity":
                    try:
                        value = int(value)
                    except:
                        value = 0
                elif our_field == "tags" and isinstance(value, str):
                    value = [tag.strip() for tag in value.split(",")]

            transformed[our_field] = value

        # 필수 필드 기본값
        if "title" not in transformed or not transformed["title"]:
            transformed["title"] = f"상품 (행 {raw_data.get('_row_number', '?')})"

        if "price" not in transformed or not transformed["price"]:
            transformed["price"] = 0.0

        return transformed

    def extract_images(self, raw_data: Dict) -> List[str]:
        """이미지 URL 추출 (엑셀에서 쉼표 구분)"""
        image_field = self.column_mapping.get("images", "이미지URL")
        images_str = raw_data.get(image_field, "")

        if not images_str:
            return []

        # 쉼표 또는 줄바꿈으로 분리
        urls = [url.strip() for url in str(images_str).replace("\n", ",").split(",")]

        return [url for url in urls if url and url.startswith("http")]

    def calculate_cost_price(self, raw_data: Dict) -> float:
        """원가 계산"""
        cost_field = self.column_mapping.get("cost_price", "원가")
        cost = raw_data.get(cost_field, 0)

        try:
            return float(cost)
        except:
            # 판매가의 70%를 원가로 추정
            price_field = self.column_mapping.get("price", "판매가")
            price = raw_data.get(price_field, 0)
            try:
                return float(price) * 0.7
            except:
                return 0.0

    def validate_credentials(self) -> bool:
        """엑셀은 인증 불필요"""
        return True
