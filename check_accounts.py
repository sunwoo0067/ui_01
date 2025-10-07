"""판매 계정 확인 스크립트"""
import asyncio
from src.services.database_service import DatabaseService

async def check_accounts():
    db = DatabaseService()
    accounts = await db.select_data('sales_accounts', {})
    marketplaces = await db.select_data('sales_marketplaces', {})
    
    print(f"\n등록된 판매 계정: {len(accounts)}개")
    
    if accounts:
        for acc in accounts:
            mp = next((m for m in marketplaces if m['id'] == acc['marketplace_id']), None)
            mp_name = mp['name'] if mp else 'Unknown'
            status = "🟢" if acc.get('is_active') else "🔴"
            print(f"  {status} {mp_name}: {acc.get('account_name', 'Unknown')}")
    else:
        print("  없음 - API 키 등록이 필요합니다.")

if __name__ == "__main__":
    asyncio.run(check_accounts())

