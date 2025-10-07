"""
마켓플레이스 판매자 통합 테스트
상품 등록, 재고 관리, 주문 조회 기능 테스트
"""

import asyncio
import os
import sys
from uuid import UUID
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.services.marketplace.marketplace_manager import MarketplaceManager
from src.services.database_service import DatabaseService
from loguru import logger

# 환경 변수 로드
load_dotenv()


class MarketplaceSellerIntegrationTester:
    """마켓플레이스 판매자 통합 테스트"""
    
    def __init__(self):
        self.manager = MarketplaceManager()
        self.db_service = DatabaseService()
        
    async def test_authentication(self):
        """인증 테스트"""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("1. 마켓플레이스 인증 테스트")
            logger.info("=" * 60)
            
            # 활성 판매 계정 조회
            accounts = await self.db_service.select_data(
                "sales_accounts",
                {"is_active": True}
            )
            
            if not accounts:
                logger.error("❌ 활성 판매 계정이 없습니다.")
                logger.info("💡 setup_marketplace_accounts.py를 먼저 실행하세요.")
                return False
            
            logger.info(f"\n📋 활성 판매 계정: {len(accounts)}개")
            
            for account in accounts:
                # 마켓플레이스 정보 조회
                marketplace = await self.db_service.select_data(
                    "sales_marketplaces",
                    {"id": account['marketplace_id']}
                )
                
                if marketplace:
                    mp_name = marketplace[0].get('name')
                    mp_code = marketplace[0].get('code')
                    
                    logger.info(f"\n  {mp_name} ({account['account_name']})")
                    
                    # 서비스 가져오기
                    try:
                        service = await self.manager.get_marketplace_service(mp_code)
                        logger.info(f"    ✅ 서비스 초기화 성공")
                        
                        # 인증 정보 확인
                        credentials = account.get('account_credentials', {})
                        if credentials:
                            logger.info(f"    ✅ 인증 정보 확인 완료")
                        else:
                            logger.warning(f"    ⚠️ 인증 정보 없음")
                            
                    except NotImplementedError as e:
                        logger.warning(f"    ⚠️ {str(e)}")
                    except Exception as e:
                        logger.error(f"    ❌ 서비스 초기화 실패: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 인증 테스트 실패: {e}")
            return False
    
    async def test_product_registration(self):
        """상품 등록 테스트"""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("2. 상품 등록 테스트")
            logger.info("=" * 60)
            
            # 테스트용 상품 조회 (정규화된 상품 중 첫 번째)
            products = await self.db_service.select_data(
                "normalized_products",
                {"status": "active"}
            )
            
            if not products or len(products) == 0:
                logger.error("❌ 테스트할 상품이 없습니다.")
                logger.info("💡 먼저 상품 데이터를 수집하고 정규화하세요.")
                return False
            
            test_product = products[0]
            product_id = UUID(test_product['id'])
            
            logger.info(f"\n📦 테스트 상품: {test_product['title']}")
            logger.info(f"   가격: {test_product['price']}원")
            logger.info(f"   재고: {test_product['stock_quantity']}개")
            
            # 활성 판매 계정 조회
            accounts = await self.db_service.select_data(
                "sales_accounts",
                {"is_active": True}
            )
            
            if not accounts:
                logger.error("❌ 활성 판매 계정이 없습니다.")
                return False
            
            # 첫 번째 계정으로 테스트 (API 키가 발급된 계정만)
            test_results = []
            
            for account in accounts[:3]:  # 최대 3개 계정 테스트
                marketplace = await self.db_service.select_data(
                    "sales_marketplaces",
                    {"id": account['marketplace_id']}
                )
                
                if not marketplace:
                    continue
                
                mp_code = marketplace[0].get('code')
                mp_name = marketplace[0].get('name')
                
                # 지마켓/옥션은 API 키 미발급이므로 건너뛰기
                if mp_code in ['gmarket', 'auction']:
                    logger.info(f"\n  {mp_name}: API 키 미발급으로 건너뛰기")
                    continue
                
                logger.info(f"\n  {mp_name} 상품 등록 시도...")
                
                result = await self.manager.register_product(
                    product_id,
                    UUID(marketplace[0]['id']),
                    UUID(account['id']),
                    custom_title=f"[테스트] {test_product['title']}"
                )
                
                if result.get('success'):
                    logger.info(f"    ✅ 등록 성공: {result.get('marketplace_product_id')}")
                    test_results.append({
                        "marketplace": mp_name,
                        "success": True,
                        "product_id": result.get('marketplace_product_id')
                    })
                else:
                    logger.error(f"    ❌ 등록 실패: {result.get('error')}")
                    test_results.append({
                        "marketplace": mp_name,
                        "success": False,
                        "error": result.get('error')
                    })
            
            # 결과 요약
            success_count = sum(1 for r in test_results if r['success'])
            logger.info(f"\n📊 상품 등록 결과: 성공 {success_count}/{len(test_results)}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ 상품 등록 테스트 실패: {e}")
            return False
    
    async def test_inventory_sync(self):
        """재고 동기화 테스트"""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("3. 재고 동기화 테스트")
            logger.info("=" * 60)
            
            # 등록된 상품 조회
            listed_products = await self.db_service.select_data(
                "listed_products",
                {"status": "active"}
            )
            
            if not listed_products or len(listed_products) == 0:
                logger.error("❌ 등록된 상품이 없습니다.")
                logger.info("💡 먼저 상품을 등록하세요.")
                return False
            
            # 첫 번째 등록 상품으로 테스트
            test_product = listed_products[0]
            
            marketplace = await self.db_service.select_data(
                "sales_marketplaces",
                {"id": test_product['marketplace_id']}
            )
            
            mp_name = marketplace[0].get('name') if marketplace else "Unknown"
            
            logger.info(f"\n📦 테스트 상품: {test_product['title']}")
            logger.info(f"   마켓플레이스: {mp_name}")
            logger.info(f"   현재 재고: 100개로 업데이트 시도")
            
            result = await self.manager.sync_inventory(
                UUID(test_product['id']),
                100
            )
            
            if result.get('success'):
                logger.info(f"  ✅ 재고 동기화 성공")
                return True
            else:
                logger.error(f"  ❌ 재고 동기화 실패: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 재고 동기화 테스트 실패: {e}")
            return False
    
    async def test_order_sync(self):
        """주문 동기화 테스트"""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("4. 주문 동기화 테스트")
            logger.info("=" * 60)
            
            # 활성 판매 계정 조회
            accounts = await self.db_service.select_data(
                "sales_accounts",
                {"is_active": True}
            )
            
            if not accounts:
                logger.error("❌ 활성 판매 계정이 없습니다.")
                return False
            
            # 각 계정별 주문 동기화
            test_results = []
            
            for account in accounts[:3]:  # 최대 3개 계정 테스트
                marketplace = await self.db_service.select_data(
                    "sales_marketplaces",
                    {"id": account['marketplace_id']}
                )
                
                if not marketplace:
                    continue
                
                mp_code = marketplace[0].get('code')
                mp_name = marketplace[0].get('name')
                
                # 지마켓/옥션은 API 키 미발급이므로 건너뛰기
                if mp_code in ['gmarket', 'auction']:
                    logger.info(f"\n  {mp_name}: API 키 미발급으로 건너뛰기")
                    continue
                
                logger.info(f"\n  {mp_name} 주문 동기화 시도...")
                
                # 최근 7일 주문 조회
                created_after = datetime.now(timezone.utc) - timedelta(days=7)
                
                result = await self.manager.sync_orders(
                    UUID(marketplace[0]['id']),
                    UUID(account['id']),
                    created_after=created_after
                )
                
                if result.get('success'):
                    order_count = result.get('total_orders', 0)
                    logger.info(f"    ✅ 동기화 성공: {order_count}개 주문")
                    test_results.append({
                        "marketplace": mp_name,
                        "success": True,
                        "order_count": order_count
                    })
                else:
                    logger.error(f"    ❌ 동기화 실패: {result.get('error')}")
                    test_results.append({
                        "marketplace": mp_name,
                        "success": False
                    })
            
            # 결과 요약
            success_count = sum(1 for r in test_results if r['success'])
            total_orders = sum(r.get('order_count', 0) for r in test_results)
            
            logger.info(f"\n📊 주문 동기화 결과: 성공 {success_count}/{len(test_results)}, 총 {total_orders}개 주문")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 주문 동기화 테스트 실패: {e}")
            return False
    
    async def test_marketplace_summary(self):
        """마켓플레이스 요약 통계 테스트"""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("5. 마켓플레이스 요약 통계")
            logger.info("=" * 60)
            
            result = await self.manager.get_marketplace_summary()
            
            if result.get('success'):
                summary = result.get('summary', [])
                
                if summary:
                    logger.info(f"\n📊 마켓플레이스별 통계:")
                    for item in summary:
                        logger.info(f"\n  {item.get('marketplace_name')} - {item.get('account_name')}")
                        logger.info(f"    등록 상품: {item.get('total_listed_products', 0)}개")
                        logger.info(f"    활성 상품: {item.get('active_products', 0)}개")
                        logger.info(f"    총 주문: {item.get('total_orders', 0)}개")
                        logger.info(f"    배송 완료: {item.get('delivered_orders', 0)}개")
                        logger.info(f"    총 매출: {item.get('total_revenue', 0):,.0f}원")
                        logger.info(f"    평균 주문액: {item.get('avg_order_value', 0):,.0f}원")
                else:
                    logger.warning("  ⚠️ 통계 데이터가 없습니다.")
                
                return True
            else:
                logger.error(f"  ❌ 통계 조회 실패: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 마켓플레이스 요약 통계 테스트 실패: {e}")
            return False
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        logger.info("\n" + "=" * 80)
        logger.info("🚀 마켓플레이스 판매자 통합 테스트 시작")
        logger.info("=" * 80)
        
        results = {
            "인증": await self.test_authentication(),
            "상품등록": await self.test_product_registration(),
            "재고동기화": await self.test_inventory_sync(),
            "주문동기화": await self.test_order_sync(),
            "요약통계": await self.test_marketplace_summary()
        }
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 테스트 결과 요약")
        logger.info("=" * 80)
        
        for test_name, result in results.items():
            status = "✅ 통과" if result else "❌ 실패"
            logger.info(f"  {test_name}: {status}")
        
        success_count = sum(1 for r in results.values() if r)
        total_count = len(results)
        
        logger.info(f"\n총 {success_count}/{total_count} 테스트 통과")
        
        if success_count == total_count:
            logger.info("\n🎉 모든 테스트 통과!")
        else:
            logger.warning("\n⚠️ 일부 테스트 실패")
        
        logger.info("\n💡 다음 단계:")
        logger.info("   1. MarketplaceManager를 사용하여 실제 상품 등록")
        logger.info("   2. 재고 동기화 자동화 스케줄링")
        logger.info("   3. 주문 처리 자동화 구현")


async def main():
    """메인 함수"""
    tester = MarketplaceSellerIntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

