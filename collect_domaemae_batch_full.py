#!/usr/bin/env python3
"""
도매꾹 전체 카탈로그 배치 수집 (최적화)
"""

import asyncio
import json
import hashlib
from datetime import datetime
from loguru import logger

from src.services.domaemae_data_collector import DomaemaeDataCollector
from src.services.database_service import DatabaseService


async def collect_domaemae_full_catalog():
    """도매꾹 전체 카탈로그 배치 수집"""
    db = DatabaseService()
    collector = DomaemaeDataCollector(db)
    
    # 도매꾹 supplier_id (데이터베이스에서 확인 필요)
    suppliers = await db.select_data("suppliers", {"code": "domaemae"})
    if not suppliers:
        logger.error("도매꾹 공급사를 찾을 수 없습니다")
        return {"status": "error"}
    
    supplier_id = suppliers[0]["id"]
    account_name = "test_account"
    
    logger.info("="*70)
    logger.info("🏢 도매꾹 전체 카탈로그 배치 수집")
    logger.info("   방식: 도매꾹 + 도매매 모든 상품")
    logger.info("="*70)
    
    start_time = datetime.now()
    
    # 1. 도매꾹(dome) 상품 수집
    logger.info("\n📦 도매꾹(dome) 상품 수집 중...")
    dome_products = await collector.collect_products_batch(
        account_name=account_name,
        batch_size=500,
        max_pages=None,  # 전체 수집
        market="dome"
    )
    
    logger.info(f"✅ 도매꾹 수집 완료: {len(dome_products)}개")
    
    # 2. 도매매(supply) 상품 수집
    logger.info("\n📦 도매매(supply) 상품 수집 중...")
    supply_products = await collector.collect_products_batch(
        account_name=account_name,
        batch_size=500,
        max_pages=None,  # 전체 수집
        market="supply"
    )
    
    logger.info(f"✅ 도매매 수집 완료: {len(supply_products)}개")
    
    # 3. 합치기
    all_products = dome_products + supply_products
    collection_time = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"\n✅ 전체 수집 완료: {len(all_products)}개")
    logger.info(f"   도매꾹: {len(dome_products)}개")
    logger.info(f"   도매매: {len(supply_products)}개")
    logger.info(f"   수집 시간: {collection_time:.2f}초")
    
    # 데이터베이스 배치 저장 (최적화)
    logger.info(f"\n💾 데이터베이스 배치 저장 중...")
    
    # 1단계: 기존 상품 ID 조회
    logger.info("   기존 상품 ID 조회 중...")
    from src.services.supabase_client import supabase_client
    
    try:
        existing_ids = set()
        page_size = 10000
        offset = 0
        
        while True:
            existing_response = (
                supabase_client.get_table("raw_product_data")
                .select("supplier_product_id")
                .eq("supplier_id", supplier_id)
                .range(offset, offset + page_size - 1)
                .execute()
            )
            
            if not existing_response.data:
                break
            
            for item in existing_response.data:
                existing_ids.add(item['supplier_product_id'])
            
            if len(existing_response.data) < page_size:
                break
            
            offset += page_size
        
        logger.info(f"   기존 상품: {len(existing_ids)}개")
    except Exception as e:
        logger.warning(f"   기존 상품 조회 실패 (전체 upsert로 진행): {e}")
        existing_ids = set()
    
    # 2단계: 신규/업데이트 상품 분리
    logger.info("   신규/업데이트 상품 분류 중...")
    new_products = []
    update_products = []
    
    for product in all_products:
        try:
            supplier_product_id = str(product.get("item_id", ""))
            
            # JSON 직렬화를 한 번만 수행
            raw_data_json = json.dumps(product, ensure_ascii=False)
            data_hash = hashlib.md5(f"{supplier_product_id}{datetime.now().isoformat()}".encode()).hexdigest()
            
            raw_data = {
                "supplier_id": supplier_id,
                "raw_data": raw_data_json,
                "collection_method": "api",
                "collection_source": "http://api.domaemae.co.kr/openapi",
                "supplier_product_id": supplier_product_id,
                "is_processed": False,
                "data_hash": data_hash,
                "metadata": json.dumps({
                    "collected_at": product.get("collected_at", datetime.now().isoformat()),
                    "account_name": account_name,
                    "market": product.get("market", "")
                }, ensure_ascii=False)
            }
            
            # 신규/업데이트 분류
            if supplier_product_id in existing_ids:
                update_products.append(raw_data)
            else:
                new_products.append(raw_data)
                
        except Exception as e:
            logger.warning(f"   데이터 준비 실패: {e}")
            continue
    
    logger.info(f"   신규: {len(new_products)}개, 업데이트: {len(update_products)}개")
    
    # 3단계: 배치 저장
    saved = 0
    new = 0
    updated = 0
    batch_size = 5000
    
    # 신규 상품 bulk insert
    if new_products:
        logger.info(f"\n   신규 상품 저장 중: {len(new_products)}개")
        total_batches = (len(new_products) + batch_size - 1) // batch_size
        
        for i in range(0, len(new_products), batch_size):
            chunk = new_products[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            try:
                count = await db.bulk_insert("raw_product_data", chunk)
                new += count
                saved += count
                progress = (batch_num / total_batches) * 100
                logger.info(f"   신규 배치 {batch_num}/{total_batches}: {count}개 ({progress:.1f}%)")
            except Exception as e:
                logger.error(f"   신규 배치 {batch_num} 실패: {e}")
                # 실패시 upsert로 재시도
                try:
                    count = await db.bulk_upsert("raw_product_data", chunk)
                    new += count
                    saved += count
                except:
                    pass
    
    # 업데이트 상품 bulk upsert
    if update_products:
        logger.info(f"\n   업데이트 상품 저장 중: {len(update_products)}개")
        total_batches = (len(update_products) + batch_size - 1) // batch_size
        
        for i in range(0, len(update_products), batch_size):
            chunk = update_products[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            try:
                count = await db.bulk_upsert("raw_product_data", chunk)
                updated += count
                saved += count
                progress = (batch_num / total_batches) * 100
                logger.info(f"   업데이트 배치 {batch_num}/{total_batches}: {count}개 ({progress:.1f}%)")
            except Exception as e:
                logger.error(f"   업데이트 배치 {batch_num} 실패: {e}")
    
    total_time = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"\n{'='*70}")
    logger.info("✅ 도매꾹 배치 수집 완료!")
    logger.info(f"{'='*70}")
    logger.info(f"   수집 상품: {len(all_products)}개 (도매꾹: {len(dome_products)}, 도매매: {len(supply_products)})")
    logger.info(f"   신규 저장: {new}개")
    logger.info(f"   업데이트: {updated}개")
    logger.info(f"   총 저장: {saved}개")
    logger.info(f"   총 시간: {total_time/60:.2f}분")
    logger.info(f"{'='*70}")
    
    result = {
        "status": "success",
        "total_collected": len(all_products),
        "dome_products": len(dome_products),
        "supply_products": len(supply_products),
        "new": new,
        "updated": updated,
        "total_saved": saved,
        "collection_time": collection_time,
        "total_time": total_time
    }
    
    with open('domaemae_batch_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info("💾 결과가 domaemae_batch_result.json에 저장되었습니다")
    
    return result


if __name__ == "__main__":
    asyncio.run(collect_domaemae_full_catalog())

