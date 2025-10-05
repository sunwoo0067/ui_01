#!/usr/bin/env python3
"""
오너클랜 데이터 수집 서비스
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from src.config.settings import settings
from src.utils.error_handler import ErrorHandler
from src.services.supplier_account_manager import supplier_account_manager


class OwnerClanDataCollector:
    """오너클랜 데이터 수집기"""
    
    def __init__(self):
        self.settings = settings
        self.error_handler = ErrorHandler()
        self.auth_endpoint = "https://auth.ownerclan.com/auth"
        self.api_endpoint = "https://api.ownerclan.com/v1/graphql"
        self._token_cache: Dict[str, Dict[str, Any]] = {}
    
    async def _get_auth_token(self, account_name: str, force_refresh: bool = False) -> Optional[str]:
        """인증 토큰 조회"""
        try:
            # 캐시된 토큰 확인
            if not force_refresh and account_name in self._token_cache:
                cached_token = self._token_cache[account_name]
                if datetime.now() < cached_token['expires_at']:
                    return cached_token['token']
            
            # 계정 정보 조회
            account = await supplier_account_manager.get_ownerclan_credentials(account_name)
            if not account:
                logger.error(f"계정 정보를 찾을 수 없습니다: {account_name}")
                return None
            
            logger.info(f"계정 정보 조회 성공: {account_name}")
            logger.info(f"계정 데이터: {account}")
            
            credentials = account
            
            # 인증 요청
            auth_data = {
                "service": "ownerclan",
                "userType": "seller",
                "username": credentials["username"],
                "password": credentials["password"]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.auth_endpoint,
                    json=auth_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        if response_text.startswith("eyJ"):
                            token = response_text.strip()
                            
                            # 토큰 캐시 저장 (30일 유효)
                            expires_at = datetime.now() + timedelta(days=30)
                            self._token_cache[account_name] = {
                                'token': token,
                                'expires_at': expires_at
                            }
                            
                            logger.info(f"토큰 발급 성공: {account_name}")
                            return token
                        else:
                            logger.error(f"토큰 형식이 올바르지 않습니다: {account_name}")
                            return None
                    else:
                        logger.error(f"인증 실패: {response.status} - {account_name}")
                        return None
                        
        except Exception as e:
            self.error_handler.log_error(e, f"토큰 발급 실패: {account_name}")
            return None
    
    async def _make_graphql_request(self, query: str, account_name: str, variables: dict = None) -> Optional[dict]:
        """GraphQL 요청 실행"""
        try:
            token = await self._get_auth_token(account_name)
            if not token:
                return None
            
            headers = {
                "Authorization": f"Bearer {token}",
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
                        if "errors" in result and result["errors"]:
                            logger.error(f"GraphQL 에러: {result['errors']}")
                            return None
                        return result
                    else:
                        logger.error(f"GraphQL 요청 실패: {response.status}")
                        error_text = await response.text()
                        logger.error(f"에러 내용: {error_text}")
                        return None
                        
        except Exception as e:
            self.error_handler.log_error(e, f"GraphQL 요청 실패: {account_name}")
            return None
    
    async def collect_products(self, account_name: str, 
                             limit: int = 1000,
                             min_price: Optional[int] = None,
                             max_price: Optional[int] = None,
                             category: Optional[str] = None) -> List[Dict[str, Any]]:
        """상품 데이터 수집"""
        try:
            logger.info(f"상품 데이터 수집 시작: {account_name}")
            
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
            
            result = await self._make_graphql_request(query, account_name)
            if not result or "data" not in result:
                logger.error("상품 데이터 수집 실패")
                return []
            
            edges = result["data"]["allItems"]["edges"]
            products = []
            
            for edge in edges:
                product = edge["node"]
                
                # 가격 필터링
                if product.get("options"):
                    first_option = product["options"][0]
                    price = first_option.get("price", 0)
                    
                    if min_price and price < min_price:
                        continue
                    if max_price and price > max_price:
                        continue
                
                # 상품 데이터 정규화
                normalized_product = {
                    "supplier_key": product["key"],
                    "name": product["name"],
                    "model": product.get("model", ""),
                    "price": first_option.get("price", 0) if product.get("options") else 0,
                    "stock": first_option.get("quantity", 0) if product.get("options") else 0,
                    "options": product.get("options", []),
                    "collected_at": datetime.utcnow().isoformat(),
                    "account_name": account_name
                }
                
                products.append(normalized_product)
            
            logger.info(f"상품 데이터 수집 완료: {len(products)}개")
            return products
            
        except Exception as e:
            self.error_handler.log_error(e, f"상품 데이터 수집 실패: {account_name}")
            return []
    
    async def collect_orders(self, account_name: str,
                           limit: int = 100,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           shipped_after: Optional[datetime] = None,
                           shipped_before: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """주문 데이터 수집"""
        try:
            logger.info(f"주문 데이터 수집 시작: {account_name}")
            
            # 날짜 기본값 설정 (최대 90일 제한)
            if not start_date:
                start_date = datetime.now() - timedelta(days=90)
            if not end_date:
                end_date = datetime.now()
            
            # 90일 제한 확인
            if (end_date - start_date).days > 90:
                logger.warning("날짜 범위가 90일을 초과합니다. 90일로 제한합니다.")
                start_date = end_date - timedelta(days=90)
            
            # Unix timestamp로 변환
            date_from_timestamp = int(start_date.timestamp())
            date_to_timestamp = int(end_date.timestamp())
            shipped_after_timestamp = int(shipped_after.timestamp()) if shipped_after else None
            shipped_before_timestamp = int(shipped_before.timestamp()) if shipped_before else None
            
            query = """
            query AllOrders($dateFrom: Timestamp, $dateTo: Timestamp, $shippedAfter: Timestamp, $shippedBefore: Timestamp) {
                allOrders(dateFrom: $dateFrom, dateTo: $dateTo, shippedAfter: $shippedAfter, shippedBefore: $shippedBefore) {
                    edges {
                        node {
                            key
                            id
                            products {
                                itemKey
                                quantity
                                price
                                itemOptionInfo {
                                    optionAttributes {
                                        name
                                        value
                                    }
                                }
                            }
                            status
                            shippingInfo {
                                sender {
                                    name
                                    phoneNumber
                                }
                                recipient {
                                    name
                                    phoneNumber
                                    destinationAddress {
                                        addr1
                                        addr2
                                        postalCode
                                    }
                                }
                                shippingFee
                            }
                            createdAt
                            updatedAt
                            note
                            ordererNote
                            sellerNote
                        }
                    }
                }
               }
               """
               
            variables = {
                "dateFrom": date_from_timestamp,
                "dateTo": date_to_timestamp,
                "shippedAfter": shipped_after_timestamp,
                "shippedBefore": shipped_before_timestamp
            }
            
            result = await self._make_graphql_request(query, account_name, variables)
            if not result or "data" not in result:
                logger.error("주문 데이터 수집 실패")
                return []
            
            edges = result["data"]["allOrders"]["edges"]
            orders = []
            
            for edge in edges:
                order = edge["node"]
                
                # 날짜 필터링
                created_at = datetime.fromtimestamp(order.get("createdAt", 0))
                if created_at < start_date or created_at > end_date:
                    continue
                
                # 주문 데이터 정규화
                normalized_order = {
                    "supplier_key": order["key"],
                    "supplier_id": order["id"],
                    "products": order.get("products", []),
                    "status": order.get("status", ""),
                    "shipping_info": order.get("shippingInfo", {}),
                    "created_at": created_at.isoformat(),
                    "updated_at": datetime.fromtimestamp(order.get("updatedAt", 0)).isoformat(),
                    "note": order.get("note", ""),
                    "orderer_note": order.get("ordererNote", ""),
                    "seller_note": order.get("sellerNote", ""),
                    "collected_at": datetime.utcnow().isoformat(),
                    "account_name": account_name
                }
                
                orders.append(normalized_order)
            
            logger.info(f"주문 데이터 수집 완료: {len(orders)}개")
            return orders
            
        except Exception as e:
            self.error_handler.log_error(e, f"주문 데이터 수집 실패: {account_name}")
            return []
    
    async def collect_categories(self, account_name: str) -> List[Dict[str, Any]]:
        """카테고리 데이터 수집"""
        try:
            logger.info(f"카테고리 데이터 수집 시작: {account_name}")
            
            query = """
            query {
                allCategories {
                    edges {
                        node {
                            key
                            name
                            parent {
                                key
                                name
                            }
                        }
                    }
                }
            }
            """
            
            result = await self._make_graphql_request(query, account_name)
            if not result or "data" not in result:
                logger.error("카테고리 데이터 수집 실패")
                return []
            
            edges = result["data"]["allCategories"]["edges"]
            categories = []
            
            for edge in edges:
                category = edge["node"]
                
                # 카테고리 데이터 정규화
                normalized_category = {
                    "supplier_key": category["key"],
                    "name": category["name"],
                    "parent_key": category.get("parent", {}).get("key") if category.get("parent") else None,
                    "parent_name": category.get("parent", {}).get("name") if category.get("parent") else None,
                    "collected_at": datetime.utcnow().isoformat(),
                    "account_name": account_name
                }
                
                categories.append(normalized_category)
            
            logger.info(f"카테고리 데이터 수집 완료: {len(categories)}개")
            return categories
            
        except Exception as e:
            self.error_handler.log_error(e, f"카테고리 데이터 수집 실패: {account_name}")
            return []


# 전역 인스턴스
ownerclan_data_collector = OwnerClanDataCollector()