#!/usr/bin/env python3
"""
전체 배치 수집 현황 확인
"""

import asyncio
from datetime import datetime
from loguru import logger
from src.services.database_service import DatabaseService


async def check_status():
    """현재 수집 현황 확인"""
    db = DatabaseService()
    
    logger.info("="*70)
    logger.info("📊 전체 배치 수집 현황")
    logger.info(f"   확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70)
    
    suppliers = {
        "오너클랜": "e458e4e2-cb03-4fc2-bff1-b05aaffde00f",
        "젠트레이드": "ab98eee5-fbc3-4c72-8a1f-e4fc2c03d2c7",
        "도매꾹(dome)": "d9e6fa42-9bd4-438f-bf3b-10cf199eabd2",
        "도매매(supply)": "a9990a09-ae6f-474b-87b8-75840a110519",
        "도매매(통합)": "baa2ccd3-a328-4387-b307-6ae89aea331b"
    }
    
    total_raw = 0
    total_normalized = 0
    
    for name, supplier_id in suppliers.items():
        logger.info(f"\n{'='*70}")
        logger.info(f"📦 {name}")
        logger.info(f"   Supplier ID: {supplier_id}")
        logger.info(f"{'='*70}")
        
        # Raw 데이터
        raw_data = await db.select_data('raw_product_data', {'supplier_id': supplier_id})
        logger.info(f"   📥 원본 데이터: {len(raw_data):,}개")
        
        total_raw += len(raw_data)
        
        if raw_data:
            # 처리 상태
            processed = [d for d in raw_data if d.get('is_processed')]
            unprocessed = [d for d in raw_data if not d.get('is_processed')]
            
            logger.info(f"      ✅ 처리됨: {len(processed):,}개")
            logger.info(f"      ⏳ 미처리: {len(unprocessed):,}개")
            
            # 수집 방법 통계
            collection_methods = {}
            for d in raw_data[:100]:  # 샘플 100개만
                method = d.get('collection_source', 'unknown')
                collection_methods[method] = collection_methods.get(method, 0) + 1
            
            if collection_methods:
                logger.info(f"      📌 수집 방법 (샘플 100개):")
                for method, count in sorted(collection_methods.items(), key=lambda x: x[1], reverse=True):
                    logger.info(f"         {method}: {count}개")
        
        # 정규화 데이터
        normalized = await db.select_data('normalized_products', {'supplier_id': supplier_id})
        logger.info(f"   📤 정규화됨: {len(normalized):,}개")
        
        total_normalized += len(normalized)
    
    logger.info(f"\n{'='*70}")
    logger.info("📊 전체 요약")
    logger.info(f"{'='*70}")
    logger.info(f"   총 원본 데이터: {total_raw:,}개")
    logger.info(f"   총 정규화 데이터: {total_normalized:,}개")
    logger.info(f"   처리율: {(total_normalized/total_raw*100) if total_raw > 0 else 0:.1f}%")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(check_status())

