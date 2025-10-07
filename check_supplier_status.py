#!/usr/bin/env python3
"""
공급사 현황 확인 및 도매꾹/도매매 구분 확인
"""

import asyncio
from src.services.database_service import DatabaseService
from loguru import logger


async def check_supplier_status():
    """공급사 및 계정 현황 확인"""
    db = DatabaseService()
    
    logger.info("=" * 60)
    logger.info("📊 공급사 현황 확인")
    logger.info("=" * 60)
    
    # 1. 모든 공급사 조회
    suppliers = await db.select_data('suppliers', {})
    
    if not suppliers:
        logger.warning("⚠️ 등록된 공급사가 없습니다!")
        return
    
    logger.info(f"\n총 {len(suppliers)}개 공급사 등록됨:\n")
    
    for supplier in suppliers:
        logger.info(f"{'='*50}")
        logger.info(f"🏢 공급사: {supplier['name']} ({supplier['code']})")
        logger.info(f"   ID: {supplier['id']}")
        logger.info(f"   타입: {supplier['type']}")
        logger.info(f"   활성: {'✅' if supplier.get('is_active', False) else '❌'}")
        logger.info(f"   API 엔드포인트: {supplier.get('api_endpoint', 'N/A')}")
        
        # 공급사별 계정 수 확인
        accounts = await db.select_data('supplier_accounts', {'supplier_id': supplier['id']})
        logger.info(f"   계정 수: {len(accounts)}개")
        
        if accounts:
            for account in accounts:
                logger.info(f"      - {account['account_name']} ({'활성' if account.get('is_active') else '비활성'})")
        
        # 수집된 원본 데이터 수
        raw_data = await db.select_data('raw_product_data', {'supplier_id': supplier['id']})
        logger.info(f"   수집된 원본 데이터: {len(raw_data)}개")
        
        # 정규화된 상품 수
        normalized = await db.select_data('normalized_products', {'supplier_id': supplier['id']})
        logger.info(f"   정규화된 상품: {len(normalized)}개")
    
    logger.info(f"\n{'='*50}")
    
    # 2. 도매꾹/도매매 구분 확인
    logger.info("\n🔍 도매꾹/도매매 구분 확인:")
    
    domaemae_suppliers = [s for s in suppliers if 'domaemae' in s['code'].lower() or 'dome' in s['code'].lower()]
    
    if len(domaemae_suppliers) == 0:
        logger.warning("⚠️ 도매꾹/도매매 공급사가 등록되지 않았습니다!")
    elif len(domaemae_suppliers) == 1:
        logger.warning("⚠️ 도매꾹과 도매매가 하나의 공급사로 통합되어 있습니다!")
        logger.info(f"   현재: {domaemae_suppliers[0]['name']} ({domaemae_suppliers[0]['code']})")
        logger.info("\n💡 권장: 도매꾹(dome)과 도매매(supply)를 별도 공급사로 분리")
        logger.info("   - 도매꾹: 대량 구매 상품 (최소 구매 수량 있음)")
        logger.info("   - 도매매: 1개씩 구매 가능 (소매)")
    else:
        logger.info("✅ 도매꾹과 도매매가 별도 공급사로 구분되어 있습니다!")
        for supplier in domaemae_suppliers:
            logger.info(f"   - {supplier['name']} ({supplier['code']})")
    
    logger.info("=" * 60)
    
    return {
        "total_suppliers": len(suppliers),
        "suppliers": suppliers,
        "domaemae_count": len(domaemae_suppliers),
        "needs_separation": len(domaemae_suppliers) == 1
    }


if __name__ == "__main__":
    result = asyncio.run(check_supplier_status())

