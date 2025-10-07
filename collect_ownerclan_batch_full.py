#!/usr/bin/env python3
"""
오너클랜 배치 타입 전체 수집
allItems GraphQL 쿼리로 전체 카탈로그 수집
"""

import asyncio
import json
import hashlib
from datetime import datetime
from loguru import logger

from src.services.ownerclan_data_collector import OwnerClanDataCollector
from src.services.database_service import DatabaseService


async def collect_ownerclan_full_catalog():
    """오너클랜 전체 카탈로그 배치 수집"""
    db = DatabaseService()
    collector = OwnerClanDataCollector()
    
    supplier_id = "e458e4e2-cb03-4fc2-bff1-b05aaffde00f"
    account_name = "test_account"
    
    logger.info("="*70)
    logger.info("🏢 오너클랜 전체 카탈로그 배치 수집")
    logger.info("   방식: allItems GraphQL 쿼리 (전체 상품)")
    logger.info("="*70)
    
    start_time = datetime.now()
    
    # allItems GraphQL 쿼리 (전체 상품)
    query = """
    query {
        allItems(first: 1000) {
            pageInfo {
                hasNextPage
                endCursor
            }
            edges {
                node {
                    key
                    name
                    model
                    category {
                        key
                        name
                    }
                    price
                    status
                    boxQuantity
                    createdAt
                    updatedAt
                    options {
                        key
                        price
                        quantity
                        optionAttributes {
                            name
                            value
                        }
                    }
                    images(size: large)
                }
            }
        }
    }
    """
    
    logger.info("📦 allItems GraphQL 쿼리 실행 중...")
    logger.info("   (전체 상품 조회 - 시간이 다소 걸릴 수 있습니다)")
    
    result = await collector._make_graphql_request(query, account_name)
    
    if not result or "data" not in result:
        logger.error("❌ GraphQL 쿼리 실패")
        return {"status": "error"}
    
    # 페이지네이션 처리
    all_edges = []
    page_info = result["data"]["allItems"]["pageInfo"]
    all_edges.extend(result["data"]["allItems"]["edges"])
    
    # 추가 페이지 조회 (hasNextPage가 true이면)
    while page_info.get("hasNextPage"):
        logger.info(f"   다음 페이지 조회 중... (누적: {len(all_edges)}개)")
        
        after_cursor = page_info.get("endCursor")
        paginated_query = query.replace("allItems(first: 1000)", f'allItems(first: 1000, after: "{after_cursor}")')
        
        result = await collector._make_graphql_request(paginated_query, account_name)
        
        if not result or "data" not in result:
            logger.warning("페이지네이션 중단")
            break
        
        page_info = result["data"]["allItems"]["pageInfo"]
        all_edges.extend(result["data"]["allItems"]["edges"])
        
        await asyncio.sleep(0.5)
    
    collection_time = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"✅ GraphQL 응답 수신: {len(all_edges)}개 상품")
    logger.info(f"   응답 시간: {collection_time:.2f}초")
    
    # 상품 데이터 변환 및 중복 제거
    logger.info(f"\n🔄 상품 데이터 변환 중...")
    
    products_dict = {}  # supplier_key를 키로 사용하여 중복 제거
    inactive_count = 0
    duplicate_count = 0
    
    for edge in all_edges:
        node = edge["node"]
        
        # 비활성 상품 제외 (status가 "available"이 아닌 경우)
        # OwnerClan status: available, unavailable, discontinued 등
        status = node.get("status", "")
        if status != "available":
            inactive_count += 1
            continue
        
        supplier_key = node["key"]
        
        # 중복 검사 (같은 supplier_key가 이미 있으면 최신 것으로 덮어쓰기)
        if supplier_key in products_dict:
            duplicate_count += 1
        
        category = node.get("category", {})
        
        product = {
            "supplier_key": supplier_key,
            "name": node.get("name", ""),
            "model": node.get("model", ""),
            "category_name": category.get("name", "") if category else "",
            "category_key": category.get("key", "") if category else "",
            "box_quantity": node.get("boxQuantity", 0),
            "price": node.get("price", 0),
            "status": node.get("status", ""),
            "options": node.get("options", []),
            "images": node.get("images", []),
            "created_at": node.get("createdAt", ""),
            "updated_at": node.get("updatedAt", ""),
            "collected_at": datetime.now().isoformat(),
            "account_name": account_name
        }
        
        products_dict[supplier_key] = product
    
    # dict를 list로 변환
    all_products = list(products_dict.values())
    
    logger.info(f"✅ 변환 완료: {len(all_products)}개 (비활성: {inactive_count}개, 중복 제거: {duplicate_count}개)")
    
    # 데이터베이스 배치 저장 (최적화 - 중복 사전 필터링)
    logger.info(f"\n💾 데이터베이스 배치 저장 중...")
    
    # 1단계: 기존 상품 ID 목록 가져오기 (페이지네이션으로 전체 조회)
    logger.info(f"   기존 상품 ID 조회 중...")
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
            logger.info(f"   기존 상품 조회 중... {len(existing_ids)}개")
        
        logger.info(f"   기존 상품: {len(existing_ids)}개")
    except Exception as e:
        logger.warning(f"   기존 상품 조회 실패 (전체 upsert로 진행): {e}")
        existing_ids = set()
    
    # 2단계: 신규/업데이트 상품 분리
    logger.info(f"   신규/업데이트 상품 분류 중...")
    new_products = []
    update_products = []
    
    for product in all_products:
        try:
            supplier_product_id = product.get("supplier_key", "")
            
            # JSON 직렬화를 한 번만 수행
            raw_data_json = json.dumps(product, ensure_ascii=False)
            
            # 간단한 해시 계산
            data_hash = hashlib.md5(f"{supplier_product_id}{product.get('collected_at')}".encode()).hexdigest()
            
            raw_data = {
                "supplier_id": supplier_id,
                "raw_data": raw_data_json,
                "collection_method": "api",
                "collection_source": "batch_allItems_graphql",
                "supplier_product_id": supplier_product_id,
                "is_processed": False,
                "data_hash": data_hash,
                "metadata": json.dumps({
                    "collected_at": product.get("collected_at"),
                    "collection_type": "batch_full_catalog"
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
    
    logger.info(f"   신규 상품: {len(new_products)}개, 업데이트 상품: {len(update_products)}개")
    
    # 3단계: 신규 상품만 대량 삽입 (훨씬 빠름)
    saved = 0
    new = 0
    updated = 0
    
    if new_products:
        logger.info(f"\n   신규 상품 저장 중: {len(new_products)}개")
        batch_size = 5000
        total_batches = (len(new_products) + batch_size - 1) // batch_size
        
        for i in range(0, len(new_products), batch_size):
            chunk = new_products[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            try:
                saved_count = await db.bulk_insert("raw_product_data", chunk)
                new += saved_count
                saved += saved_count
                progress = (batch_num / total_batches) * 100
                logger.info(f"   신규 배치 {batch_num}/{total_batches}: {saved_count}개 (진행률: {progress:.1f}%)")
            except Exception as e:
                logger.error(f"   신규 배치 {batch_num} 실패: {e}")
                # 실패시 upsert로 재시도 (중복 처리)
                try:
                    saved_count = await db.bulk_upsert("raw_product_data", chunk)
                    new += saved_count
                    saved += saved_count
                except Exception as e2:
                    logger.error(f"   upsert도 실패: {e2}")
    
    # 4단계: 업데이트 상품 처리 (변경된 것만)
    if update_products:
        logger.info(f"\n   업데이트 상품 저장 중: {len(update_products)}개")
        batch_size = 5000
        total_batches = (len(update_products) + batch_size - 1) // batch_size
        
        for i in range(0, len(update_products), batch_size):
            chunk = update_products[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            try:
                saved_count = await db.bulk_upsert("raw_product_data", chunk)
                updated += saved_count
                saved += saved_count
                progress = (batch_num / total_batches) * 100
                logger.info(f"   업데이트 배치 {batch_num}/{total_batches}: {saved_count}개 (진행률: {progress:.1f}%)")
            except Exception as e:
                logger.error(f"   업데이트 배치 {batch_num} 실패: {e}")
    
    total_time = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"\n{'='*70}")
    logger.info("✅ 오너클랜 배치 수집 완료!")
    logger.info(f"{'='*70}")
    logger.info(f"   API 응답: {len(all_edges)}개")
    logger.info(f"   활성 상품: {len(all_products)}개")
    logger.info(f"   비활성 상품: {inactive_count}개")
    logger.info(f"   신규 저장: {new}개")
    logger.info(f"   업데이트: {updated}개")
    logger.info(f"   총 저장: {saved}개")
    logger.info(f"   총 시간: {total_time/60:.2f}분")
    logger.info(f"{'='*70}")
    
    result = {
        "status": "success",
        "total_from_api": len(all_edges),
        "active_products": len(all_products),
        "inactive_products": inactive_count,
        "new": new,
        "updated": updated,
        "total_saved": saved,
        "collection_time": collection_time,
        "total_time": total_time
    }
    
    with open('ownerclan_batch_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info("💾 결과가 ownerclan_batch_result.json에 저장되었습니다")
    
    return result


if __name__ == "__main__":
    asyncio.run(collect_ownerclan_full_catalog())

