"""쿠팡 계정 정보 확인 (간단 버전)"""
import asyncio
import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.services.database_service import DatabaseService


async def main():
    db = DatabaseService()
    
    print("\n" + "="*60)
    print("쿠팡 계정 정보 확인")
    print("="*60)
    
    # 마켓플레이스 조회
    mp = await db.select_data("sales_marketplaces", {"code": "coupang"})
    if mp:
        print(f"\n마켓플레이스: {mp[0]['name']}")
        print(f"코드: {mp[0]['code']}")
        print(f"ID: {mp[0]['id']}")
        
        # 계정 조회
        accounts = await db.select_data(
            "sales_accounts",
            {"marketplace_id": mp[0]['id']}
        )
        
        if accounts:
            acc = accounts[0]
            print(f"\n계정 이름: {acc['account_name']}")
            print(f"Store ID: {acc.get('store_id')}")
            print(f"활성: {acc['is_active']}")
            
            creds = acc.get('account_credentials', {})
            if creds:
                print(f"\nVendor ID: {creds.get('vendor_id')}")
                print(f"Access Key: {creds.get('access_key')[:20]}...")
                print(f"Secret Key: {'*' * 40}")
                print("\n✅ 계정 정보가 정상적으로 저장되어 있습니다!")
            else:
                print("\n❌ 인증 정보가 없습니다.")
        else:
            print("\n❌ 등록된 계정이 없습니다.")
    else:
        print("\n❌ 쿠팡 마켓플레이스가 없습니다.")
    
    # 정규화된 상품 수 확인
    products = await db.select_data("normalized_products", {"status": "active"})
    print(f"\n정규화된 상품 수: {len(products)}개")
    
    if products:
        print(f"\n첫 번째 상품 예시:")
        p = products[0]
        print(f"  제목: {p['title'][:50]}...")
        print(f"  가격: {p['price']:,.0f}원")
        print(f"  재고: {p['stock_quantity']}개")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())

