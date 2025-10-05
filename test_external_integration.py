"""
외부 시스템 연동 테스트
웹훅과 API 연동 시스템의 통합 테스트
"""

import asyncio
import json
from datetime import datetime
from loguru import logger

from src.services.database_service import DatabaseService
from src.services.external_integration_service import ExternalIntegrationService
from src.services.webhook_service import WebhookEventType
from src.services.api_integration_service import APIType, AuthType


class ExternalIntegrationTester:
    """외부 시스템 연동 테스터"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.test_results = {}
        
    async def run_all_tests(self):
        """모든 테스트 실행"""
        logger.info("🧪 외부 시스템 연동 테스트 시작")
        
        tests = [
            ("웹훅 시스템 테스트", self.test_webhook_system),
            ("API 연동 시스템 테스트", self.test_api_integration),
            ("마켓플레이스 연동 테스트", self.test_marketplace_integration),
            ("공급사 연동 테스트", self.test_supplier_integration),
            ("통합 연동 테스트", self.test_integrated_system),
            ("연결 테스트", self.test_connections),
            ("대시보드 데이터 테스트", self.test_dashboard_data)
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"🔍 {test_name} 실행 중...")
                result = await test_func()
                self.test_results[test_name] = {
                    "status": "success",
                    "result": result
                }
                logger.info(f"✅ {test_name} 완료")
            except Exception as e:
                logger.error(f"❌ {test_name} 실패: {e}")
                self.test_results[test_name] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        # 테스트 결과 요약
        self.print_test_summary()
        
    async def test_webhook_system(self):
        """웹훅 시스템 테스트"""
        from src.services.webhook_service import WebhookService, WebhookEndpoint
        
        async with WebhookService(self.db_service) as webhook_service:
            # 테스트 엔드포인트 생성
            test_endpoint = WebhookEndpoint(
                id="test_webhook_1",
                url="https://webhook.site/test-webhook-url",
                secret="test_secret_key_123456789",
                events=[WebhookEventType.PRODUCT_CREATED, WebhookEventType.PRICE_CHANGED],
                max_retries=2,
                timeout=10
            )
            
            # 엔드포인트 생성
            create_result = await webhook_service.create_endpoint(test_endpoint)
            
            # 테스트 웹훅 전송
            test_data = {
                "product_id": "test_product_123",
                "name": "테스트 상품",
                "price": 10000,
                "category": "electronics"
            }
            
            webhook_result = await webhook_service.trigger_webhook(
                WebhookEventType.PRODUCT_CREATED,
                test_data
            )
            
            # 통계 조회
            stats = await webhook_service.get_endpoint_stats()
            
            return {
                "endpoint_created": create_result,
                "webhook_sent": webhook_result,
                "stats": stats
            }
    
    async def test_api_integration(self):
        """API 연동 시스템 테스트"""
        from src.services.api_integration_service import APIIntegrationService, APIConfig, APIRequest
        
        api_service = APIIntegrationService(self.db_service)
        await api_service.load_configs()
        
        # 테스트 API 설정 생성
        test_config = APIConfig(
            id="test_api_1",
            name="테스트 API",
            base_url="https://jsonplaceholder.typicode.com",
            api_type=APIType.REST,
            auth_type=AuthType.NONE,
            auth_config={},
            headers={"User-Agent": "DropshippingBot/1.0"},
            timeout=30,
            retry_count=3
        )
        
        # 설정 생성
        create_result = await api_service.create_config(test_config)
        
        # 연결 테스트
        test_result = await api_service.test_connection("test_api_1")
        
        # API 호출 테스트
        request = APIRequest(
            method="GET",
            endpoint="/posts/1"
        )
        
        response = await api_service.make_api_call("test_api_1", request)
        
        # 통계 조회
        stats = await api_service.get_integration_stats()
        
        return {
            "config_created": create_result,
            "connection_test": test_result,
            "api_call": {
                "status_code": response.status_code,
                "success": response.success,
                "response_time": response.response_time
            },
            "stats": stats
        }
    
    async def test_marketplace_integration(self):
        """마켓플레이스 연동 테스트"""
        async with ExternalIntegrationService(self.db_service) as integration_service:
            # 마켓플레이스 설정
            marketplace_config = {
                "id": "test_marketplace_1",
                "name": "테스트 마켓플레이스",
                "base_url": "https://api.testmarketplace.com",
                "api_type": "rest",
                "auth_type": "api_key",
                "auth_config": {
                    "api_key": "test_api_key_123",
                    "key_name": "X-API-Key"
                },
                "webhook_url": "https://webhook.site/marketplace-webhook",
                "webhook_secret": "test_marketplace_webhook_secret_123"
            }
            
            # 마켓플레이스 연동 설정
            setup_result = await integration_service.setup_marketplace_integration(marketplace_config)
            
            # 테스트 상품 데이터
            test_products = [
                {
                    "id": "product_1",
                    "name": "테스트 상품 1",
                    "price": 10000,
                    "category": "electronics",
                    "description": "테스트용 상품입니다"
                },
                {
                    "id": "product_2",
                    "name": "테스트 상품 2",
                    "price": 20000,
                    "category": "clothing",
                    "description": "테스트용 상품입니다"
                }
            ]
            
            # 상품 동기화 테스트
            sync_result = await integration_service.sync_products_to_all_marketplaces(test_products)
            
            return {
                "setup_result": setup_result,
                "sync_result": sync_result
            }
    
    async def test_supplier_integration(self):
        """공급사 연동 테스트"""
        async with ExternalIntegrationService(self.db_service) as integration_service:
            # 공급사 설정
            supplier_config = {
                "id": "test_supplier_1",
                "name": "테스트 공급사",
                "base_url": "https://api.testsupplier.com",
                "api_type": "rest",
                "auth_type": "bearer_token",
                "auth_config": {
                    "token": "test_bearer_token_123"
                },
                "webhook_url": "https://webhook.site/supplier-webhook",
                "webhook_secret": "test_supplier_webhook_secret_123"
            }
            
            # 공급사 연동 설정
            setup_result = await integration_service.setup_supplier_integration(supplier_config)
            
            # 주문 조회 테스트
            orders_result = await integration_service.fetch_orders_from_all_suppliers()
            
            # 재고 업데이트 테스트
            inventory_data = {
                "product_id": "product_1",
                "quantity": 100,
                "reserved_quantity": 10,
                "available_quantity": 90
            }
            
            inventory_result = await integration_service.update_inventory_to_all_suppliers(inventory_data)
            
            return {
                "setup_result": setup_result,
                "orders_result": orders_result,
                "inventory_result": inventory_result
            }
    
    async def test_integrated_system(self):
        """통합 연동 시스템 테스트"""
        async with ExternalIntegrationService(self.db_service) as integration_service:
            # 전체 시스템 연결 테스트
            connection_test = await integration_service.test_all_connections()
            
            # 대시보드 데이터 조회
            dashboard_data = await integration_service.get_integration_dashboard_data()
            
            return {
                "connection_test": connection_test,
                "dashboard_data": dashboard_data
            }
    
    async def test_connections(self):
        """연결 테스트"""
        async with ExternalIntegrationService(self.db_service) as integration_service:
            # 모든 연결 테스트
            test_results = await integration_service.test_all_connections()
            
            return test_results
    
    async def test_dashboard_data(self):
        """대시보드 데이터 테스트"""
        async with ExternalIntegrationService(self.db_service) as integration_service:
            # 대시보드 데이터 조회
            dashboard_data = await integration_service.get_integration_dashboard_data()
            
            # 데이터 구조 검증
            required_keys = ["webhook_stats", "api_stats", "recent_activities", "system_health"]
            data_valid = all(key in dashboard_data for key in required_keys)
            
            return {
                "data_retrieved": bool(dashboard_data),
                "data_valid": data_valid,
                "keys_present": list(dashboard_data.keys()),
                "sample_data": dashboard_data
            }
    
    def print_test_summary(self):
        """테스트 결과 요약 출력"""
        logger.info("\n" + "="*60)
        logger.info("🧪 외부 시스템 연동 테스트 결과 요약")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results.values() if r["status"] == "success"])
        failed_tests = total_tests - successful_tests
        
        logger.info(f"📊 총 테스트: {total_tests}")
        logger.info(f"✅ 성공: {successful_tests}")
        logger.info(f"❌ 실패: {failed_tests}")
        logger.info(f"📈 성공률: {(successful_tests/total_tests)*100:.1f}%")
        
        logger.info("\n📋 상세 결과:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result["status"] == "success" else "❌"
            logger.info(f"{status_icon} {test_name}: {result['status']}")
            
            if result["status"] == "failed":
                logger.info(f"   오류: {result['error']}")
        
        logger.info("="*60)
        
        # 전체 결과 반환
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": (successful_tests/total_tests)*100,
            "detailed_results": self.test_results
        }


# 테스트 실행 함수
async def run_external_integration_tests():
    """외부 시스템 연동 테스트 실행"""
    tester = ExternalIntegrationTester()
    return await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(run_external_integration_tests())
