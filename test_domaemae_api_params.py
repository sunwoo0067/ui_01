#!/usr/bin/env python3
"""
도매꾹 API 파라미터 실험
실제로 작동하는 파라미터 조합 찾기
"""

import asyncio
import aiohttp
import json
from loguru import logger
from src.services.database_service import DatabaseService


async def test_api_params():
    """다양한 API 파라미터 조합 테스트"""
    db = DatabaseService()
    
    # 인증 정보
    accounts = await db.select_data(
        'supplier_accounts',
        {'supplier_id': 'baa2ccd3-a328-4387-b307-6ae89aea331b'}
    )
    
    credentials = json.loads(accounts[0]['account_credentials'])
    api_key = credentials.get('api_key')
    version = credentials.get('version', '4.1')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://domeggook.com/'
    }
    
    url = "https://domeggook.com/ssl/api/"
    
    logger.info("="*70)
    logger.info("🧪 도매꾹 API 파라미터 실험")
    logger.info("="*70)
    
    # 성공했던 방식 재현
    logger.info("\n✅ 테스트 1: 이전 성공 방식 (키워드 '상품')")
    params1 = {
        "ver": version,
        "mode": "getItemList",
        "aid": api_key,
        "market": "dome",
        "om": "json",
        "sz": 10,
        "pg": 1,
        "kw": "상품"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params1) as response:
            if response.status == 200:
                data = await response.json()
                count = data.get("domeggook", {}).get("header", {}).get("tcount", 0)
                items = data.get("domeggook", {}).get("itemList", {}).get("item", [])
                logger.info(f"   결과: {count:,}개 (실제 반환: {len(items) if isinstance(items, list) else 1}개)")
                
                # 실제 상품 확인
                if items:
                    if isinstance(items, dict):
                        items = [items]
                    if items:
                        logger.info(f"   샘플: {items[0].get('it_name', 'N/A')}")
    
    await asyncio.sleep(1)
    
    # 빈 키워드 테스트
    logger.info("\n🧪 테스트 2: 빈 키워드 ('')")
    params2 = {
        "ver": version,
        "mode": "getItemList",
        "aid": api_key,
        "market": "dome",
        "om": "json",
        "sz": 10,
        "pg": 1,
        "kw": ""
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params2) as response:
            if response.status == 200:
                data = await response.json()
                count = data.get("domeggook", {}).get("header", {}).get("tcount", 0)
                logger.info(f"   결과: {count:,}개")
    
    await asyncio.sleep(1)
    
    # 와일드카드 테스트
    logger.info("\n🧪 테스트 3: 와일드카드 키워드 ('*' 또는 '%')")
    for wildcard in ["*", "%", ".", " "]:
        params = {
            "ver": version,
            "mode": "getItemList",
            "aid": api_key,
            "market": "dome",
            "om": "json",
            "sz": 10,
            "pg": 1,
            "kw": wildcard
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    count = data.get("domeggook", {}).get("header", {}).get("tcount", 0)
                    logger.info(f"   kw='{wildcard}': {count:,}개")
        
        await asyncio.sleep(0.5)
    
    # 모든 파라미터 생략 (키워드, 카테고리 모두 없음)
    logger.info("\n🧪 테스트 4: 검색 파라미터 없음 (kw, ca 모두 생략)")
    params4 = {
        "ver": version,
        "mode": "getItemList",
        "aid": api_key,
        "market": "dome",
        "om": "json",
        "sz": 10,
        "pg": 1
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params4) as response:
            if response.status == 200:
                data = await response.json()
                if "errors" in data:
                    logger.error(f"   에러: {data['errors'].get('message')}")
                else:
                    count = data.get("domeggook", {}).get("header", {}).get("tcount", 0)
                    logger.info(f"   결과: {count:,}개")
    
    logger.info("\n" + "="*70)
    logger.info("💡 실험 결론:")
    logger.info("   - 키워드 검색은 작동하지만 전체가 아닌 검색 결과만 반환")
    logger.info("   - 카테고리 검색은 작동하지 않음 (0개)")
    logger.info("   - 최소 하나의 파라미터 필수 (kw 또는 ca)")
    logger.info("\n🔑 추천 방법:")
    logger.info("   1. 주요 키워드 리스트로 순환 수집")
    logger.info("   2. 공백(' '), 별표('*') 등 시도")
    logger.info("   3. 판매자 ID 기반 수집 (만약 지원된다면)")
    logger.info("="*70)


if __name__ == "__main__":
    asyncio.run(test_api_params())

