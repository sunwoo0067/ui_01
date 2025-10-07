import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger

from src.services.database_service import DatabaseService
from src.services.supplier_account_manager import SupplierAccountManager
from src.utils.error_handler import ErrorHandler


class DomaemaeTokenManager:
    """도매꾹 API 토큰 관리"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
        self.account_manager = SupplierAccountManager()
        
    async def get_credentials(self, account_name: str) -> Dict[str, str]:
        """계정 정보에서 인증 정보 가져오기"""
        try:
            account = await self.account_manager.get_supplier_account("domaemae", account_name)
            if not account:
                raise ValueError(f"도매꾹 계정을 찾을 수 없습니다: {account_name}")
            
            credentials = account.get("account_credentials", {})
            return {
                "api_key": credentials.get("api_key"),
                "version": credentials.get("version", "4.1")
            }
        except Exception as e:
            self.error_handler.log_error(e, f"도매꾹 인증 정보 조회 실패: {account_name}")
            raise


class DomaemaeDataCollector:
    """도매꾹 데이터 수집기 (도매꾹/도매매 구분 지원)"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
        self.token_manager = DomaemaeTokenManager(db_service)
        
        # 도매꾹/도매매 시장 정보
        self.market_info = {
            "dome": {
                "name": "도매꾹",
                "description": "대량 구매 상품 (도매) - 최소 구매 수량 있음",
                "min_order_type": "bulk",
                "supplier_type": "wholesale"
            },
            "supply": {
                "name": "도매매", 
                "description": "1개씩 구매 가능 (소매)",
                "min_order_type": "single",
                "supplier_type": "retail"
            }
        }
        
    async def _make_api_request(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """API 요청 실행"""
        try:
            url = "https://domeggook.com/ssl/api/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        
                        if 'application/json' in content_type:
                            return await response.json()
                        else:
                            # XML 응답인 경우 JSON으로 변환 시도
                            xml_content = await response.text()
                            # 간단한 XML 파싱 (실제로는 더 정교한 파싱 필요)
                            logger.warning("XML 응답을 받았지만 JSON으로 처리합니다")
                            return {"raw_xml": xml_content}
                    else:
                        logger.error(f"API 요청 실패: {response.status}")
                        return None
        except Exception as e:
            self.error_handler.log_error(e, f"API 요청 실패: {url}")
            return None
    
    async def collect_products(self, account_name: str,
                            market: str = "dome",  # dome: 도매꾹, supply: 도매매
                            size: int = 200,  # 페이지당 상품 개수 (최대 200)
                            page: int = 1,
                            sort: str = "rd",  # 정렬 방식
                            keyword: Optional[str] = None,  # 검색어 (선택사항)
                            category: Optional[str] = None,  # 카테고리 (선택사항)
                            seller_id: Optional[str] = None,
                            min_price: Optional[int] = None,
                            max_price: Optional[int] = None,
                            min_quantity: Optional[int] = None,
                            max_quantity: Optional[int] = None,
                            shipping: Optional[str] = None,
                            origin: Optional[str] = None,
                            excellent_seller: Optional[bool] = None,
                            fast_delivery: Optional[bool] = None,
                            lowest_price: Optional[bool] = None) -> List[Dict[str, Any]]:
        """상품 데이터 수집 (도매꾹/도매매 구분)"""
        try:
            market_name = self.market_info[market]["name"]
            logger.info(f"{market_name} 상품 데이터 수집 시작: {account_name} (시장: {market})")
            
            # 인증 정보 가져오기
            credentials = await self.token_manager.get_credentials(account_name)
            
            # API 파라미터 구성
            params = {
                "ver": credentials["version"],
                "mode": "getItemList",
                "aid": credentials["api_key"],
                "market": market,
                "om": "json",  # JSON 형식
                "sz": size,
                "pg": page,
                "so": sort
            }
            
            # 선택적 파라미터 추가 (최소 하나는 필요)
            search_params_added = False
            
            if category:
                params["ca"] = category
                search_params_added = True
            if seller_id:
                params["id"] = seller_id
                search_params_added = True
            if keyword:
                params["kw"] = keyword
                search_params_added = True
            
            # 검색 조건이 없으면 에러 (전체 수집시에는 카테고리 순환 필요)
            if not search_params_added:
                logger.error("검색 조건 필수: 기획전(ev), 카테고리(ca), 아이디(id), 검색어(kw), 상품번호(itemNo) 중 1개 필요")
                return []
            if min_price is not None:
                params["mnp"] = min_price
            if max_price is not None:
                params["mxp"] = max_price
            if min_quantity is not None:
                params["mnq"] = min_quantity
            if max_quantity is not None:
                params["mxq"] = max_quantity
            if shipping:
                params["who"] = shipping
            if origin:
                params["org"] = origin
            if excellent_seller is not None:
                params["sgd"] = excellent_seller
            if fast_delivery is not None:
                params["fdl"] = fast_delivery
            if lowest_price is not None:
                params["lwp"] = lowest_price
            
            # None 값 제거
            params = {k: v for k, v in params.items() if v is not None}
            
            # API 요청
            result = await self._make_api_request(params)
            
            if not result:
                logger.error("도매꾹 API 응답 없음")
                return []
            
            # 응답 데이터 파싱
            products = await self._parse_api_response(result)
            
            # 시장별 메타데이터 추가
            for product in products:
                product["account_name"] = account_name
                product["market"] = market
                product["market_name"] = market_name
                product["market_type"] = self.market_info[market]["supplier_type"]
                product["min_order_type"] = self.market_info[market]["min_order_type"]
                product["collected_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"{market_name} 상품 데이터 수집 완료: {len(products)}개")
            return products
            
        except Exception as e:
            self.error_handler.log_error(e, f"도매꾹 상품 데이터 수집 실패: {account_name}")
            return []
    
    async def _parse_api_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """API 응답 파싱 (1차 수집 - getItemList)"""
        try:
            products = []

            # 도매꾹 JSON 응답 구조 확인
            if "domeggook" in response:
                domeggook_data = response["domeggook"]

                if "list" in domeggook_data and "item" in domeggook_data["list"]:
                    items = domeggook_data["list"]["item"]

                    # 단일 아이템인 경우 리스트로 변환
                    if not isinstance(items, list):
                        items = [items]

                    for item in items:
                        product_data = {
                            "supplier_key": str(item.get("no", "")),
                            "title": item.get("title", ""),
                            "price": int(item.get("price", 0)) if item.get("price") else 0,
                            "unit_quantity": int(item.get("unitQty", 1)) if item.get("unitQty") else 1,
                            "seller_id": item.get("id", ""),
                            "seller_nick": item.get("nick", ""),
                            "thumbnail_url": item.get("thumb", ""),
                            "product_url": item.get("url", ""),
                            "company_only": item.get("comOnly", "false").lower() == "true",
                            "adult_only": item.get("adultOnly", "false").lower() == "true",
                            "lowest_price": item.get("lwp", "false").lower() == "true",
                            "use_options": item.get("useopt", "false").lower() == "true",
                            "market_info": item.get("market", {}),
                            "dome_price": item.get("domePrice", ""),
                            "quantity_info": item.get("qty", {}),
                            "delivery_info": item.get("deli", {}),
                            "idx_com": item.get("idxCOM", "")
                        }

                        products.append(product_data)

                # 헤더 정보도 로깅
                if "header" in domeggook_data:
                    header = domeggook_data["header"]
                    logger.info(f"도매꾹 응답 헤더 - 총 상품: {header.get('numberOfItems', 0)}, 현재 페이지: {header.get('currentPage', 1)}")

            # 에러 응답인 경우
            elif "errors" in response:
                error_info = response["errors"]
                logger.error(f"도매꾹 API 에러: {error_info.get('message', 'Unknown error')}")
                return []

            # XML 응답인 경우 (raw_xml이 있는 경우)
            elif "raw_xml" in response:
                logger.warning("XML 응답은 현재 지원하지 않습니다")
                return []

            else:
                logger.warning(f"예상하지 못한 응답 형식: {list(response.keys())}")
                return []

            return products

        except Exception as e:
            self.error_handler.log_error(e, "도매꾹 API 응답 파싱 실패")
            return []

    async def collect_product_details(self, account_name: str,
                                     product_ids: List[str],
                                     batch_size: int = 100) -> List[Dict[str, Any]]:
        """
        2차 수집: 상품 상세 정보 수집 (getItemView)
        한 번에 최대 100개까지 조회 가능 (comma-separated)
        """
        try:
            logger.info(f"상품 상세 정보 수집 시작: {len(product_ids)}개 상품")

            # 인증 정보 가져오기
            credentials = await self.token_manager.get_credentials(account_name)

            all_details = []

            # 100개씩 배치로 나누어 요청
            for i in range(0, len(product_ids), batch_size):
                batch = product_ids[i:i + batch_size]
                batch_num = (i // batch_size) + 1

                logger.info(f"배치 {batch_num} 상세 조회 시작: {len(batch)}개 상품")

                # API 파라미터 구성
                params = {
                    "ver": credentials["version"],
                    "mode": "getItemView",
                    "aid": credentials["api_key"],
                    "no": ",".join(batch),  # comma-separated item numbers
                    "multiple": "true",
                    "om": "json"
                }

                # API 요청
                result = await self._make_api_request(params)

                if not result:
                    logger.error(f"배치 {batch_num} 상세 조회 실패")
                    continue

                # 응답 파싱
                details = await self._parse_detail_response(result)

                if details:
                    # 메타데이터 추가
                    for detail in details:
                        detail["account_name"] = account_name
                        detail["collected_at"] = datetime.utcnow().isoformat()

                    all_details.extend(details)
                    logger.info(f"배치 {batch_num} 상세 조회 완료: {len(details)}개 상품")

                # API 호출 간격
                await asyncio.sleep(0.5)

            logger.info(f"전체 상품 상세 정보 수집 완료: {len(all_details)}개")
            return all_details

        except Exception as e:
            self.error_handler.log_error(e, f"상품 상세 정보 수집 실패: {account_name}")
            return []

    async def _parse_detail_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """API 응답 파싱 (2차 수집 - getItemView)"""
        try:
            details = []

            if "domeggook" in response:
                domeggook_data = response["domeggook"]

                # 상세 정보는 items 배열에 있음
                if "items" in domeggook_data:
                    items = domeggook_data["items"]

                    # 단일 아이템인 경우 리스트로 변환
                    if not isinstance(items, list):
                        items = [items]

                    for item in items:
                        detail_data = {
                            "supplier_key": str(item.get("it_id", "")),
                            "name": item.get("it_name", ""),
                            "price": int(item.get("it_price", 0)) if item.get("it_price") else 0,
                            "stock_quantity": int(item.get("it_stock_qty", 0)) if item.get("it_stock_qty") else 0,
                            "description": item.get("it_desc", ""),
                            "brand": item.get("it_brand", ""),
                            "manufacturer": item.get("it_maker", ""),
                            "origin": item.get("it_origin", ""),
                            "barcode": item.get("it_barcode", ""),
                            "model": item.get("it_model", ""),
                            "weight": item.get("it_weight", ""),
                            "dimensions": item.get("it_dimensions", ""),
                            "images": item.get("images", []),
                            "options": item.get("options", []),
                            "category": item.get("ca_id", ""),
                            "seller_id": item.get("mb_id", ""),
                            "min_order_qty": int(item.get("it_min_qty", 1)) if item.get("it_min_qty") else 1,
                            "max_order_qty": int(item.get("it_max_qty", 0)) if item.get("it_max_qty") else 0,
                            "shipping_cost": int(item.get("it_sc_price", 0)) if item.get("it_sc_price") else 0,
                            "shipping_type": item.get("it_sc_type", ""),
                            "return_cost": int(item.get("it_return_cost", 0)) if item.get("it_return_cost") else 0,
                            "exchange_cost": int(item.get("it_exchange_cost", 0)) if item.get("it_exchange_cost") else 0,
                            "is_soldout": item.get("it_soldout", "0") == "1",
                            "is_discontinued": item.get("it_use", "1") == "0"
                        }

                        details.append(detail_data)

                logger.info(f"상세 정보 파싱 완료: {len(details)}개")

            return details

        except Exception as e:
            self.error_handler.log_error(e, "상품 상세 정보 파싱 실패")
            return []
    
    async def collect_products_batch(self, account_name: str,
                                   batch_size: int = 200,
                                   max_pages: int = 10,
                                   market: str = "dome",
                                   **kwargs) -> List[Dict[str, Any]]:
        """상품 데이터 배치 수집 (단일 시장)"""
        try:
            market_name = self.market_info[market]["name"]
            logger.info(f"{market_name} 상품 데이터 배치 수집 시작: {account_name} (배치 크기: {batch_size}, 최대 페이지: {max_pages if max_pages else '무제한'})")
            
            all_products = []
            page = 1
            
            while True:
                # max_pages가 설정되어 있으면 제한 확인
                if max_pages and page > max_pages:
                    break
                
                logger.info(f"{market_name} 페이지 {page} 수집 중...")
                
                products = await self.collect_products(
                    account_name=account_name,
                    market=market,
                    size=batch_size,
                    page=page,
                    **kwargs
                )
                
                if not products:
                    logger.info(f"{market_name} 페이지 {page}에서 상품을 찾지 못했습니다. 수집을 종료합니다.")
                    break
                
                all_products.extend(products)
                logger.info(f"{market_name} 페이지 {page} 완료: {len(products)}개 상품 (누적: {len(all_products)}개)")
                
                # 페이지당 상품이 배치 크기보다 작으면 마지막 페이지
                if len(products) < batch_size:
                    logger.info(f"{market_name} 마지막 페이지 도달")
                    break
                
                # API 호출 간격 조절
                await asyncio.sleep(0.5)
                page += 1
            
            logger.info(f"{market_name} 배치 수집 완료: 총 {len(all_products)}개 상품 ({page}페이지)")
            return all_products
            
        except Exception as e:
            self.error_handler.log_error(e, f"{market_name} 배치 수집 실패: {account_name}")
            return []
    
    async def collect_products_by_category(self, account_name: str,
                                         categories: List[str],
                                         batch_size: int = 200,
                                         max_pages_per_category: int = 5,
                                         markets: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """카테고리별 상품 데이터 수집 (도매꾹/도매매 모두)"""
        try:
            if markets is None:
                markets = ["dome", "supply"]  # 기본적으로 두 시장 모두 수집
            
            logger.info(f"카테고리별 상품 데이터 수집 시작: {account_name}")
            logger.info(f"카테고리: {categories}")
            logger.info(f"시장: {markets}")
            
            results = {}
            
            for market in markets:
                market_name = self.market_info[market]["name"]
                logger.info(f"{market_name} 카테고리별 수집 시작...")
                
                market_products = []
                
                for category in categories:
                    logger.info(f"{market_name} 카테고리 '{category}' 수집 중...")
                    
                    category_products = []
                    
                    for page in range(1, max_pages_per_category + 1):
                        products = await self.collect_products(
                            account_name=account_name,
                            market=market,
                            category=category,
                            size=batch_size,
                            page=page
                        )
                        
                        if not products:
                            logger.info(f"{market_name} 카테고리 '{category}' 페이지 {page}에서 상품을 찾지 못했습니다.")
                            break
                        
                        category_products.extend(products)
                        logger.info(f"{market_name} 카테고리 '{category}' 페이지 {page} 완료: {len(products)}개 상품")
                        
                        # API 호출 간격 조절
                        await asyncio.sleep(0.5)
                    
                    market_products.extend(category_products)
                    logger.info(f"{market_name} 카테고리 '{category}' 수집 완료: {len(category_products)}개 상품")
                
                results[market] = market_products
                logger.info(f"{market_name} 카테고리별 수집 완료: 총 {len(market_products)}개 상품")
            
            total_products = sum(len(products) for products in results.values())
            logger.info(f"카테고리별 수집 전체 완료: 총 {total_products}개 상품")
            
            return results
            
        except Exception as e:
            self.error_handler.log_error(e, f"카테고리별 수집 실패: {account_name}")
            return {}
    
    async def collect_all_markets_batch(self, account_name: str,
                                      batch_size: int = 200,
                                      max_pages: int = 10,
                                      **kwargs) -> Dict[str, List[Dict[str, Any]]]:
        """도매꾹/도매매 모든 시장 배치 수집"""
        try:
            logger.info(f"모든 시장 배치 수집 시작: {account_name}")
            
            results = {}
            markets = ["dome", "supply"]
            
            for market in markets:
                market_name = self.market_info[market]["name"]
                logger.info(f"{market_name} 배치 수집 시작...")
                
                products = await self.collect_products_batch(
                    account_name=account_name,
                    batch_size=batch_size,
                    max_pages=max_pages,
                    market=market,
                    **kwargs
                )
                
                results[market] = products
                logger.info(f"{market_name} 배치 수집 완료: {len(products)}개 상품")
            
            total_products = sum(len(products) for products in results.values())
            logger.info(f"모든 시장 배치 수집 완료: 총 {total_products}개 상품")
            
            return results
            
        except Exception as e:
            self.error_handler.log_error(e, f"모든 시장 배치 수집 실패: {account_name}")
            return {}
    
    async def collect_orders(self, account_name: str,
                           market: str = "dome",
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None,
                           order_status: Optional[str] = None,
                           seller_id: Optional[str] = None,
                           page: int = 1,
                           size: int = 200) -> List[Dict[str, Any]]:
        """주문 데이터 수집 (도매꾹/도매매 구분)"""
        try:
            market_name = self.market_info[market]["name"]
            logger.info(f"{market_name} 주문 데이터 수집 시작: {account_name} (시장: {market})")
            
            # 인증 정보 가져오기
            credentials = await self.token_manager.get_credentials(account_name)
            
            # API 파라미터 구성 - 도매꾹 API는 주문 조회를 직접 지원하지 않을 수 있음
            # 대신 상품 수집과 유사한 방식으로 시도
            params = {
                "ver": credentials["version"],
                "mode": "getItemList",  # 상품 목록 조회 모드 사용
                "aid": credentials["api_key"],
                "market": market,
                "om": "json",  # JSON 형식
                "sz": size,
                "pg": page,
                "kw": "주문"  # 주문 관련 키워드로 검색 시도
            }
            
            # 디버깅을 위한 로그 추가
            logger.info(f"도매꾹 주문 API 요청 파라미터: {params}")
            
            # 선택적 파라미터 추가
            if start_date:
                params["startDate"] = start_date
            if end_date:
                params["endDate"] = end_date
            if order_status:
                params["orderStatus"] = order_status
            if seller_id:
                params["sellerId"] = seller_id
            
            # None 값 제거
            params = {k: v for k, v in params.items() if v is not None}
            
            # API 요청
            result = await self._make_api_request(params)
            
            # 디버깅을 위한 응답 로그 추가
            logger.info(f"도매꾹 주문 API 응답: {result}")
            
            if not result:
                logger.error(f"{market_name} 주문 API 응답 없음")
                return []
            
            # 응답 데이터 파싱
            orders = await self._parse_order_response(result)
            
            # 시장별 메타데이터 추가
            for order in orders:
                order["account_name"] = account_name
                order["market"] = market
                order["market_name"] = market_name
                order["market_type"] = self.market_info[market]["supplier_type"]
                order["collected_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"{market_name} 주문 데이터 수집 완료: {len(orders)}개")
            return orders
            
        except Exception as e:
            self.error_handler.log_error(e, f"{market_name} 주문 데이터 수집 실패: {account_name}")
            return []
    
    async def _parse_order_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """주문 API 응답 파싱"""
        try:
            orders = []
            
            # 도매꾹 주문 JSON 응답 구조 확인
            if "domeggook" in response:
                domeggook_data = response["domeggook"]
                
                if "orderList" in domeggook_data and "order" in domeggook_data["orderList"]:
                    order_items = domeggook_data["orderList"]["order"]
                    
                    # 단일 주문인 경우 리스트로 변환
                    if not isinstance(order_items, list):
                        order_items = [order_items]
                    
                    for order_item in order_items:
                        order_data = {
                            "order_id": str(order_item.get("orderNo", "")),
                            "order_date": order_item.get("orderDate", ""),
                            "order_status": order_item.get("orderStatus", ""),
                            "total_amount": int(order_item.get("totalAmount", 0)) if order_item.get("totalAmount") else 0,
                            "shipping_fee": int(order_item.get("shippingFee", 0)) if order_item.get("shippingFee") else 0,
                            "buyer_name": order_item.get("buyerName", ""),
                            "buyer_phone": order_item.get("buyerPhone", ""),
                            "shipping_address": order_item.get("shippingAddress", ""),
                            "payment_method": order_item.get("paymentMethod", ""),
                            "seller_id": order_item.get("sellerId", ""),
                            "seller_nick": order_item.get("sellerNick", ""),
                            "order_items": order_item.get("orderItems", []),
                            "memo": order_item.get("memo", ""),
                            "tracking_number": order_item.get("trackingNumber", "")
                        }
                        
                        orders.append(order_data)
                
                # 헤더 정보도 로깅
                if "header" in domeggook_data:
                    header = domeggook_data["header"]
                    logger.info(f"도매꾹 주문 응답 헤더 - 총 주문: {header.get('numberOfOrders', 0)}, 현재 페이지: {header.get('currentPage', 1)}")
            
            # 에러 응답인 경우
            elif "errors" in response:
                error_info = response["errors"]
                logger.error(f"도매꾹 주문 API 에러: {error_info.get('message', 'Unknown error')}")
                return []
            
            else:
                logger.warning(f"예상하지 못한 주문 응답 형식: {list(response.keys())}")
                return []
            
            return orders
            
        except Exception as e:
            self.error_handler.log_error(e, "도매꾹 주문 API 응답 파싱 실패")
            return []
    
    async def collect_orders_batch(self, account_name: str,
                                 batch_size: int = 200,
                                 max_pages: int = 10,
                                 market: str = "dome",
                                 **kwargs) -> List[Dict[str, Any]]:
        """주문 데이터 배치 수집 (단일 시장)"""
        try:
            market_name = self.market_info[market]["name"]
            logger.info(f"{market_name} 주문 데이터 배치 수집 시작: {account_name} (배치 크기: {batch_size}, 최대 페이지: {max_pages})")
            
            all_orders = []
            
            for page in range(1, max_pages + 1):
                logger.info(f"{market_name} 주문 페이지 {page} 수집 중...")
                
                orders = await self.collect_orders(
                    account_name=account_name,
                    market=market,
                    size=batch_size,
                    page=page,
                    **kwargs
                )
                
                if not orders:
                    logger.info(f"{market_name} 주문 페이지 {page}에서 주문을 찾지 못했습니다. 수집을 종료합니다.")
                    break
                
                all_orders.extend(orders)
                logger.info(f"{market_name} 주문 페이지 {page} 완료: {len(orders)}개 주문")
                
                # API 호출 간격 조절
                await asyncio.sleep(0.5)
            
            logger.info(f"{market_name} 주문 배치 수집 완료: 총 {len(all_orders)}개 주문")
            return all_orders
            
        except Exception as e:
            self.error_handler.log_error(e, f"{market_name} 주문 배치 수집 실패: {account_name}")
            return []


class DomaemaeDataStorage:
    """도매꾹 데이터 저장 서비스 (도매꾹/도매매 구분 저장)"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
        
        # 시장별 공급사 코드 매핑
        self.market_supplier_mapping = {
            "dome": "domaemae_dome",      # 도매꾹
            "supply": "domaemae_supply"   # 도매매
        }
    
    async def _get_supplier_id(self, supplier_code: str) -> str:
        """공급사 ID 조회"""
        try:
            result = await self.db_service.select_data(
                "suppliers",
                {"code": supplier_code}
            )
            if result:
                return result[0]["id"]
            else:
                raise ValueError(f"공급사를 찾을 수 없습니다: {supplier_code}")
        except Exception as e:
            self.error_handler.log_error(e, f"공급사 ID 조회 실패: {supplier_code}")
            raise
    
    async def _get_supplier_account_id(self, supplier_code: str, account_name: str) -> str:
        """공급사 계정 ID 조회"""
        try:
            supplier_id = await self._get_supplier_id(supplier_code)
            result = await self.db_service.select_data(
                "supplier_accounts",
                {"supplier_id": supplier_id, "account_name": account_name}
            )
            if result:
                return result[0]["id"]
            else:
                raise ValueError(f"공급사 계정을 찾을 수 없습니다: {supplier_code}/{account_name}")
        except Exception as e:
            self.error_handler.log_error(e, f"공급사 계정 ID 조회 실패: {supplier_code}/{account_name}")
            raise
    
    def _calculate_hash(self, data: Dict[str, Any]) -> str:
        """데이터 해시 계산"""
        import hashlib
        import json
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
    
    async def save_products(self, products: List[Dict[str, Any]]) -> int:
        """상품 데이터 저장 (시장별 구분)"""
        try:
            if not products:
                logger.info("저장할 상품 데이터가 없습니다")
                return 0
            
            # 시장별로 그룹화
            market_groups = {}
            for product in products:
                market = product.get("market", "dome")
                if market not in market_groups:
                    market_groups[market] = []
                market_groups[market].append(product)
            
            logger.info(f"도매꾹 상품 데이터 저장 시작: {len(products)}개 (시장별: {dict((k, len(v)) for k, v in market_groups.items())})")
            
            saved_count = 0
            for market, market_products in market_groups.items():
                market_name = "도매꾹" if market == "dome" else "도매매"
                logger.info(f"{market_name} 상품 저장 시작: {len(market_products)}개")
                
                for product in market_products:
                    try:
                        # 시장별 공급사 코드 결정
                        supplier_code = self.market_supplier_mapping.get(market, "domaemae")
                        
                        # 원본 데이터 저장 (raw_product_data 테이블)
                        raw_data = {
                            "supplier_id": await self._get_supplier_id(supplier_code),
                            "supplier_account_id": await self._get_supplier_account_id(supplier_code, product["account_name"]),
                            "raw_data": json.dumps(product, ensure_ascii=False),
                            "collection_method": "api",
                            "collection_source": "https://domeggook.com/ssl/api/",
                            "supplier_product_id": f"{market}_{product['supplier_key']}",  # 시장 구분을 위한 접두사
                            "is_processed": False,
                            "data_hash": self._calculate_hash(product),
                            "metadata": json.dumps({
                                "collected_at": product["collected_at"],
                                "account_name": product["account_name"],
                                "market": product.get("market", ""),
                                "market_name": product.get("market_name", ""),
                                "market_type": product.get("market_type", ""),
                                "min_order_type": product.get("min_order_type", "")
                            }, ensure_ascii=False)
                        }
                    
                        # 기존 데이터 확인 (시장 구분된 ID로)
                        product_id = f"{market}_{product['supplier_key']}"
                        existing = await self.db_service.select_data(
                            "raw_product_data",
                            {"supplier_product_id": product_id}
                        )
                        
                        if existing:
                            # 업데이트
                            update_result = await self.db_service.update_data(
                                "raw_product_data",
                                {"supplier_product_id": product_id},
                                raw_data
                            )
                            if update_result:
                                logger.debug(f"{market_name} 상품 데이터 업데이트: {product_id}")
                            else:
                                logger.warning(f"{market_name} 상품 데이터 업데이트 실패 (레코드 없음): {product_id}")
                                # 업데이트 실패 시 새로 삽입 시도
                                await self.db_service.insert_data("raw_product_data", raw_data)
                                logger.debug(f"{market_name} 상품 데이터 삽입 (업데이트 실패 후): {product_id}")
                        else:
                            # 새로 삽입
                            await self.db_service.insert_data("raw_product_data", raw_data)
                            logger.debug(f"{market_name} 상품 데이터 삽입: {product_id}")
                        
                        saved_count += 1
                        
                    except Exception as e:
                        self.error_handler.log_error(e, f"{market_name} 상품 저장 실패: {product.get('supplier_key', 'Unknown')}")
                        continue
                
                logger.info(f"{market_name} 상품 저장 완료: {len(market_products)}개")
            
            logger.info(f"도매꾹 상품 데이터 저장 완료: 총 {saved_count}개")
            return saved_count
        except Exception as e:
            self.error_handler.log_error(e, "도매꾹 상품 데이터 저장 실패")
            return 0
    
    async def save_orders(self, orders: List[Dict[str, Any]]) -> int:
        """주문 데이터 저장 (시장별 구분)"""
        try:
            if not orders:
                logger.info("저장할 주문 데이터가 없습니다")
                return 0
            
            # 시장별로 그룹화
            market_groups = {}
            for order in orders:
                market = order.get("market", "dome")
                if market not in market_groups:
                    market_groups[market] = []
                market_groups[market].append(order)
            
            logger.info(f"도매꾹 주문 데이터 저장 시작: {len(orders)}개 (시장별: {dict((k, len(v)) for k, v in market_groups.items())})")
            
            saved_count = 0
            for market, market_orders in market_groups.items():
                market_name = "도매꾹" if market == "dome" else "도매매"
                logger.info(f"{market_name} 주문 저장 시작: {len(market_orders)}개")
                
                for order in market_orders:
                    try:
                        # 시장별 공급사 코드 결정
                        supplier_code = self.market_supplier_mapping.get(market, "domaemae")
                        
                        # 주문 데이터 저장 (raw_order_data 테이블)
                        raw_data = {
                            "supplier_id": await self._get_supplier_id(supplier_code),
                            "supplier_account_id": await self._get_supplier_account_id(supplier_code, order["account_name"]),
                            "raw_data": json.dumps(order, ensure_ascii=False),
                            "collection_method": "api",
                            "collection_source": "https://domeggook.com/ssl/api/",
                            "supplier_order_id": f"{market}_{order['order_id']}",  # 시장 구분을 위한 접두사
                            "is_processed": False,
                            "data_hash": self._calculate_hash(order),
                            "metadata": json.dumps({
                                "collected_at": order["collected_at"],
                                "account_name": order["account_name"],
                                "market": order.get("market", ""),
                                "market_name": order.get("market_name", ""),
                                "market_type": order.get("market_type", ""),
                                "order_date": order.get("order_date", ""),
                                "order_status": order.get("order_status", ""),
                                "total_amount": order.get("total_amount", 0)
                            }, ensure_ascii=False)
                        }
                        
                        # 기존 주문 데이터 확인 (시장 구분된 ID로)
                        order_id = f"{market}_{order['order_id']}"
                        existing = await self.db_service.select_data(
                            "raw_order_data",
                            {"supplier_order_id": order_id}
                        )
                        
                        if existing:
                            # 업데이트
                            update_result = await self.db_service.update_data(
                                "raw_order_data",
                                {"supplier_order_id": order_id},
                                raw_data
                            )
                            if update_result:
                                logger.debug(f"{market_name} 주문 데이터 업데이트: {order_id}")
                            else:
                                logger.warning(f"{market_name} 주문 데이터 업데이트 실패 (레코드 없음): {order_id}")
                                # 업데이트 실패 시 새로 삽입 시도
                                await self.db_service.insert_data("raw_order_data", raw_data)
                                logger.debug(f"{market_name} 주문 데이터 삽입 (업데이트 실패 후): {order_id}")
                        else:
                            # 새로 삽입
                            await self.db_service.insert_data("raw_order_data", raw_data)
                            logger.debug(f"{market_name} 주문 데이터 삽입: {order_id}")
                        
                        saved_count += 1
                        
                    except Exception as e:
                        self.error_handler.log_error(e, f"{market_name} 주문 저장 실패: {order.get('order_id', 'Unknown')}")
                        continue
                
                logger.info(f"{market_name} 주문 저장 완료: {len(market_orders)}개")
            
            logger.info(f"도매꾹 주문 데이터 저장 완료: 총 {saved_count}개")
            return saved_count
        except Exception as e:
            self.error_handler.log_error(e, "도매꾹 주문 데이터 저장 실패")
            return 0
