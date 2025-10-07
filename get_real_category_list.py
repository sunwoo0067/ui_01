#!/usr/bin/env python3
"""
도매꾹 실제 카테고리 목록 조회 (getCategoryList API)
"""

import asyncio
import json
import requests
from loguru import logger
from src.services.database_service import DatabaseService


async def get_category_list():
    """getCategoryList API로 실제 카테고리 조회"""
    db = DatabaseService()
    
    # 인증 정보
    accounts = await db.select_data(
        'supplier_accounts',
        {'supplier_id': 'baa2ccd3-a328-4387-b307-6ae89aea331b'}
    )
    
    credentials = json.loads(accounts[0]['account_credentials'])
    api_key = credentials.get('api_key')
    
    logger.info("="*70)
    logger.info("📂 도매꾹 실제 카테고리 목록 조회")
    logger.info("="*70)
    
    url = 'https://domeggook.com/ssl/api/'
    
    # getCategoryList API 호출
    param = {
        'ver': '4.1',
        'mode': 'getCategoryList',
        'aid': api_key,
        'isReg': 'true',  # 등록 가능한 카테고리만
        'om': 'json'
    }
    
    logger.info("\n📡 getCategoryList API 호출 중...")
    res = requests.get(url, params=param)
    
    logger.info(f"   응답 상태: {res.status_code}")
    
    if res.status_code == 200:
        data = json.loads(res.content)
        
        # 전체 응답 저장
        with open('domaemae_real_categories.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info("💾 전체 카테고리가 domaemae_real_categories.json에 저장됨")
        
        # 에러 체크
        if 'errors' in data:
            logger.error(f"❌ API 에러: {data['errors']}")
            return []
        
        # 카테고리 파싱
        logger.info("\n📂 카테고리 구조 분석...")
        
        categories = []
        
        def parse_category(item, parent_path="", depth=0):
            """재귀적으로 카테고리 파싱"""
            code = item.get('code', '')
            name = item.get('name', '')
            locked = item.get('locked')
            int_val = item.get('int')
            
            full_name = f"{parent_path} > {name}" if parent_path else name
            
            # int 값이 있으면 등록 가능한 카테고리
            if int_val is not None:
                categories.append({
                    'code': code,
                    'name': name,
                    'full_name': full_name,
                    'int': int_val,
                    'locked': locked,
                    'depth': depth
                })
                
                if depth <= 2:  # 중분류까지만 로그 출력
                    logger.info(f"   {'  ' * depth}└─ {name} ({code}) [int: {int_val}]")
            
            # 하위 카테고리
            child = item.get('child')
            if child:
                if isinstance(child, list):
                    for c in child:
                        parse_category(c, full_name, depth + 1)
                elif isinstance(child, dict):
                    parse_category(child, full_name, depth + 1)
        
        items = data.get('domeggook', {}).get('items')
        if items:
            if isinstance(items, list):
                for item in items:
                    parse_category(item)
            else:
                parse_category(items)
        
        logger.info(f"\n✅ 총 {len(categories)}개 등록 가능한 카테고리 발견")
        
        # 카테고리 리스트 저장
        with open('domaemae_category_codes.json', 'w', encoding='utf-8') as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
        
        logger.info("💾 카테고리 목록이 domaemae_category_codes.json에 저장됨")
        
        # 중분류 카테고리만 추출 (배치 수집용)
        mid_categories = [c for c in categories if c['depth'] == 1]
        
        logger.info(f"\n📋 중분류 카테고리 ({len(mid_categories)}개):")
        for cat in mid_categories[:10]:  # 처음 10개만
            logger.info(f"   {cat['full_name']} ({cat['code']})")
        
        if len(mid_categories) > 10:
            logger.info(f"   ... 외 {len(mid_categories) - 10}개")
        
        return categories
    
    else:
        logger.error(f"API 호출 실패: {res.status_code}")
        return []


if __name__ == "__main__":
    asyncio.run(get_category_list())

