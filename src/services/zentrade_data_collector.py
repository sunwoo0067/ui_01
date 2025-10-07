import asyncio
import aiohttp
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger

from src.services.database_service import DatabaseService
from src.services.supplier_account_manager import SupplierAccountManager
from src.utils.error_handler import ErrorHandler


class ZentradeTokenManager:
    """젠트레이드 API 토큰 관리"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
        self.account_manager = SupplierAccountManager()
        
    async def get_credentials(self, account_name: str) -> Dict[str, str]:
        """계정 정보에서 인증 정보 가져오기"""
        try:
            account = await self.account_manager.get_supplier_account("zentrade", account_name)
            if not account:
                raise ValueError(f"젠트레이드 계정을 찾을 수 없습니다: {account_name}")
            
            credentials = account.get("account_credentials", {})
            return {
                "id": credentials.get("id"),
                "m_skey": credentials.get("m_skey")
            }
        except Exception as e:
            self.error_handler.log_error(e, f"젠트레이드 인증 정보 조회 실패: {account_name}")
            raise


class ZentradeDataCollector:
    """젠트레이드 데이터 수집기"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
        self.token_manager = ZentradeTokenManager(db_service)
        
    async def _make_api_request(self, url: str, params: Dict[str, Any]) -> Optional[str]:
        """API 요청 실행 (POST 방식으로 변경)"""
        try:
            # 브라우저 헤더 추가 (WAF 우회)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                'Referer': 'https://www.zentrade.co.kr/',
                'Origin': 'https://www.zentrade.co.kr',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # POST 방식으로 변경 (API 문서에서 GET/POST 모두 지원)
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(url, data=params, timeout=30) as response:
                    if response.status == 200:
                        # 젠트레이드 API는 euc-kr 인코딩 사용
                        content = await response.text(encoding='euc-kr')
                        return content
                    else:
                        logger.error(f"API 요청 실패: {response.status}")
                        error_text = await response.text()
                        logger.error(f"오류 내용: {error_text[:200]}")
                        return None
        except Exception as e:
            self.error_handler.log_error(e, f"API 요청 실패: {url}")
            return None
    
    async def _parse_xml_products(self, xml_content: str) -> List[Dict[str, Any]]:
        """XML 상품 데이터 파싱"""
        try:
            root = ET.fromstring(xml_content)
            products = []
            
            # 모든 product 태그 찾기
            product_elements = root.findall('.//product')
            
            for product in product_elements:
                product_data = {
                    "supplier_key": product.get('code', ''),
                    "category": "",
                    "category_code": "",
                    "title": "",
                    "brand": "",
                    "model": "",
                    "price": 0,
                    "consumer_price": 0,
                    "tax_mode": "",
                    "images": [],
                    "options": [],
                    "content": "",
                    "keywords": "",
                    "runout": 0,
                    "opendate": "",
                    "collected_at": datetime.utcnow().isoformat()
                }
                
                # 카테고리 정보
                dome_category = product.find('dome_category')
                if dome_category is not None:
                    product_data["category"] = dome_category.text or ""
                    product_data["category_code"] = dome_category.get('dome_catecode', "")
                
                # 상품명
                prdtname = product.find('prdtname')
                if prdtname is not None:
                    product_data["title"] = prdtname.text or ""
                
                # 기본 정보
                baseinfo = product.find('baseinfo')
                if baseinfo is not None:
                    product_data["brand"] = baseinfo.get('brand', "")
                    product_data["model"] = baseinfo.get('model', "")
                
                # 가격 정보
                price = product.find('price')
                if price is not None:
                    product_data["price"] = float(price.get('buyprice', 0))
                    product_data["consumer_price"] = float(price.get('consumerprice', 0))
                    product_data["tax_mode"] = price.get('taxmode', "")
                
                # 이미지 정보
                listimg = product.find('listimg')
                if listimg is not None:
                    images = []
                    for i in range(1, 6):  # url1 ~ url5
                        url = listimg.get(f'url{i}', '')
                        if url:
                            images.append(url)
                    product_data["images"] = images
                
                # 옵션 정보
                option = product.find('option')
                if option is not None:
                    opt1nm = option.get('opt1nm', '')
                    opt_content = option.text or ""
                    
                    if opt_content:
                        options = []
                        for opt_line in opt_content.split('↑=↑'):
                            if '^|^' in opt_line:
                                parts = opt_line.split('^|^')
                                if len(parts) >= 3:
                                    options.append({
                                        "name": parts[0].strip(),
                                        "price": float(parts[1]) if parts[1] else 0,
                                        "consumer_price": float(parts[2]) if parts[2] else 0,
                                        "image": parts[3] if len(parts) > 3 else ""
                                    })
                        product_data["options"] = options
                
                # 상세 내용
                content = product.find('content')
                if content is not None:
                    product_data["content"] = content.text or ""
                
                # 키워드
                keyword = product.find('keyword')
                if keyword is not None:
                    product_data["keywords"] = keyword.text or ""
                
                # 상태 정보
                status = product.find('status')
                if status is not None:
                    product_data["runout"] = int(status.get('runout', 0))
                    product_data["opendate"] = status.get('opendate', "")
                
                products.append(product_data)
            
            return products
            
        except Exception as e:
            self.error_handler.log_error(e, "XML 상품 데이터 파싱 실패")
            return []
    
    async def collect_products(self, account_name: str, 
                            goodsno: Optional[str] = None,
                            runout: Optional[int] = None,
                            opendate_s: Optional[str] = None,
                            opendate_e: Optional[str] = None) -> List[Dict[str, Any]]:
        """상품 데이터 수집"""
        try:
            logger.info(f"젠트레이드 상품 데이터 수집 시작: {account_name}")
            
            # 인증 정보 가져오기
            credentials = await self.token_manager.get_credentials(account_name)
            
            # API 파라미터 구성
            params = {
                "id": credentials["id"],
                "m_skey": credentials["m_skey"]
            }
            
            # 선택적 파라미터 추가 (None 값 제외)
            if goodsno:
                params["goodsno"] = goodsno
            if runout is not None:
                params["runout"] = runout
            if opendate_s:
                params["opendate_s"] = opendate_s
            if opendate_e:
                params["opendate_e"] = opendate_e
            
            # None 값 제거
            params = {k: v for k, v in params.items() if v is not None}
            
            # API 요청
            url = "https://www.zentrade.co.kr/shop/proc/product_api.php"
            xml_content = await self._make_api_request(url, params)
            
            if not xml_content:
                logger.error("젠트레이드 API 응답 없음")
                return []
            
            # XML 파싱
            products = await self._parse_xml_products(xml_content)
            
            # 계정명 추가
            for product in products:
                product["account_name"] = account_name
            
            logger.info(f"젠트레이드 상품 데이터 수집 완료: {len(products)}개")
            return products
            
        except Exception as e:
            self.error_handler.log_error(e, f"젠트레이드 상품 데이터 수집 실패: {account_name}")
            return []
    
    async def collect_orders(self, account_name: str, 
                           ordno: Optional[str] = None,
                           pordno: Optional[str] = None) -> List[Dict[str, Any]]:
        """주문 데이터 수집"""
        try:
            logger.info(f"젠트레이드 주문 데이터 수집 시작: {account_name}")
            
            # 인증 정보 가져오기
            credentials = await self.token_manager.get_credentials(account_name)
            
            # API 파라미터 구성
            params = {
                "id": credentials["id"],
                "m_skey": credentials["m_skey"]
            }
            
            # 주문번호 파라미터 (ordno 또는 pordno 중 하나는 필수)
            if ordno:
                params["ordno"] = ordno
            elif pordno:
                params["pordno"] = pordno
            else:
                logger.error("주문번호(ordno 또는 pordno)가 필요합니다")
                return []
            
            # API 요청
            url = "https://www.zentrade.co.kr/shop/proc/order_api.php"
            xml_content = await self._make_api_request(url, params)
            
            if not xml_content:
                logger.error("젠트레이드 주문 API 응답 없음")
                return []
            
            # XML 파싱
            orders = await self._parse_xml_orders(xml_content)
            
            # 계정명 추가
            for order in orders:
                order["account_name"] = account_name
            
            logger.info(f"젠트레이드 주문 데이터 수집 완료: {len(orders)}개")
            return orders
            
        except Exception as e:
            self.error_handler.log_error(e, f"젠트레이드 주문 데이터 수집 실패: {account_name}")
            return []
    
    async def _parse_xml_orders(self, xml_content: str) -> List[Dict[str, Any]]:
        """XML 주문 데이터 파싱"""
        try:
            root = ET.fromstring(xml_content)
            orders = []
            
            for ord_info in root.findall('ord_info'):
                order_data = {
                    "supplier_key": ord_info.get('ordno', ''),
                    "personal_order_no": ord_info.get('pordno', ''),
                    "order_date": "",
                    "receiver_name": "",
                    "receiver_phone": "",
                    "receiver_mobile": "",
                    "address": "",
                    "items": [],
                    "delivery_company": "",
                    "delivery_number": "",
                    "zentrade_message": "",
                    "collected_at": datetime.utcnow().isoformat()
                }
                
                # 주문일시
                ord_date = ord_info.find('ord_date')
                if ord_date is not None:
                    order_data["order_date"] = ord_date.text or ""
                
                # 받는사람 정보
                name_receiver = ord_info.find('nameReceiver')
                if name_receiver is not None:
                    order_data["receiver_name"] = name_receiver.text or ""
                
                phone_receiver = ord_info.find('phoneReceiver')
                if phone_receiver is not None:
                    order_data["receiver_phone"] = phone_receiver.text or ""
                
                mobile_receiver = ord_info.find('mobileReceiver')
                if mobile_receiver is not None:
                    order_data["receiver_mobile"] = mobile_receiver.text or ""
                
                # 주소
                address = ord_info.find('address')
                if address is not None:
                    order_data["address"] = address.text or ""
                
                # 주문 상품들
                items = []
                for i in range(1, 10):  # ord_item1 ~ ord_item9
                    item = ord_info.find(f'ord_item{i}')
                    if item is not None and item.text:
                        items.append(item.text.strip())
                order_data["items"] = items
                
                # 배송 정보
                deli_info = ord_info.find('deli_info')
                if deli_info is not None:
                    order_data["delivery_company"] = deli_info.get('delicom', '')
                    order_data["delivery_number"] = deli_info.get('delinum', '')
                
                # 젠트레이드 메시지
                zentrade_msg = ord_info.find('zentrade_msg')
                if zentrade_msg is not None:
                    order_data["zentrade_message"] = zentrade_msg.text or ""
                
                orders.append(order_data)
            
            return orders
            
        except Exception as e:
            self.error_handler.log_error(e, "XML 주문 데이터 파싱 실패")
            return []
    
    async def collect_products_batch(self, account_name: str,
                                   batch_size: int = 1000,
                                   goodsno: Optional[str] = None,
                                   runout: Optional[int] = None,
                                   opendate_s: Optional[str] = None,
                                   opendate_e: Optional[str] = None,
                                   storage_service = None) -> int:
        """상품 데이터 배치 수집 및 저장"""
        try:
            logger.info(f"젠트레이드 상품 데이터 배치 수집 시작: {account_name} (배치 크기: {batch_size})")
            
            # 전체 상품 데이터 수집
            all_products = await self.collect_products(
                account_name=account_name,
                goodsno=goodsno,
                runout=runout,
                opendate_s=opendate_s,
                opendate_e=opendate_e
            )
            
            logger.info(f"전체 상품 데이터 수집 완료: {len(all_products)}개")
            
            # 배치별로 저장
            total_saved = 0
            for i in range(0, len(all_products), batch_size):
                batch = all_products[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                logger.info(f"배치 {batch_num} 저장 시작: {len(batch)}개 상품")
                
                if storage_service:
                    saved_count = await storage_service.save_products(batch)
                    total_saved += saved_count
                    logger.info(f"배치 {batch_num} 저장 완료: {saved_count}개 저장됨")
                else:
                    logger.info(f"배치 {batch_num} 준비 완료: {len(batch)}개 상품 (저장 서비스 없음)")
                
                # 배치 간 짧은 지연
                await asyncio.sleep(0.1)
            
            logger.info(f"모든 배치 저장 완료: 총 {total_saved}개 상품 저장됨")
            return total_saved
            
        except Exception as e:
            self.error_handler.log_error(e, f"젠트레이드 상품 데이터 배치 수집 실패: {account_name}")
            return 0


class ZentradeDataStorage:
    """젠트레이드 데이터 저장 서비스"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
    
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
        """상품 데이터 저장"""
        try:
            if not products:
                logger.info("저장할 상품 데이터가 없습니다")
                return 0
            
            logger.info(f"젠트레이드 상품 데이터 저장 시작: {len(products)}개")
            
            saved_count = 0
            for product in products:
                try:
                    # 원본 데이터 저장 (raw_product_data 테이블)
                    raw_data = {
                        "supplier_id": await self._get_supplier_id("zentrade"),
                        "supplier_account_id": await self._get_supplier_account_id("zentrade", product["account_name"]),
                        "raw_data": json.dumps(product, ensure_ascii=False),
                        "collection_method": "api",
                        "collection_source": "https://www.zentrade.co.kr/shop/proc/product_api.php",
                        "supplier_product_id": product["supplier_key"],
                        "is_processed": False,
                        "data_hash": self._calculate_hash(product),
                        "metadata": json.dumps({
                            "collected_at": product["collected_at"],
                            "account_name": product["account_name"]
                        }, ensure_ascii=False)
                    }
                    
                    # 기존 데이터 확인
                    existing = await self.db_service.select_data(
                        "raw_product_data",
                        {"supplier_product_id": product["supplier_key"]}
                    )
                    
                    if existing:
                        # 업데이트
                        update_result = await self.db_service.update_data(
                            "raw_product_data",
                            {"supplier_product_id": product["supplier_key"]},
                            raw_data
                        )
                        if update_result:
                            logger.debug(f"젠트레이드 상품 데이터 업데이트: {product['supplier_key']}")
                        else:
                            logger.warning(f"젠트레이드 상품 데이터 업데이트 실패 (레코드 없음): {product['supplier_key']}")
                            # 업데이트 실패 시 새로 삽입 시도
                            await self.db_service.insert_data("raw_product_data", raw_data)
                            logger.debug(f"젠트레이드 상품 데이터 삽입 (업데이트 실패 후): {product['supplier_key']}")
                    else:
                        # 새로 삽입
                        await self.db_service.insert_data("raw_product_data", raw_data)
                        logger.debug(f"젠트레이드 상품 데이터 삽입: {product['supplier_key']}")
                    
                    saved_count += 1
                    
                except Exception as e:
                    self.error_handler.log_error(e, f"젠트레이드 상품 저장 실패: {product.get('supplier_key', 'Unknown')}")
                    continue
            
            logger.info(f"젠트레이드 상품 데이터 저장 완료: {saved_count}개")
            return saved_count
        except Exception as e:
            self.error_handler.log_error(e, "젠트레이드 상품 데이터 저장 실패")
            return 0
    
    async def save_orders(self, orders: List[Dict[str, Any]]) -> int:
        """주문 데이터 저장"""
        try:
            if not orders:
                logger.info("저장할 주문 데이터가 없습니다")
                return 0
            
            logger.info(f"젠트레이드 주문 데이터 저장 시작: {len(orders)}개")
            
            saved_count = 0
            for order in orders:
                try:
                    # 주문 데이터 저장 (raw_order_data 테이블)
                    order_data = {
                        "supplier_id": await self._get_supplier_id("zentrade"),
                        "supplier_account_id": await self._get_supplier_account_id("zentrade", order["account_name"]),
                        "supplier_order_id": order["supplier_key"],
                        "personal_order_no": order.get("personal_order_no", ""),
                        "order_date": order.get("order_date", ""),
                        "receiver_name": order.get("receiver_name", ""),
                        "receiver_phone": order.get("receiver_phone", ""),
                        "receiver_mobile": order.get("receiver_mobile", ""),
                        "address": order.get("address", ""),
                        "items": order.get("items", []),
                        "delivery_company": order.get("delivery_company", ""),
                        "delivery_number": order.get("delivery_number", ""),
                        "zentrade_message": order.get("zentrade_message", ""),
                        "collected_at": order["collected_at"],
                        "account_name": order["account_name"]
                    }
                    
                    # 기존 데이터 확인
                    existing = await self.db_service.select_data(
                        "raw_order_data",
                        {"supplier_order_id": order["supplier_key"]}
                    )
                    
                    if existing:
                        # 업데이트
                        await self.db_service.update_data(
                            "raw_order_data",
                            {"supplier_order_id": order["supplier_key"]},
                            order_data
                        )
                        logger.debug(f"젠트레이드 주문 데이터 업데이트: {order['supplier_key']}")
                    else:
                        # 새로 삽입
                        await self.db_service.insert_data("raw_order_data", order_data)
                        logger.debug(f"젠트레이드 주문 데이터 삽입: {order['supplier_key']}")
                    
                    saved_count += 1
                    
                except Exception as e:
                    self.error_handler.log_error(e, f"젠트레이드 주문 저장 실패: {order.get('supplier_key', 'Unknown')}")
                    continue
            
            logger.info(f"젠트레이드 주문 데이터 저장 완료: {saved_count}개")
            return saved_count
        except Exception as e:
            self.error_handler.log_error(e, "젠트레이드 주문 데이터 저장 실패")
            return 0
