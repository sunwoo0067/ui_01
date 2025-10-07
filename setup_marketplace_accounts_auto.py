"""
마켓플레이스 판매 계정 자동 설정 스크립트
환경 변수에서 API 키를 읽어 데이터베이스에 저장
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.services.database_service import DatabaseService
from loguru import logger

# 환경 변수 로드
load_dotenv()


async def setup_marketplace_accounts_auto():
    """환경 변수에서 API 키를 읽어 마켓플레이스 판매 계정 자동 설정"""
    
    db_service = DatabaseService()
    
    try:
        logger.info("🚀 마켓플레이스 판매 계정 자동 설정 시작\n")
        
        # 1. 마켓플레이스 조회
        marketplaces = await db_service.select_data("sales_marketplaces", {})
        
        if not marketplaces:
            logger.error("❌ 등록된 마켓플레이스가 없습니다.")
            logger.info("💡 먼저 setup_marketplaces.py를 실행하여 마켓플레이스를 등록하세요.")
            return False
        
        # 마켓플레이스 코드 매핑
        mp_map = {mp['code']: mp for mp in marketplaces}
        
        # 2. 기존 계정 확인
        existing_accounts = await db_service.select_data("sales_accounts", {})
        existing_mp_ids = {acc['marketplace_id'] for acc in existing_accounts}
        
        registered_count = 0
        skipped_count = 0
        
        # 3. 쿠팡 계정 설정
        if 'coupang' in mp_map:
            coupang = mp_map['coupang']
            
            if coupang['id'] in existing_mp_ids:
                logger.info("⏭️  쿠팡 계정 - 이미 등록됨")
                skipped_count += 1
            else:
                access_key = os.getenv('COUPANG_ACCESS_KEY')
                secret_key = os.getenv('COUPANG_SECRET_KEY')
                vendor_id = os.getenv('COUPANG_VENDOR_ID')
                account_name = os.getenv('COUPANG_ACCOUNT_NAME', '쿠팡 메인 계정')
                
                if access_key and secret_key:
                    await db_service.insert_data(
                        "sales_accounts",
                        {
                            "marketplace_id": coupang['id'],
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
                    registered_count += 1
                else:
                    logger.warning("⚠️ 쿠팡 API 키 없음 (COUPANG_ACCESS_KEY, COUPANG_SECRET_KEY)")
        
        # 4. 네이버 스마트스토어 계정 설정
        if 'naver_smartstore' in mp_map:
            naver = mp_map['naver_smartstore']
            
            if naver['id'] in existing_mp_ids:
                logger.info("⏭️  네이버 스마트스토어 계정 - 이미 등록됨")
                skipped_count += 1
            else:
                client_id = os.getenv('NAVER_CLIENT_ID')
                client_secret = os.getenv('NAVER_CLIENT_SECRET')
                access_token = os.getenv('NAVER_ACCESS_TOKEN')
                account_name = os.getenv('NAVER_ACCOUNT_NAME', '네이버 메인 계정')
                
                if client_id and client_secret:
                    await db_service.insert_data(
                        "sales_accounts",
                        {
                            "marketplace_id": naver['id'],
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
                    registered_count += 1
                else:
                    logger.warning("⚠️ 네이버 API 키 없음 (NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)")
        
        # 5. 11번가 계정 설정
        if '11st' in mp_map:
            elevenst = mp_map['11st']
            
            if elevenst['id'] in existing_mp_ids:
                logger.info("⏭️  11번가 계정 - 이미 등록됨")
                skipped_count += 1
            else:
                api_key = os.getenv('ELEVENST_API_KEY')
                account_name = os.getenv('ELEVENST_ACCOUNT_NAME', '11번가 메인 계정')
                
                if api_key:
                    await db_service.insert_data(
                        "sales_accounts",
                        {
                            "marketplace_id": elevenst['id'],
                            "account_name": account_name,
                            "account_credentials": {
                                "api_key": api_key
                            },
                            "is_active": True
                        }
                    )
                    logger.info(f"✅ 11번가 계정 '{account_name}' 설정 완료")
                    registered_count += 1
                else:
                    logger.warning("⚠️ 11번가 API 키 없음 (ELEVENST_API_KEY)")
        
        # 6. 지마켓 계정 설정 (API 키 미발급)
        if 'gmarket' in mp_map:
            gmarket = mp_map['gmarket']
            
            if gmarket['id'] not in existing_mp_ids:
                api_key = os.getenv('GMARKET_API_KEY')
                if api_key:
                    account_name = os.getenv('GMARKET_ACCOUNT_NAME', '지마켓 메인 계정')
                    await db_service.insert_data(
                        "sales_accounts",
                        {
                            "marketplace_id": gmarket['id'],
                            "account_name": account_name,
                            "account_credentials": {
                                "api_key": api_key
                            },
                            "is_active": True
                        }
                    )
                    logger.info(f"✅ 지마켓 계정 '{account_name}' 설정 완료")
                    registered_count += 1
                else:
                    logger.info("ℹ️  지마켓 API 키 미발급 (나중에 추가 가능)")
        
        # 7. 옥션 계정 설정 (API 키 미발급)
        if 'auction' in mp_map:
            auction = mp_map['auction']
            
            if auction['id'] not in existing_mp_ids:
                api_key = os.getenv('AUCTION_API_KEY')
                if api_key:
                    account_name = os.getenv('AUCTION_ACCOUNT_NAME', '옥션 메인 계정')
                    await db_service.insert_data(
                        "sales_accounts",
                        {
                            "marketplace_id": auction['id'],
                            "account_name": account_name,
                            "account_credentials": {
                                "api_key": api_key
                            },
                            "is_active": True
                        }
                    )
                    logger.info(f"✅ 옥션 계정 '{account_name}' 설정 완료")
                    registered_count += 1
                else:
                    logger.info("ℹ️  옥션 API 키 미발급 (나중에 추가 가능)")
        
        # 8. 결과 요약
        logger.info(f"\n📊 계정 등록 결과:")
        logger.info(f"   신규 등록: {registered_count}개")
        logger.info(f"   기존 존재: {skipped_count}개")
        
        # 9. 등록된 계정 목록
        all_accounts = await db_service.select_data("sales_accounts", {"is_active": True})
        
        if all_accounts:
            logger.info(f"\n📋 등록된 판매 계정 ({len(all_accounts)}개):")
            for account in all_accounts:
                marketplace = next((m for m in marketplaces if m['id'] == account['marketplace_id']), None)
                if marketplace:
                    status = "🟢" if account.get('is_active') else "🔴"
                    logger.info(f"   {status} {marketplace['name']}: {account['account_name']}")
        else:
            logger.warning("\n⚠️ 등록된 판매 계정이 없습니다.")
            logger.info("\n💡 API 키 설정 방법:")
            logger.info("   1. .env.marketplace.example 파일 참조")
            logger.info("   2. .env 파일에 API 키 추가")
            logger.info("   3. 이 스크립트 다시 실행")
            return False
        
        logger.info("\n💡 다음 단계:")
        logger.info("   1. test_marketplace_seller_integration.py 실행하여 테스트")
        logger.info("   2. MarketplaceManager를 사용하여 상품 등록")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 계정 설정 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(setup_marketplace_accounts_auto())
    exit(0 if success else 1)

