#!/usr/bin/env python3
"""
도매꾹/도매매 카테고리 확인 및 테스트
"""

import asyncio
import aiohttp
from loguru import logger
from src.services.database_service import DatabaseService


async def test_domaemae_categories():
    """도매꾹 카테고리 구조 확인"""
    db = DatabaseService()
    
    logger.info("="*70)
    logger.info("🔍 도매꾹/도매매 카테고리 확인")
    logger.info("="*70)
    
    # 계정 정보 가져오기
    accounts = await db.select_data(
        'supplier_accounts',
        {'supplier_id': 'baa2ccd3-a328-4387-b307-6ae89aea331b'}
    )
    
    if not accounts:
        logger.error("❌ 도매꾹 계정이 없습니다")
        return
    
    import json
    credentials = json.loads(accounts[0]['account_credentials']) if isinstance(accounts[0]['account_credentials'], str) else accounts[0]['account_credentials']
    
    api_key = credentials.get('api_key')
    version = credentials.get('version', '4.1')
    
    # 도매꾹 카테고리 목록 테스트
    logger.info("\n📂 도매꾹(dome) 카테고리 테스트:")
    
    # 카테고리별 상품 수 확인
    test_categories = [
        {"cat": "", "name": "전체 카테고리"},
        {"cat": "1", "name": "패션/의류"},
        {"cat": "2", "name": "뷰티/화장품"},
        {"cat": "3", "name": "디지털/가전"},
        {"cat": "4", "name": "식품"},
        {"cat": "5", "name": "생활/건강"},
        {"cat": "6", "name": "유아동"},
        {"cat": "7", "name": "스포츠/레저"},
        {"cat": "8", "name": "문구/도서"}
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://domeggook.com/'
    }
    
    results = []
    
    for category in test_categories:
        try:
            params = {
                "ver": version,
                "mode": "getItemList",
                "aid": api_key,
                "market": "dome",
                "om": "json",
                "sz": 10,  # 샘플 10개만
                "pg": 1
            }
            
            if category["cat"]:
                params["cat"] = category["cat"]
            
            url = "https://domeggook.com/ssl/api/"
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 응답 구조 확인
                        total_count = 0
                        if "domeggook" in data:
                            dome_data = data["domeggook"]
                            if "header" in dome_data:
                                total_count = int(dome_data["header"].get("tcount", 0))
                        
                        result_info = {
                            "category": category["name"],
                            "cat_code": category["cat"],
                            "total_products": total_count
                        }
                        
                        results.append(result_info)
                        
                        logger.info(f"   {category['name']:20s} (cat={category['cat'] or '없음':3s}): {total_count:>6,d}개")
                    else:
                        logger.error(f"   {category['name']}: API 오류 {response.status}")
            
            await asyncio.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            logger.error(f"   {category['name']}: 오류 - {e}")
    
    # 도매매(supply) 카테고리 테스트
    logger.info("\n📂 도매매(supply) 카테고리 테스트:")
    
    for category in test_categories:
        try:
            params = {
                "ver": version,
                "mode": "getItemList",
                "aid": api_key,
                "market": "supply",  # 도매매
                "om": "json",
                "sz": 10,
                "pg": 1
            }
            
            if category["cat"]:
                params["cat"] = category["cat"]
            
            url = "https://domeggook.com/ssl/api/"
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        total_count = 0
                        if "domeggook" in data:
                            dome_data = data["domeggook"]
                            if "header" in dome_data:
                                total_count = int(dome_data["header"].get("tcount", 0))
                        
                        logger.info(f"   {category['name']:20s} (cat={category['cat'] or '없음':3s}): {total_count:>6,d}개")
                    else:
                        logger.error(f"   {category['name']}: API 오류 {response.status}")
            
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"   {category['name']}: 오류 - {e}")
    
    logger.info("\n" + "="*70)
    logger.info("💡 카테고리 기반 수집 전략:")
    logger.info("   - 각 카테고리별로 순회하며 전체 상품 수집")
    logger.info("   - 카테고리당 페이징으로 모든 상품 확보")
    logger.info("   - 전체 카탈로그 동기화 보장")
    logger.info("="*70)
    
    # 결과 저장
    with open('domaemae_categories.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info("\n💾 카테고리 정보가 domaemae_categories.json에 저장되었습니다")


if __name__ == "__main__":
    asyncio.run(test_domaemae_categories())

