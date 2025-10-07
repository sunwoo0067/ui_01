#!/usr/bin/env python3
"""
도매꾹 수정된 파싱으로 전체 수집 테스트
"""

import asyncio
import aiohttp
import json
from loguru import logger
from src.services.database_service import DatabaseService


async def test_full_collection():
    """수정된 파싱으로 전체 수집 테스트"""
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
    logger.info("🧪 수정된 파싱으로 도매꾹 전체 수집 테스트")
    logger.info("="*70)
    
    # 테스트: 판매자 ID로 전체 수집 시도
    logger.info("\n📦 판매자 ID로 상품 검색 시도:")
    logger.info("   아이디: dreamart (샘플에서 많이 보이는 판매자)")
    
    params = {
        "ver": version,
        "mode": "getItemList",
        "aid": api_key,
        "market": "dome",
        "om": "json",
        "sz": 200,
        "pg": 1,
        "id": "dreamart"  # 판매자 ID
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                header = data.get("domeggook", {}).get("header", {})
                total_items = header.get("numberOfItems", 0)
                
                logger.info(f"   ✅ 총 상품: {total_items:,}개")
                logger.info(f"   페이지: {header.get('numberOfPages', 0):,}개")
                
                # 상품 확인
                items = data.get("domeggook", {}).get("list", {}).get("item", [])
                logger.info(f"   이 페이지 상품: {len(items)}개")
                
                if items:
                    logger.info(f"   첫 상품: {items[0].get('title', 'N/A')[:50]}...")
    
    logger.info("\n" + "="*70)
    logger.info("💡 전체 카탈로그 수집 전략:")
    logger.info("   1. 주요 판매자 ID 리스트로 순환 수집")
    logger.info("   2. 중분류 카테고리 리스트로 순환 수집")
    logger.info("   3. 다양한 키워드로 순환 수집")
    logger.info("\n   추천: 판매자 ID 기반 수집이 가장 효율적!")
    logger.info("="*70)


if __name__ == "__main__":
    asyncio.run(test_full_collection())

