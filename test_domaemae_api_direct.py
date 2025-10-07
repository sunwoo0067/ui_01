#!/usr/bin/env python3
"""
도매꾹 API 직접 테스트 스크립트
"""

import asyncio
import aiohttp
import json
import time
from loguru import logger


async def test_domaemae_api_direct():
    """도매꾹 API 직접 테스트"""
    try:
        logger.info("도매꾹 API 직접 테스트 시작")
        
        # API 설정
        api_key = "96ef1110327e9ce5be389e5eaa612f4a"
        base_url = "https://domeggook.com/ssl/api/"
        
        # 테스트 파라미터
        test_params = {
            "ver": "4.1",
            "mode": "getItemList",
            "aid": api_key,
            "market": "dome",  # 도매꾹
            "om": "json",
            "sz": 20,  # 20개 상품
            "pg": 1,   # 첫 페이지
            "so": "rd"  # 랭킹순
        }
        
        # API 요청
        logger.info("도매꾹 API 요청 시작")
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=test_params, timeout=30) as response:
                request_time = time.time() - start_time
                
                logger.info(f"API 응답 상태: {response.status}")
                logger.info(f"응답 헤더: {dict(response.headers)}")
                logger.info(f"요청 소요시간: {request_time:.2f}초")
                
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    logger.info(f"응답 타입: {content_type}")
                    
                    if 'application/json' in content_type:
                        # JSON 응답
                        data = await response.json()
                        logger.info("JSON 응답 수신")
                        
                        # 응답 구조 분석
                        logger.info(f"응답 키: {list(data.keys())}")
                        
                        if "list" in data:
                            list_info = data["list"]
                            logger.info(f"리스트 정보: {list_info}")
                            
                            if "item" in list_info:
                                items = list_info["item"]
                                
                                # 단일 아이템인 경우 리스트로 변환
                                if not isinstance(items, list):
                                    items = [items]
                                
                                logger.info(f"상품 개수: {len(items)}개")
                                
                                # 첫 번째 상품 정보 출력
                                if items:
                                    first_item = items[0]
                                    logger.info("첫 번째 상품 정보:")
                                    logger.info(f"  - 상품번호: {first_item.get('no', 'N/A')}")
                                    logger.info(f"  - 제목: {first_item.get('title', 'N/A')}")
                                    logger.info(f"  - 가격: {first_item.get('price', 'N/A')}원")
                                    logger.info(f"  - 판매자: {first_item.get('id', 'N/A')}")
                                    logger.info(f"  - 단위수량: {first_item.get('unitQty', 'N/A')}")
                                    logger.info(f"  - 재고: {first_item.get('qty', {}).get('inventory', 'N/A')}")
                                    logger.info(f"  - 썸네일: {first_item.get('thumb', 'N/A')}")
                                    logger.info(f"  - URL: {first_item.get('url', 'N/A')}")
                                    
                                    # 배송 정보
                                    deli_info = first_item.get('deli', {})
                                    if deli_info:
                                        logger.info(f"  - 배송비: {deli_info.get('fee', 'N/A')}원")
                                        logger.info(f"  - 배송방식: {deli_info.get('who', 'N/A')}")
                                
                                # 상품별 기본 정보 요약
                                logger.info("상품 요약 정보:")
                                for i, item in enumerate(items[:5]):  # 처음 5개만
                                    logger.info(f"  {i+1}. {item.get('title', 'N/A')} - {item.get('price', 0)}원")
                        
                        # 전체 응답 크기
                        response_text = json.dumps(data, ensure_ascii=False)
                        logger.info(f"응답 크기: {len(response_text)} 문자")
                        
                    else:
                        # XML 응답
                        xml_content = await response.text()
                        logger.info(f"XML 응답 수신 (크기: {len(xml_content)} 문자)")
                        logger.info("XML 응답 샘플:")
                        logger.info(xml_content[:500] + "..." if len(xml_content) > 500 else xml_content)
                
                else:
                    logger.error(f"API 요청 실패: {response.status}")
                    error_text = await response.text()
                    logger.error(f"에러 응답: {error_text}")
        
        # 도매매 시장 테스트
        logger.info("\n도매매 시장 테스트")
        supply_params = test_params.copy()
        supply_params["market"] = "supply"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=supply_params, timeout=30) as response:
                logger.info(f"도매매 API 응답 상태: {response.status}")
                
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        data = await response.json()
                        if "list" in data and "item" in data["list"]:
                            items = data["list"]["item"]
                            if not isinstance(items, list):
                                items = [items]
                            logger.info(f"도매매 상품 개수: {len(items)}개")
                        else:
                            logger.info("도매매 상품 데이터 없음")
                    else:
                        logger.info("도매매 XML 응답 수신")
                else:
                    logger.error(f"도매매 API 요청 실패: {response.status}")
        
        logger.info("✅ 도매꾹 API 직접 테스트 완료")
        
    except Exception as e:
        logger.error(f"❌ 도매꾹 API 직접 테스트 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_domaemae_api_direct())
