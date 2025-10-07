#!/usr/bin/env python3
"""
도매꾹 API 분석 - 카테고리 파라미터 확인
"""

import asyncio
import aiohttp
import json as json_lib
from loguru import logger
from src.services.database_service import DatabaseService


async def analyze_domaemae_api():
    """도매꾹 API 파라미터 분석"""
    db = DatabaseService()
    
    logger.info("="*70)
    logger.info("🔍 도매꾹 API 파라미터 분석")
    logger.info("="*70)
    
    # 계정 정보
    accounts = await db.select_data(
        'supplier_accounts',
        {'supplier_id': 'baa2ccd3-a328-4387-b307-6ae89aea331b'}
    )
    
    if not accounts:
        logger.error("❌ 계정 없음")
        return
    
    credentials = json_lib.loads(accounts[0]['account_credentials']) if isinstance(accounts[0]['account_credentials'], str) else accounts[0]['account_credentials']
    
    api_key = credentials.get('api_key')
    version = credentials.get('version', '4.1')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://domeggook.com/'
    }
    
    url = "https://domeggook.com/ssl/api/"
    
    # 테스트 1: 기본 파라미터 (키워드 없음)
    logger.info("\n테스트 1: 기본 파라미터 (키워드 없음)")
    params1 = {
        "ver": version,
        "mode": "getItemList",
        "aid": api_key,
        "market": "dome",
        "om": "json",
        "sz": 10,
        "pg": 1
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params1) as response:
            if response.status == 200:
                data = await response.json()
                total = data.get("domeggook", {}).get("header", {}).get("tcount", 0)
                logger.info(f"   응답: {total}개 상품")
                
                # 상품 샘플 확인
                items = data.get("domeggook", {}).get("itemList", {}).get("item", [])
                if items and isinstance(items, list) and len(items) > 0:
                    sample = items[0]
                    logger.info(f"   샘플 상품: {sample.get('it_name', 'N/A')}")
                    logger.info(f"   카테고리 정보: {sample.get('ca_name', 'N/A')}")
                    logger.info(f"   카테고리 코드: {sample.get('ca_id', 'N/A')}")
    
    await asyncio.sleep(1)
    
    # 테스트 2: 키워드 검색
    logger.info("\n테스트 2: 키워드 검색 (kw='상품')")
    params2 = {
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
        async with session.get(url, params=params2) as response:
            if response.status == 200:
                data = await response.json()
                total = data.get("domeggook", {}).get("header", {}).get("tcount", 0)
                logger.info(f"   응답: {total}개 상품")
    
    await asyncio.sleep(1)
    
    # 테스트 3: 카테고리 파라미터 테스트
    logger.info("\n테스트 3: 다양한 카테고리 파라미터 테스트")
    
    category_params = [
        {"param": "ca", "value": "01", "desc": "ca=01"},
        {"param": "cat", "value": "01", "desc": "cat=01"},
        {"param": "cate", "value": "01", "desc": "cate=01"},
        {"param": "category", "value": "01", "desc": "category=01"},
        {"param": "ca_id", "value": "01", "desc": "ca_id=01"},
    ]
    
    for test in category_params:
        params = {
            "ver": version,
            "mode": "getItemList",
            "aid": api_key,
            "market": "dome",
            "om": "json",
            "sz": 10,
            "pg": 1,
            test["param"]: test["value"]
        }
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        total = data.get("domeggook", {}).get("header", {}).get("tcount", 0)
                        logger.info(f"   {test['desc']:20s}: {total:>6,d}개")
                    else:
                        logger.error(f"   {test['desc']:20s}: 오류 {response.status}")
        except Exception as e:
            logger.error(f"   {test['desc']:20s}: {e}")
        
        await asyncio.sleep(0.5)
    
    logger.info("\n" + "="*70)
    logger.info("💡 분석 결과:")
    logger.info("   - 도매꾹 API는 카테고리 파라미터를 지원할 수 있음")
    logger.info("   - 하지만 빈 결과는 파라미터 이름 또는 값이 잘못됨을 의미")
    logger.info("   - 키워드 기반 수집이 현재 가장 효과적")
    logger.info("="*70)


if __name__ == "__main__":
    asyncio.run(analyze_domaemae_api())

