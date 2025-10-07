#!/usr/bin/env python3
"""
젠트레이드 전체 상품 수집 스크립트
모든 상품을 한번에 수집
"""

import asyncio
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger

from src.services.zentrade_data_collector import ZentradeDataCollector
from src.services.database_service import DatabaseService


async def collect_zentrade_all():
    """젠트레이드 전체 상품 수집 (한번에)"""
    db = DatabaseService()
    collector = ZentradeDataCollector(db)
    
    supplier_id = "959ddf49-c25f-4ebb-a292-bc4e0f1cd28a"
    account_name = "test_account"
    
    logger.info("="*60)
    logger.info("🏢 젠트레이드 전체 상품 수집 시작")
    logger.info("   전략: 모든 상품을 한번에 수집")
    logger.info("="*60)
    
    # 현재 데이터 확인
    existing = await db.select_data('raw_product_data', {'supplier_id': supplier_id})
    current_count = len(existing)
    
    logger.info(f"현재 저장된 데이터: {current_count}개")
    
    # 전체 상품 수집 (품절 제외: runout=0)
    logger.info("\n📦 젠트레이드 전체 상품 수집 중...")
    logger.info("   옵션: runout=0 (품절 상품 제외)")
    
    start_time = datetime.now()
    
    products = await collector.collect_products(
        account_name=account_name,
        runout=0  # 품절 제외
    )
    
    collection_time = (datetime.now() - start_time).total_seconds()
    
    if not products:
        logger.error("❌ 상품 수집 실패")
        return {"status": "error", "message": "No products collected"}
    
    logger.info(f"✅ 수집 완료: {len(products)}개 상품")
    logger.info(f"   소요 시간: {collection_time:.2f}초")
    logger.info(f"   수집 속도: {len(products)/collection_time:.2f}개/초")
    
    # 데이터베이스에 저장
    logger.info(f"\n💾 {len(products)}개 데이터 저장 시작...")
    
    saved_count = 0
    new_count = 0
    updated_count = 0
    
    for idx, product in enumerate(products, 1):
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
                "collection_source": "https://www.zentrade.co.kr/shop/proc/product_api.php",
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
                # 업데이트
                await db.update_data("raw_product_data", raw_data, {"id": existing_item[0]["id"]})
                updated_count += 1
            else:
                # 신규 삽입
                await db.insert_data("raw_product_data", raw_data)
                new_count += 1
            
            saved_count += 1
            
            # 진행 상황 로그 (100개마다)
            if idx % 100 == 0:
                logger.info(f"   진행: {idx}/{len(products)}개 저장... (신규: {new_count}, 업데이트: {updated_count})")
                    
        except Exception as e:
            logger.warning(f"저장 실패: {e}")
            continue
    
    save_time = (datetime.now() - start_time).total_seconds() - collection_time
    
    final_count = current_count + new_count
    
    logger.info(f"\n{'='*60}")
    logger.info("✅ 젠트레이드 전체 수집 완료!")
    logger.info(f"{'='*60}")
    logger.info(f"📊 수집 결과:")
    logger.info(f"   - 수집된 상품: {len(products)}개")
    logger.info(f"   - 신규 저장: {new_count}개")
    logger.info(f"   - 업데이트: {updated_count}개")
    logger.info(f"   - 총 저장: {saved_count}개")
    logger.info(f"   - 최종 데이터: {final_count}개")
    logger.info(f"\n⏱️ 성능:")
    logger.info(f"   - 수집 시간: {collection_time:.2f}초")
    logger.info(f"   - 저장 시간: {save_time:.2f}초")
    logger.info(f"   - 총 시간: {(collection_time + save_time):.2f}초")
    logger.info(f"   - 수집 속도: {len(products)/collection_time:.2f}개/초")
    logger.info(f"   - 저장 속도: {saved_count/save_time:.2f}개/초" if save_time > 0 else "   - 저장 속도: N/A")
    logger.info(f"{'='*60}")
    
    result = {
        "status": "success",
        "collected": len(products),
        "new": new_count,
        "updated": updated_count,
        "total": final_count,
        "collection_time": collection_time,
        "save_time": save_time,
        "timestamp": datetime.now().isoformat()
    }
    
    return result


if __name__ == "__main__":
    result = asyncio.run(collect_zentrade_all())
    
    # 결과 저장
    with open('zentrade_collection_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info("💾 결과가 zentrade_collection_result.json에 저장되었습니다")

