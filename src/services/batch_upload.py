"""
배치 업로드 서비스
대량 상품 등록 처리
"""

import asyncio
from typing import List, Dict, Optional
from uuid import UUID, uuid4
from loguru import logger
from tqdm import tqdm

from src.config import settings
from src.models.product import ProductCreate, ProductBatch
from src.services.supabase_client import AsyncSupabaseClient, supabase_client


class BatchUploadService:
    """배치 업로드 서비스"""

    def __init__(self, seller_id: UUID):
        self.seller_id = seller_id
        self.batch_size = settings.BATCH_SIZE

    async def upload_batch(
        self, products: List[ProductCreate], batch_name: str
    ) -> Dict:
        """
        배치 업로드 실행

        Args:
            products: 업로드할 상품 리스트
            batch_name: 배치 이름

        Returns:
            업로드 결과 통계
        """
        batch_id = uuid4()
        total_count = len(products)

        # 1. 배치 레코드 생성
        await self._create_batch_record(batch_id, batch_name, total_count)

        # 2. 비동기 배치 업로드
        async with AsyncSupabaseClient() as async_client:
            try:
                # 상품 데이터를 dict로 변환
                product_dicts = [p.model_dump() for p in products]

                # 배치 삽입 실행
                result = await async_client.batch_insert(
                    table_name="products",
                    data=product_dicts,
                    chunk_size=self.batch_size,
                    use_service_key=True,  # RLS 우회
                )

                # 3. 배치 상태 업데이트
                await self._update_batch_status(
                    batch_id,
                    success_count=result["success"],
                    failed_count=result["failed"],
                    errors=result.get("errors", []),
                )

                logger.info(
                    f"Batch upload completed: {result['success']}/{total_count} succeeded"
                )

                return {
                    "batch_id": str(batch_id),
                    "total": total_count,
                    "success": result["success"],
                    "failed": result["failed"],
                    "errors": result.get("errors", []),
                }

            except Exception as e:
                logger.error(f"Batch upload failed: {e}")
                await self._update_batch_status(
                    batch_id, success_count=0, failed_count=total_count, errors=[str(e)]
                )
                raise

    async def _create_batch_record(
        self, batch_id: UUID, batch_name: str, total_count: int
    ):
        """배치 레코드 생성"""
        batch_data = {
            "id": str(batch_id),
            "seller_id": str(self.seller_id),
            "name": batch_name,
            "total_count": total_count,
            "status": "processing",
        }

        try:
            supabase_client.get_table("upload_batches", use_service_key=True).insert(
                batch_data
            ).execute()
            logger.info(f"Batch record created: {batch_id}")
        except Exception as e:
            logger.error(f"Failed to create batch record: {e}")
            raise

    async def _update_batch_status(
        self,
        batch_id: UUID,
        success_count: int,
        failed_count: int,
        errors: List[str],
    ):
        """배치 상태 업데이트"""
        update_data = {
            "success_count": success_count,
            "failed_count": failed_count,
            "error_log": {"errors": errors} if errors else None,
            "status": "completed" if failed_count == 0 else "failed",
        }

        try:
            (
                supabase_client.get_table("upload_batches", use_service_key=True)
                .update(update_data)
                .eq("id", str(batch_id))
                .execute()
            )
            logger.info(f"Batch status updated: {batch_id}")
        except Exception as e:
            logger.error(f"Failed to update batch status: {e}")

    async def upload_with_progress(
        self, products: List[ProductCreate], batch_name: str
    ) -> Dict:
        """
        진행 상황 표시와 함께 배치 업로드

        Args:
            products: 업로드할 상품 리스트
            batch_name: 배치 이름

        Returns:
            업로드 결과 통계
        """
        batch_id = uuid4()
        total_count = len(products)

        await self._create_batch_record(batch_id, batch_name, total_count)

        success_count = 0
        failed_count = 0
        errors = []

        async with AsyncSupabaseClient() as async_client:
            # 청크 단위로 분할
            chunks = [
                products[i : i + self.batch_size]
                for i in range(0, total_count, self.batch_size)
            ]

            # tqdm 진행바
            with tqdm(total=total_count, desc="Uploading products") as pbar:
                for chunk_idx, chunk in enumerate(chunks):
                    chunk_dicts = [p.model_dump() for p in chunk]

                    try:
                        await async_client.client.table("products").insert(
                            chunk_dicts
                        ).execute()

                        success_count += len(chunk)
                        pbar.update(len(chunk))

                        # Realtime으로 진행 상황 전송
                        await self._publish_progress(
                            batch_id, success_count, failed_count, total_count
                        )

                    except Exception as e:
                        failed_count += len(chunk)
                        error_msg = f"Chunk {chunk_idx + 1} failed: {str(e)}"
                        errors.append(error_msg)
                        pbar.update(len(chunk))
                        logger.error(error_msg)

            # 최종 배치 상태 업데이트
            await self._update_batch_status(
                batch_id, success_count, failed_count, errors
            )

        return {
            "batch_id": str(batch_id),
            "total": total_count,
            "success": success_count,
            "failed": failed_count,
            "errors": errors,
        }

    async def _publish_progress(
        self,
        batch_id: UUID,
        success_count: int,
        failed_count: int,
        total_count: int,
    ):
        """Realtime으로 진행 상황 전송"""
        try:
            progress = int(((success_count + failed_count) / total_count) * 100)

            # 배치 테이블 업데이트 (Realtime 구독자에게 전파)
            (
                supabase_client.get_table("upload_batches", use_service_key=True)
                .update(
                    {
                        "success_count": success_count,
                        "failed_count": failed_count,
                        "progress": progress,
                    }
                )
                .eq("id", str(batch_id))
                .execute()
            )

        except Exception as e:
            logger.warning(f"Failed to publish progress: {e}")

    def load_from_csv(self, csv_path: str) -> List[ProductCreate]:
        """
        CSV 파일에서 상품 로드

        Args:
            csv_path: CSV 파일 경로

        Returns:
            상품 리스트
        """
        import pandas as pd

        df = pd.read_csv(csv_path)

        products = []
        for _, row in df.iterrows():
            product = ProductCreate(
                seller_id=self.seller_id,
                title=row["title"],
                description=row.get("description"),
                price=row["price"],
                original_price=row.get("original_price"),
                stock_quantity=row.get("stock_quantity", 0),
                category=row.get("category"),
                tags=row.get("tags", "").split(",") if row.get("tags") else None,
            )
            products.append(product)

        logger.info(f"Loaded {len(products)} products from CSV")
        return products


class RealtimeProgressMonitor:
    """Realtime 진행 상황 모니터"""

    def __init__(self, batch_id: UUID):
        self.batch_id = batch_id
        self.channel = None

    def subscribe(self, callback):
        """배치 진행 상황 구독"""
        try:
            realtime = supabase_client.get_realtime()
            self.channel = realtime.channel(f"batch-{self.batch_id}")

            self.channel.on(
                "postgres_changes",
                event="UPDATE",
                schema="public",
                table="upload_batches",
                filter=f"id=eq.{self.batch_id}",
                callback=callback,
            ).subscribe()

            logger.info(f"Subscribed to batch progress: {self.batch_id}")

        except Exception as e:
            logger.error(f"Failed to subscribe to progress: {e}")

    def unsubscribe(self):
        """구독 해제"""
        if self.channel:
            self.channel.unsubscribe()
            logger.info(f"Unsubscribed from batch progress: {self.batch_id}")
