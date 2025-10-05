"""
외부 시스템 연동 통합 서비스
웹훅과 API 연동을 통합 관리하는 서비스
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from loguru import logger

from src.services.database_service import DatabaseService
from src.services.webhook_service import WebhookService, WebhookEventType, WebhookManager
from src.services.api_integration_service import APIIntegrationService, ExternalSystemManager
from src.utils.error_handler import ErrorHandler


class ExternalIntegrationService:
    """외부 시스템 연동 통합 서비스"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.webhook_service: Optional[WebhookService] = None
        self.api_service: Optional[APIIntegrationService] = None
        self.webhook_manager: Optional[WebhookManager] = None
        self.system_manager: Optional[ExternalSystemManager] = None
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.webhook_service = WebhookService(self.db_service)
        await self.webhook_service.__aenter__()
        
        self.api_service = APIIntegrationService(self.db_service)
        await self.api_service.load_configs()
        
        self.webhook_manager = WebhookManager(self.webhook_service)
        self.system_manager = ExternalSystemManager(self.api_service)
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.webhook_service:
            await self.webhook_service.__aexit__(exc_type, exc_val, exc_tb)
    
    async def setup_marketplace_integration(self, marketplace_config: Dict[str, Any]) -> bool:
        """마켓플레이스 연동 설정"""
        try:
            logger.info(f"🔗 마켓플레이스 연동 설정: {marketplace_config['name']}")
            
            # API 연동 설정 생성
            from src.services.api_integration_service import APIConfig, APIType, AuthType
            
            api_config = APIConfig(
                id=marketplace_config["id"],
                name=marketplace_config["name"],
                base_url=marketplace_config["base_url"],
                api_type=APIType(marketplace_config["api_type"]),
                auth_type=AuthType(marketplace_config["auth_type"]),
                auth_config=marketplace_config["auth_config"],
                headers=marketplace_config.get("headers", {}),
                timeout=marketplace_config.get("timeout", 30),
                retry_count=marketplace_config.get("retry_count", 3),
                rate_limit=marketplace_config.get("rate_limit"),
                is_active=True
            )
            
            success = await self.api_service.create_config(api_config)
            
            if success and marketplace_config.get("webhook_url"):
                # 웹훅 엔드포인트 생성
                webhook_endpoint = {
                    "id": f"{marketplace_config['id']}_webhook",
                    "url": marketplace_config["webhook_url"],
                    "secret": marketplace_config["webhook_secret"],
                    "events": [
                        WebhookEventType.PRODUCT_CREATED.value,
                        WebhookEventType.PRODUCT_UPDATED.value,
                        WebhookEventType.PRICE_CHANGED.value,
                        WebhookEventType.ORDER_CREATED.value
                    ],
                    "is_active": True,
                    "max_retries": 3,
                    "timeout": 30
                }
                
                await self.webhook_service.create_endpoint(webhook_endpoint)
            
            logger.info(f"✅ 마켓플레이스 연동 설정 완료: {marketplace_config['name']}")
            return True
            
        except Exception as e:
            ErrorHandler.log_error(e, f"마켓플레이스 연동 설정 실패: {marketplace_config['name']}")
            return False
    
    async def setup_supplier_integration(self, supplier_config: Dict[str, Any]) -> bool:
        """공급사 연동 설정"""
        try:
            logger.info(f"🏭 공급사 연동 설정: {supplier_config['name']}")
            
            # API 연동 설정 생성
            from src.services.api_integration_service import APIConfig, APIType, AuthType
            
            api_config = APIConfig(
                id=supplier_config["id"],
                name=supplier_config["name"],
                base_url=supplier_config["base_url"],
                api_type=APIType(supplier_config["api_type"]),
                auth_type=AuthType(supplier_config["auth_type"]),
                auth_config=supplier_config["auth_config"],
                headers=supplier_config.get("headers", {}),
                timeout=supplier_config.get("timeout", 30),
                retry_count=supplier_config.get("retry_count", 3),
                rate_limit=supplier_config.get("rate_limit"),
                is_active=True
            )
            
            success = await self.api_service.create_config(api_config)
            
            if success and supplier_config.get("webhook_url"):
                # 웹훅 엔드포인트 생성
                webhook_endpoint = {
                    "id": f"{supplier_config['id']}_webhook",
                    "url": supplier_config["webhook_url"],
                    "secret": supplier_config["webhook_secret"],
                    "events": [
                        WebhookEventType.INVENTORY_UPDATED.value,
                        WebhookEventType.ORDER_UPDATED.value,
                        WebhookEventType.PRODUCT_UPDATED.value
                    ],
                    "is_active": True,
                    "max_retries": 3,
                    "timeout": 30
                }
                
                await self.webhook_service.create_endpoint(webhook_endpoint)
            
            logger.info(f"✅ 공급사 연동 설정 완료: {supplier_config['name']}")
            return True
            
        except Exception as e:
            ErrorHandler.log_error(e, f"공급사 연동 설정 실패: {supplier_config['name']}")
            return False
    
    async def sync_products_to_all_marketplaces(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """모든 마켓플레이스에 상품 동기화"""
        logger.info(f"📤 {len(products)}개 상품을 모든 마켓플레이스에 동기화 시작")
        
        results = {
            "total_products": len(products),
            "marketplaces": {},
            "overall_success": True,
            "total_successful": 0,
            "total_failed": 0
        }
        
        # 마켓플레이스별 동기화
        marketplace_configs = await self._get_marketplace_configs()
        
        for marketplace_id, config in marketplace_configs.items():
            try:
                sync_result = await self.system_manager.sync_products_to_marketplace(
                    marketplace_id, products
                )
                
                results["marketplaces"][marketplace_id] = sync_result
                results["total_successful"] += sync_result["successful"]
                results["total_failed"] += sync_result["failed"]
                
                if sync_result["failed"] > 0:
                    results["overall_success"] = False
                    
            except Exception as e:
                ErrorHandler.log_error(e, f"마켓플레이스 동기화 실패: {marketplace_id}")
                results["marketplaces"][marketplace_id] = {
                    "successful": 0,
                    "failed": len(products),
                    "error": str(e)
                }
                results["total_failed"] += len(products)
                results["overall_success"] = False
        
        # 웹훅으로 동기화 결과 알림
        await self.webhook_manager.notify_marketplace_sync({
            "sync_type": "products",
            "total_products": len(products),
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"📊 마켓플레이스 동기화 완료 - 성공: {results['total_successful']}, 실패: {results['total_failed']}")
        return results
    
    async def fetch_orders_from_all_suppliers(self, date_from: datetime = None) -> Dict[str, Any]:
        """모든 공급사에서 주문 정보 가져오기"""
        logger.info("📥 모든 공급사에서 주문 정보 조회 시작")
        
        results = {
            "suppliers": {},
            "total_orders": 0,
            "successful_suppliers": 0,
            "failed_suppliers": 0
        }
        
        # 공급사별 주문 조회
        supplier_configs = await self._get_supplier_configs()
        
        for supplier_id, config in supplier_configs.items():
            try:
                orders_result = await self.system_manager.fetch_orders_from_supplier(
                    supplier_id, date_from
                )
                
                results["suppliers"][supplier_id] = orders_result
                
                if orders_result["success"]:
                    results["successful_suppliers"] += 1
                    results["total_orders"] += orders_result["total_count"]
                else:
                    results["failed_suppliers"] += 1
                    
            except Exception as e:
                ErrorHandler.log_error(e, f"공급사 주문 조회 실패: {supplier_id}")
                results["suppliers"][supplier_id] = {
                    "success": False,
                    "error": str(e)
                }
                results["failed_suppliers"] += 1
        
        # 웹훅으로 주문 조회 결과 알림
        await self.webhook_manager.notify_order_created({
            "fetch_type": "bulk",
            "total_orders": results["total_orders"],
            "suppliers_processed": len(supplier_configs),
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"📊 공급사 주문 조회 완료 - 총 주문: {results['total_orders']}, 성공: {results['successful_suppliers']}, 실패: {results['failed_suppliers']}")
        return results
    
    async def update_inventory_to_all_suppliers(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """모든 공급사에 재고 정보 업데이트"""
        logger.info("📤 모든 공급사에 재고 정보 업데이트 시작")
        
        results = {
            "suppliers": {},
            "successful_suppliers": 0,
            "failed_suppliers": 0
        }
        
        # 공급사별 재고 업데이트
        supplier_configs = await self._get_supplier_configs()
        
        for supplier_id, config in supplier_configs.items():
            try:
                update_result = await self.system_manager.update_inventory_to_supplier(
                    supplier_id, inventory_data
                )
                
                results["suppliers"][supplier_id] = update_result
                
                if update_result["success"]:
                    results["successful_suppliers"] += 1
                else:
                    results["failed_suppliers"] += 1
                    
            except Exception as e:
                ErrorHandler.log_error(e, f"공급사 재고 업데이트 실패: {supplier_id}")
                results["suppliers"][supplier_id] = {
                    "success": False,
                    "error": str(e)
                }
                results["failed_suppliers"] += 1
        
        # 웹훅으로 재고 업데이트 결과 알림
        await self.webhook_manager.notify_inventory_updated({
            "update_type": "bulk",
            "suppliers_processed": len(supplier_configs),
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"📊 공급사 재고 업데이트 완료 - 성공: {results['successful_suppliers']}, 실패: {results['failed_suppliers']}")
        return results
    
    async def test_all_connections(self) -> Dict[str, Any]:
        """모든 외부 시스템 연결 테스트"""
        logger.info("🔍 모든 외부 시스템 연결 테스트 시작")
        
        results = {
            "api_connections": {},
            "webhook_endpoints": {},
            "overall_status": "healthy"
        }
        
        # API 연결 테스트
        api_configs = await self._get_all_api_configs()
        for config_id, config in api_configs.items():
            try:
                test_result = await self.api_service.test_connection(config_id)
                results["api_connections"][config_id] = test_result
                
                if not test_result["success"]:
                    results["overall_status"] = "degraded"
                    
            except Exception as e:
                ErrorHandler.log_error(e, f"API 연결 테스트 실패: {config_id}")
                results["api_connections"][config_id] = {
                    "success": False,
                    "error": str(e)
                }
                results["overall_status"] = "degraded"
        
        # 웹훅 엔드포인트 상태 확인
        webhook_stats = await self.webhook_service.get_endpoint_stats()
        results["webhook_endpoints"] = webhook_stats
        
        logger.info(f"🔍 연결 테스트 완료 - 전체 상태: {results['overall_status']}")
        return results
    
    async def get_integration_dashboard_data(self) -> Dict[str, Any]:
        """연동 대시보드 데이터 조회"""
        try:
            dashboard_data = {
                "webhook_stats": await self.webhook_service.get_endpoint_stats(),
                "api_stats": await self.api_service.get_integration_stats(),
                "recent_activities": await self._get_recent_activities(),
                "system_health": await self._get_system_health_status()
            }
            
            return dashboard_data
            
        except Exception as e:
            ErrorHandler.log_error(e, "연동 대시보드 데이터 조회 실패")
            return {}
    
    async def _get_marketplace_configs(self) -> Dict[str, Any]:
        """마켓플레이스 설정 조회"""
        try:
            configs = await self.db_service.select_data(
                "api_integrations"
            )
            
            # 마켓플레이스만 필터링 (실제로는 시스템 타입으로 구분)
            marketplace_configs = {}
            for config in configs:
                if "marketplace" in config["name"].lower() or config["id"].startswith("marketplace_"):
                    marketplace_configs[config["id"]] = config
            
            return marketplace_configs
            
        except Exception as e:
            ErrorHandler.log_error(e, "마켓플레이스 설정 조회 실패")
            return {}
    
    async def _get_supplier_configs(self) -> Dict[str, Any]:
        """공급사 설정 조회"""
        try:
            configs = await self.db_service.select_data(
                "api_integrations"
            )
            
            # 공급사만 필터링
            supplier_configs = {}
            for config in configs:
                if "supplier" in config["name"].lower() or config["id"].startswith("supplier_"):
                    supplier_configs[config["id"]] = config
            
            return supplier_configs
            
        except Exception as e:
            ErrorHandler.log_error(e, "공급사 설정 조회 실패")
            return {}
    
    async def _get_all_api_configs(self) -> Dict[str, Any]:
        """모든 API 설정 조회"""
        try:
            configs = await self.db_service.select_data(
                "api_integrations"
            )
            
            return {config["id"]: config for config in configs}
            
        except Exception as e:
            ErrorHandler.log_error(e, "API 설정 조회 실패")
            return {}
    
    async def _get_recent_activities(self) -> List[Dict[str, Any]]:
        """최근 활동 조회"""
        try:
            # 최근 웹훅 로그
            webhook_logs = await self.db_service.select_data(
                "webhook_logs"
            )
            
            # 최근 API 호출 로그
            api_logs = await self.db_service.select_data(
                "api_call_logs"
            )
            
            activities = []
            
            # 웹훅 활동 추가
            for log in webhook_logs:
                activities.append({
                    "type": "webhook",
                    "event_type": log["event_type"],
                    "success": log["success"],
                    "timestamp": log["created_at"],
                    "details": {
                        "endpoint_id": log["endpoint_id"],
                        "response_time": log["response_time"]
                    }
                })
            
            # API 호출 활동 추가
            for log in api_logs:
                activities.append({
                    "type": "api_call",
                    "method": log["method"],
                    "endpoint": log["endpoint"],
                    "success": log["success"],
                    "timestamp": log["created_at"],
                    "details": {
                        "integration_id": log["integration_id"],
                        "response_time": log["response_time"]
                    }
                })
            
            # 시간순 정렬
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return activities[:20]  # 최근 20개 활동
            
        except Exception as e:
            ErrorHandler.log_error(e, "최근 활동 조회 실패")
            return []
    
    async def _get_system_health_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        try:
            # 시스템 상태 조회
            system_status = await self.db_service.select_data(
                "system_status"
            )
            
            health_status = {
                "total_systems": len(system_status),
                "online_systems": len([s for s in system_status if s["status"] == "online"]),
                "offline_systems": len([s for s in system_status if s["status"] == "offline"]),
                "error_systems": len([s for s in system_status if s["status"] == "error"]),
                "last_check": max([s["last_check"] for s in system_status]) if system_status else None
            }
            
            # 전체 상태 결정
            if health_status["error_systems"] > 0:
                health_status["overall_status"] = "error"
            elif health_status["offline_systems"] > 0:
                health_status["overall_status"] = "degraded"
            else:
                health_status["overall_status"] = "healthy"
            
            return health_status
            
        except Exception as e:
            ErrorHandler.log_error(e, "시스템 상태 조회 실패")
            return {"overall_status": "unknown"}


# 테스트 함수
async def test_external_integration():
    """외부 시스템 연동 테스트"""
    logger.info("🧪 외부 시스템 연동 통합 테스트 시작")
    
    db_service = DatabaseService()
    
    async with ExternalIntegrationService(db_service) as integration_service:
        # 마켓플레이스 연동 설정 테스트
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
            "webhook_url": "https://webhook.site/test-webhook",
            "webhook_secret": "test_webhook_secret_123"
        }
        
        await integration_service.setup_marketplace_integration(marketplace_config)
        
        # 공급사 연동 설정 테스트
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
        
        await integration_service.setup_supplier_integration(supplier_config)
        
        # 연결 테스트
        test_results = await integration_service.test_all_connections()
        logger.info(f"📊 연결 테스트 결과: {test_results}")
        
        # 대시보드 데이터 조회
        dashboard_data = await integration_service.get_integration_dashboard_data()
        logger.info(f"📈 대시보드 데이터: {dashboard_data}")


if __name__ == "__main__":
    asyncio.run(test_external_integration())
