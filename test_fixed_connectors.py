#!/usr/bin/env python3
"""
수정된 커넥터 테스트 (각 공급사 1개씩)
"""

import asyncio
from uuid import UUID
from loguru import logger
from src.services.product_pipeline import ProductPipeline
from src.services.supabase_client import supabase_client


async def test_connectors():
    """각 공급사별로 1개씩만 처리 테스트"""
    pipeline = ProductPipeline()
    
    suppliers = {
        "젠트레이드": "ab98eee5-fbc3-4c72-8a1f-e4fc2c03d2c7",
        "오너클랜": "e458e4e2-cb03-4fc2-bff1-b05aaffde00f",
        "도매꾹": "d9e6fa42-9bd4-438f-bf3b-10cf199eabd2",
    }
    
    for name, supplier_id in suppliers.items():
        logger.info(f"\n{'='*70}")
        logger.info(f"🧪 {name} 테스트")
        logger.info(f"{'='*70}")
        
        # 미처리 데이터 1개 조회
        response = (
            supabase_client.get_table("raw_product_data")
            .select("id")
            .eq("supplier_id", supplier_id)
            .eq("is_processed", False)
            .limit(1)
            .execute()
        )
        
        if not response.data:
            logger.warning(f"{name}: 미처리 데이터 없음")
            continue
        
        raw_data_id = UUID(response.data[0]["id"])
        logger.info(f"처리할 데이터 ID: {raw_data_id}")
        
        try:
            result = await pipeline.process_raw_data(raw_data_id, auto_list=False)
            logger.info(f"✅ {name} 성공: {result}")
        except Exception as e:
            logger.error(f"❌ {name} 실패: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_connectors())

