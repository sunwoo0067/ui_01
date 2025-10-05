"""
상품 수집 서비스
공급사별 데이터 수집 및 저장
"""

import asyncio
from typing import List, Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime
from loguru import logger

from src.services.supabase_client import supabase_client, AsyncSupabaseClient
from src.services.connectors import ConnectorFactory, CollectionMethod


class CollectionService:
    """상품 수집 서비스"""

    def __init__(self):
        self.connector_factory = ConnectorFactory

    async def collect_from_supplier(
        self,
        supplier_id: UUID,
        account_id: Optional[UUID] = None,
        job_name: str = "Manual Collection",
        **kwargs,
    ) -> Dict:
        """
        공급사로부터 상품 수집

        Args:
            supplier_id: 공급사 ID
            account_id: 공급사 계정 ID (멀티 계정)
            job_name: 작업 이름
            **kwargs: 수집 파라미터 (file_path, start_url, category 등)

        Returns:
            수집 결과
        """
        # 1. 공급사 정보 조회
        supplier = await self._get_supplier(supplier_id)

        if not supplier:
            raise ValueError(f"Supplier not found: {supplier_id}")

        # 2. 수집 작업 생성
        job_id = await self._create_collection_job(
            supplier_id, account_id, supplier["type"], job_name, kwargs
        )

        # 3. 커넥터 생성
        connector = self._create_connector(supplier, account_id)

        # 4. 상품 수집
        try:
            # 작업 시작
            await self._update_job_status(job_id, "running", started_at=datetime.now())

            raw_products = await connector.collect_products(
                account_id=account_id, **kwargs
            )

            # 5. 원본 데이터 저장
            saved_count = await self._save_raw_products(
                raw_products, supplier_id, account_id, supplier["type"], kwargs
            )

            # 6. 작업 완료
            await self._update_job_status(
                job_id,
                "completed",
                total_items=len(raw_products),
                collected_items=saved_count,
                completed_at=datetime.now(),
            )

            logger.info(
                f"Collection completed: {saved_count}/{len(raw_products)} products saved"
            )

            return {
                "job_id": str(job_id),
                "total": len(raw_products),
                "saved": saved_count,
                "failed": len(raw_products) - saved_count,
            }

        except Exception as e:
            # 작업 실패
            await self._update_job_status(
                job_id,
                "failed",
                error_log={"error": str(e)},
                completed_at=datetime.now(),
            )
            logger.error(f"Collection failed: {e}")
            raise

    async def _get_supplier(self, supplier_id: UUID) -> Optional[Dict]:
        """공급사 정보 조회"""
        response = (
            supabase_client.get_table("suppliers")
            .select("*")
            .eq("id", str(supplier_id))
            .execute()
        )

        return response.data[0] if response.data else None

    async def _create_collection_job(
        self,
        supplier_id: UUID,
        account_id: Optional[UUID],
        job_type: str,
        job_name: str,
        config: Dict,
    ) -> UUID:
        """수집 작업 생성"""
        job_id = uuid4()

        job_data = {
            "id": str(job_id),
            "supplier_id": str(supplier_id),
            "supplier_account_id": str(account_id) if account_id else None,
            "job_type": job_type,
            "job_name": job_name,
            "config": config,
            "status": "pending",
        }

        supabase_client.get_table("collection_jobs").insert(job_data).execute()

        logger.info(f"Created collection job: {job_id}")

        return job_id

    async def _update_job_status(self, job_id: UUID, status: str, **updates):
        """작업 상태 업데이트"""
        update_data = {"status": status, **updates}

        supabase_client.get_table("collection_jobs").update(update_data).eq(
            "id", str(job_id)
        ).execute()

    def _create_connector(self, supplier: Dict, account_id: Optional[UUID]):
        """커넥터 생성"""
        supplier_code = supplier["code"]
        supplier_type = CollectionMethod(supplier["type"])
        credentials = supplier.get("credentials", {})

        # 계정별 credentials 오버라이드
        if account_id:
            account = self._get_supplier_account(account_id)
            if account:
                credentials.update(account.get("account_credentials", {}))

        # 설정 구성
        config = {}
        if supplier_type == CollectionMethod.API:
            config = {
                "api_endpoint": supplier.get("api_endpoint"),
                "api_version": supplier.get("api_version"),
                "auth_type": supplier.get("auth_type"),
            }
        elif supplier_type == CollectionMethod.EXCEL:
            config = supplier.get("excel_config", {})
        elif supplier_type == CollectionMethod.WEB_CRAWLING:
            config = supplier.get("crawl_config", {})

        return self.connector_factory.create(
            supplier_code,
            UUID(supplier["id"]),
            supplier_type,
            credentials,
            config,
        )

    def _get_supplier_account(self, account_id: UUID) -> Optional[Dict]:
        """공급사 계정 조회"""
        response = (
            supabase_client.get_table("supplier_accounts")
            .select("*")
            .eq("id", str(account_id))
            .execute()
        )

        return response.data[0] if response.data else None

    async def _save_raw_products(
        self,
        products: List[Dict],
        supplier_id: UUID,
        account_id: Optional[UUID],
        collection_method: str,
        source_info: Dict,
    ) -> int:
        """원본 상품 데이터 저장"""
        saved_count = 0

        async with AsyncSupabaseClient() as client:
            for product in products:
                try:
                    # 공급사 상품 ID 추출 (중복 방지)
                    supplier_product_id = self._extract_product_id(product)

                    raw_data_item = {
                        "supplier_id": str(supplier_id),
                        "supplier_account_id": str(account_id) if account_id else None,
                        "raw_data": product,
                        "collection_method": collection_method,
                        "collection_source": source_info.get("file_path")
                        or source_info.get("start_url")
                        or "api",
                        "supplier_product_id": supplier_product_id,
                        "is_processed": False,
                        "metadata": {
                            "collected_at": datetime.now().isoformat(),
                            "source_info": source_info,
                        },
                    }

                    # Upsert (중복 시 업데이트)
                    await client.client.table("raw_product_data").upsert(
                        raw_data_item, on_conflict="supplier_id,supplier_product_id"
                    ).execute()

                    saved_count += 1

                except Exception as e:
                    logger.warning(f"Failed to save raw product: {e}")
                    continue

        return saved_count

    def _extract_product_id(self, raw_data: Dict) -> Optional[str]:
        """원본 데이터에서 상품 ID 추출"""
        # 공급사별로 다를 수 있음
        possible_keys = [
            "id",
            "product_id",
            "productId",
            "productCode",
            "product_code",
            "sku",
            "SKU",
        ]

        for key in possible_keys:
            if key in raw_data and raw_data[key]:
                return str(raw_data[key])

        # ID가 없으면 데이터 해시 사용 (중복 감지)
        import hashlib

        data_str = str(sorted(raw_data.items()))
        return hashlib.md5(data_str.encode()).hexdigest()

    async def collect_from_excel(
        self, supplier_id: UUID, file_path: str, account_id: Optional[UUID] = None
    ) -> Dict:
        """엑셀 파일에서 수집"""
        return await self.collect_from_supplier(
            supplier_id=supplier_id,
            account_id=account_id,
            job_name=f"Excel Import: {file_path}",
            file_path=file_path,
        )

    async def collect_from_web(
        self,
        supplier_id: UUID,
        start_url: str,
        max_pages: int = 10,
        account_id: Optional[UUID] = None,
    ) -> Dict:
        """웹 크롤링으로 수집"""
        return await self.collect_from_supplier(
            supplier_id=supplier_id,
            account_id=account_id,
            job_name=f"Web Crawling: {start_url}",
            start_url=start_url,
            max_pages=max_pages,
        )

    async def collect_from_api(
        self,
        supplier_id: UUID,
        account_id: Optional[UUID] = None,
        **api_params,
    ) -> Dict:
        """API로 수집"""
        return await self.collect_from_supplier(
            supplier_id=supplier_id,
            account_id=account_id,
            job_name=f"API Collection",
            **api_params,
        )
