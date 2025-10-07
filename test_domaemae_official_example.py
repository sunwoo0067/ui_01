#!/usr/bin/env python3
"""
도매꾹 OpenAPI 공식 Python 예제 테스트
문서의 예제 코드를 정확히 재현
"""

import asyncio
import json
import requests
from loguru import logger
from src.services.database_service import DatabaseService


async def test_official_example():
    """공식 Python 예제 그대로 테스트"""
    db = DatabaseService()
    
    # 인증 정보
    accounts = await db.select_data(
        'supplier_accounts',
        {'supplier_id': 'baa2ccd3-a328-4387-b307-6ae89aea331b'}
    )
    
    credentials = json.loads(accounts[0]['account_credentials'])
    api_key = credentials.get('api_key')
    
    logger.info("="*70)
    logger.info("🧪 도매꾹 OpenAPI 공식 Python 예제 테스트")
    logger.info("="*70)
    
    # Setting URL (공식 예제 그대로)
    url = 'https://domeggook.com/ssl/api/'
    
    # Setting Request Parameters (공식 예제 그대로)
    param = dict()
    param['ver'] = '4.0'  # 예제는 4.0 사용
    param['mode'] = 'getItemList'
    param['aid'] = api_key
    param['market'] = 'dome'
    param['om'] = 'json'
    # 검색 조건 없음! (공식 예제가 이렇게 되어 있음)
    
    logger.info("\n📝 요청 파라미터:")
    for key, value in param.items():
        if key == 'aid':
            logger.info(f"   {key}: {value[:10]}...{value[-10:]}")
        else:
            logger.info(f"   {key}: {value}")
    
    # Getting API Response (동기 방식 - 예제 그대로)
    logger.info("\n📡 API 호출 중...")
    res = requests.get(url, params=param)
    
    logger.info(f"   응답 상태: {res.status_code}")
    
    if res.status_code == 200:
        # Parsing
        data = json.loads(res.content)
        
        logger.info("\n📄 응답 구조:")
        logger.info(f"   최상위 키: {list(data.keys())}")
        
        if 'domeggook' in data:
            dome_data = data['domeggook']
            logger.info(f"   domeggook 키: {list(dome_data.keys())}")
            
            header = dome_data.get('header', {})
            logger.info(f"\n📊 헤더 정보:")
            logger.info(f"   전체 상품: {header.get('numberOfItems', 0):,}개")
            logger.info(f"   현재 페이지: {header.get('currentPage', 0)}")
            logger.info(f"   페이지당 상품: {header.get('itemsPerPage', 0)}")
            logger.info(f"   전체 페이지: {header.get('numberOfPages', 0):,}개")
            
            items = dome_data.get('list', {}).get('item', [])
            if items:
                if isinstance(items, dict):
                    items = [items]
                
                logger.info(f"\n📦 상품 목록: {len(items)}개")
                logger.info(f"   첫 상품: {items[0].get('title', 'N/A')[:50]}...")
                logger.info(f"   상품번호: {items[0].get('no', 'N/A')}")
                logger.info(f"   가격: {items[0].get('price', 0):,}원")
        
        elif 'errors' in data:
            logger.error(f"\n❌ API 에러: {data['errors']}")
        
        # 전체 응답 저장
        with open('domaemae_official_example_response.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n💾 전체 응답이 domaemae_official_example_response.json에 저장됨")
    
    else:
        logger.error(f"API 호출 실패: {res.status_code}")
        logger.error(f"응답: {res.text[:500]}")
    
    # 추가 테스트: sz=200, pg=1 추가
    logger.info("\n" + "="*70)
    logger.info("🧪 추가 테스트: sz=200, pg=1 추가")
    logger.info("="*70)
    
    param['sz'] = 200
    param['pg'] = 1
    
    res2 = requests.get(url, params=param)
    
    if res2.status_code == 200:
        data2 = json.loads(res2.content)
        
        header2 = data2.get('domeggook', {}).get('header', {})
        items2 = data2.get('domeggook', {}).get('list', {}).get('item', [])
        
        logger.info(f"\n📊 결과:")
        logger.info(f"   전체 상품: {header2.get('numberOfItems', 0):,}개")
        logger.info(f"   이 페이지: {len(items2) if isinstance(items2, list) else 1}개")
        
        if header2.get('numberOfItems', 0) > 0:
            logger.info(f"\n✅ 성공! 파라미터 없이도 전체 상품 조회 가능!")
            logger.info(f"   전략: sz=200으로 페이지 순환하여 전체 수집")
    
    logger.info("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(test_official_example())

