#!/usr/bin/env python3
"""
수집된 데이터 확인 스크립트
"""

import asyncio
from src.services.database_service import DatabaseService

async def check_collected_data():
    """수집된 데이터 확인"""
    db = DatabaseService()
    
    # 수집된 상품 데이터 확인
    products = await db.select_data('raw_product_data')
    print(f'📊 수집된 상품 데이터: {len(products)}개')
    
    if products:
        print(f'📅 최신 수집 시간: {products[0].get("created_at", "N/A")}')
        print(f'🏷️ 첫 번째 상품 ID: {products[0].get("supplier_product_id", "N/A")}')
        
        # 공급사별 통계
        suppliers = {}
        for product in products:
            supplier_id = product.get('supplier_id')
            if supplier_id:
                suppliers[supplier_id] = suppliers.get(supplier_id, 0) + 1
        
        print(f'🏢 공급사별 상품 수:')
        for supplier_id, count in suppliers.items():
            print(f'  - {supplier_id}: {count}개')
        
        # 상품 샘플 데이터 확인
        if len(products) > 0:
            sample_product = products[0]
            print(f'\n📦 샘플 상품 데이터:')
            print(f'  - 상품 ID: {sample_product.get("supplier_product_id")}')
            print(f'  - 수집 방법: {sample_product.get("collection_method")}')
            print(f'  - 수집 소스: {sample_product.get("collection_source")}')
            print(f'  - 처리 상태: {sample_product.get("is_processed")}')
            
            # 원본 데이터 일부 확인
            raw_data = sample_product.get('raw_data', {})
            if raw_data:
                print(f'  - 상품명: {raw_data.get("name", "N/A")}')
                print(f'  - 가격: {raw_data.get("price", "N/A")}')
                print(f'  - 재고: {raw_data.get("stock", "N/A")}')

if __name__ == "__main__":
    asyncio.run(check_collected_data())
