"""
마켓플레이스 판매 계정 설정 스크립트
API 키를 데이터베이스에 저장
"""

import asyncio
import os
import sys
from uuid import UUID
from dotenv import load_dotenv

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.services.database_service import DatabaseService
from loguru import logger

# 환경 변수 로드
load_dotenv()


async def setup_marketplace_accounts():
    """마켓플레이스 판매 계정 설정"""
    
    db_service = DatabaseService()
    
    try:
        logger.info("🚀 마켓플레이스 판매 계정 설정 시작\n")
        
        # 1. 마켓플레이스 조회
        marketplaces = await db_service.select_data("sales_marketplaces", {})
        
        if not marketplaces:
            logger.error("❌ 등록된 마켓플레이스가 없습니다.")
            logger.info("💡 먼저 setup_marketplaces.py를 실행하여 마켓플레이스를 등록하세요.")
            return
        
        logger.info("📋 등록된 마켓플레이스:")
        for mp in marketplaces:
            logger.info(f"  - {mp['name']} ({mp['code']})")
        
        print("\n" + "=" * 60)
        print("마켓플레이스 판매 계정 설정")
        print("=" * 60 + "\n")
        
        # 2. 마켓플레이스별 계정 설정
        
        # 쿠팡 계정 설정
        print("\n[1] 쿠팡 판매 계정")
        print("-" * 60)
        coupang_marketplace = next((m for m in marketplaces if m['code'] == 'coupang'), None)
        
        if coupang_marketplace:
            setup_coupang = input("쿠팡 계정을 설정하시겠습니까? (y/n): ").strip().lower()
            
            if setup_coupang == 'y':
                account_name = input("  계정 이름: ").strip() or "쿠팡 메인 계정"
                access_key = input("  Access Key: ").strip()
                secret_key = input("  Secret Key: ").strip()
                vendor_id = input("  Vendor ID: ").strip()
                
                if access_key and secret_key:
                    await db_service.insert_data(
                        "sales_accounts",
                        {
                            "marketplace_id": coupang_marketplace['id'],
                            "account_name": account_name,
                            "account_credentials": {
                                "access_key": access_key,
                                "secret_key": secret_key,
                                "vendor_id": vendor_id
                            },
                            "is_active": True
                        }
                    )
                    logger.info(f"✅ 쿠팡 계정 '{account_name}' 설정 완료")
                else:
                    logger.warning("⚠️ 쿠팡 계정 설정 건너뛰기")
        
        # 네이버 스마트스토어 계정 설정
        print("\n[2] 네이버 스마트스토어 판매 계정")
        print("-" * 60)
        naver_marketplace = next((m for m in marketplaces if m['code'] == 'naver_smartstore'), None)
        
        if naver_marketplace:
            setup_naver = input("네이버 스마트스토어 계정을 설정하시겠습니까? (y/n): ").strip().lower()
            
            if setup_naver == 'y':
                account_name = input("  계정 이름: ").strip() or "네이버 메인 계정"
                client_id = input("  Client ID: ").strip()
                client_secret = input("  Client Secret: ").strip()
                access_token = input("  Access Token (선택): ").strip()
                
                if client_id and client_secret:
                    await db_service.insert_data(
                        "sales_accounts",
                        {
                            "marketplace_id": naver_marketplace['id'],
                            "account_name": account_name,
                            "account_credentials": {
                                "client_id": client_id,
                                "client_secret": client_secret,
                                "access_token": access_token if access_token else None
                            },
                            "is_active": True
                        }
                    )
                    logger.info(f"✅ 네이버 스마트스토어 계정 '{account_name}' 설정 완료")
                else:
                    logger.warning("⚠️ 네이버 스마트스토어 계정 설정 건너뛰기")
        
        # 11번가 계정 설정
        print("\n[3] 11번가 판매 계정")
        print("-" * 60)
        elevenst_marketplace = next((m for m in marketplaces if m['code'] == '11st'), None)
        
        if elevenst_marketplace:
            setup_11st = input("11번가 계정을 설정하시겠습니까? (y/n): ").strip().lower()
            
            if setup_11st == 'y':
                account_name = input("  계정 이름: ").strip() or "11번가 메인 계정"
                api_key = input("  API Key: ").strip()
                
                if api_key:
                    await db_service.insert_data(
                        "sales_accounts",
                        {
                            "marketplace_id": elevenst_marketplace['id'],
                            "account_name": account_name,
                            "account_credentials": {
                                "api_key": api_key
                            },
                            "is_active": True
                        }
                    )
                    logger.info(f"✅ 11번가 계정 '{account_name}' 설정 완료")
                else:
                    logger.warning("⚠️ 11번가 계정 설정 건너뛰기")
        
        # 지마켓 계정 설정 (API 키 미발급)
        print("\n[4] 지마켓 판매 계정")
        print("-" * 60)
        print("⚠️ 지마켓 API 키가 아직 발급되지 않았습니다.")
        print("   API 키 발급 후 설정이 가능합니다.\n")
        
        # 옥션 계정 설정 (API 키 미발급)
        print("\n[5] 옥션 판매 계정")
        print("-" * 60)
        print("⚠️ 옥션 API 키가 아직 발급되지 않았습니다.")
        print("   API 키 발급 후 설정이 가능합니다.\n")
        
        # 3. 설정 완료 확인
        print("\n" + "=" * 60)
        logger.info("✅ 마켓플레이스 판매 계정 설정 완료")
        print("=" * 60 + "\n")
        
        # 저장된 계정 조회
        accounts = await db_service.select_data("sales_accounts", {"is_active": True})
        
        if accounts:
            logger.info(f"\n📋 등록된 판매 계정 ({len(accounts)}개):")
            for account in accounts:
                marketplace = next((m for m in marketplaces if m['id'] == account['marketplace_id']), None)
                if marketplace:
                    logger.info(f"  - {marketplace['name']}: {account['account_name']}")
        else:
            logger.warning("\n⚠️ 등록된 판매 계정이 없습니다.")
        
        logger.info("\n💡 다음 단계:")
        logger.info("   1. test_marketplace_seller_integration.py 실행하여 테스트")
        logger.info("   2. MarketplaceManager를 사용하여 상품 등록")
        
    except Exception as e:
        logger.error(f"❌ 계정 설정 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(setup_marketplace_accounts())

