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
    
    # 상품 데이터 변환
    logger.info(f"\n🔄 상품 데이터 변환 중...")
    
    all_products = []
    inactive_count = 0
    
    for edge in all_edges:
        node = edge["node"]
        
        # 비활성 상품 제외 (status가 "available"이 아닌 경우)
        # OwnerClan status: available, unavailable, discontinued 등
        status = node.get("status", "")
        if status != "available":
            inactive_count += 1
            continue
        
        category = node.get("category", {})
        
        product = {
            "supplier_key": node["key"],
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
        
        all_products.append(product)
    
    logger.info(f"✅ 변환 완료: {len(all_products)}개 (비활성 제외: {inactive_count}개)")
    
    # 데이터베이스 저장
    logger.info(f"\n💾 데이터베이스 저장 중...")
    
    saved = 0
    new = 0
    updated = 0
    
    for idx, product in enumerate(all_products, 1):
        try:
            supplier_product_id = product.get("supplier_key", "")
            
            data_str = json.dumps(product, sort_keys=True, ensure_ascii=False)
            data_hash = hashlib.md5(data_str.encode('utf-8')).hexdigest()
            
            raw_data = {
                "supplier_id": supplier_id,
                "raw_data": json.dumps(product, ensure_ascii=False),
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
            
            existing = await db.select_data(
                "raw_product_data",
                {"supplier_id": supplier_id, "supplier_product_id": supplier_product_id}
            )
            
            if existing:
                await db.update_data("raw_product_data", raw_data, {"id": existing[0]["id"]})
                updated += 1
            else:
                await db.insert_data("raw_product_data", raw_data)
                new += 1
            
            saved += 1
            
            if idx % 500 == 0:
                logger.info(f"   진행: {idx}/{len(all_products)}개 (신규: {new}, 업데이트: {updated})")
                
        except Exception as e:
            logger.warning(f"   저장 실패: {e}")
            continue
    
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

