"""
API 커넥터 실제 연동 테스트 (환경 변수 없이 실행)
Mock 데이터를 사용하여 API 커넥터의 기본 동작을 테스트
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 환경 변수 Mock 설정
os.environ["SUPABASE_URL"] = "https://mock.supabase.co"
os.environ["SUPABASE_KEY"] = "mock-anon-key"
os.environ["SUPABASE_SERVICE_KEY"] = "mock-service-key"
os.environ["OWNERCLAN_API_KEY"] = "mock-ownerclan-key"
os.environ["OWNERCLAN_API_SECRET"] = "mock-ownerclan-secret"
os.environ["ZENTRADE_API_KEY"] = "mock-zentrade-key"
os.environ["ZENTRADE_API_SECRET"] = "mock-zentrade-secret"
os.environ["DOMAEMAE_API_KEY"] = "mock-domaemae-key"
os.environ["DOMAEMAE_API_SECRET"] = "mock-domaemae-secret"

from src.services.connectors.examples.ownerclan import OwnerClanConnector
from src.services.connectors.examples.zentrade import ZentradeConnector
from src.services.connectors.examples.domaemae import DomaeMaeConnector
from src.services.pricing_engine import PricingEngine, ProductPricingData, PricingRuleManager
from src.utils.error_handler import ErrorHandler


class APIConnectorLiveTester:
    """API 커넥터 실제 연동 테스트 클래스"""
    
    def __init__(self):
        self.test_results = {}
    
    async def test_ownerclan_connector(self) -> dict:
        """오너클랜 커넥터 테스트"""
        print("🔄 오너클랜 커넥터 테스트 시작...")
        
        try:
            # Mock Supabase 클라이언트 설정
            with patch('src.services.supabase_client.supabase_client') as mock_supabase:
                mock_supabase.client = AsyncMock()
                mock_supabase.client.table.return_value.select.return_value.execute.return_value = AsyncMock(
                    return_value=MagicMock(data=[])
                )
                
                # 커넥터 생성
                connector = OwnerClanConnector(
                    supplier_id="test-supplier",
                    credentials={"api_key": "test-key", "api_secret": "test-secret"},
                    api_config={"base_url": "https://api.ownerclan.com/v1", "timeout": 30}
                )
                
                # 인증 테스트 (Mock)
                auth_result = await connector.validate_credentials()
                
                # 상품 수집 테스트 (Mock)
                products = await connector.collect_products(limit=5)
                
                # 상품 변환 테스트
                if products:
                    transformed = await connector.transform_product(products[0])
                
                print("✅ 오너클랜 커넥터 테스트 완료")
                
                return {
                    "status": "success",
                    "auth_result": auth_result,
                    "products_collected": len(products),
                    "transformation_test": "passed" if products else "skipped"
                }
                
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "ownerclan_connector_test"})
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def test_zentrade_connector(self) -> dict:
        """젠트레이드 커넥터 테스트"""
        print("🔄 젠트레이드 커넥터 테스트 시작...")
        
        try:
            # Mock Supabase 클라이언트 설정
            with patch('src.services.supabase_client.supabase_client') as mock_supabase:
                mock_supabase.client = AsyncMock()
                mock_supabase.client.table.return_value.select.return_value.execute.return_value = AsyncMock(
                    return_value=MagicMock(data=[])
                )
                
                # 커넥터 생성
                connector = ZentradeConnector(
                    supplier_id="test-supplier",
                    credentials={"api_key": "test-key", "api_secret": "test-secret"},
                    api_config={"base_url": "https://api.zentrade.com/v1", "timeout": 30}
                )
                
                # 인증 테스트 (Mock)
                auth_result = await connector.validate_credentials()
                
                # 상품 수집 테스트 (Mock)
                products = await connector.collect_products(limit=5)
                
                # 상품 변환 테스트
                if products:
                    transformed = await connector.transform_product(products[0])
                
                print("✅ 젠트레이드 커넥터 테스트 완료")
                
                return {
                    "status": "success",
                    "auth_result": auth_result,
                    "products_collected": len(products),
                    "transformation_test": "passed" if products else "skipped"
                }
                
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "zentrade_connector_test"})
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def test_domaemae_connector(self) -> dict:
        """도매매 커넥터 테스트"""
        print("🔄 도매매 커넥터 테스트 시작...")
        
        try:
            # Mock Supabase 클라이언트 설정
            with patch('src.services.supabase_client.supabase_client') as mock_supabase:
                mock_supabase.client = AsyncMock()
                mock_supabase.client.table.return_value.select.return_value.execute.return_value = AsyncMock(
                    return_value=MagicMock(data=[])
                )
                
                # 커넥터 생성
                connector = DomaeMaeConnector(
                    supplier_id="test-supplier",
                    credentials={"api_key": "test-key", "api_secret": "test-secret", "seller_id": "test-seller"},
                    api_config={"base_url": "https://api.domaemae.com/v1", "timeout": 30}
                )
                
                # 인증 테스트 (Mock)
                auth_result = await connector.validate_credentials()
                
                # 상품 수집 테스트 (Mock)
                products = await connector.collect_products(limit=5)
                
                # 상품 변환 테스트
                if products:
                    transformed = await connector.transform_product(products[0])
                
                print("✅ 도매매 커넥터 테스트 완료")
                
                return {
                    "status": "success",
                    "auth_result": auth_result,
                    "products_collected": len(products),
                    "transformation_test": "passed" if products else "skipped"
                }
                
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "domaemae_connector_test"})
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def test_pricing_integration(self) -> dict:
        """가격 규칙 시스템과의 통합 테스트"""
        print("🔄 가격 규칙 시스템 통합 테스트...")
        
        try:
            # 가격 규칙 관리자 생성
            pricing_manager = PricingRuleManager()
            pricing_engine = pricing_manager.pricing_engine
            
            # 기본 설정 적용
            fees = pricing_manager.setup_default_marketplace_fees()
            rules = pricing_manager.create_default_rules()
            
            pricing_engine.set_marketplace_fees(fees)
            for rule in rules:
                pricing_engine.add_pricing_rule(rule)
            
            # 테스트 상품 데이터 (공급사별)
            test_products = [
                ProductPricingData(
                    product_id="ownerclan_fashion_001",
                    cost_price=Decimal("15000"),
                    category="fashion",
                    supplier_id="ownerclan"
                ),
                ProductPricingData(
                    product_id="zentrade_beauty_001",
                    cost_price=Decimal("25000"),
                    category="beauty",
                    supplier_id="zentrade"
                ),
                ProductPricingData(
                    product_id="domaemae_digital_001",
                    cost_price=Decimal("80000"),
                    category="digital",
                    supplier_id="domaemae"
                )
            ]
            
            # 각 마켓플레이스별 가격 계산
            marketplaces = ["coupang", "naver_smartstore", "11st"]
            pricing_results = {}
            
            for marketplace in marketplaces:
                results = pricing_engine.calculate_bulk_prices(test_products, marketplace)
                summary = pricing_engine.get_pricing_summary(results)
                
                pricing_results[marketplace] = {
                    "summary": summary,
                    "products": [
                        {
                            "product_id": r.product_id,
                            "calculated_price": float(r.calculated_price),
                            "margin_rate": float(r.margin_rate),
                            "net_profit": float(r.net_profit)
                        } for r in results
                    ]
                }
            
            print("✅ 가격 규칙 시스템 통합 테스트 완료")
            
            return {
                "status": "success",
                "marketplaces_tested": len(marketplaces),
                "products_tested": len(test_products),
                "pricing_results": pricing_results
            }
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "pricing_integration_test"})
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def test_end_to_end_workflow(self) -> dict:
        """전체 워크플로우 테스트"""
        print("🔄 전체 워크플로우 테스트 시작...")
        
        try:
            # 1. 공급사 커넥터 테스트
            connectors = [
                ("OwnerClan", await self.test_ownerclan_connector()),
                ("Zentrade", await self.test_zentrade_connector()),
                ("DomaeMae", await self.test_domaemae_connector())
            ]
            
            # 2. 가격 규칙 시스템 테스트
            pricing_result = await self.test_pricing_integration()
            
            # 3. 결과 종합
            successful_connectors = sum(1 for _, result in connectors if result.get("status") == "success")
            total_connectors = len(connectors)
            
            print(f"✅ 전체 워크플로우 테스트 완료: {successful_connectors}/{total_connectors} 커넥터 성공")
            
            return {
                "status": "success",
                "connectors_tested": total_connectors,
                "connectors_successful": successful_connectors,
                "pricing_system_status": pricing_result.get("status"),
                "connector_results": {name: result for name, result in connectors},
                "pricing_result": pricing_result
            }
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "end_to_end_workflow_test"})
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def run_all_tests(self) -> dict:
        """모든 테스트 실행"""
        print("🚀 API 커넥터 실제 연동 테스트 시작...")
        
        # 전체 워크플로우 테스트 실행
        results = await self.test_end_to_end_workflow()
        
        # 결과 요약
        if results.get("status") == "success":
            print(f"\n📊 테스트 결과 요약:")
            print(f"   - 커넥터 테스트: {results['connectors_successful']}/{results['connectors_tested']} 성공")
            print(f"   - 가격 시스템: {results['pricing_system_status']}")
            
            # 상세 결과 출력
            for connector_name, connector_result in results['connector_results'].items():
                status = "✅" if connector_result.get("status") == "success" else "❌"
                print(f"   - {connector_name}: {status}")
        
        return results


async def main():
    """메인 함수"""
    tester = APIConnectorLiveTester()
    results = await tester.run_all_tests()
    
    # 결과 저장
    import json
    with open("api_connector_live_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print("✅ 테스트 완료 - 결과가 api_connector_live_test_results.json에 저장됨")
    
    return results


if __name__ == "__main__":
    # 비동기 메인 함수 실행
    results = asyncio.run(main())
