#!/usr/bin/env python3
"""
오너클랜 1,000개 목표 완료 스크립트
"""

import asyncio
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger

from src.services.ownerclan_data_collector import OwnerClanDataCollector
from src.services.database_service import DatabaseService


async def complete_ownerclan():
    """오너클랜 1,000개 수집 완료"""
    db = DatabaseService()
    collector = OwnerClanDataCollector()
    
    supplier_id = "e458e4e2-cb03-4fc2-bff1-b05aaffde00f"
    account_name = "test_account"
    target = 1000
    
    logger.info("="*60)
    logger.info("🏢 오너클랜 1,000개 목표 완료 작업")
    logger.info("="*60)
    
    # 현재 데이터 확인
    existing = await db.select_data('raw_product_data', {'supplier_id': supplier_id})
    current_count = len(existing)
    
    logger.info(f"현재: {current_count}개")
    logger.info(f"목표: {target}개")
    logger.info(f"필요: {target - current_count}개")
    
    if current_count >= target:
        logger.info(f"✅ 이미 목표 달성! ({current_count}/{target})")
        return {"status": "complete", "count": current_count}
    
    needed = target - current_count
    
    # 추가 수집
    logger.info(f"\n📦 {needed}개 추가 수집 시작...")
    
    all_products = []
    attempt = 0
    max_attempts = 10
    
    while len(all_products) < needed and attempt < max_attempts:
        attempt += 1
        logger.info(f"시도 {attempt}: {len(all_products)}/{needed}개...")
        
        try:
            products = await collector.collect_products(
                account_name=account_name,
                limit=200
            )
            
            if not products:
                logger.warning("더 이상 수집할 상품이 없습니다")
                break
            
            all_products.extend(products)
            logger.info(f"   수집: +{len(products)}개 (누적: {len(all_products)}개)")
            
            # API Rate Limiting
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"수집 중 오류: {e}")
            break
    
    if not all_products:
        logger.warning("신규 수집된 상품이 없습니다")
        return {"status": "no_new_data", "count": current_count}
    
    # 데이터 저장
    logger.info(f"\n💾 {len(all_products)}개 데이터 저장 시작...")
    
    saved_count = 0
    for product in all_products:
        try:
            supplier_product_id = product.get("supplier_key", str(product.get("id", "")))
            
            data_str = json.dumps(product, sort_keys=True, ensure_ascii=False)
            data_hash = hashlib.md5(data_str.encode('utf-8')).hexdigest()
            
            raw_data = {
                "supplier_id": supplier_id,
                "raw_data": json.dumps(product, ensure_ascii=False),
                "collection_method": "api",
                "collection_source": "https://api.ownerclan.com/v1/graphql",
                "supplier_product_id": supplier_product_id,
                "is_processed": False,
                "data_hash": data_hash,
                "metadata": json.dumps({
                    "collected_at": product.get("collected_at", datetime.now().isoformat()),
                    "account_name": product.get("account_name", "")
                }, ensure_ascii=False)
            }
            
            # 중복 확인
            existing_item = await db.select_data(
                "raw_product_data",
                {"supplier_id": supplier_id, "supplier_product_id": supplier_product_id}
            )
            
            if existing_item:
                await db.update_data("raw_product_data", raw_data, {"id": existing_item[0]["id"]})
            else:
                await db.insert_data("raw_product_data", raw_data)
            
            saved_count += 1
            
            if saved_count % 100 == 0:
                logger.info(f"   진행: {saved_count}/{len(all_products)}개 저장...")
                
        except Exception as e:
            logger.warning(f"저장 실패: {e}")
            continue
    
    final_count = current_count + saved_count
    logger.info(f"\n✅ 오너클랜 수집 완료!")
    logger.info(f"   시작: {current_count}개")
    logger.info(f"   신규: {saved_count}개")
    logger.info(f"   최종: {final_count}개")
    logger.info(f"   목표 달성률: {(final_count/target*100):.1f}%")
    
    return {
        "status": "success",
        "initial": current_count,
        "collected": saved_count,
        "final": final_count,
        "target": target,
        "achievement_rate": final_count/target*100
    }


if __name__ == "__main__":
    result = asyncio.run(complete_ownerclan())
    
    # 결과 저장
    with open('ownerclan_collection_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

