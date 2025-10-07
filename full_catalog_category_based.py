#!/usr/bin/env python3
"""
도매꾹/도매매 카테고리 기반 전체 카탈로그 수집
모든 중분류 카테고리를 순환하여 전체 상품 수집
"""

import asyncio
import aiohttp
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger

from src.services.database_service import DatabaseService


class FullCatalogCollector:
    """전체 카탈로그 수집기"""
    
    def __init__(self):
        self.db = DatabaseService()
        self.api_key = None
        self.version = "4.1"
        
        self.supplier_ids = {
            "domaemae_dome": "d9e6fa42-9bd4-438f-bf3b-10cf199eabd2",
            "domaemae_supply": "a9990a09-ae6f-474b-87b8-75840a110519"
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://domeggook.com/'
        }
        
        self.url = "https://domeggook.com/ssl/api/"
        
        # 주요 중분류 카테고리 (대량등록용)
        self.categories = [
            {"code": "01_01_00_00_00", "name": "패션잡화/화장품 > 패션소품/액세서리"},
            {"code": "01_02_00_00_00", "name": "패션잡화/화장품 > 가방/핸드백"},
            {"code": "01_03_00_00_00", "name": "패션잡화/화장품 > 화장품/뷰티"},
            {"code": "01_04_00_00_00", "name": "패션잡화/화장품 > 여성의류"},
            {"code": "01_05_00_00_00", "name": "패션잡화/화장품 > 남성의류"},
            {"code": "02_01_00_00_00", "name": "디지털/가전 > 디지털기기"},
            {"code": "02_02_00_00_00", "name": "디지털/가전 > 가전제품"},
            {"code": "03_01_00_00_00", "name": "생활/건강 > 생활용품"},
            {"code": "03_02_00_00_00", "name": "생활/건강 > 건강용품"},
            {"code": "03_03_00_00_00", "name": "생활/건강 > 주방용품"},
            {"code": "04_01_00_00_00", "name": "식품 > 식품"},
            {"code": "05_01_00_00_00", "name": "유아동/완구 > 유아동용품"},
            {"code": "05_02_00_00_00", "name": "유아동/완구 > 완구/취미"},
            {"code": "06_01_00_00_00", "name": "스포츠/레저 > 스포츠용품"},
            {"code": "06_02_00_00_00", "name": "스포츠/레저 > 레저용품"},
            {"code": "07_01_00_00_00", "name": "문구/도서 > 문구/사무용품"},
            {"code": "07_02_00_00_00", "name": "문구/도서 > 도서"},
            {"code": "08_01_00_00_00", "name": "반려동물 > 반려동물용품"},
        ]
    
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
    
    async def collect_by_category(self, market: str, category: Dict) -> List[Dict]:
        """카테고리별 전체 상품 수집"""
        market_name = "도매꾹" if market == "dome" else "도매매"
        
        logger.info(f"📦 {market_name} - {category['name']}")
        logger.info(f"   카테고리 코드: {category['code']}")
        
        all_products = []
        page = 1
        max_pages = 1000
        
        while page <= max_pages:
            params = {
                "ver": self.version,
                "mode": "getItemList",
                "aid": self.api_key,
                "market": market,
                "om": "json",
                "sz": 200,
                "pg": page,
                "ca": category['code']
            }
            
            try:
                async with aiohttp.ClientSession(headers=self.headers) as session:
                    async with session.get(self.url, params=params) as response:
                        if response.status != 200:
                            logger.error(f"   API 오류: {response.status}")
                            break
                        
                        data = await response.json()
                        
                        # 에러 체크
                        if "errors" in data:
                            logger.warning(f"   카테고리 에러 (스킵): {data['errors'].get('message')}")
                            break
                        
                        # 헤더 정보
                        header = data.get("domeggook", {}).get("header", {})
                        total_items = header.get("numberOfItems", 0)
                        
                        if page == 1:
                            logger.info(f"   총 상품: {total_items:,}개")
                            if total_items == 0:
                                logger.info(f"   → 카테고리 스킵 (상품 없음)")
                                break
                        
                        # 상품 목록
                        items = data.get("domeggook", {}).get("list", {}).get("item", [])
                        
                        if not items:
                            break
                        
                        # 단일 상품인 경우 리스트로 변환
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
                                "category_code": category['code'],
                                "category_name": category['name'],
                                "collected_at": datetime.now().isoformat()
                            }
                            
                            all_products.append(product)
                        
                        if page % 10 == 0 or len(all_products) >= total_items:
                            logger.info(f"   진행: {len(all_products)}/{total_items}")
                        
                        # 마지막 페이지 체크
                        if len(all_products) >= total_items:
                            break
                        
                        page += 1
                        await asyncio.sleep(0.3)
                        
            except Exception as e:
                logger.error(f"   수집 오류: {e}")
                break
        
        logger.info(f"   ✅ 수집 완료: {len(all_products)}개\n")
        return all_products
    
    async def collect_full_market(self, market: str = "dome"):
        """특정 시장 전체 카탈로그 수집"""
        market_name = "도매꾹" if market == "dome" else "도매매"
        supplier_code = f"domaemae_{market}"
        
        logger.info("="*70)
        logger.info(f"🚀 {market_name} 전체 카탈로그 수집")
        logger.info(f"   전략: 카테고리 순환 (중분류 이하)")
        logger.info("="*70)
        
        await self._init_credentials()
        
        logger.info(f"\n📂 총 {len(self.categories)}개 카테고리 순환 시작\n")
        
        all_products = []
        category_results = []
        
        for idx, category in enumerate(self.categories, 1):
            logger.info(f"[{idx}/{len(self.categories)}]")
            
            products = await self.collect_by_category(market, category)
            
            all_products.extend(products)
            
            category_results.append({
                "category": category['name'],
                "code": category['code'],
                "count": len(products)
            })
            
            logger.info(f"누적: {len(all_products):,}개\n")
            
            await asyncio.sleep(1)
        
        logger.info(f"\n✅ 전체 수집 완료: {len(all_products):,}개")
        
        # 데이터베이스 저장
        logger.info(f"\n💾 데이터베이스 저장 중...")
        
        supplier_id = self.supplier_ids[supplier_code]
        saved = 0
        new = 0
        updated = 0
        
        for idx, product in enumerate(all_products, 1):
            try:
                supplier_product_id = f"{market}_{product.get('supplier_key', '')}"
                
                data_str = json.dumps(product, sort_keys=True, ensure_ascii=False)
                data_hash = hashlib.md5(data_str.encode('utf-8')).hexdigest()
                
                raw_data = {
                    "supplier_id": supplier_id,
                    "raw_data": json.dumps(product, ensure_ascii=False),
                    "collection_method": "api",
                    "collection_source": "category_full_catalog",
                    "supplier_product_id": supplier_product_id,
                    "is_processed": False,
                    "data_hash": data_hash,
                    "metadata": json.dumps({
                        "collected_at": product.get("collected_at"),
                        "category_code": product.get("category_code"),
                        "category_name": product.get("category_name"),
                        "collection_type": "category_batch"
                    }, ensure_ascii=False)
                }
                
                existing = await self.db.select_data(
                    "raw_product_data",
                    {"supplier_id": supplier_id, "supplier_product_id": supplier_product_id}
                )
                
                if existing:
                    await self.db.update_data("raw_product_data", raw_data, {"id": existing[0]["id"]})
                    updated += 1
                else:
                    await self.db.insert_data("raw_product_data", raw_data)
                    new += 1
                
                saved += 1
                
                if idx % 1000 == 0:
                    logger.info(f"   저장: {idx}/{len(all_products)}개 (신규: {new}, 업데이트: {updated})")
                    
            except Exception as e:
                logger.warning(f"   저장 실패: {e}")
                continue
        
        logger.info(f"\n✅ {market_name} 저장 완료: {saved:,}개")
        
        return {
            "market": market_name,
            "categories": len(self.categories),
            "total": len(all_products),
            "new": new,
            "updated": updated,
            "category_results": category_results
        }


async def main():
    """메인 실행"""
    collector = FullCatalogCollector()
    
    logger.info("🎯 도매꾹/도매매 전체 카탈로그 수집")
    logger.info("   방식: 카테고리 기반 순환 (드롭쉬핑 대량등록용)\n")
    
    # 1. 도매꾹(dome) 수집
    dome_result = await collector.collect_full_market("dome")
    
    # 2. 도매매(supply) 수집  
    supply_result = await collector.collect_full_market("supply")
    
    # 결과 요약
    logger.info("\n" + "="*70)
    logger.info("📊 전체 카탈로그 수집 완료")
    logger.info("="*70)
    
    logger.info(f"\n도매꾹(dome):")
    logger.info(f"   카테고리: {dome_result['categories']}개")
    logger.info(f"   총 상품: {dome_result['total']:,}개")
    logger.info(f"   신규: {dome_result['new']:,}개")
    logger.info(f"   업데이트: {dome_result['updated']:,}개")
    
    logger.info(f"\n도매매(supply):")
    logger.info(f"   카테고리: {supply_result['categories']}개")
    logger.info(f"   총 상품: {supply_result['total']:,}개")
    logger.info(f"   신규: {supply_result['new']:,}개")
    logger.info(f"   업데이트: {supply_result['updated']:,}개")
    
    total = dome_result['total'] + supply_result['total']
    logger.info(f"\n🎉 총 수집: {total:,}개")
    
    # 결과 저장
    results = {
        "dome": dome_result,
        "supply": supply_result,
        "total": total,
        "timestamp": datetime.now().isoformat()
    }
    
    with open('full_catalog_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info("\n💾 결과가 full_catalog_results.json에 저장되었습니다")


if __name__ == "__main__":
    asyncio.run(main())

