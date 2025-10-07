#!/usr/bin/env python3
"""
대량 데이터 수집 마스터 스크립트
목표: 각 공급사별 1,000개 이상 상품 수집
"""

import asyncio
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger

from src.services.ownerclan_data_collector import OwnerClanDataCollector
from src.services.zentrade_data_collector import ZentradeDataCollector
from src.services.domaemae_data_collector import DomaemaeDataCollector
from src.services.database_service import DatabaseService


class BulkCollectionMaster:
    """대량 데이터 수집 마스터"""
    
    def __init__(self):
        self.db = DatabaseService()
        self.ownerclan_collector = OwnerClanDataCollector()
        self.zentrade_collector = ZentradeDataCollector(self.db)
        self.domaemae_collector = DomaemaeDataCollector(self.db)
        
        # 공급사 ID 매핑
        self.supplier_ids = {
            "ownerclan": "e458e4e2-cb03-4fc2-bff1-b05aaffde00f",
            "zentrade": "959ddf49-c25f-4ebb-a292-bc4e0f1cd28a",
            "domaemae": "baa2ccd3-a328-4387-b307-6ae89aea331b",
            "domaemae_dome": "d9e6fa42-9bd4-438f-bf3b-10cf199eabd2",
            "domaemae_supply": "a9990a09-ae6f-474b-87b8-75840a110519"
        }
        
        self.results = {
            "start_time": datetime.now(),
            "suppliers": {}
        }
    
    async def _save_raw_products(self, products: List[Dict[str, Any]], supplier_code: str, 
                                 collection_source: str = "api") -> int:
        """원본 상품 데이터를 raw_product_data 테이블에 저장"""
        try:
            if not products:
                return 0
            
            supplier_id = self.supplier_ids.get(supplier_code)
            if not supplier_id:
                logger.error(f"알 수 없는 공급사 코드: {supplier_code}")
                return 0
            
            saved_count = 0
            for product in products:
                try:
                    # 상품 ID 추출
                    supplier_product_id = product.get("supplier_key", 
                                                     product.get("id", 
                                                                str(product.get("product_id", ""))))
                    
                    # 데이터 해시 계산
                    data_str = json.dumps(product, sort_keys=True, ensure_ascii=False)
                    data_hash = hashlib.md5(data_str.encode('utf-8')).hexdigest()
                    
                    # 원본 데이터 생성
                    raw_data = {
                        "supplier_id": supplier_id,
                        "raw_data": json.dumps(product, ensure_ascii=False),
                        "collection_method": "api",
                        "collection_source": collection_source,
                        "supplier_product_id": supplier_product_id,
                        "is_processed": False,
                        "data_hash": data_hash,
                        "metadata": json.dumps({
                            "collected_at": product.get("collected_at", datetime.now().isoformat()),
                            "account_name": product.get("account_name", "")
                        }, ensure_ascii=False)
                    }
                    
                    # 기존 데이터 확인
                    existing = await self.db.select_data(
                        "raw_product_data",
                        {"supplier_id": supplier_id, "supplier_product_id": supplier_product_id}
                    )
                    
                    if existing:
                        # 업데이트
                        await self.db.update_data(
                            "raw_product_data",
                            raw_data,
                            {"id": existing[0]["id"]}
                        )
                    else:
                        # 신규 삽입
                        await self.db.insert_data("raw_product_data", raw_data)
                    
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"상품 저장 실패: {e}")
                    continue
            
            logger.info(f"✅ {supplier_code} 데이터 저장 완료: {saved_count}개")
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ 데이터 저장 실패: {e}")
            return 0
    
    async def collect_ownerclan(self, target: int = 1000):
        """오너클랜 데이터 수집"""
        logger.info("="*60)
        logger.info("🏢 오너클랜 대량 데이터 수집 시작")
        logger.info(f"   목표: {target}개 상품")
        logger.info("="*60)
        
        try:
            account_name = "test_account"
            
            # 현재 수집된 데이터 확인
            existing_data = await self.db.select_data(
                'raw_product_data',
                {'supplier_id': 'e458e4e2-cb03-4fc2-bff1-b05aaffde00f'}
            )
            current_count = len(existing_data)
            logger.info(f"현재 수집된 데이터: {current_count}개")
            
            if current_count >= target:
                logger.info(f"✅ 이미 목표 달성! ({current_count}/{target})")
                return {"status": "already_complete", "count": current_count}
            
            # 추가로 수집할 개수
            needed = target - current_count
            logger.info(f"추가 수집 필요: {needed}개")
            
            # 상품 수집 (페이지네이션 방식)
            logger.info(f"📦 {needed}개 상품 수집 시작...")
            
            all_products = []
            page_size = 200  # 한 번에 200개씩
            
            while len(all_products) < needed:
                logger.info(f"   진행: {len(all_products)}/{needed}개...")
                
                # 상품 수집
                products = await self.ownerclan_collector.collect_products(
                    account_name=account_name,
                    limit=min(page_size, needed - len(all_products))
                )
                
                if not products:
                    logger.warning(f"더 이상 수집할 상품이 없습니다 (현재: {len(all_products)}개)")
                    break
                
                all_products.extend(products)
                
                # API Rate Limiting
                await asyncio.sleep(1)
            
            if not all_products:
                logger.warning("수집된 상품이 없습니다")
                return {"status": "no_data", "count": 0}
            
            logger.info(f"   수집 완료: {len(all_products)}개")
            
            # 데이터베이스에 저장
            saved = await self._save_raw_products(
                all_products, 
                "ownerclan",
                "https://api.ownerclan.com/v1/graphql"
            )
            collected_count = saved
            
            logger.info(f"   저장 완료: {saved}개")
            
            total_count = current_count + collected_count
            logger.info(f"✅ 오너클랜 수집 완료: {total_count}개 (신규 {collected_count}개)")
            
            self.results["suppliers"]["ownerclan"] = {
                "target": target,
                "collected": collected_count,
                "total": total_count,
                "status": "success"
            }
            
            return {"status": "success", "collected": collected_count, "total": total_count}
            
        except Exception as e:
            logger.error(f"❌ 오너클랜 수집 실패: {e}")
            self.results["suppliers"]["ownerclan"] = {"status": "error", "error": str(e)}
            return {"status": "error", "error": str(e)}
    
    async def collect_zentrade(self, target: int = 1000):
        """젠트레이드 데이터 수집"""
        logger.info("="*60)
        logger.info("🏢 젠트레이드 대량 데이터 수집 시작")
        logger.info(f"   목표: {target}개 상품")
        logger.info("="*60)
        
        try:
            account_name = "test_account"
            
            # 현재 수집된 데이터 확인
            existing_data = await self.db.select_data(
                'raw_product_data',
                {'supplier_id': '959ddf49-c25f-4ebb-a292-bc4e0f1cd28a'}
            )
            current_count = len(existing_data)
            logger.info(f"현재 수집된 데이터: {current_count}개")
            
            if current_count >= target:
                logger.info(f"✅ 이미 목표 달성! ({current_count}/{target})")
                return {"status": "already_complete", "count": current_count}
            
            # 추가로 수집할 개수
            needed = target - current_count
            logger.info(f"추가 수집 필요: {needed}개")
            
            # 상품 수집 (단순 수집 - 젠트레이드는 전체 목록 반환)
            logger.info(f"📦 젠트레이드 상품 수집 시작...")
            
            # 젠트레이드는 파라미터 없이 전체 목록을 가져옴
            products = await self.zentrade_collector.collect_products(
                account_name=account_name
            )
            
            if not products:
                logger.warning("수집된 상품이 없습니다")
                return {"status": "no_data", "count": 0}
            
            logger.info(f"   수집 완료: {len(products)}개")
            
            # 필요한 만큼만 사용
            products_to_save = products[:needed] if len(products) > needed else products
            
            # 데이터베이스에 저장
            saved = await self._save_raw_products(
                products_to_save,
                "zentrade",
                "https://www.zentrade.co.kr/shop/proc/product_api.php"
            )
            
            total_count = current_count + saved
            logger.info(f"✅ 젠트레이드 수집 완료: {total_count}개 (신규 {saved}개)")
            
            self.results["suppliers"]["zentrade"] = {
                "target": target,
                "collected": saved,
                "total": total_count,
                "status": "success"
            }
            
            return {"status": "success", "collected": saved, "total": total_count}
            
        except Exception as e:
            logger.error(f"❌ 젠트레이드 수집 실패: {e}")
            self.results["suppliers"]["zentrade"] = {"status": "error", "error": str(e)}
            return {"status": "error", "error": str(e)}
    
    async def collect_domaemae_dome(self, target: int = 1000):
        """도매꾹(dome) 데이터 수집"""
        logger.info("="*60)
        logger.info("🏢 도매꾹(dome) 대량 데이터 수집 시작")
        logger.info(f"   목표: {target}개 상품")
        logger.info("="*60)
        
        try:
            account_name = "test_account"
            market = "dome"  # 도매꾹
            
            # 현재 수집된 데이터 확인 (domaemae_dome)
            existing_data = await self.db.select_data(
                'raw_product_data',
                {'supplier_id': 'd9e6fa42-9bd4-438f-bf3b-10cf199eabd2'}
            )
            current_count = len(existing_data)
            logger.info(f"현재 수집된 데이터: {current_count}개")
            
            if current_count >= target:
                logger.info(f"✅ 이미 목표 달성! ({current_count}/{target})")
                return {"status": "already_complete", "count": current_count}
            
            # 추가로 수집할 개수
            needed = target - current_count
            logger.info(f"추가 수집 필요: {needed}개")
            
            # 상품 수집 (여러 페이지)
            page = 1
            collected_count = 0
            page_size = 200
            
            while collected_count < needed:
                logger.info(f"📦 페이지 {page} 수집 중...")
                
                products = await self.domaemae_collector.collect_products(
                    account_name=account_name,
                    market=market,
                    size=page_size,
                    page=page
                )
                
                if not products:
                    logger.warning("더 이상 수집할 상품이 없습니다")
                    break
                
                logger.info(f"   수집 완료: {len(products)}개")
                
                # 데이터베이스에 저장 (도매꾹 dome 전용)
                saved = await self._save_raw_products(
                    products,
                    "domaemae_dome",
                    "https://domeggook.com/ssl/api/"
                )
                collected_count += saved
                
                logger.info(f"   저장: {saved}개 (누적: {current_count + collected_count}/{target})")
                
                page += 1
                
                # API Rate Limiting
                await asyncio.sleep(2)
                
                if current_count + collected_count >= target:
                    break
            
            total_count = current_count + collected_count
            logger.info(f"✅ 도매꾹(dome) 수집 완료: {total_count}개 (신규 {collected_count}개)")
            
            self.results["suppliers"]["domaemae_dome"] = {
                "target": target,
                "collected": collected_count,
                "total": total_count,
                "status": "success"
            }
            
            return {"status": "success", "collected": collected_count, "total": total_count}
            
        except Exception as e:
            logger.error(f"❌ 도매꾹(dome) 수집 실패: {e}")
            self.results["suppliers"]["domaemae_dome"] = {"status": "error", "error": str(e)}
            return {"status": "error", "error": str(e)}
    
    async def run_all(self):
        """모든 공급사 대량 수집 실행"""
        logger.info("🚀 대량 데이터 수집 시작")
        logger.info(f"시작 시간: {self.results['start_time']}")
        logger.info("="*60)
        
        # 1. 오너클랜
        await self.collect_ownerclan(target=1000)
        
        # 2. 젠트레이드
        await self.collect_zentrade(target=1000)
        
        # 3. 도매꾹 (dome)
        await self.collect_domaemae_dome(target=1000)
        
        # 결과 요약
        self.results["end_time"] = datetime.now()
        self.results["duration"] = (self.results["end_time"] - self.results["start_time"]).total_seconds()
        
        logger.info("="*60)
        logger.info("📊 대량 수집 결과 요약")
        logger.info("="*60)
        
        total_collected = 0
        for supplier, result in self.results["suppliers"].items():
            logger.info(f"🏢 {supplier}:")
            if result.get("status") == "success":
                logger.info(f"   ✅ 신규 수집: {result.get('collected', 0)}개")
                logger.info(f"   📦 전체: {result.get('total', 0)}개")
                total_collected += result.get('collected', 0)
            else:
                logger.info(f"   ❌ 실패: {result.get('error', 'Unknown')}")
        
        logger.info(f"\n총 신규 수집: {total_collected}개")
        logger.info(f"소요 시간: {self.results['duration']:.2f}초")
        logger.info("="*60)
        
        return self.results


async def main():
    """메인 실행 함수"""
    master = BulkCollectionMaster()
    results = await master.run_all()
    
    # 결과를 JSON으로 저장
    import json
    with open('bulk_collection_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info("✅ 결과가 bulk_collection_results.json에 저장되었습니다")


if __name__ == "__main__":
    asyncio.run(main())

