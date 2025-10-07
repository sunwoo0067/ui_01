#!/usr/bin/env python3
"""
남은 모든 미처리 데이터 정규화
"""

import asyncio
from loguru import logger
from src.services.product_pipeline import ProductPipeline
from src.services.database_service import DatabaseService


async def process_all_remaining():
    """남은 모든 데이터 처리"""
    pipeline = ProductPipeline()
    db = DatabaseService()
    
    # 전체 현황 확인
    total_raw = await db.select_data("raw_product_data", {})
    processed = await db.select_data("raw_product_data", {"is_processed": True})
    unprocessed = await db.select_data("raw_product_data", {"is_processed": False})
    
    logger.info("="*70)
    logger.info("📊 전체 데이터 현황")
    logger.info("="*70)
    logger.info(f"총 원본 데이터: {len(total_raw):,}개")
    logger.info(f"처리 완료: {len(processed):,}개")
    logger.info(f"미처리: {len(unprocessed):,}개")
    logger.info("="*70)
    
    if len(unprocessed) == 0:
        logger.info("✅ 모든 데이터가 이미 처리되었습니다!")
        return
    
    # 공급사별로 처리
    suppliers = {
        "오너클랜": "e458e4e2-cb03-4fc2-bff1-b05aaffde00f",
        "젠트레이드": "ab98eee5-fbc3-4c72-8a1f-e4fc2c03d2c7",
        "도매꾹(dome)": "d9e6fa42-9bd4-438f-bf3b-10cf199eabd2",
        "도매매(supply)": "a9990a09-ae6f-474b-87b8-75840a110519",
        "도매매(통합)": "baa2ccd3-a328-4387-b307-6ae89aea331b"
    }
    
    total_processed = 0
    total_failed = 0
    
    for name, supplier_id in suppliers.items():
        # 해당 공급사의 미처리 데이터 확인
        supplier_unprocessed = await db.select_data(
            "raw_product_data",
            {"supplier_id": supplier_id, "is_processed": False}
        )
        
        if len(supplier_unprocessed) == 0:
            logger.info(f"⏭️  {name}: 처리할 데이터 없음")
            continue
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 {name} 처리 시작: {len(supplier_unprocessed):,}개")
        logger.info(f"{'='*70}")
        
        # 배치 단위로 처리 (한 번에 너무 많이 처리하지 않도록)
        batch_size = 500
        total_for_supplier = len(supplier_unprocessed)
        
        for i in range(0, total_for_supplier, batch_size):
            batch_num = (i // batch_size) + 1
            total_batches = (total_for_supplier + batch_size - 1) // batch_size
            
            logger.info(f"\n📦 배치 {batch_num}/{total_batches} 처리 중...")
            
            from uuid import UUID
            result = await pipeline.process_all_unprocessed(
                supplier_id=UUID(supplier_id),
                limit=batch_size
            )
            
            logger.info(f"   결과: {result['success']:,}개 성공, {result['failed']:,}개 실패")
            
            total_processed += result['success']
            total_failed += result['failed']
    
    # 최종 결과
    logger.info(f"\n{'='*70}")
    logger.info("✅ 전체 처리 완료")
    logger.info(f"{'='*70}")
    logger.info(f"총 처리 성공: {total_processed:,}개")
    logger.info(f"총 처리 실패: {total_failed:,}개")
    
    # 최종 통계
    final_normalized = await db.select_data("normalized_products", {})
    logger.info(f"전체 정규화된 데이터: {len(final_normalized):,}개")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(process_all_remaining())

