#!/usr/bin/env python3
"""
실제 수집된 도매꾹 데이터 구조 확인
"""

import asyncio
import json
from loguru import logger
from src.services.supabase_client import supabase_client


async def check_actual_data():
    """실제 도매꾹 데이터 확인"""
    
    response = (
        supabase_client.get_table("raw_product_data")
        .select("*")
        .eq("supplier_id", "d9e6fa42-9bd4-438f-bf3b-10cf199eabd2")
        .limit(1)
        .execute()
    )
    
    if response.data:
        record = response.data[0]
        raw_data = record['raw_data']
        
        logger.info(f"raw_data 타입: {type(raw_data)}")
        
        # 문자열이면 파싱
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)
            logger.info("✅ 문자열을 dict로 파싱함")
        
        logger.info(f"\n실제 데이터 필드:")
        for key in raw_data.keys():
            logger.info(f"  - {key}: {type(raw_data[key]).__name__}")
        
        logger.info(f"\n샘플 값 (처음 10개):")
        for i, (key, value) in enumerate(list(raw_data.items())[:10]):
            logger.info(f"  {key}: {value}")
    else:
        logger.info("데이터 없음")


if __name__ == "__main__":
    asyncio.run(check_actual_data())

