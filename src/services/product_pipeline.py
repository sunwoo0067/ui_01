"""
상품 변환 파이프라인
원본 데이터 → 정규화 → 가격 계산 → 등록
"""

from typing import Dict, List, Optional
from uuid import UUID, uuid4
from decimal import Decimal
from loguru import logger

from src.services.supabase_client import supabase_client
from src.services.connectors import ConnectorFactory, CollectionMethod


class ProductPipeline:
    """상품 변환 파이프라인"""

    async def process_raw_data(
        self, raw_data_id: UUID, auto_list: bool = False
    ) -> Dict:
        """
        원본 데이터 처리

        Args:
            raw_data_id: 원본 데이터 ID
            auto_list: 자동 등록 여부

        Returns:
            처리 결과
        """
        # 1. 원본 데이터 조회
        raw_data_record = await self._get_raw_data(raw_data_id)

        if not raw_data_record:
            raise ValueError(f"Raw data not found: {raw_data_id}")

        if raw_data_record["is_processed"]:
            logger.info(f"Raw data already processed: {raw_data_id}")
            return {"status": "already_processed"}

        # 2. 공급사 정보 조회
        supplier = await self._get_supplier(UUID(raw_data_record["supplier_id"]))

        # 3. 커넥터로 변환
        connector = self._create_connector(supplier)
        
        # raw_data가 JSON 문자열인 경우 파싱
        raw_data = raw_data_record["raw_data"]
        if isinstance(raw_data, str):
            import json
            raw_data = json.loads(raw_data)
        
        normalized_data = await connector.transform_product(raw_data)

        # 4. 정규화된 상품 저장
        normalized_product_id = await self._save_normalized_product(
            raw_data_record, normalized_data
        )

        # 5. 원본 데이터 처리 완료 표시
        await self._mark_processed(raw_data_id)

        # 6. 자동 등록
        if auto_list:
            await self._auto_list_product(
                normalized_product_id, UUID(raw_data_record["supplier_id"])
            )

        return {
            "status": "success",
            "normalized_product_id": str(normalized_product_id),
            "auto_listed": auto_list,
        }

    async def process_all_unprocessed(
        self, supplier_id: Optional[UUID] = None, limit: int = 100
    ) -> Dict:
        """미처리 원본 데이터 일괄 처리"""
        query = supabase_client.get_table("raw_product_data").select("id").eq(
            "is_processed", False
        )

        if supplier_id:
            query = query.eq("supplier_id", str(supplier_id))

        response = query.limit(limit).execute()

        total = len(response.data)
        success = 0
        failed = 0

        for item in response.data:
            try:
                await self.process_raw_data(UUID(item["id"]))
                success += 1
            except Exception as e:
                logger.error(f"Failed to process {item['id']}: {e}")
                failed += 1

        return {"total": total, "success": success, "failed": failed}

    async def _get_raw_data(self, raw_data_id: UUID) -> Optional[Dict]:
        """원본 데이터 조회"""
        response = (
            supabase_client.get_table("raw_product_data")
            .select("*")
            .eq("id", str(raw_data_id))
            .execute()
        )

        return response.data[0] if response.data else None

    async def _get_supplier(self, supplier_id: UUID) -> Dict:
        """공급사 조회 (계정 정보 포함)"""
        # 공급사 기본 정보 조회
        supplier_response = (
            supabase_client.get_table("suppliers")
            .select("*")
            .eq("id", str(supplier_id))
            .execute()
        )
        
        supplier = supplier_response.data[0]
        
        # 계정 정보 조회
        account_response = (
            supabase_client.get_table("supplier_accounts")
            .select("account_credentials")
            .eq("supplier_id", str(supplier_id))
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        
        if account_response.data:
            import json
            account_credentials = account_response.data[0]["account_credentials"]
            
            # account_credentials가 이미 dict면 그대로 사용, 문자열이면 파싱
            if isinstance(account_credentials, str):
                credentials = json.loads(account_credentials)
            else:
                credentials = account_credentials
            
            supplier["credentials"] = credentials
        
        return supplier

    def _create_connector(self, supplier: Dict):
        """커넥터 생성"""
        supplier_code = supplier["code"]
        supplier_type = CollectionMethod(supplier["type"])
        credentials = supplier.get("credentials", {})

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

        return ConnectorFactory.create(
            supplier_code, UUID(supplier["id"]), supplier_type, credentials, config
        )

    async def _save_normalized_product(
        self, raw_data_record: Dict, normalized_data: Dict
    ) -> UUID:
        """정규화된 상품 저장"""
        product_id = uuid4()

        product_data = {
            "id": str(product_id),
            "raw_data_id": raw_data_record["id"],
            "supplier_id": raw_data_record["supplier_id"],
            "supplier_product_id": raw_data_record.get("supplier_product_id"),
            **normalized_data,
            "status": "active",
        }

        supabase_client.get_table("normalized_products").insert(product_data).execute()

        logger.info(f"Saved normalized product: {product_id}")

        return product_id

    async def _mark_processed(self, raw_data_id: UUID):
        """원본 데이터 처리 완료 표시"""
        from datetime import datetime

        supabase_client.get_table("raw_product_data").update(
            {"is_processed": True, "processed_at": datetime.now().isoformat()}
        ).eq("id", str(raw_data_id)).execute()

    async def _auto_list_product(
        self, normalized_product_id: UUID, supplier_id: UUID
    ):
        """자동 등록 (모든 활성 마켓플레이스에)"""
        # 활성 마켓플레이스 조회
        marketplaces = (
            supabase_client.get_table("sales_marketplaces")
            .select("*")
            .eq("is_active", True)
            .execute()
        )

        for marketplace in marketplaces.data:
            try:
                await self.list_product(
                    normalized_product_id,
                    UUID(marketplace["id"]),
                    supplier_id,
                )
            except Exception as e:
                logger.warning(
                    f"Failed to list product to {marketplace['name']}: {e}"
                )

    async def list_product(
        self,
        normalized_product_id: UUID,
        marketplace_id: UUID,
        supplier_id: Optional[UUID] = None,
        sales_account_id: Optional[UUID] = None,
    ) -> UUID:
        """
        마켓플레이스에 상품 등록

        Args:
            normalized_product_id: 정규화된 상품 ID
            marketplace_id: 판매 마켓플레이스 ID
            supplier_id: 공급사 ID (가격 규칙용)
            sales_account_id: 판매 계정 ID (멀티 계정)

        Returns:
            등록 상품 ID
        """
        # 정규화된 상품 조회
        product = (
            supabase_client.get_table("normalized_products")
            .select("*")
            .eq("id", str(normalized_product_id))
            .execute()
        ).data[0]

        # 가격 계산 (가격 규칙 적용)
        selling_price = await self._calculate_selling_price(
            supplier_id or UUID(product["supplier_id"]),
            marketplace_id,
            Decimal(str(product.get("cost_price") or product["price"])),
            product.get("category"),
        )

        # 등록 상품 데이터
        listed_product_id = uuid4()

        listed_data = {
            "id": str(listed_product_id),
            "normalized_product_id": str(normalized_product_id),
            "marketplace_id": str(marketplace_id),
            "sales_account_id": str(sales_account_id) if sales_account_id else None,
            "selling_price": float(selling_price),
            "margin_rate": self._calculate_margin_rate(
                Decimal(str(product["price"])), selling_price
            ),
            "title": product["title"],
            "description": product.get("description"),
            "images": product.get("images"),
            "status": "draft",  # 수동 확인 후 등록
            "sync_status": "pending",
        }

        supabase_client.get_table("listed_products").insert(listed_data).execute()

        logger.info(f"Listed product {normalized_product_id} to marketplace")

        return listed_product_id

    async def _calculate_selling_price(
        self,
        supplier_id: UUID,
        marketplace_id: UUID,
        cost_price: Decimal,
        category: Optional[str] = None,
    ) -> Decimal:
        """판매가 계산 (가격 규칙 적용)"""
        response = supabase_client.client.rpc(
            "apply_pricing_rule",
            {
                "p_supplier_id": str(supplier_id),
                "p_marketplace_id": str(marketplace_id),
                "p_cost_price": float(cost_price),
                "p_category": category,
            },
        ).execute()

        return Decimal(str(response.data))

    def _calculate_margin_rate(
        self, cost_price: Decimal, selling_price: Decimal
    ) -> float:
        """마진율 계산"""
        if cost_price == 0:
            return 0.0

        return float(((selling_price - cost_price) / cost_price) * 100)
