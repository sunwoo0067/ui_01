#!/usr/bin/env python3
"""
도매꾹/도매매 카테고리 기반 배치 타입 수집
전체 카탈로그 수집을 위해 모든 카테고리 순환
"""

import asyncio
import aiohttp
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger

from src.services.database_service import DatabaseService


class CategoryBatchCollector:
    """카테고리 기반 배치 수집기"""
    
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
    
    async def _init_credentials(self):
        """인증 정보 초기화"""
        accounts = await self.db.select_data(
            'supplier_accounts',
            {'supplier_id': 'baa2ccd3-a328-4387-b307-6ae89aea331b'}
        )
        
        if accounts:
            credentials = json.loads(accounts[0]['account_credentials']) if isinstance(accounts[0]['account_credentials'], str) else accounts[0]['account_credentials']
            self.api_key = credentials.get('api_key')
            self.version = credentials.get('version', '4.1')
    
    async def get_categories(self) -> List[Dict]:
        """카테고리 목록 조회"""
        logger.info("📂 카테고리 목록 조회 중...")
        
        params = {
            "ver": self.version,
            "mode": "getCategoryList",
            "aid": self.api_key,
            "om": "json"
        }
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"카테고리 조회 실패: {response.status}")
                        return []
                    
                    data = await response.json()
                    
                    # 에러 확인
                    if "errors" in data:
                        logger.error(f"API 에러: {data['errors']}")
                        # getCategoryList가 지원되지 않으면 수동 카테고리 리스트 사용
                        logger.warning("getCategoryList API가 지원되지 않습니다. 수동 카테고리 리스트 사용")
                        return self._get_manual_categories()
                    
                    # 카테고리 파싱
                    categories = []
                    
                    def parse_category(item, depth=0):
                        """재귀적으로 카테고리 파싱"""
                        code = item.get("code", "")
                        name = item.get("name", "")
                        int_val = item.get("int")
                        
                        # 등록 가능한 카테고리만 (int 값이 있는 경우)
                        if int_val is not None:
                            categories.append({
                                "code": code,
                                "name": name,
                                "int": int_val,
                                "depth": depth
                            })
                        
                        # 하위 카테고리
                        child = item.get("child")
                        if child:
                            if isinstance(child, list):
                                for c in child:
                                    parse_category(c, depth + 1)
                            elif isinstance(child, dict):
                                parse_category(child, depth + 1)
                    
                    items = data.get("domeggook", {}).get("items")
                    if items:
                        if isinstance(items, list):
                            for item in items:
                                parse_category(item)
                        else:
                            parse_category(items)
                    
                    logger.info(f"✅ {len(categories)}개 카테고리 조회 완료")
                    return categories
                    
        except Exception as e:
            logger.error(f"카테고리 조회 실패: {e}")
            return self._get_manual_categories()
    
    def _get_manual_categories(self) -> List[Dict]:
        """수동 카테고리 리스트 (API 미지원시)"""
        logger.info("📝 수동 카테고리 리스트 사용")
        
        # 주요 중분류 카테고리 (대량등록용)
        return [
            {"code": "01_01_00_00_00", "name": "패션잡화/화장품 > 패션소품/액세서리", "int": None},
            {"code": "01_02_00_00_00", "name": "패션잡화/화장품 > 가방/핸드백", "int": None},
            {"code": "01_03_00_00_00", "name": "패션잡화/화장품 > 화장품/뷰티", "int": None},
            {"code": "02_01_00_00_00", "name": "디지털/가전 > 디지털기기", "int": None},
            {"code": "02_02_00_00_00", "name": "디지털/가전 > 가전제품", "int": None},
            {"code": "03_01_00_00_00", "name": "생활/건강 > 생활용품", "int": None},
            {"code": "03_02_00_00_00", "name": "생활/건강 > 건강용품", "int": None},
            {"code": "04_01_00_00_00", "name": "식품 > 식품", "int": None},
            {"code": "05_01_00_00_00", "name": "유아동/완구 > 유아동용품", "int": None},
            {"code": "06_01_00_00_00", "name": "스포츠/레저 > 스포츠용품", "int": None},
            {"code": "07_01_00_00_00", "name": "문구/도서 > 문구/사무용품", "int": None},
        ]
    
    async def collect_by_category(self, market: str, category_code: str, category_name: str) -> List[Dict]:
        """카테고리별 전체 상품 수집"""
        market_name = "도매꾹" if market == "dome" else "도매매"
        
        logger.info(f"📦 {market_name} - {category_name} ({category_code}) 수집 시작...")
        
        all_products = []
        page = 1
        max_pages = 500  # 안전장치
        
        while page <= max_pages:
            params = {
                "ver": self.version,
                "mode": "getItemList",
                "aid": self.api_key,
                "market": market,
                "om": "json",
                "sz": 200,
                "pg": page,
                "ca": category_code  # 카테고리 파라미터!
            }
            
            try:
                async with aiohttp.ClientSession(headers=self.headers) as session:
                    async with session.get(self.url, params=params) as response:
                        if response.status != 200:
                            logger.error(f"API 오류: {response.status}")
                            break
                        
                        data = await response.json()
                        
                        # 에러 체크
                        if "errors" in data:
                            logger.error(f"API 에러: {data['errors'].get('message')}")
                            break
                        
                        # 헤더 정보
                        header = data.get("domeggook", {}).get("header", {})
                        total_count = int(header.get("tcount", 0))
                        
                        if page == 1:
                            logger.info(f"   총 상품: {total_count:,}개")
                        
                        # 상품 목록
                        items = data.get("domeggook", {}).get("itemList", {}).get("item", [])
                        
                        if not items:
                            logger.info(f"   페이지 {page}에서 상품 없음 - 종료")
                            break
                        
                        # 단일 아이템인 경우 리스트로 변환
                        if isinstance(items, dict):
                            items = [items]
                        
                        # 상품 정보 추출
                        for item in items:
                            product = {
                                "supplier_key": item.get("it_id", ""),
                                "title": item.get("it_name", ""),
                                "price": int(item.get("it_price", 0)),
                                "category_code": item.get("ca_id", ""),
                                "category_name": item.get("ca_name", ""),
                                "seller_id": item.get("mb_id", ""),
                                "seller_nick": item.get("mb_nick", ""),
                                "image": item.get("it_img", ""),
                                "stock": int(item.get("it_stock_qty", 0)),
                                "min_order_qty": int(item.get("it_buy_min_qty", 1)),
                                "delivery_fee": int(item.get("it_sc_price", 0)),
                                "market": market,
                                "market_name": market_name,
                                "collected_at": datetime.now().isoformat(),
                                "collection_category": category_code
                            }
                            
                            all_products.append(product)
                        
                        logger.info(f"   페이지 {page}: +{len(items)}개 (누적: {len(all_products)}/{total_count})")
                        
                        # 마지막 페이지 체크
                        if len(all_products) >= total_count:
                            logger.info(f"   전체 수집 완료!")
                            break
                        
                        page += 1
                        await asyncio.sleep(0.5)  # Rate limiting
                        
            except Exception as e:
                logger.error(f"수집 중 오류: {e}")
                break
        
        logger.info(f"✅ {market_name} - {category_name} 수집 완료: {len(all_products)}개")
        return all_products
    
    async def collect_full_catalog(self, market: str = "dome"):
        """전체 카탈로그 배치 수집 (카테고리 순환)"""
        market_name = "도매꾹" if market == "dome" else "도매매"
        supplier_code = f"domaemae_{market}"
        
        logger.info("="*70)
        logger.info(f"🚀 {market_name} 전체 카탈로그 배치 수집")
        logger.info("   전략: 모든 카테고리 순환 수집")
        logger.info("="*70)
        
        await self._init_credentials()
        
        # 1단계: 카테고리 목록 조회
        categories = await self.get_categories()
        
        if not categories:
            logger.error("❌ 카테고리 목록이 없습니다")
            return {"status": "error", "message": "No categories"}
        
        logger.info(f"📂 총 {len(categories)}개 카테고리에서 수집 시작\n")
        
        # 2단계: 카테고리별 순환 수집
        all_products = []
        category_stats = []
        
        for idx, category in enumerate(categories, 1):
            logger.info(f"[{idx}/{len(categories)}] {category['name']}")
            
            products = await self.collect_by_category(
                market=market,
                category_code=category['code'],
                category_name=category['name']
            )
            
            all_products.extend(products)
            
            category_stats.append({
                "category": category['name'],
                "code": category['code'],
                "count": len(products)
            })
            
            logger.info(f"   카테고리 누적: {len(all_products)}개\n")
            
            # Rate limiting
            await asyncio.sleep(1)
        
        logger.info(f"\n✅ 전체 카테고리 수집 완료: {len(all_products)}개")
        
        # 3단계: 데이터베이스 저장
        logger.info(f"\n💾 {market_name} 배치 데이터 저장 시작...")
        
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
                    "collection_source": "category_batch",
                    "supplier_product_id": supplier_product_id,
                    "is_processed": False,
                    "data_hash": data_hash,
                    "metadata": json.dumps({
                        "collected_at": product.get("collected_at"),
                        "category_code": product.get("collection_category"),
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
                
                if idx % 500 == 0:
                    logger.info(f"   저장: {idx}/{len(all_products)}개 (신규: {new}, 업데이트: {updated})")
                    
            except Exception as e:
                logger.warning(f"저장 실패: {e}")
                continue
        
        logger.info(f"\n✅ {market_name} 배치 저장 완료!")
        logger.info(f"   총 수집: {len(all_products)}개")
        logger.info(f"   신규: {new}개")
        logger.info(f"   업데이트: {updated}개")
        logger.info(f"   저장: {saved}개")
        
        result = {
            "status": "success",
            "market": market_name,
            "categories_processed": len(categories),
            "total_products": len(all_products),
            "new": new,
            "updated": updated,
            "category_stats": category_stats
        }
        
        return result


async def main():
    """메인 실행"""
    collector = CategoryBatchCollector()
    
    logger.info("🎯 도매꾹/도매매 카테고리 기반 배치 수집")
    logger.info("   목표: 전체 카탈로그 수집 (모든 카테고리 순환)\n")
    
    results = {}
    
    # 1. 도매꾹(dome) 수집
    logger.info("\n" + "="*70)
    logger.info("1단계: 도매꾹(dome) 전체 카탈로그 수집")
    logger.info("="*70)
    
    dome_result = await collector.collect_full_catalog(market="dome")
    results["dome"] = dome_result
    
    # 2. 도매매(supply) 수집
    logger.info("\n" + "="*70)
    logger.info("2단계: 도매매(supply) 전체 카탈로그 수집")
    logger.info("="*70)
    
    supply_result = await collector.collect_full_catalog(market="supply")
    results["supply"] = supply_result
    
    # 최종 요약
    logger.info("\n" + "="*70)
    logger.info("📊 카테고리 기반 배치 수집 최종 결과")
    logger.info("="*70)
    
    for market, result in results.items():
        market_name = "도매꾹" if market == "dome" else "도매매"
        logger.info(f"\n{market_name}:")
        if result.get("status") == "success":
            logger.info(f"   ✅ 카테고리: {result['categories_processed']}개 처리")
            logger.info(f"   📦 총 상품: {result['total_products']:,}개")
            logger.info(f"   📝 신규: {result['new']:,}개")
            logger.info(f"   🔄 업데이트: {result['updated']:,}개")
        else:
            logger.info(f"   ❌ 실패: {result.get('message', 'Unknown')}")
    
    # 결과 저장
    with open('category_batch_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n💾 결과가 category_batch_results.json에 저장되었습니다")


if __name__ == "__main__":
    asyncio.run(main())

