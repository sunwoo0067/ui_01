#!/usr/bin/env python3
"""
OwnerClan 데이터 확인 스크립트
"""

import asyncio
from src.services.database_service import DatabaseService

async def check_ownerclan_data():
    """OwnerClan 데이터 확인"""
    db = DatabaseService()
    
    # OwnerClan 공급사 ID 찾기
    suppliers = await db.select_data('suppliers')
    ownerclan_id = None
    for supplier in suppliers:
        if supplier.get('code') == 'ownerclan':
            ownerclan_id = supplier.get('id')
            break
    
    if not ownerclan_id:
        print('❌ OwnerClan 공급사를 찾을 수 없습니다.')
        return
    
    print(f'🏢 OwnerClan 공급사 ID: {ownerclan_id}')
    
    # OwnerClan 상품 데이터만 조회
    ownerclan_products = await db.select_data('raw_product_data', {'supplier_id': ownerclan_id})
    print(f'📊 OwnerClan 상품 데이터: {len(ownerclan_products)}개')
    
    if ownerclan_products:
        # 최신 데이터 확인
        latest_product = ownerclan_products[0]
        print(f'📅 최신 수집 시간: {latest_product.get("created_at")}')
        print(f'🏷️ 최신 상품 ID: {latest_product.get("supplier_product_id")}')
        
        # 원본 데이터 확인
        raw_data = latest_product.get('raw_data', {})
        if raw_data:
            print(f'📦 최신 상품 정보:')
            print(f'  - 상품명: {raw_data.get("name", "N/A")}')
            print(f'  - 가격: {raw_data.get("price", "N/A")}')
            print(f'  - 재고: {raw_data.get("stock", "N/A")}')
            print(f'  - 모델: {raw_data.get("model", "N/A")}')
            print(f'  - 계정명: {raw_data.get("account_name", "N/A")}')
        
        # 상품 옵션 정보 확인
        if raw_data.get('options'):
            print(f'🔧 상품 옵션:')
            for i, option in enumerate(raw_data['options'][:3]):  # 처음 3개만 표시
                print(f'  - 옵션 {i+1}: {option}')
        
        # 가격 범위 확인
        prices = []
        for product in ownerclan_products:
            raw_data = product.get('raw_data', {})
            if raw_data.get('price'):
                prices.append(raw_data['price'])
        
        if prices:
            print(f'💰 가격 통계:')
            print(f'  - 최저가: {min(prices):,}원')
            print(f'  - 최고가: {max(prices):,}원')
            print(f'  - 평균가: {sum(prices)/len(prices):,.0f}원')

if __name__ == "__main__":
    asyncio.run(check_ownerclan_data())
