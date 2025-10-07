#!/usr/bin/env python3
"""
젠트레이드 API 직접 테스트 스크립트
"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from loguru import logger


async def test_zentrade_api():
    """젠트레이드 API 직접 테스트"""
    try:
        logger.info("젠트레이드 API 직접 테스트 시작")
        
        # API 파라미터
        params = {
            "id": "b00679540",
            "m_skey": "5284c44b0fcf0f877e6791c5884d6ea9"
        }
        
        url = "https://www.zentrade.co.kr/shop/proc/product_api.php"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as response:
                logger.info(f"응답 상태: {response.status}")
                logger.info(f"응답 헤더: {dict(response.headers)}")
                
                if response.status == 200:
                    # euc-kr 인코딩으로 텍스트 읽기
                    content = await response.text(encoding='euc-kr')
                    logger.info(f"응답 길이: {len(content)} 문자")
                    logger.info(f"응답 내용 (처음 500자): {content[:500]}")
                    
                    # XML 파싱 시도
                    try:
                        root = ET.fromstring(content)
                        logger.info(f"XML 루트 태그: {root.tag}")
                        logger.info(f"XML 버전: {root.get('version', 'N/A')}")
                        
                        products = root.findall('product')
                        logger.info(f"상품 개수: {len(products)}")
                        
                        if products:
                            first_product = products[0]
                            logger.info(f"첫 번째 상품 코드: {first_product.get('code', 'N/A')}")
                            
                            # 상품명 확인
                            prdtname = first_product.find('prdtname')
                            if prdtname is not None:
                                logger.info(f"첫 번째 상품명: {prdtname.text}")
                            
                    except ET.ParseError as e:
                        logger.error(f"XML 파싱 오류: {e}")
                        logger.info(f"XML 내용 (처음 1000자): {content[:1000]}")
                        
                else:
                    logger.error(f"API 요청 실패: {response.status}")
                    error_content = await response.text()
                    logger.error(f"오류 내용: {error_content}")
        
        logger.info("젠트레이드 API 직접 테스트 완료")
        
    except Exception as e:
        logger.error(f"젠트레이드 API 직접 테스트 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_zentrade_api())
