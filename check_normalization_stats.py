#!/usr/bin/env python3
"""
전체 정규화 상품 통계 확인
"""

import asyncio
from loguru import logger
from src.services.supabase_client import supabase_client


async def check_stats():
    """통계 확인"""
    
    suppliers = [
        ('오너클랜', 'e458e4e2-cb03-4fc2-bff1-b05aaffde00f'),
        ('젠트레이드', '959ddf49-c25f-4ebb-a292-bc4e0f1cd28a'),
        ('도매꾹', 'baa2ccd3-a328-4387-b307-6ae89aea331b')
    ]
    
    logger.info("="*70)
    logger.info("📊 전체 정규화 상품 통계")
    logger.info("="*70)
    
    total = 0
    
    for name, supplier_id in suppliers:
        # 정규화 상품 수
        norm_result = (
            supabase_client.get_table('normalized_products')
            .select('id', count='exact')
            .eq('supplier_id', supplier_id)
            .execute()
        )
        
        # 원본 데이터 수
        raw_result = (
            supabase_client.get_table('raw_product_data')
            .select('id', count='exact')
            .eq('supplier_id', supplier_id)
            .execute()
        )
        
        # 미처리 수
        unprocessed_result = (
            supabase_client.get_table('raw_product_data')
            .select('id', count='exact')
            .eq('supplier_id', supplier_id)
            .eq('is_processed', False)
            .execute()
        )
        
        norm_count = norm_result.count
        raw_count = raw_result.count
        unprocessed = unprocessed_result.count
        
        processing_rate = ((raw_count - unprocessed) / raw_count * 100) if raw_count > 0 else 0
        
        logger.info(f"\n{name}:")
        logger.info(f"  원본 데이터: {raw_count:,}개")
        logger.info(f"  정규화 완료: {norm_count:,}개")
        logger.info(f"  미처리: {unprocessed:,}개")
        logger.info(f"  처리율: {processing_rate:.1f}%")
        
        total += norm_count
    
    logger.info(f"\n{'='*70}")
    logger.info(f"🎉 총 정규화 상품: {total:,}개")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(check_stats())

