#!/usr/bin/env python3
"""
기존 도매꾹 데이터 상세 분석
"""

import asyncio
import json
import aiohttp
from loguru import logger
from src.services.database_service import DatabaseService


async def debug_existing_data():
    """기존 데이터 상세 분석"""
    db = DatabaseService()
    
    logger.info("="*70)
    logger.info("🔬 기존 도매꾹 데이터 상세 분석")
    logger.info("="*70)
    
    # 모든 도매꾹 관련 공급사 데이터 확인
    all_suppliers = {
        "domaemae": "baa2ccd3-a328-4387-b307-6ae89aea331b",
        "domaemae_dome": "d9e6fa42-9bd4-438f-bf3b-10cf199eabd2",
        "domaemae_supply": "a9990a09-ae6f-474b-87b8-75840a110519"
    }
    
    for name, supplier_id in all_suppliers.items():
        logger.info(f"\n📂 {name}:")
        
        data = await db.select_data('raw_product_data', {'supplier_id': supplier_id})
        logger.info(f"   저장된 데이터: {len(data)}개")
        
        if data and len(data) > 0:
            # 첫 번째 데이터 상세 분석
            sample = data[0]
            
            logger.info(f"\n   📦 첫 번째 상품:")
            logger.info(f"      supplier_product_id: {sample.get('supplier_product_id')}")
            logger.info(f"      created_at: {sample.get('created_at')}")
            
            # raw_data 파싱
            raw_str = sample.get('raw_data')
            if raw_str:
                raw = json.loads(raw_str) if isinstance(raw_str, str) else raw_str
                
                logger.info(f"\n   📄 원본 데이터:")
                logger.info(f"      상품명: {raw.get('title', 'N/A')}")
                logger.info(f"      가격: {raw.get('price', 0):,}원")
                logger.info(f"      시장: {raw.get('market', 'N/A')}")
                logger.info(f"      수집 키워드: {raw.get('search_keyword', 'N/A')}")
                
                # 메타데이터 확인
                metadata_str = sample.get('metadata')
                if metadata_str:
                    metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
                    logger.info(f"\n   🏷️ 메타데이터:")
                    logger.info(f"      collected_at: {metadata.get('collected_at', 'N/A')}")
                    logger.info(f"      기타: {metadata}")
            
            # 여러 샘플 확인 (다양성 체크)
            logger.info(f"\n   📊 상품 다양성 (처음 10개):")
            for i, item in enumerate(data[:10], 1):
                raw_str = item.get('raw_data')
                if raw_str:
                    raw = json.loads(raw_str) if isinstance(raw_str, str) else raw_str
                    logger.info(f"      {i}. {raw.get('title', 'N/A')[:30]}... - {raw.get('price', 0):,}원")
    
    # 현재 API 상태 확인
    logger.info("\n" + "="*70)
    logger.info("🔍 현재 API 상태 확인")
    logger.info("="*70)
    
    accounts = await db.select_data(
        'supplier_accounts',
        {'supplier_id': 'baa2ccd3-a328-4387-b307-6ae89aea331b'}
    )
    
    if accounts:
        credentials = json.loads(accounts[0]['account_credentials'])
        api_key = credentials.get('api_key')
        version = credentials.get('version', '4.1')
        
        # 실제 API 호출 (키워드 "상품")
        params = {
            "ver": version,
            "mode": "getItemList",
            "aid": api_key,
            "market": "dome",
            "om": "json",
            "sz": 1,
            "pg": 1,
            "kw": "상품"
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://domeggook.com/'
        }
        
        url = "https://domeggook.com/ssl/api/"
        
        logger.info(f"\nAPI 호출 테스트 (kw='상품'):")
        logger.info(f"  URL: {url}")
        logger.info(f"  Market: dome")
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as response:
                logger.info(f"  응답 상태: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # 응답 전체 구조 확인
                    logger.info(f"\n  응답 구조:")
                    logger.info(f"    최상위 키: {list(data.keys())}")
                    
                    if "domeggook" in data:
                        dome_data = data["domeggook"]
                        logger.info(f"    domeggook 키: {list(dome_data.keys())}")
                        
                        if "header" in dome_data:
                            header = dome_data["header"]
                            logger.info(f"\n  헤더 정보:")
                            logger.info(f"    tcount: {header.get('tcount', 0)}")
                            logger.info(f"    기타: {header}")
                        
                        if "itemList" in dome_data:
                            item_list = dome_data["itemList"]
                            logger.info(f"\n  아이템 리스트:")
                            logger.info(f"    타입: {type(item_list)}")
                            if isinstance(item_list, dict):
                                logger.info(f"    키: {list(item_list.keys())}")
                                items = item_list.get("item")
                                if items:
                                    logger.info(f"    item 타입: {type(items)}")
                                    logger.info(f"    item 개수: {len(items) if isinstance(items, list) else 1}")
                    
                    # 전체 응답 저장
                    with open('domaemae_api_response_debug.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    logger.info(f"\n  💾 전체 응답이 domaemae_api_response_debug.json에 저장됨")
    
    logger.info("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(debug_existing_data())

