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
    
    async def collect_products_batch(self, account_name: str,
                                   batch_size: int = 1000,
                                   min_price: Optional[int] = None,
                                   max_price: Optional[int] = None,
                                   category: Optional[str] = None,
                                   search: Optional[str] = None,
                                   storage_service = None) -> int:
        """
        상품 데이터 배치 수집 및 저장 (Pagination 지원)
        오너클랜 API는 한 번에 최대 1000개까지 조회 가능하며 cursor 기반 pagination을 지원합니다.
        """
        try:
            logger.info(f"상품 데이터 배치 수집 시작: {account_name} (배치 크기: {batch_size})")

            all_products = []
            cursor = None
            page_count = 0

            while True:
                page_count += 1
                logger.info(f"페이지 {page_count} 수집 시작 (cursor: {cursor})")

                # GraphQL 쿼리 (pagination 지원)
                query = """
                query AllItems($first: Int, $after: String, $minPrice: Int, $maxPrice: Int, $search: String) {
                    allItems(first: $first, after: $after, minPrice: $minPrice, maxPrice: $maxPrice, search: $search) {
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                        edges {
                            node {
                                key
                                name
                                model
                                price
                                status
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

                variables = {
                    "first": batch_size,
                    "after": cursor,
                    "minPrice": min_price,
                    "maxPrice": max_price,
                    "search": search
                }

                result = await self._make_graphql_request(query, account_name, variables)
                if not result or "data" not in result:
                    logger.error(f"상품 데이터 수집 실패 (페이지 {page_count})")
                    break

                all_items_data = result["data"]["allItems"]
                edges = all_items_data.get("edges", [])
                page_info = all_items_data.get("pageInfo", {})

                if not edges:
                    logger.info(f"페이지 {page_count}: 수집할 데이터 없음")
                    break

                logger.info(f"페이지 {page_count}: {len(edges)}개 상품 수집")

                # 상품 데이터 정규화
                for edge in edges:
                    product = edge["node"]

                    # 상품 데이터 정규화
                    normalized_product = {
                        "supplier_key": product["key"],
                        "name": product["name"],
                        "model": product.get("model", ""),
                        "price": product.get("price", 0),
                        "status": product.get("status", ""),
                        "options": product.get("options", []),
                        "collected_at": datetime.utcnow().isoformat(),
                        "account_name": account_name
                    }

                    all_products.append(normalized_product)

                # 다음 페이지 확인
                has_next_page = page_info.get("hasNextPage", False)
                cursor = page_info.get("endCursor")

                logger.info(f"페이지 {page_count} 완료: 누적 {len(all_products)}개, 다음 페이지: {has_next_page}")

                if not has_next_page:
                    break

                # API 호출 간격
                await asyncio.sleep(0.5)

            logger.info(f"전체 상품 데이터 수집 완료: {len(all_products)}개 ({page_count}페이지)")

            # 저장 서비스가 있으면 저장 (한 번에 대량 저장)
            if storage_service:
                logger.info(f"전체 상품 데이터 저장 시작: {len(all_products)}개")
                total_saved = await storage_service.save_products(all_products)
                logger.info(f"전체 상품 데이터 저장 완료: 총 {total_saved}개 상품 저장됨")
                return total_saved
            else:
                logger.info(f"수집만 완료 (저장 서비스 없음): {len(all_products)}개")
                return len(all_products)

        except Exception as e:
            self.error_handler.log_error(e, f"상품 데이터 배치 수집 실패: {account_name}")
            return 0

    async def collect_products(self, account_name: str, 
                             limit: int = 1000,
                             min_price: Optional[int] = None,
                             max_price: Optional[int] = None,
                             category: Optional[str] = None) -> List[Dict[str, Any]]:
        """상품 데이터 수집 (기존 방식 유지)"""
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
    
    async def collect_orders_batch(self, account_name: str,
                                  batch_size: int = 1000,
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None,
                                  shipped_after: Optional[datetime] = None,
                                  shipped_before: Optional[datetime] = None,
                                  storage_service = None) -> int:
        """주문 데이터 배치 수집 및 저장"""
        try:
            logger.info(f"주문 데이터 배치 수집 시작: {account_name} (배치 크기: {batch_size})")
            
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
                return 0
            
            edges = result["data"]["allOrders"]["edges"]
            all_orders = []
            
            # 모든 주문 데이터 수집
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
                
                all_orders.append(normalized_order)
            
            logger.info(f"전체 주문 데이터 수집 완료: {len(all_orders)}개")
            
            # 저장 서비스가 있으면 저장 (한 번에 대량 저장)
            if storage_service:
                logger.info(f"전체 주문 데이터 저장 시작: {len(all_orders)}개")
                total_saved = await storage_service.save_orders(all_orders)
                logger.info(f"전체 주문 데이터 저장 완료: 총 {total_saved}개 주문 저장됨")
                return total_saved
            else:
                logger.info(f"수집만 완료 (저장 서비스 없음): {len(all_orders)}개")
                return len(all_orders)
            
        except Exception as e:
            self.error_handler.log_error(e, f"주문 데이터 배치 수집 실패: {account_name}")
            return 0

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