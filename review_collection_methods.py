#!/usr/bin/env python3
"""
현재 수집 방식 검토
배치 타입 vs 개별 수집 비교
"""

import asyncio
from loguru import logger
from src.services.database_service import DatabaseService


async def review_collection_methods():
    """수집 방식 검토"""
    db = DatabaseService()
    
    logger.info("="*70)
    logger.info("📋 현재 수집 방식 검토")
    logger.info("="*70)
    
    suppliers_data = {
        "ownerclan": {
            "name": "오너클랜",
            "id": "e458e4e2-cb03-4fc2-bff1-b05aaffde00f",
            "current_method": "개별 페이징 (collect_products)",
            "batch_method": "allItems GraphQL 쿼리",
            "recommendation": "배치 타입 필요"
        },
        "zentrade": {
            "name": "젠트레이드",
            "id": "959ddf49-c25f-4ebb-a292-bc4e0f1cd28a",
            "current_method": "전체 XML 수집 (이미 배치 타입)",
            "batch_method": "현재 방식 유지",
            "recommendation": "이미 배치 타입 ✅"
        },
        "domaemae": {
            "name": "도매꾹",
            "id": "baa2ccd3-a328-4387-b307-6ae89aea331b",
            "current_method": "페이징 수집 (page 단위)",
            "batch_method": "전체 상품 수집 필요",
            "recommendation": "배치 타입 필요"
        },
        "domaemae_dome": {
            "name": "도매꾹(dome)",
            "id": "d9e6fa42-9bd4-438f-bf3b-10cf199eabd2",
            "current_method": "페이징 수집 (page 단위)",
            "batch_method": "전체 상품 수집 필요",
            "recommendation": "배치 타입 필요"
        },
        "domaemae_supply": {
            "name": "도매매(supply)",
            "id": "a9990a09-ae6f-474b-87b8-75840a110519",
            "current_method": "미수집",
            "batch_method": "전체 상품 수집",
            "recommendation": "배치 타입으로 시작"
        }
    }
    
    logger.info("\n🔍 공급사별 수집 방식 분석:\n")
    
    for code, info in suppliers_data.items():
        # 현재 데이터 확인
        raw_data = await db.select_data('raw_product_data', {'supplier_id': info['id']})
        
        logger.info(f"{'='*70}")
        logger.info(f"🏢 {info['name']} ({code})")
        logger.info(f"   현재 수집 데이터: {len(raw_data)}개")
        logger.info(f"   현재 방식: {info['current_method']}")
        logger.info(f"   배치 방식: {info['batch_method']}")
        logger.info(f"   권장사항: {info['recommendation']}")
    
    logger.info(f"\n{'='*70}")
    logger.info("\n💡 드롭쉬핑 대량등록을 위한 배치 타입 수집 필요 공급사:\n")
    logger.info("   1. ✅ 젠트레이드 - 이미 배치 타입 수집 완료 (3,510개)")
    logger.info("   2. ⚠️ 오너클랜 - 배치 타입으로 재수집 필요")
    logger.info("   3. ⚠️ 도매꾹(dome) - 배치 타입으로 재수집 필요")
    logger.info("   4. ⚠️ 도매매(supply) - 배치 타입으로 신규 수집 필요")
    
    logger.info(f"\n{'='*70}")
    logger.info("\n📊 배치 타입 수집의 장점:")
    logger.info("   ✅ 전체 카탈로그 동기화 - 모든 상품 누락 없이 수집")
    logger.info("   ✅ 대량등록 최적화 - 한번에 수천개 상품 처리")
    logger.info("   ✅ 네트워크 효율 - API 호출 횟수 최소화")
    logger.info("   ✅ 데이터 일관성 - 특정 시점의 전체 스냅샷")
    
    logger.info(f"\n{'='*70}")
    logger.info("\n🎯 다음 작업 계획:")
    logger.info("   1. 오너클랜 배치 타입 수집 (allItems GraphQL)")
    logger.info("   2. 도매꾹(dome) 배치 타입 수집 (전체 상품)")
    logger.info("   3. 도매매(supply) 계정 설정 및 배치 수집")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(review_collection_methods())

