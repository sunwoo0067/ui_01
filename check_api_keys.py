"""API 키 확인 스크립트"""
import os
from dotenv import load_dotenv

load_dotenv()

print("\n마켓플레이스 API 키 확인:")
keys_to_check = {
    '쿠팡': ['COUPANG_ACCESS_KEY', 'COUPANG_SECRET_KEY', 'COUPANG_VENDOR_ID'],
    '네이버': ['NAVER_CLIENT_ID', 'NAVER_CLIENT_SECRET'],
    '11번가': ['ELEVENST_API_KEY'],
    '지마켓': ['GMARKET_API_KEY'],
    '옥션': ['AUCTION_API_KEY']
}

for marketplace, keys in keys_to_check.items():
    print(f"\n{marketplace}:")
    all_exist = True
    for key in keys:
        value = os.getenv(key)
        status = "✅ 존재" if value else "❌ 없음"
        print(f"  {key}: {status}")
        if not value:
            all_exist = False
    
    if all_exist:
        print(f"  → {marketplace} 계정 등록 가능")
    else:
        print(f"  → {marketplace} API 키 필요")

