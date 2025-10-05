"""
마켓플레이스 API 연동 구현
쿠팡, 네이버 스마트스토어 등 주요 마켓플레이스와의 연동
"""

import asyncio
import sys
import os
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime
import json

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.services.pricing_engine import PricingEngine, ProductPricingData, PricingRuleManager
from src.utils.error_handler import ErrorHandler


class MarketplaceAPIConnector:
    """마켓플레이스 API 연동 기본 클래스"""
    
    def __init__(self, marketplace_name: str, api_config: Dict[str, Any]):
        """
        마켓플레이스 API 커넥터 초기화
        
        Args:
            marketplace_name: 마켓플레이스 이름
            api_config: API 설정 정보
        """
        self.marketplace_name = marketplace_name
        self.api_config = api_config
        self.base_url = api_config.get('base_url', '')
        self.api_key = api_config.get('api_key', '')
        self.api_secret = api_config.get('api_secret', '')
        self.timeout = api_config.get('timeout', 30)
    
    async def authenticate(self) -> bool:
        """API 인증"""
        raise NotImplementedError("서브클래스에서 구현해야 합니다")
    
    async def upload_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """상품 업로드"""
        raise NotImplementedError("서브클래스에서 구현해야 합니다")
    
    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """상품 정보 업데이트"""
        raise NotImplementedError("서브클래스에서 구현해야 합니다")
    
    async def delete_product(self, product_id: str) -> bool:
        """상품 삭제"""
        raise NotImplementedError("서브클래스에서 구현해야 합니다")
    
    async def get_product_status(self, product_id: str) -> Dict[str, Any]:
        """상품 상태 조회"""
        raise NotImplementedError("서브클래스에서 구현해야 합니다")
    
    async def sync_inventory(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """재고 동기화"""
        raise NotImplementedError("서브클래스에서 구현해야 합니다")


class CoupangAPIConnector(MarketplaceAPIConnector):
    """쿠팡 API 연동"""
    
    def __init__(self, api_config: Dict[str, Any]):
        super().__init__("Coupang", api_config)
        self.access_token = None
        self.refresh_token = None
    
    async def authenticate(self) -> bool:
        """쿠팡 API 인증"""
        try:
            # 실제 쿠팡 API 인증 로직 (OAuth 2.0)
            # 여기서는 Mock 구현
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.api_secret
            }
            
            # Mock 인증 성공
            self.access_token = "mock_access_token"
            self.refresh_token = "mock_refresh_token"
            
            print(f"✅ {self.marketplace_name} API 인증 성공")
            return True
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "coupang_authentication"})
            return False
    
    async def upload_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """쿠팡 상품 업로드"""
        try:
            if not self.access_token:
                await self.authenticate()
            
            # 쿠팡 상품 업로드 API 호출 (Mock)
            upload_result = {
                "success": True,
                "product_id": f"coupang_{product_data.get('id', 'unknown')}",
                "marketplace_product_id": f"CP_{product_data.get('id', 'unknown')}",
                "status": "pending_review",
                "uploaded_at": datetime.now().isoformat(),
                "message": "상품이 성공적으로 업로드되었습니다"
            }
            
            print(f"✅ {self.marketplace_name} 상품 업로드 성공: {upload_result['product_id']}")
            return upload_result
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "coupang_product_upload"})
            return {
                "success": False,
                "error": str(e),
                "message": "상품 업로드 실패"
            }
    
    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """쿠팡 상품 정보 업데이트"""
        try:
            if not self.access_token:
                await self.authenticate()
            
            # 쿠팡 상품 업데이트 API 호출 (Mock)
            update_result = {
                "success": True,
                "product_id": product_id,
                "updated_at": datetime.now().isoformat(),
                "message": "상품 정보가 성공적으로 업데이트되었습니다"
            }
            
            print(f"✅ {self.marketplace_name} 상품 업데이트 성공: {product_id}")
            return update_result
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "coupang_product_update"})
            return {
                "success": False,
                "error": str(e),
                "message": "상품 업데이트 실패"
            }
    
    async def get_product_status(self, product_id: str) -> Dict[str, Any]:
        """쿠팡 상품 상태 조회"""
        try:
            if not self.access_token:
                await self.authenticate()
            
            # 쿠팡 상품 상태 조회 API 호출 (Mock)
            status_result = {
                "product_id": product_id,
                "status": "active",
                "visibility": "visible",
                "last_updated": datetime.now().isoformat(),
                "reviews_count": 0,
                "sales_count": 0
            }
            
            return status_result
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "coupang_product_status"})
            return {
                "product_id": product_id,
                "status": "error",
                "error": str(e)
            }
    
    async def sync_inventory(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """쿠팡 재고 동기화"""
        try:
            if not self.access_token:
                await self.authenticate()
            
            # 쿠팡 재고 동기화 API 호출 (Mock)
            sync_result = {
                "success": True,
                "total_products": len(products),
                "synced_products": len(products),
                "failed_products": 0,
                "synced_at": datetime.now().isoformat()
            }
            
            print(f"✅ {self.marketplace_name} 재고 동기화 완료: {len(products)}개 상품")
            return sync_result
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "coupang_inventory_sync"})
            return {
                "success": False,
                "error": str(e),
                "message": "재고 동기화 실패"
            }


class NaverSmartStoreAPIConnector(MarketplaceAPIConnector):
    """네이버 스마트스토어 API 연동"""
    
    def __init__(self, api_config: Dict[str, Any]):
        super().__init__("Naver SmartStore", api_config)
        self.access_token = None
    
    async def authenticate(self) -> bool:
        """네이버 스마트스토어 API 인증"""
        try:
            # 실제 네이버 스마트스토어 API 인증 로직
            # 여기서는 Mock 구현
            auth_data = {
                "client_id": self.api_key,
                "client_secret": self.api_secret,
                "grant_type": "client_credentials"
            }
            
            # Mock 인증 성공
            self.access_token = "mock_naver_access_token"
            
            print(f"✅ {self.marketplace_name} API 인증 성공")
            return True
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "naver_authentication"})
            return False
    
    async def upload_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """네이버 스마트스토어 상품 업로드"""
        try:
            if not self.access_token:
                await self.authenticate()
            
            # 네이버 스마트스토어 상품 업로드 API 호출 (Mock)
            upload_result = {
                "success": True,
                "product_id": f"naver_{product_data.get('id', 'unknown')}",
                "marketplace_product_id": f"NV_{product_data.get('id', 'unknown')}",
                "status": "active",
                "uploaded_at": datetime.now().isoformat(),
                "message": "상품이 성공적으로 업로드되었습니다"
            }
            
            print(f"✅ {self.marketplace_name} 상품 업로드 성공: {upload_result['product_id']}")
            return upload_result
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "naver_product_upload"})
            return {
                "success": False,
                "error": str(e),
                "message": "상품 업로드 실패"
            }
    
    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """네이버 스마트스토어 상품 정보 업데이트"""
        try:
            if not self.access_token:
                await self.authenticate()
            
            # 네이버 스마트스토어 상품 업데이트 API 호출 (Mock)
            update_result = {
                "success": True,
                "product_id": product_id,
                "updated_at": datetime.now().isoformat(),
                "message": "상품 정보가 성공적으로 업데이트되었습니다"
            }
            
            print(f"✅ {self.marketplace_name} 상품 업데이트 성공: {product_id}")
            return update_result
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "naver_product_update"})
            return {
                "success": False,
                "error": str(e),
                "message": "상품 업데이트 실패"
            }
    
    async def get_product_status(self, product_id: str) -> Dict[str, Any]:
        """네이버 스마트스토어 상품 상태 조회"""
        try:
            if not self.access_token:
                await self.authenticate()
            
            # 네이버 스마트스토어 상품 상태 조회 API 호출 (Mock)
            status_result = {
                "product_id": product_id,
                "status": "active",
                "visibility": "visible",
                "last_updated": datetime.now().isoformat(),
                "reviews_count": 0,
                "sales_count": 0
            }
            
            return status_result
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "naver_product_status"})
            return {
                "product_id": product_id,
                "status": "error",
                "error": str(e)
            }
    
    async def sync_inventory(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """네이버 스마트스토어 재고 동기화"""
        try:
            if not self.access_token:
                await self.authenticate()
            
            # 네이버 스마트스토어 재고 동기화 API 호출 (Mock)
            sync_result = {
                "success": True,
                "total_products": len(products),
                "synced_products": len(products),
                "failed_products": 0,
                "synced_at": datetime.now().isoformat()
            }
            
            print(f"✅ {self.marketplace_name} 재고 동기화 완료: {len(products)}개 상품")
            return sync_result
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "naver_inventory_sync"})
            return {
                "success": False,
                "error": str(e),
                "message": "재고 동기화 실패"
            }


class MarketplaceIntegrationManager:
    """마켓플레이스 통합 관리자"""
    
    def __init__(self):
        self.connectors: Dict[str, MarketplaceAPIConnector] = {}
        self.pricing_manager = PricingRuleManager()
        self.pricing_engine = self.pricing_manager.pricing_engine
    
    def add_marketplace(self, marketplace_name: str, api_config: Dict[str, Any]):
        """마켓플레이스 추가"""
        if marketplace_name.lower() == "coupang":
            connector = CoupangAPIConnector(api_config)
        elif marketplace_name.lower() == "naver_smartstore":
            connector = NaverSmartStoreAPIConnector(api_config)
        else:
            raise ValueError(f"지원하지 않는 마켓플레이스: {marketplace_name}")
        
        self.connectors[marketplace_name.lower()] = connector
        print(f"✅ {marketplace_name} 마켓플레이스 추가 완료")
    
    async def authenticate_all(self) -> Dict[str, bool]:
        """모든 마켓플레이스 인증"""
        results = {}
        
        for marketplace_name, connector in self.connectors.items():
            try:
                auth_result = await connector.authenticate()
                results[marketplace_name] = auth_result
            except Exception as e:
                ErrorHandler.log_error(e, {"operation": f"{marketplace_name}_authentication"})
                results[marketplace_name] = False
        
        return results
    
    async def upload_product_to_all_marketplaces(
        self, 
        product_data: Dict[str, Any], 
        pricing_data: ProductPricingData
    ) -> Dict[str, Any]:
        """모든 마켓플레이스에 상품 업로드"""
        results = {}
        
        # 가격 계산
        pricing_results = {}
        for marketplace_name in self.connectors.keys():
            pricing_result = self.pricing_engine.calculate_price(pricing_data, marketplace_name)
            pricing_results[marketplace_name] = pricing_result
        
        # 각 마켓플레이스에 업로드
        for marketplace_name, connector in self.connectors.items():
            try:
                # 가격 정보 추가
                marketplace_product_data = product_data.copy()
                pricing_result = pricing_results[marketplace_name]
                
                marketplace_product_data.update({
                    "price": float(pricing_result.calculated_price),
                    "margin_rate": float(pricing_result.margin_rate),
                    "fee_rate": float(pricing_result.fee_rate),
                    "net_profit": float(pricing_result.net_profit)
                })
                
                upload_result = await connector.upload_product(marketplace_product_data)
                results[marketplace_name] = upload_result
                
            except Exception as e:
                ErrorHandler.log_error(e, {"operation": f"{marketplace_name}_product_upload"})
                results[marketplace_name] = {
                    "success": False,
                    "error": str(e),
                    "message": f"{marketplace_name} 업로드 실패"
                }
        
        return results
    
    async def sync_inventory_all(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """모든 마켓플레이스 재고 동기화"""
        results = {}
        
        for marketplace_name, connector in self.connectors.items():
            try:
                sync_result = await connector.sync_inventory(products)
                results[marketplace_name] = sync_result
            except Exception as e:
                ErrorHandler.log_error(e, {"operation": f"{marketplace_name}_inventory_sync"})
                results[marketplace_name] = {
                    "success": False,
                    "error": str(e),
                    "message": f"{marketplace_name} 재고 동기화 실패"
                }
        
        return results
    
    async def get_all_product_statuses(self, product_id: str) -> Dict[str, Any]:
        """모든 마켓플레이스 상품 상태 조회"""
        results = {}
        
        for marketplace_name, connector in self.connectors.items():
            try:
                status_result = await connector.get_product_status(product_id)
                results[marketplace_name] = status_result
            except Exception as e:
                ErrorHandler.log_error(e, {"operation": f"{marketplace_name}_product_status"})
                results[marketplace_name] = {
                    "product_id": product_id,
                    "status": "error",
                    "error": str(e)
                }
        
        return results


async def test_marketplace_integration():
    """마켓플레이스 연동 테스트"""
    print("🚀 마켓플레이스 API 연동 테스트 시작...")
    
    # 통합 관리자 생성
    manager = MarketplaceIntegrationManager()
    
    # 가격 규칙 설정
    fees = manager.pricing_manager.setup_default_marketplace_fees()
    rules = manager.pricing_manager.create_default_rules()
    
    manager.pricing_engine.set_marketplace_fees(fees)
    for rule in rules:
        manager.pricing_engine.add_pricing_rule(rule)
    
    # 마켓플레이스 추가
    manager.add_marketplace("Coupang", {
        "base_url": "https://api.coupang.com/v2",
        "api_key": "mock_coupang_key",
        "api_secret": "mock_coupang_secret",
        "timeout": 30
    })
    
    manager.add_marketplace("Naver_SmartStore", {
        "base_url": "https://api.commerce.naver.com/v1",
        "api_key": "mock_naver_key",
        "api_secret": "mock_naver_secret",
        "timeout": 30
    })
    
    # 인증 테스트
    print("\n🔄 마켓플레이스 인증 테스트...")
    auth_results = await manager.authenticate_all()
    
    for marketplace, success in auth_results.items():
        status = "✅" if success else "❌"
        print(f"   - {marketplace}: {status}")
    
    # 상품 업로드 테스트
    print("\n🔄 상품 업로드 테스트...")
    
    test_product_data = {
        "id": "test_product_001",
        "name": "테스트 상품",
        "description": "마켓플레이스 연동 테스트용 상품",
        "category": "fashion",
        "brand": "Test Brand",
        "images": ["https://example.com/image1.jpg"],
        "attributes": {
            "color": "black",
            "size": "M",
            "material": "cotton"
        }
    }
    
    test_pricing_data = ProductPricingData(
        product_id="test_product_001",
        cost_price=Decimal("15000"),
        category="fashion",
        brand="Test Brand"
    )
    
    upload_results = await manager.upload_product_to_all_marketplaces(
        test_product_data, 
        test_pricing_data
    )
    
    for marketplace, result in upload_results.items():
        status = "✅" if result.get("success") else "❌"
        print(f"   - {marketplace}: {status}")
        if result.get("success"):
            print(f"     상품 ID: {result.get('product_id')}")
            print(f"     상태: {result.get('status')}")
    
    # 재고 동기화 테스트
    print("\n🔄 재고 동기화 테스트...")
    
    test_products = [
        {
            "id": "test_product_001",
            "stock": 100,
            "price": 19500
        },
        {
            "id": "test_product_002", 
            "stock": 50,
            "price": 25000
        }
    ]
    
    sync_results = await manager.sync_inventory_all(test_products)
    
    for marketplace, result in sync_results.items():
        status = "✅" if result.get("success") else "❌"
        print(f"   - {marketplace}: {status}")
        if result.get("success"):
            print(f"     동기화된 상품: {result.get('synced_products')}개")
    
    # 상품 상태 조회 테스트
    print("\n🔄 상품 상태 조회 테스트...")
    
    status_results = await manager.get_all_product_statuses("test_product_001")
    
    for marketplace, result in status_results.items():
        status = "✅" if result.get("status") != "error" else "❌"
        print(f"   - {marketplace}: {status}")
        if result.get("status") != "error":
            print(f"     상태: {result.get('status')}")
    
    print("\n✅ 마켓플레이스 API 연동 테스트 완료!")
    
    return {
        "authentication": auth_results,
        "upload": upload_results,
        "sync": sync_results,
        "status": status_results
    }


if __name__ == "__main__":
    # 비동기 메인 함수 실행
    results = asyncio.run(test_marketplace_integration())
    
    # 결과 저장
    with open("marketplace_api_integration_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print("✅ 테스트 완료 - 결과가 marketplace_api_integration_results.json에 저장됨")
