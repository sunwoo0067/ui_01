#!/usr/bin/env python3
"""
기존에 수집된 도매꾹 데이터 분석
어떤 파라미터로 수집되었는지 확인
"""

import asyncio
import json
from loguru import logger
from src.services.database_service import DatabaseService


async def check_collected_data():
    """수집된 도매꾹 데이터 분석"""
    db = DatabaseService()
    
    logger.info("="*70)
    logger.info("🔍 기존 수집 데이터 분석")
    logger.info("="*70)
    
    # 도매꾹(dome) 데이터 확인
    dome_data = await db.select_data(
        'raw_product_data',
        {'supplier_id': 'd9e6fa42-9bd4-438f-bf3b-10cf199eabd2'}
    )
    
    logger.info(f"\n도매꾹(dome) 수집 데이터: {len(dome_data)}개")
    
    if dome_data:
        # 샘플 데이터 확인
        sample = dome_data[0]
        logger.info(f"\n📦 샘플 데이터:")
        logger.info(f"  supplier_product_id: {sample.get('supplier_product_id')}")
        logger.info(f"  collection_source: {sample.get('collection_source')}")
        logger.info(f"  collection_method: {sample.get('collection_method')}")
        
        # raw_data 파싱
        raw_data_str = sample.get('raw_data')
        if raw_data_str:
            if isinstance(raw_data_str, str):
                raw_data = json.loads(raw_data_str)
            else:
                raw_data = raw_data_str
            
            logger.info(f"\n원본 데이터 구조:")
            logger.info(f"  키: {list(raw_data.keys())}")
            logger.info(f"  상품명: {raw_data.get('title', 'N/A')}")
            logger.info(f"  가격: {raw_data.get('price', 0):,}원")
            logger.info(f"  카테고리 코드: {raw_data.get('category_code', 'N/A')}")
            logger.info(f"  카테고리명: {raw_data.get('category_name', 'N/A')}")
            logger.info(f"  시장: {raw_data.get('market', 'N/A')}")
        
        # 카테고리 통계
        logger.info(f"\n📊 카테고리 통계:")
        category_counts = {}
        
        for data in dome_data[:100]:  # 처음 100개만 확인
            try:
                raw_str = data.get('raw_data')
                if isinstance(raw_str, str):
                    raw = json.loads(raw_str)
                else:
                    raw = raw_str
                
                cat_code = raw.get('category_code', 'unknown')
                cat_name = raw.get('category_name', 'unknown')
                
                key = f"{cat_name} ({cat_code})"
                category_counts[key] = category_counts.get(key, 0) + 1
            except:
                continue
        
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  {cat}: {count}개")
    
    # 도매매(supply) 데이터 확인
    supply_data = await db.select_data(
        'raw_product_data',
        {'supplier_id': 'a9990a09-ae6f-474b-87b8-75840a110519'}
    )
    
    logger.info(f"\n도매매(supply) 수집 데이터: {len(supply_data)}개")
    
    if supply_data:
        sample = supply_data[0]
        raw_data_str = sample.get('raw_data')
        if raw_data_str:
            if isinstance(raw_data_str, str):
                raw_data = json.loads(raw_data_str)
            else:
                raw_data = raw_data_str
            
            logger.info(f"\n📦 샘플 데이터:")
            logger.info(f"  상품명: {raw_data.get('title', 'N/A')}")
            logger.info(f"  가격: {raw_data.get('price', 0):,}원")
    
    logger.info("\n" + "="*70)
    logger.info("💡 분석 결과:")
    logger.info("   - 기존 수집은 키워드 '상품'으로 일부만 수집")
    logger.info("   - 전체 카탈로그 수집을 위해서는 카테고리 순환 필요")
    logger.info("   - 하지만 현재 카테고리 조회/검색이 작동하지 않음")
    logger.info("\n🔍 가능한 원인:")
    logger.info("   1. API 키 권한 부족 (카테고리 API 미허용)")
    logger.info("   2. API 버전 불일치")
    logger.info("   3. 파라미터 형식 오류")
    logger.info("="*70)


if __name__ == "__main__":
    asyncio.run(check_collected_data())

