#!/usr/bin/env python3
"""
도매꾹 카테고리 목록 조회
"""

import asyncio
import aiohttp
import json
from loguru import logger
from src.services.database_service import DatabaseService


async def get_domaemae_categories():
    """도매꾹 카테고리 목록 조회"""
    db = DatabaseService()
    
    logger.info("="*70)
    logger.info("📂 도매꾹 카테고리 목록 조회")
    logger.info("="*70)
    
    # 계정 정보
    accounts = await db.select_data(
        'supplier_accounts',
        {'supplier_id': 'baa2ccd3-a328-4387-b307-6ae89aea331b'}
    )
    
    if not accounts:
        logger.error("❌ 계정 없음")
        return
    
    credentials = json.loads(accounts[0]['account_credentials']) if isinstance(accounts[0]['account_credentials'], str) else accounts[0]['account_credentials']
    
    api_key = credentials.get('api_key')
    version = credentials.get('version', '4.1')
    
    # 카테고리 목록 조회 파라미터
    params = {
        "ver": version,
        "mode": "getCategoryList",  # 카테고리 목록 조회
        "aid": api_key,
        "isReg": "true",  # 등록 가능한 카테고리만
        "om": "json"
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://domeggook.com/'
    }
    
    url = "https://domeggook.com/ssl/api/"
    
    logger.info(f"URL: {url}")
    logger.info(f"Params: {params}")
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params) as response:
            logger.info(f"응답 상태: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                
                # 응답 구조 확인
                logger.info("\n📄 API 응답 구조:")
                logger.info(f"응답 키: {list(data.keys())}")
                
                # 전체 응답 저장 (디버깅용)
                with open('domaemae_category_response.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info("전체 응답이 domaemae_category_response.json에 저장됨")
                
                # 카테고리 데이터 파싱
                categories = []
                
                def parse_category(item, depth=0):
                    """재귀적으로 카테고리 파싱"""
                    category_info = {
                        "code": item.get("code", ""),
                        "name": item.get("name", ""),
                        "int": item.get("int"),  # 대량등록시 사용
                        "locked": item.get("locked"),
                        "depth": depth
                    }
                    
                    # 등록 가능한 카테고리만 (locked=FALSE 또는 int가 있는 경우)
                    if category_info["int"] is not None:
                        categories.append(category_info)
                        logger.info(f"{'  '*depth}{'└─' if depth > 0 else ''} {category_info['name']} ({category_info['code']}) [int:{category_info['int']}]")
                    
                    # 하위 카테고리 처리
                    child = item.get("child")
                    if child:
                        if isinstance(child, list):
                            for child_item in child:
                                parse_category(child_item, depth + 1)
                        elif isinstance(child, dict):
                            parse_category(child, depth + 1)
                
                # 최상위 카테고리부터 파싱
                items = data.get("domeggook", {}).get("items", {})
                
                if isinstance(items, dict):
                    items = [items]
                
                logger.info("\n📂 등록 가능한 카테고리 목록:\n")
                for item in items:
                    parse_category(item)
                
                logger.info(f"\n총 {len(categories)}개의 등록 가능한 카테고리 발견")
                
                # 결과 저장
                with open('domaemae_category_list.json', 'w', encoding='utf-8') as f:
                    json.dump(categories, f, ensure_ascii=False, indent=2)
                
                logger.info("💾 카테고리 목록이 domaemae_category_list.json에 저장되었습니다")
                
                # 상위 10개 카테고리로 상품 수 테스트
                logger.info("\n" + "="*70)
                logger.info("🧪 상위 카테고리별 상품 수 테스트 (도매꾹/도매매)")
                logger.info("="*70)
                
                test_categories = categories[:min(5, len(categories))]  # 상위 5개만
                
                for market in ["dome", "supply"]:
                    market_name = "도매꾹" if market == "dome" else "도매매"
                    logger.info(f"\n{market_name}:")
                    
                    for cat in test_categories:
                        test_params = {
                            "ver": version,
                            "mode": "getItemList",
                            "aid": api_key,
                            "market": market,
                            "om": "json",
                            "sz": 1,
                            "pg": 1,
                            "ca": cat["code"]  # 카테고리 코드 사용
                        }
                        
                        try:
                            async with session.get(url, params=test_params) as resp:
                                if resp.status == 200:
                                    test_data = await resp.json()
                                    count = test_data.get("domeggook", {}).get("header", {}).get("tcount", 0)
                                    logger.info(f"   {cat['name']:30s} ({cat['code']}): {count:>8,d}개")
                            
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            logger.error(f"   {cat['name']}: 오류 - {e}")
                
                return categories
            else:
                logger.error(f"❌ API 오류: {response.status}")
                error_text = await response.text()
                logger.error(f"오류 내용: {error_text[:200]}")


if __name__ == "__main__":
    asyncio.run(get_domaemae_categories())

