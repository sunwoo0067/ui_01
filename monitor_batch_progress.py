#!/usr/bin/env python3
"""
배치 수집 진행 상황 실시간 모니터링
"""

import asyncio
import time
from datetime import datetime
from loguru import logger
from src.services.database_service import DatabaseService


async def monitor_progress():
    """배치 수집 진행 상황 모니터링"""
    db = DatabaseService()
    
    supplier_info = {
        "오너클랜": "e458e4e2-cb03-4fc2-bff1-b05aaffde00f",
        "도매꾹(dome)": "d9e6fa42-9bd4-438f-bf3b-10cf199eabd2",
        "도매매(supply)": "a9990a09-ae6f-474b-87b8-75840a110519"
    }
    
    start_counts = {}
    
    # 초기 카운트 기록
    logger.info("="*70)
    logger.info("📊 배치 수집 진행 상황 모니터링 시작")
    logger.info(f"   시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70)
    
    for name, supplier_id in supplier_info.items():
        data = await db.select_data('raw_product_data', {'supplier_id': supplier_id})
        start_counts[name] = len(data)
        logger.info(f"   {name}: {len(data):,}개")
    
    logger.info("\n⏱️  10초마다 업데이트... (Ctrl+C로 종료)\n")
    
    try:
        iteration = 0
        while True:
            await asyncio.sleep(10)
            iteration += 1
            
            logger.info(f"\n[{iteration}] {datetime.now().strftime('%H:%M:%S')} 업데이트:")
            
            for name, supplier_id in supplier_info.items():
                data = await db.select_data('raw_product_data', {'supplier_id': supplier_id})
                current = len(data)
                diff = current - start_counts[name]
                
                if diff > 0:
                    logger.info(f"   {name}: {current:,}개 (+{diff:,})")
                else:
                    logger.info(f"   {name}: {current:,}개")
    
    except KeyboardInterrupt:
        logger.info("\n\n" + "="*70)
        logger.info("📊 최종 수집 결과")
        logger.info("="*70)
        
        for name, supplier_id in supplier_info.items():
            data = await db.select_data('raw_product_data', {'supplier_id': supplier_id})
            current = len(data)
            diff = current - start_counts[name]
            
            logger.info(f"\n{name}:")
            logger.info(f"   시작: {start_counts[name]:,}개")
            logger.info(f"   현재: {current:,}개")
            logger.info(f"   증가: +{diff:,}개")
        
        logger.info("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(monitor_progress())

