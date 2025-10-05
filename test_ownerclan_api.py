#!/usr/bin/env python3
"""
오너클랜 API 연결 테스트
"""

import asyncio
import aiohttp
import json
from loguru import logger
from src.config.settings import settings
from src.utils.error_handler import ErrorHandler

class OwnerClanAPITester:
    """오너클랜 API 테스터"""
    
    def __init__(self):
        self.auth_endpoint = "https://auth.ownerclan.com/auth"
        self.api_endpoint = "https://api.ownerclan.com/v1/graphql"
        self.username = "b00679540"
        self.password = "ehdgod1101*"
        self.error_handler = ErrorHandler()
        self.token = None
    
    async def authenticate(self) -> bool:
        """인증 토큰 발급"""
        try:
            logger.info("오너클랜 인증 시작...")
            
            auth_data = {
                "service": "ownerclan",
                "userType": "seller",
                "username": self.username,
                "password": self.password
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.auth_endpoint,
                    json=auth_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    logger.info(f"응답 상태: {response.status}")
                    logger.info(f"응답 헤더: {dict(response.headers)}")
                    
                    response_text = await response.text()
                    logger.info(f"응답 내용: {response_text[:500]}...")
                    
                    if response.status == 200:
                        # 응답이 JWT 토큰 자체인 경우
                        if response_text.startswith("eyJ"):
                            self.token = response_text.strip()
                            logger.info("인증 성공!")
                            logger.info(f"토큰 길이: {len(self.token)}")
                            return True
                        else:
                            # JSON 형태인 경우
                            try:
                                result = await response.json()
                                self.token = result.get("token")
                                if self.token:
                                    logger.info("인증 성공!")
                                    logger.info(f"토큰 길이: {len(self.token)}")
                                    return True
                                else:
                                    logger.error("토큰이 응답에 없습니다")
                                    logger.error(f"응답 내용: {result}")
                                    return False
                            except Exception as json_error:
                                logger.error(f"JSON 파싱 실패: {json_error}")
                                logger.error(f"응답 내용: {response_text}")
                                return False
                    else:
                        logger.error(f"인증 실패: {response.status}")
                        logger.error(f"에러 내용: {response_text}")
                        return False
                        
        except Exception as e:
            self.error_handler.log_error(e, "오너클랜 인증 실패")
            return False
    
    async def test_graphql_query(self, query: str, variables: dict = None) -> dict:
        """GraphQL 쿼리 테스트"""
        if not self.token:
            logger.error("인증 토큰이 없습니다")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": query,
                "variables": variables or {}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_endpoint,
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("GraphQL 쿼리 성공!")
                        logger.info(f"응답 내용: {result}")
                        return result
                    else:
                        logger.error(f"GraphQL 쿼리 실패: {response.status}")
                        error_text = await response.text()
                        logger.error(f"에러 내용: {error_text}")
                        return None
                        
        except Exception as e:
            self.error_handler.log_error(e, "GraphQL 쿼리 실패")
            return None
    
    async def test_item_query(self) -> bool:
        """상품 조회 테스트"""
        # 먼저 실제 상품 키를 조회
        all_items_query = """
        query {
            allItems {
                edges {
                    node {
                        key
                        name
                    }
                }
            }
        }
        """
        
        result = await self.test_graphql_query(all_items_query)
        if result and "data" in result and result["data"]["allItems"]["edges"]:
            # 첫 번째 상품의 키를 사용
            first_item_key = result["data"]["allItems"]["edges"][0]["node"]["key"]
            logger.info(f"실제 상품 키 사용: {first_item_key}")
            
            # 해당 키로 상품 상세 조회
            query = f"""
            query {{
                item(key: "{first_item_key}") {{
                    name
                    model
                    options {{
                        price
                        quantity
                        optionAttributes {{
                            name
                            value
                        }}
                    }}
                }}
            }}
            """
            
            result = await self.test_graphql_query(query)
            if result and "data" in result:
                logger.info("상품 조회 테스트 성공!")
                logger.info(f"응답 데이터: {result['data']}")
                if result["data"]["item"]:
                    item = result["data"]["item"]
                    logger.info(f"상품명: {item.get('name', 'N/A')}")
                    logger.info(f"모델: {item.get('model', 'N/A')}")
                    if item.get("options"):
                        first_option = item["options"][0]
                        logger.info(f"가격: {first_option.get('price', 'N/A')}원")
                        logger.info(f"재고: {first_option.get('quantity', 'N/A')}개")
                else:
                    logger.info("상품 데이터가 없습니다")
                return True
            else:
                logger.error("상품 조회 테스트 실패")
                return False
        else:
            logger.error("상품 목록 조회 실패")
            return False
    
    async def test_all_items_query(self) -> bool:
        """전체 상품 조회 테스트"""
        query = """
        query {
            allItems {
                edges {
                    node {
                        key
                        name
                        model
                        options {
                            price
                            quantity
                            optionAttributes {
                                name
                                value
                            }
                        }
                    }
                }
            }
        }
        """
        
        result = await self.test_graphql_query(query)
        if result and "data" in result:
            edges = result["data"]["allItems"]["edges"]
            logger.info(f"전체 상품 조회 테스트 성공! 상품 수: {len(edges)}")
            
            if edges:
                # 첫 번째 상품 정보 출력
                first_item = edges[0]["node"]
                logger.info(f"첫 번째 상품: {first_item.get('name', 'N/A')}")
                logger.info(f"키: {first_item.get('key', 'N/A')}")
                if first_item.get("options"):
                    first_option = first_item["options"][0]
                    logger.info(f"가격: {first_option.get('price', 'N/A')}원")
                    logger.info(f"재고: {first_option.get('quantity', 'N/A')}개")
            
            return True
        else:
            logger.error("전체 상품 조회 테스트 실패")
            return False
    
    async def test_category_query(self) -> bool:
        """카테고리 조회 테스트"""
        query = """
        query {
            category(key: "C000000") {
                key
                name
                parent {
                    key
                    name
                }
            }
        }
        """
        
        result = await self.test_graphql_query(query)
        if result and "data" in result:
            category = result["data"]["category"]
            if category:
                logger.info(f"카테고리 조회 테스트 성공!")
                logger.info(f"카테고리명: {category.get('name', 'N/A')}")
                logger.info(f"키: {category.get('key', 'N/A')}")
                if category.get("parent"):
                    logger.info(f"부모 카테고리: {category['parent'].get('name', 'N/A')}")
            else:
                logger.info("카테고리 데이터가 없습니다")
            return True
        else:
            logger.error("카테고리 조회 테스트 실패")
            return False

async def main():
    """메인 테스트 함수"""
    logger.info("=== 오너클랜 API 테스트 시작 ===")
    
    tester = OwnerClanAPITester()
    
    # 1. 인증 테스트
    logger.info("\n1. 인증 테스트")
    auth_success = await tester.authenticate()
    if not auth_success:
        logger.error("인증 실패로 테스트 중단")
        return
    
    # 2. 상품 조회 테스트
    logger.info("\n2. 상품 조회 테스트")
    await tester.test_item_query()
    
    # 3. 전체 상품 조회 테스트
    logger.info("\n3. 전체 상품 조회 테스트")
    await tester.test_all_items_query()
    
    # 4. 카테고리 조회 테스트
    logger.info("\n4. 카테고리 조회 테스트")
    await tester.test_category_query()
    
    logger.info("\n=== 오너클랜 API 테스트 완료 ===")

if __name__ == "__main__":
    asyncio.run(main())
