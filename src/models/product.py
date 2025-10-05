"""
상품 데이터 모델
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class ProductImage(BaseModel):
    """상품 이미지 모델"""

    url: str
    is_primary: bool = False
    width: Optional[int] = None
    height: Optional[int] = None
    display_order: int = 0


class ProductOption(BaseModel):
    """상품 옵션 모델"""

    name: str  # 예: "색상", "사이즈"
    values: List[str]  # 예: ["빨강", "파랑"], ["S", "M", "L"]
    price_modifier: Optional[Decimal] = None  # 옵션별 가격 차이


class ProductCreate(BaseModel):
    """상품 생성 모델"""

    seller_id: UUID
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    original_price: Optional[Decimal] = None
    currency: str = "KRW"
    stock_quantity: int = Field(default=0, ge=0)
    options: Optional[List[ProductOption]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    images: Optional[List[ProductImage]] = None
    metadata: Optional[dict] = None

    @validator("original_price")
    def validate_original_price(cls, v, values):
        """원가는 판매가보다 높아야 함"""
        if v is not None and "price" in values and v < values["price"]:
            raise ValueError("Original price must be greater than or equal to price")
        return v


class Product(ProductCreate):
    """상품 전체 모델"""

    id: UUID
    embedding: Optional[List[float]] = None
    status: str = "draft"
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductBatch(BaseModel):
    """상품 배치 업로드 모델"""

    products: List[ProductCreate]
    batch_name: str = Field(..., min_length=1)

    @validator("products")
    def validate_products_count(cls, v):
        """배치 크기 검증"""
        if len(v) == 0:
            raise ValueError("Products list cannot be empty")
        if len(v) > 10000:
            raise ValueError("Maximum 10,000 products per batch")
        return v
