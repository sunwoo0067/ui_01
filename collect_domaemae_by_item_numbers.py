#!/usr/bin/env python3
"""
도매꾹/도매매 상품번호 기반 배치 수집
getItemView + multiple=true로 100개씩 수집
"""

import asyncio
import json
import requests
import hashlib
from datetime import datetime
from loguru import logger
from src.services.database_service import DatabaseService


class ItemNumberBatchCollector:
    """상품번호 기반 배치 수집기"""
    
    def __init__(self):
        self.db = DatabaseService()
        self.api_key = None
        self.version = "4.1"
        self.url = 'https://domeggook.com/ssl/api/'
        
        self.supplier_ids = {
            "dome": "d9e6fa42-9bd4-438f-bf3b-10cf199eabd2",
            "supply": "a9990a09-ae6f-474b-87b8-75840a110519"
        }
    
    async def _init_credentials(self):
        """인증 정보 초기화"""
        accounts = await self.db.select_data(
            'supplier_accounts',
            {'supplier_id': 'baa2ccd3-a328-4387-b307-6ae89aea331b'}
        )
        
        if accounts:
            credentials = json.loads(accounts[0]['account_credentials'])
            self.api_key = credentials.get('api_key')
            self.version = credentials.get('version', '4.1')
    
    def collect_batch_by_numbers(self, start_no: int, end_no: int, batch_size: int = 100):
        """상품번호 범위로 배치 수집 (getItemView multiple)"""
        
        all_products = []
        
        current = start_no
        while current <= end_no:
            # 100개씩 상품번호 생성
            numbers = []
            for i in range(batch_size):
                if current + i > end_no:
                    break
                numbers.append(str(current + i))
            
            if not numbers:
                break
            
            # 콤마로 연결
            no_param = ','.join(numbers)
            
            param = {
                'ver': self.version,
                'mode': 'getItemView',
                'aid': self.api_key,
                'no': no_param,
                'multiple': 'true',
                'om': 'json'
            }
            
            try:
                res = requests.get(self.url, params=param, timeout=30)
                
                if res.status_code == 200:
                    data = json.loads(res.content)
                    
                    # 에러 체크
                    if 'errors' in data:
                        logger.warning(f"   범위 {current}-{current+len(numbers)-1}: 에러")
                        current += batch_size
                        continue
                    
                    # 상품 데이터 추출
                    items_data = data.get('domeggook', {}).get('items', [])
                    
                    if items_data:
                        if not isinstance(items_data, list):
                            items_data = [items_data]
                        
                        all_products.extend(items_data)
                        logger.info(f"   범위 {current}-{current+len(numbers)-1}: +{len(items_data)}개 (누적: {len(all_products)})")
                    else:
                        logger.debug(f"   범위 {current}-{current+len(numbers)-1}: 0개")
                
                current += batch_size
                
            except Exception as e:
                logger.error(f"   오류: {e}")
                current += batch_size
                continue
        
        return all_products
    
    async def collect_simple_keyword(self, market: str, keyword: str = "가방", target: int = 5000):
        """간단한 키워드로 배치 수집 (sz=200)"""
        market_name = "도매꾹" if market == "dome" else "도매매"
        
        logger.info("="*70)
        logger.info(f"🔍 {market_name} 키워드 기반 배치 수집")
        logger.info(f"   키워드: '{keyword}'")
        logger.info(f"   목표: {target:,}개")
        logger.info("="*70)
        
        all_products = []
        page = 1
        max_pages = (target // 200) + 1
        
        while len(all_products) < target and page <= max_pages:
            param = {
                'ver': self.version,
                'mode': 'getItemList',
                'aid': self.api_key,
                'market': market,
                'om': 'json',
                'sz': 200,
                'pg': page,
                'kw': keyword,
                'so': 'rd'  # 도매꾹랭킹순
            }
            
            try:
                res = requests.get(self.url, params=param, timeout=30)
                
                if res.status_code == 200:
                    data = json.loads(res.content)
                    
                    if 'errors' in data:
                        logger.error(f"API 에러: {data['errors'].get('message')}")
                        break
                    
                    header = data.get('domeggook', {}).get('header', {})
                    total_items = header.get('numberOfItems', 0)
                    
                    if page == 1:
                        logger.info(f"\n📊 검색 결과: {total_items:,}개")
                        if total_items == 0:
                            logger.warning(f"키워드 '{keyword}'로 상품을 찾을 수 없습니다")
                            return []
                    
                    items = data.get('domeggook', {}).get('list', {}).get('item', [])
                    
                    if not items:
                        break
                    
                    if isinstance(items, dict):
                        items = [items]
                    
                    # 상품 정보 추출
                    for item in items:
                        product = {
                            "supplier_key": str(item.get("no", "")),
                            "title": item.get("title", ""),
                            "price": int(item.get("price", 0)),
                            "unit_quantity": int(item.get("unitQty", 1)),
                            "seller_id": item.get("id", ""),
                            "seller_nick": item.get("nick", ""),
                            "thumbnail_url": item.get("thumb", ""),
                            "product_url": item.get("url", ""),
                            "company_only": item.get("comOnly") == "true",
                            "adult_only": item.get("adultOnly") == "true",
                            "lowest_price": item.get("lwp") == "true",
                            "use_options": item.get("useopt") == "true",
                            "market_info": item.get("market", {}),
                            "dome_price": item.get("domePrice", ""),
                            "quantity_info": item.get("qty", {}),
                            "delivery_info": item.get("deli", {}),
                            "idx_com": item.get("idxCOM", ""),
                            "market": market,
                            "market_name": market_name,
                            "search_keyword": keyword,
                            "collected_at": datetime.now().isoformat()
                        }
                        
                        all_products.append(product)
                    
                    logger.info(f"   페이지 {page}: +{len(items)}개 (누적: {len(all_products)}/{total_items})")
                    
                    if len(all_products) >= total_items or len(all_products) >= target:
                        break
                    
                    page += 1
                    
                else:
                    logger.error(f"API 오류: {res.status_code}")
                    break
                    
            except Exception as e:
                logger.error(f"수집 오류: {e}")
                break
        
        logger.info(f"\n✅ 수집 완료: {len(all_products)}개")
        
        # 데이터베이스 저장
        supplier_id = self.supplier_ids[market]
        saved = await self._save_to_db(all_products, supplier_id, market)
        
        logger.info(f"💾 저장 완료: {saved}개")
        
        return {
            "market": market_name,
            "keyword": keyword,
            "total": len(all_products),
            "saved": saved
        }
    
    async def _save_to_db(self, products, supplier_id, market):
        """데이터베이스 저장"""
        saved = 0
        
        for product in products:
            try:
                supplier_product_id = f"{market}_{product.get('supplier_key', '')}"
                
                data_str = json.dumps(product, sort_keys=True, ensure_ascii=False)
                data_hash = hashlib.md5(data_str.encode('utf-8')).hexdigest()
                
                raw_data = {
                    "supplier_id": supplier_id,
                    "raw_data": json.dumps(product, ensure_ascii=False),
                    "collection_method": "api",
                    "collection_source": "keyword_batch",
                    "supplier_product_id": supplier_product_id,
                    "is_processed": False,
                    "data_hash": data_hash,
                    "metadata": json.dumps({
                        "collected_at": product.get("collected_at"),
                        "keyword": product.get("search_keyword")
                    }, ensure_ascii=False)
                }
                
                existing = await self.db.select_data(
                    "raw_product_data",
                    {"supplier_id": supplier_id, "supplier_product_id": supplier_product_id}
                )
                
                if existing:
                    await self.db.update_data("raw_product_data", raw_data, {"id": existing[0]["id"]})
                else:
                    await self.db.insert_data("raw_product_data", raw_data)
                
                saved += 1
                
            except Exception as e:
                logger.warning(f"저장 실패: {e}")
                continue
        
        return saved


async def main():
    """메인 실행"""
    collector = ItemNumberBatchCollector()
    await collector._init_credentials()
    
    logger.info("🎯 도매꾹/도매매 배치 타입 수집")
    logger.info("   방식: 키워드 기반 (sz=200개씩)\n")
    
    # 다양한 키워드로 수집 (중복 제거됨)
    keywords = [
        ("가방", 5000),
        ("의류", 5000),
        ("화장품", 3000),
        ("생활용품", 3000),
        ("주방용품", 2000),
        ("전자제품", 2000),
        ("문구", 2000),
        ("완구", 2000),
        ("스포츠", 2000),
        ("식품", 2000)
    ]
    
    results = {}
    
    # 도매꾹
    logger.info("\n" + "="*70)
    logger.info("1단계: 도매꾹(dome) 수집")
    logger.info("="*70)
    
    dome_total = 0
    for keyword, target in keywords:
        result = await collector.collect_simple_keyword("dome", keyword, target)
        dome_total += result['total']
        logger.info(f"\n   '{keyword}': {result['total']:,}개 수집, {result['saved']:,}개 저장")
    
    results['dome'] = {"total": dome_total}
    
    # 도매매
    logger.info("\n" + "="*70)
    logger.info("2단계: 도매매(supply) 수집")
    logger.info("="*70)
    
    supply_total = 0
    for keyword, target in keywords:
        result = await collector.collect_simple_keyword("supply", keyword, target)
        supply_total += result['total']
        logger.info(f"\n   '{keyword}': {result['total']:,}개 수집, {result['saved']:,}개 저장")
    
    results['supply'] = {"total": supply_total}
    
    # 최종 결과
    logger.info("\n" + "="*70)
    logger.info("✅ 배치 수집 완료")
    logger.info("="*70)
    logger.info(f"   도매꾹(dome): {dome_total:,}개")
    logger.info(f"   도매매(supply): {supply_total:,}개")
    logger.info(f"   총계: {dome_total + supply_total:,}개")
    logger.info("="*70)
    
    with open('domaemae_keyword_batch_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(main())

