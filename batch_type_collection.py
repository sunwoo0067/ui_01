#!/usr/bin/env python3
"""
배치 타입 대량 수집 스크립트
드롭쉬핑 대량등록을 위한 전체 카탈로그 수집
"""

import asyncio
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger

from src.services.ownerclan_data_collector import OwnerClanDataCollector
from src.services.domaemae_data_collector import DomaemaeDataCollector
from src.services.database_service import DatabaseService


class BatchTypeCollector:
    """배치 타입 수집기"""
    
    def __init__(self):
        self.db = DatabaseService()
        self.ownerclan_collector = OwnerClanDataCollector()
        self.domaemae_collector = DomaemaeDataCollector(self.db)
        
        self.supplier_ids = {
            "ownerclan": "e458e4e2-cb03-4fc2-bff1-b05aaffde00f",
            "domaemae_dome": "d9e6fa42-9bd4-438f-bf3b-10cf199eabd2",
            "domaemae_supply": "a9990a09-ae6f-474b-87b8-75840a110519"
        }
        
        self.results = {}
    
    async def _save_batch_products(self, products: List[Dict], supplier_code: str) -> Dict[str, int]:
        """배치 상품 데이터 저장"""
        try:
            supplier_id = self.supplier_ids[supplier_code]
            
            saved = 0
            new = 0
            updated = 0
            
            logger.info(f"💾 {supplier_code} 배치 저장 시작: {len(products)}개")
            
            for idx, product in enumerate(products, 1):
                try:
                    supplier_product_id = product.get("supplier_key", 
                                                     product.get("id", 
                                                                str(product.get("product_id", ""))))
                    
                    data_str = json.dumps(product, sort_keys=True, ensure_ascii=False)
                    data_hash = hashlib.md5(data_str.encode('utf-8')).hexdigest()
                    
                    raw_data = {
                        "supplier_id": supplier_id,
                        "raw_data": json.dumps(product, ensure_ascii=False),
                        "collection_method": "api",
                        "collection_source": "batch_collection",
                        "supplier_product_id": supplier_product_id,
                        "is_processed": False,
                        "data_hash": data_hash,
                        "metadata": json.dumps({
                            "collected_at": product.get("collected_at", datetime.now().isoformat()),
                            "collection_type": "batch"
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
                        logger.info(f"   진행: {idx}/{len(products)}개 (신규: {new}, 업데이트: {updated})")
                        
                except Exception as e:
                    logger.warning(f"저장 실패: {e}")
                    continue
            
            logger.info(f"✅ {supplier_code} 배치 저장 완료: {saved}개")
            
            return {"saved": saved, "new": new, "updated": updated}
            
        except Exception as e:
            logger.error(f"❌ 배치 저장 실패: {e}")
            return {"saved": 0, "new": 0, "updated": 0}
    
    async def collect_ownerclan_batch(self):
        """오너클랜 배치 타입 수집 (allItems GraphQL)"""
        logger.info("="*70)
        logger.info("🏢 오너클랜 배치 타입 수집 시작")
        logger.info("   방식: allItems GraphQL 쿼리 (전체 상품)")
        logger.info("="*70)
        
        try:
            account_name = "test_account"
            start_time = datetime.now()
            
            # GraphQL allItems 쿼리로 전체 상품 수집
            query = """
            query {
                allItems {
                    edges {
                        node {
                            key
                            name
                            model
                            categoryName
                            categoryKey
                            quantity
                            deleted
                            createdAt
                            updatedAt
                            options {
                                key
                                price
                                quantity
                                barcode
                                skuBarcode
                                optionAttributes {
                                    name
                                    value
                                }
                            }
                            itemImages {
                                url
                            }
                        }
                    }
                }
            }
            """
            
            logger.info("📦 allItems GraphQL 쿼리 실행 중...")
            
            result = await self.ownerclan_collector._make_graphql_request(query, account_name)
            
            if not result or "data" not in result:
                logger.error("❌ GraphQL 쿼리 실패")
                return {"status": "error", "message": "GraphQL query failed"}
            
            edges = result["data"]["allItems"]["edges"]
            
            logger.info(f"✅ GraphQL 응답 수신: {len(edges)}개 상품")
            
            # 상품 데이터 변환
            all_products = []
            for edge in edges:
                node = edge["node"]
                
                # 삭제된 상품 제외
                if node.get("deleted"):
                    continue
                
                product = {
                    "supplier_key": node["key"],
                    "name": node.get("name", ""),
                    "model": node.get("model", ""),
                    "category_name": node.get("categoryName", ""),
                    "category_key": node.get("categoryKey", ""),
                    "quantity": node.get("quantity", 0),
                    "options": node.get("options", []),
                    "images": [img.get("url") for img in node.get("itemImages", [])],
                    "created_at": node.get("createdAt", ""),
                    "updated_at": node.get("updatedAt", ""),
                    "collected_at": datetime.now().isoformat(),
                    "account_name": account_name
                }
                
                # 가격 정보 (첫 번째 옵션에서 추출)
                if product["options"]:
                    product["price"] = product["options"][0].get("price", 0)
                
                all_products.append(product)
            
            collection_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ 상품 변환 완료: {len(all_products)}개 (삭제된 상품 제외)")
            logger.info(f"   수집 시간: {collection_time:.2f}초")
            
            # 데이터베이스 저장
            save_result = await self._save_batch_products(all_products, "ownerclan")
            
            total_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "status": "success",
                "total_from_api": len(edges),
                "active_products": len(all_products),
                "new": save_result["new"],
                "updated": save_result["updated"],
                "collection_time": collection_time,
                "total_time": total_time
            }
            
            self.results["ownerclan"] = result
            
            logger.info(f"✅ 오너클랜 배치 타입 수집 완료!")
            logger.info(f"   API 응답: {len(edges)}개")
            logger.info(f"   활성 상품: {len(all_products)}개")
            logger.info(f"   신규: {save_result['new']}개")
            logger.info(f"   업데이트: {save_result['updated']}개")
            logger.info(f"   총 시간: {total_time:.2f}초")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 오너클랜 배치 수집 실패: {e}")
            self.results["ownerclan"] = {"status": "error", "error": str(e)}
            return {"status": "error", "error": str(e)}
    
    async def collect_domaemae_batch(self, market: str = "dome"):
        """도매꾹/도매매 배치 타입 수집 (전체 상품)"""
        market_name = "도매꾹" if market == "dome" else "도매매"
        supplier_code = f"domaemae_{market}"
        
        logger.info("="*70)
        logger.info(f"🏢 {market_name} 배치 타입 수집 시작")
        logger.info(f"   방식: 전체 페이지 순회 (대량 수집)")
        logger.info("="*70)
        
        try:
            account_name = "test_account"
            start_time = datetime.now()
            
            # 전체 상품 수집 (모든 페이지)
            all_products = []
            page = 1
            page_size = 200
            max_products = 50000  # 최대 5만개 (안전장치)
            
            logger.info(f"📦 {market_name} 전체 상품 배치 수집 시작...")
            
            while len(all_products) < max_products:
                logger.info(f"   페이지 {page} 수집 중... (누적: {len(all_products)}개)")
                
                products = await self.domaemae_collector.collect_products(
                    account_name=account_name,
                    market=market,
                    size=page_size,
                    page=page
                )
                
                if not products:
                    logger.info(f"   마지막 페이지 도달 (페이지 {page})")
                    break
                
                all_products.extend(products)
                page += 1
                
                # API Rate Limiting
                await asyncio.sleep(1)
                
                # 안전장치: 너무 많은 페이지는 방지
                if page > 250:  # 250페이지 = 50,000개
                    logger.warning("최대 페이지 도달")
                    break
            
            collection_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ {market_name} 배치 수집 완료: {len(all_products)}개")
            logger.info(f"   수집 시간: {collection_time:.2f}초")
            logger.info(f"   수집 속도: {len(all_products)/collection_time:.2f}개/초")
            
            if not all_products:
                return {"status": "no_data"}
            
            # 데이터베이스 저장
            save_result = await self._save_batch_products(all_products, supplier_code)
            
            total_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "status": "success",
                "collected": len(all_products),
                "new": save_result["new"],
                "updated": save_result["updated"],
                "pages": page - 1,
                "collection_time": collection_time,
                "total_time": total_time
            }
            
            self.results[supplier_code] = result
            
            logger.info(f"✅ {market_name} 배치 타입 수집 완료!")
            logger.info(f"   수집: {len(all_products)}개")
            logger.info(f"   페이지: {page-1}개")
            logger.info(f"   신규: {save_result['new']}개")
            logger.info(f"   업데이트: {save_result['updated']}개")
            logger.info(f"   총 시간: {total_time:.2f}초")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ {market_name} 배치 수집 실패: {e}")
            self.results[supplier_code] = {"status": "error", "error": str(e)}
            return {"status": "error", "error": str(e)}
    
    async def run_all_batch_collections(self):
        """모든 배치 타입 수집 실행"""
        logger.info("🚀 배치 타입 대량 수집 시작")
        logger.info("   목표: 드롭쉬핑 대량등록을 위한 전체 카탈로그 수집")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        # 1. 오너클랜 배치 수집
        await self.collect_ownerclan_batch()
        
        # 2. 도매꾹(dome) 배치 수집
        await self.collect_domaemae_batch(market="dome")
        
        # 3. 도매매(supply) 배치 수집
        await self.collect_domaemae_batch(market="supply")
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        # 결과 요약
        logger.info("\n" + "="*70)
        logger.info("📊 배치 타입 수집 결과 요약")
        logger.info("="*70)
        
        total_collected = 0
        total_new = 0
        total_updated = 0
        
        for supplier, result in self.results.items():
            logger.info(f"\n🏢 {supplier}:")
            if result.get("status") == "success":
                logger.info(f"   ✅ 수집: {result.get('collected', 0)}개")
                logger.info(f"   📝 신규: {result.get('new', 0)}개")
                logger.info(f"   🔄 업데이트: {result.get('updated', 0)}개")
                total_collected += result.get('collected', 0)
                total_new += result.get('new', 0)
                total_updated += result.get('updated', 0)
            else:
                logger.info(f"   ❌ 실패: {result.get('error', 'Unknown')}")
        
        logger.info(f"\n{'='*70}")
        logger.info(f"총 수집: {total_collected}개")
        logger.info(f"신규 저장: {total_new}개")
        logger.info(f"업데이트: {total_updated}개")
        logger.info(f"총 소요 시간: {total_time/60:.2f}분")
        logger.info("="*70)
        
        self.results["summary"] = {
            "total_collected": total_collected,
            "total_new": total_new,
            "total_updated": total_updated,
            "total_time": total_time,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.results


async def main():
    """메인 실행"""
    collector = BatchTypeCollector()
    results = await collector.run_all_batch_collections()
    
    # 결과 저장
    with open('batch_type_collection_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info("\n💾 결과가 batch_type_collection_results.json에 저장되었습니다")


if __name__ == "__main__":
    asyncio.run(main())

