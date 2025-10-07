#!/usr/bin/env python3
"""
젠트레이드 API 디버깅 스크립트
"""

import asyncio
import aiohttp
from src.services.database_service import DatabaseService
from loguru import logger


async def debug_zentrade_api():
    """젠트레이드 API 직접 호출 디버깅"""
    db = DatabaseService()
    
    logger.info("="*60)
    logger.info("🔍 젠트레이드 API 디버깅")
    logger.info("="*60)
    
    # 1. 계정 정보 조회
    accounts = await db.select_data(
        'supplier_accounts',
        {'supplier_id': '959ddf49-c25f-4ebb-a292-bc4e0f1cd28a'}
    )
    
    if not accounts:
        logger.error("❌ 젠트레이드 계정이 없습니다!")
        return
    
    account = accounts[0]
    logger.info(f"계정명: {account['account_name']}")
    
    import json
    credentials = json.loads(account['account_credentials']) if isinstance(account['account_credentials'], str) else account['account_credentials']
    
    logger.info(f"인증 정보:")
    logger.info(f"  - id: {credentials.get('id', 'MISSING')}")
    logger.info(f"  - m_skey: {credentials.get('m_skey', 'MISSING')[:20]}..." if credentials.get('m_skey') else "  - m_skey: MISSING")
    
    # 2. API 직접 호출 테스트
    url = "https://www.zentrade.co.kr/shop/proc/product_api.php"
    
    # 브라우저 헤더 추가 (WAF 우회)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Referer': 'https://www.zentrade.co.kr/',
        'Origin': 'https://www.zentrade.co.kr',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # 테스트 1: POST 방식으로 최소 파라미터만 (id, m_skey)
    logger.info("\n테스트 1: POST 방식 - 최소 파라미터 (id, m_skey)")
    params = {
        "id": credentials.get("id"),
        "m_skey": credentials.get("m_skey")
    }
    
    logger.info(f"URL: {url}")
    logger.info(f"Params: {params}")
    logger.info(f"Headers: User-Agent 추가됨")
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, data=params, timeout=30) as response:
                logger.info(f"응답 상태 코드: {response.status}")
                logger.info(f"응답 헤더: {dict(response.headers)}")
                
                if response.status == 200:
                    content = await response.text(encoding='euc-kr')
                    logger.info(f"응답 길이: {len(content)} 바이트")
                    logger.info(f"응답 시작 부분:\n{content[:500]}")
                    
                    # XML 파싱 테스트
                    import xml.etree.ElementTree as ET
                    try:
                        root = ET.fromstring(content)
                        products = root.findall('.//product')
                        logger.info(f"✅ XML 파싱 성공: {len(products)}개 상품 발견")
                    except Exception as e:
                        logger.error(f"❌ XML 파싱 실패: {e}")
                else:
                    error_content = await response.text()
                    logger.error(f"❌ API 오류 응답:")
                    logger.error(error_content[:500])
    except Exception as e:
        logger.error(f"❌ API 호출 실패: {e}")
    
    # 테스트 2: runout=0 추가 (정상 상품만)
    logger.info("\n테스트 2: POST 방식 - runout=0 추가 (정상 상품만)")
    params_with_runout = {
        "id": credentials.get("id"),
        "m_skey": credentials.get("m_skey"),
        "runout": "0"  # 문자열로 전송
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, data=params_with_runout, timeout=30) as response:
                logger.info(f"응답 상태 코드: {response.status}")
                
                if response.status == 200:
                    content = await response.text(encoding='euc-kr')
                    logger.info(f"응답 길이: {len(content)} 바이트")
                    
                    import xml.etree.ElementTree as ET
                    try:
                        root = ET.fromstring(content)
                        products = root.findall('.//product')
                        logger.info(f"✅ XML 파싱 성공: {len(products)}개 상품 발견")
                    except Exception as e:
                        logger.error(f"❌ XML 파싱 실패: {e}")
                else:
                    error_content = await response.text()
                    logger.error(f"❌ API 오류 응답: {error_content[:200]}")
    except Exception as e:
        logger.error(f"❌ API 호출 실패: {e}")
    
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(debug_zentrade_api())

