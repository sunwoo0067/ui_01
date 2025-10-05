"""
이미지 처리 서비스
Supabase Storage API 통합
"""

import os
import io
from typing import List, Optional, Dict
from uuid import UUID
from pathlib import Path
from PIL import Image
from loguru import logger

from src.config import settings
from src.services.supabase_client import supabase_client


class ImageProcessor:
    """이미지 처리 및 Storage 업로드"""

    def __init__(self):
        self.bucket = settings.STORAGE_BUCKET
        self.max_width = settings.IMAGE_MAX_WIDTH
        self.max_height = settings.IMAGE_MAX_HEIGHT
        self.quality = settings.IMAGE_QUALITY
        self.supported_formats = settings.SUPPORTED_IMAGE_FORMATS

    def optimize_image(
        self,
        image_path: str,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        quality: Optional[int] = None,
    ) -> bytes:
        """
        이미지 최적화 (리사이징, 압축)

        Args:
            image_path: 원본 이미지 경로
            max_width: 최대 너비
            max_height: 최대 높이
            quality: 압축 품질 (1-100)

        Returns:
            최적화된 이미지 바이트
        """
        max_width = max_width or self.max_width
        max_height = max_height or self.max_height
        quality = quality or self.quality

        try:
            with Image.open(image_path) as img:
                # RGBA -> RGB 변환 (JPEG 저장용)
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = background

                # 리사이징 (비율 유지)
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                # 메모리에 저장
                output = io.BytesIO()
                img.save(output, format="JPEG", quality=quality, optimize=True)
                output.seek(0)

                logger.info(
                    f"Image optimized: {image_path} -> {img.size} @ {quality}% quality"
                )

                return output.getvalue()

        except Exception as e:
            logger.error(f"Failed to optimize image {image_path}: {e}")
            raise

    def upload_image(
        self,
        image_bytes: bytes,
        storage_path: str,
        content_type: str = "image/jpeg",
    ) -> str:
        """
        이미지를 Supabase Storage에 업로드

        Args:
            image_bytes: 이미지 바이트
            storage_path: Storage 경로 (예: 'products/uuid/image1.jpg')
            content_type: MIME 타입

        Returns:
            Public URL
        """
        try:
            storage = supabase_client.get_storage(use_service_key=True)

            # 업로드
            response = storage.from_(self.bucket).upload(
                path=storage_path,
                file=image_bytes,
                file_options={"content-type": content_type},
            )

            # Public URL 생성
            public_url = storage.from_(self.bucket).get_public_url(storage_path)

            logger.info(f"Image uploaded: {storage_path} -> {public_url}")

            return public_url

        except Exception as e:
            logger.error(f"Failed to upload image {storage_path}: {e}")
            raise

    async def upload_product_images(
        self, product_id: UUID, image_paths: List[str]
    ) -> List[Dict]:
        """
        상품 이미지 일괄 업로드

        Args:
            product_id: 상품 ID
            image_paths: 이미지 파일 경로 리스트

        Returns:
            업로드된 이미지 정보 리스트
        """
        uploaded_images = []

        for idx, image_path in enumerate(image_paths):
            try:
                # 1. 이미지 최적화
                optimized_bytes = self.optimize_image(image_path)

                # 2. Storage 경로 생성
                file_ext = Path(image_path).suffix or ".jpg"
                storage_path = f"products/{product_id}/image_{idx}{file_ext}"

                # 3. 업로드
                public_url = self.upload_image(optimized_bytes, storage_path)

                # 4. 이미지 메타데이터 저장
                with Image.open(image_path) as img:
                    width, height = img.size

                image_info = {
                    "product_id": str(product_id),
                    "storage_path": storage_path,
                    "public_url": public_url,
                    "width": width,
                    "height": height,
                    "file_size": len(optimized_bytes),
                    "format": "jpeg",
                    "is_optimized": True,
                    "original_path": image_path,
                    "display_order": idx,
                    "is_primary": idx == 0,  # 첫 번째 이미지를 대표 이미지로
                }

                # 메타데이터 DB 저장
                supabase_client.get_table("image_metadata", use_service_key=True).insert(
                    image_info
                ).execute()

                uploaded_images.append(image_info)

                logger.info(
                    f"Product image uploaded: {product_id} - {idx + 1}/{len(image_paths)}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to upload image {image_path} for product {product_id}: {e}"
                )
                # 에러 발생 시에도 계속 진행

        return uploaded_images

    def delete_product_images(self, product_id: UUID) -> int:
        """
        상품의 모든 이미지 삭제

        Args:
            product_id: 상품 ID

        Returns:
            삭제된 이미지 수
        """
        try:
            # 1. 메타데이터 조회
            response = (
                supabase_client.get_table("image_metadata", use_service_key=True)
                .select("storage_path")
                .eq("product_id", str(product_id))
                .execute()
            )

            image_metadata = response.data
            deleted_count = 0

            storage = supabase_client.get_storage(use_service_key=True)

            # 2. Storage에서 파일 삭제
            for metadata in image_metadata:
                try:
                    storage.from_(self.bucket).remove([metadata["storage_path"]])
                    deleted_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to delete image {metadata['storage_path']}: {e}"
                    )

            # 3. 메타데이터 삭제
            (
                supabase_client.get_table("image_metadata", use_service_key=True)
                .delete()
                .eq("product_id", str(product_id))
                .execute()
            )

            logger.info(f"Deleted {deleted_count} images for product {product_id}")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete images for product {product_id}: {e}")
            raise

    def get_product_images(self, product_id: UUID) -> List[Dict]:
        """
        상품 이미지 메타데이터 조회

        Args:
            product_id: 상품 ID

        Returns:
            이미지 메타데이터 리스트
        """
        try:
            response = (
                supabase_client.get_table("image_metadata", use_service_key=True)
                .select("*")
                .eq("product_id", str(product_id))
                .order("display_order")
                .execute()
            )

            return response.data

        except Exception as e:
            logger.error(f"Failed to get images for product {product_id}: {e}")
            raise

    def create_thumbnail(self, image_path: str, size: tuple = (300, 300)) -> bytes:
        """
        썸네일 생성

        Args:
            image_path: 원본 이미지 경로
            size: 썸네일 크기 (width, height)

        Returns:
            썸네일 이미지 바이트
        """
        try:
            with Image.open(image_path) as img:
                # 정사각형 크롭
                width, height = img.size
                min_dimension = min(width, height)

                left = (width - min_dimension) // 2
                top = (height - min_dimension) // 2
                right = left + min_dimension
                bottom = top + min_dimension

                img_cropped = img.crop((left, top, right, bottom))
                img_cropped.thumbnail(size, Image.Resampling.LANCZOS)

                output = io.BytesIO()
                img_cropped.save(output, format="JPEG", quality=90, optimize=True)
                output.seek(0)

                logger.info(f"Thumbnail created: {image_path} -> {size}")

                return output.getvalue()

        except Exception as e:
            logger.error(f"Failed to create thumbnail for {image_path}: {e}")
            raise


class BulkImageUploader:
    """대량 이미지 업로드"""

    def __init__(self):
        self.processor = ImageProcessor()

    async def upload_from_directory(
        self, directory: str, product_id: UUID
    ) -> List[Dict]:
        """
        디렉토리의 모든 이미지 업로드

        Args:
            directory: 이미지 디렉토리 경로
            product_id: 상품 ID

        Returns:
            업로드된 이미지 정보 리스트
        """
        image_paths = []

        # 지원 포맷 필터링
        for ext in self.processor.supported_formats:
            image_paths.extend(Path(directory).glob(f"*.{ext}"))

        image_paths = [str(p) for p in image_paths]

        logger.info(f"Found {len(image_paths)} images in {directory}")

        return await self.processor.upload_product_images(product_id, image_paths)
