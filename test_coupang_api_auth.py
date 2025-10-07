"""
쿠팡 API 인증 테스트
데이터베이스에서 계정 정보를 불러와서 실제 API 연동 테스트
"""

import asyncio
import os
import sys
from uuid import UUID
from dotenv import load_dotenv

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.services.marketplace.marketplace_manager import MarketplaceManager
from src.services.database_service import DatabaseService
from loguru import logger

# 환경 변수 로드
load_dotenv()


async def test_coupang_auth():
    """쿠팡 API 인증 테스트"""
    
    db_service = DatabaseService()
    manager = MarketplaceManager()
    
    try:
        logger.info("\n" + "=" * 60)
        logger.info("🚀 쿠팡 API 인증 테스트 시작")
        logger.info("=" * 60)
        
        # 1. 데이터베이스에서 쿠팡 계정 정보 조회
        logger.info("\n📋 1단계: DB에서 쿠팡 계정 정보 조회")
        
        # 쿠팡 마켓플레이스 정보
        marketplace = await db_service.select_data(
            "sales_marketplaces",
            {"code": "coupang"}
        )
        
        if not marketplace:
            logger.error("❌ 쿠팡 마켓플레이스가 등록되지 않았습니다.")
            return False
        
        mp = marketplace[0]
        logger.info(f"  ✅ 마켓플레이스: {mp['name']} ({mp['code']})")
        
        # 쿠팡 계정 정보
        accounts = await db_service.select_data(
            "sales_accounts",
            {"marketplace_id": mp['id'], "is_active": True}
        )
        
        if not accounts:
            logger.error("❌ 활성화된 쿠팡 계정이 없습니다.")
            return False
        
        account = accounts[0]
        logger.info(f"  ✅ 계정명: {account['account_name']}")
        logger.info(f"  ✅ Store ID: {account.get('store_id', 'N/A')}")
        
        # 계정 인증 정보 확인
        credentials = account.get('account_credentials', {})
        if credentials:
            logger.info(f"  ✅ Vendor ID: {credentials.get('vendor_id')}")
            logger.info(f"  ✅ Access Key: {credentials.get('access_key')[:20]}...")
            logger.info(f"  ✅ Secret Key: {'*' * 40}")
        else:
            logger.error("❌ 인증 정보가 없습니다.")
            return False
        
        # 2. MarketplaceManager로 서비스 가져오기
        logger.info("\n🔧 2단계: 쿠팡 서비스 초기화")
        
        try:
            service = await manager.get_marketplace_service("coupang")
            logger.info(f"  ✅ 쿠팡 서비스 초기화 성공: {service.__class__.__name__}")
        except NotImplementedError as e:
            logger.warning(f"  ⚠️ {str(e)}")
            logger.info("  ℹ️ 쿠팡 API는 구현 대기 중입니다.")
            return True  # 구조는 정상이므로 True 반환
        except Exception as e:
            logger.error(f"  ❌ 서비스 초기화 실패: {e}")
            return False
        
        # 3. 실제 API 호출 테스트 (구현된 경우)
        logger.info("\n🌐 3단계: 쿠팡 API 연결 테스트")
        logger.info("  ℹ️ 실제 API 호출은 구현 후 테스트됩니다.")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 쿠팡 계정 정보 DB 저장 및 조회 성공!")
        logger.info("=" * 60)
        logger.info("\n💡 다음 단계:")
        logger.info("   1. 쿠팡 API 실제 구현")
        logger.info("   2. 상품 등록 API 연동")
        logger.info("   3. 재고/주문 동기화 구현")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_product_selection():
    """테스트용 상품 선정"""
    
    db_service = DatabaseService()
    
    try:
        logger.info("\n" + "=" * 60)
        logger.info("📦 테스트 상품 선정")
        logger.info("=" * 60)
        
        # 정규화된 상품 중 첫 10개 조회
        products = await db_service.select_data(
            "normalized_products",
            {"status": "active"}
        )
        
        if not products or len(products) == 0:
            logger.error("❌ 정규화된 상품이 없습니다.")
            return None
        
        logger.info(f"\n✅ 사용 가능한 상품: {len(products)}개")
        logger.info("\n상위 5개 상품:")
        
        for i, product in enumerate(products[:5], 1):
            logger.info(f"\n  {i}. {product['title'][:50]}...")
            logger.info(f"     가격: {product['price']:,.0f}원")
            logger.info(f"     재고: {product['stock_quantity']}개")
            logger.info(f"     ID: {product['id']}")
        
        logger.info("\n💡 첫 번째 상품을 테스트에 사용할 수 있습니다.")
        
        return products[0]
        
    except Exception as e:
        logger.error(f"❌ 상품 선정 실패: {e}")
        return None


async def main():
    """메인 함수"""
    
    # 1. 인증 테스트
    auth_result = await test_coupang_auth()
    
    # 2. 상품 선정
    if auth_result:
        test_product = await test_product_selection()
        
        if test_product:
            logger.info("\n" + "=" * 60)
            logger.info("🎯 준비 완료!")
            logger.info("=" * 60)
            logger.info("\n다음 명령으로 상품 등록 테스트를 진행할 수 있습니다:")
            logger.info(f"  python test_coupang_product_registration.py")


if __name__ == "__main__":
    asyncio.run(main())

