"""
전체 시스템 통합 테스트
공급사 API 커넥터 + 가격 규칙 시스템 + 마켓플레이스 API 연동 통합 테스트
"""

import asyncio
import sys
import os
from typing import Dict, List, Any
from decimal import Decimal
import json

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.services.connectors.examples.ownerclan import OwnerClanConnector
from src.services.connectors.examples.zentrade import ZentradeConnector
from src.services.connectors.examples.domaemae import DomaeMaeConnector
from src.services.pricing_engine import PricingEngine, ProductPricingData, PricingRuleManager
from src.utils.error_handler import ErrorHandler


class SystemIntegrationTester:
    """전체 시스템 통합 테스트 클래스"""
    
    def __init__(self):
        self.test_results = {}
        self.pricing_manager = PricingRuleManager()
        self.pricing_engine = self.pricing_manager.pricing_engine
    
    async def test_supplier_connectors(self) -> Dict[str, Any]:
        """공급사 커넥터 테스트"""
        print("🔄 공급사 커넥터 테스트...")
        
        connectors = [
            ("OwnerClan", OwnerClanConnector(
                supplier_id="test-supplier-001",
                credentials={"api_key": "test-key", "api_secret": "test-secret"},
                api_config={"base_url": "https://api.ownerclan.com/v1", "timeout": 30}
            )),
            ("Zentrade", ZentradeConnector(
                supplier_id="test-supplier-002", 
                credentials={"api_key": "test-key", "api_secret": "test-secret"},
                api_config={"base_url": "https://api.zentrade.com/api/v1", "timeout": 30}
            )),
            ("DomaeMae", DomaeMaeConnector(
                supplier_id="test-supplier-003",
                credentials={"api_key": "test-key", "api_secret": "test-secret", "seller_id": "test-seller"},
                api_config={"base_url": "https://api.dodomall.com/v2", "timeout": 30}
            ))
        ]
        
        results = {}
        
        for name, connector in connectors:
            try:
                # 인증 테스트 (Mock)
                auth_result = await connector.validate_credentials()
                
                # 상품 수집 테스트 (Mock)
                products = await connector.collect_products(limit=3)
                
                # 상품 변환 테스트
                transformation_success = False
                if products:
                    try:
                        transformed = await connector.transform_product(products[0])
                        transformation_success = True
                    except Exception as e:
                        print(f"   ⚠️ {name} 상품 변환 실패: {e}")
                
                results[name] = {
                    "status": "success",
                    "auth_result": auth_result,
                    "products_collected": len(products),
                    "transformation_success": transformation_success
                }
                
                print(f"   ✅ {name}: {len(products)}개 상품 수집, 변환 {'성공' if transformation_success else '실패'}")
                
            except Exception as e:
                ErrorHandler.log_error(e, {"operation": f"{name}_connector_test"})
                results[name] = {
                    "status": "error",
                    "message": str(e)
                }
                print(f"   ❌ {name}: {str(e)}")
        
        return results
    
    async def test_pricing_system(self) -> Dict[str, Any]:
        """가격 규칙 시스템 테스트"""
        print("🔄 가격 규칙 시스템 테스트...")
        
        try:
            # 기본 설정 적용
            fees = self.pricing_manager.setup_default_marketplace_fees()
            rules = self.pricing_manager.create_default_rules()
            
            self.pricing_engine.set_marketplace_fees(fees)
            for rule in rules:
                self.pricing_engine.add_pricing_rule(rule)
            
            # 테스트 상품 데이터
            test_products = [
                ProductPricingData(
                    product_id="supplier_fashion_001",
                    cost_price=Decimal("12000"),
                    category="fashion",
                    supplier_id="test-supplier-001"
                ),
                ProductPricingData(
                    product_id="supplier_beauty_001",
                    cost_price=Decimal("18000"),
                    category="beauty",
                    supplier_id="test-supplier-002"
                ),
                ProductPricingData(
                    product_id="supplier_digital_001",
                    cost_price=Decimal("45000"),
                    category="digital",
                    supplier_id="test-supplier-003"
                )
            ]
            
            # 각 마켓플레이스별 가격 계산
            marketplaces = ["coupang", "naver_smartstore", "11st"]
            pricing_results = {}
            
            for marketplace in marketplaces:
                results = self.pricing_engine.calculate_bulk_prices(test_products, marketplace)
                summary = self.pricing_engine.get_pricing_summary(results)
                
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
            
            print(f"   ✅ 가격 계산 완료: {len(marketplaces)}개 마켓플레이스, {len(test_products)}개 상품")
            
            return {
                "status": "success",
                "marketplaces_tested": len(marketplaces),
                "products_tested": len(test_products),
                "pricing_results": pricing_results
            }
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "pricing_system_test"})
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def test_end_to_end_workflow(self) -> Dict[str, Any]:
        """전체 워크플로우 테스트"""
        print("🔄 전체 워크플로우 테스트...")
        
        try:
            # 1. 공급사에서 상품 수집
            print("   📥 공급사 상품 수집...")
            supplier_results = await self.test_supplier_connectors()
            
            # 2. 가격 계산
            print("   💰 가격 계산...")
            pricing_results = await self.test_pricing_system()
            
            # 3. 마켓플레이스 업로드 시뮬레이션
            print("   📤 마켓플레이스 업로드 시뮬레이션...")
            
            # 테스트 상품 데이터 생성
            test_product = {
                "id": "integration_test_001",
                "name": "통합 테스트 상품",
                "description": "전체 시스템 통합 테스트용 상품",
                "category": "fashion",
                "brand": "Integration Test Brand",
                "cost_price": 15000,
                "supplier_id": "test-supplier-001"
            }
            
            # 가격 계산
            pricing_data = ProductPricingData(
                product_id="integration_test_001",
                cost_price=Decimal("15000"),
                category="fashion",
                supplier_id="test-supplier-001"
            )
            
            marketplace_upload_results = {}
            for marketplace in ["coupang", "naver_smartstore"]:
                pricing_result = self.pricing_engine.calculate_price(pricing_data, marketplace)
                
                # 업로드 시뮬레이션
                upload_result = {
                    "success": True,
                    "product_id": f"{marketplace}_{test_product['id']}",
                    "calculated_price": float(pricing_result.calculated_price),
                    "margin_rate": float(pricing_result.margin_rate),
                    "net_profit": float(pricing_result.net_profit),
                    "status": "active"
                }
                
                marketplace_upload_results[marketplace] = upload_result
                print(f"     ✅ {marketplace}: {upload_result['calculated_price']:,.0f}원 (마진: {upload_result['margin_rate']*100:.1f}%)")
            
            # 결과 종합
            successful_suppliers = sum(1 for result in supplier_results.values() if result.get("status") == "success")
            total_suppliers = len(supplier_results)
            
            print(f"   ✅ 전체 워크플로우 완료: {successful_suppliers}/{total_suppliers} 공급사 성공")
            
            return {
                "status": "success",
                "suppliers_tested": total_suppliers,
                "suppliers_successful": successful_suppliers,
                "pricing_system_status": pricing_results.get("status"),
                "marketplace_uploads": len(marketplace_upload_results),
                "supplier_results": supplier_results,
                "pricing_results": pricing_results,
                "marketplace_upload_results": marketplace_upload_results
            }
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "end_to_end_workflow_test"})
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def test_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 테스트"""
        print("🔄 성능 메트릭 테스트...")
        
        try:
            import time
            
            # 대량 상품 처리 테스트
            start_time = time.time()
            
            # 100개 상품 가격 계산
            bulk_products = []
            for i in range(100):
                bulk_products.append(ProductPricingData(
                    product_id=f"bulk_test_{i:03d}",
                    cost_price=Decimal(str(10000 + i * 100)),
                    category="fashion" if i % 3 == 0 else "beauty" if i % 3 == 1 else "digital",
                    supplier_id=f"supplier_{i % 3 + 1:03d}"
                ))
            
            # 가격 계산 실행
            results = self.pricing_engine.calculate_bulk_prices(bulk_products, "coupang")
            summary = self.pricing_engine.get_pricing_summary(results)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"   ✅ 대량 처리 완료: {len(bulk_products)}개 상품, {processing_time:.2f}초")
            print(f"     평균 처리 시간: {processing_time/len(bulk_products)*1000:.2f}ms/상품")
            print(f"     평균 마진율: {summary['average_margin_percentage']}")
            print(f"     총 순이익: {summary['total_net_profit']:,.0f}원")
            
            return {
                "status": "success",
                "products_processed": len(bulk_products),
                "processing_time": processing_time,
                "avg_time_per_product": processing_time / len(bulk_products),
                "summary": summary
            }
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "performance_metrics_test"})
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """종합 테스트 실행"""
        print("🚀 전체 시스템 통합 테스트 시작...")
        
        # 전체 워크플로우 테스트
        workflow_results = await self.test_end_to_end_workflow()
        
        # 성능 메트릭 테스트
        performance_results = await self.test_performance_metrics()
        
        # 결과 요약
        total_tests = 2
        successful_tests = sum(1 for result in [workflow_results, performance_results] if result.get("status") == "success")
        
        print(f"\n📊 종합 테스트 결과:")
        print(f"   - 전체 테스트: {successful_tests}/{total_tests} 성공")
        print(f"   - 워크플로우: {'✅' if workflow_results.get('status') == 'success' else '❌'}")
        print(f"   - 성능 메트릭: {'✅' if performance_results.get('status') == 'success' else '❌'}")
        
        if workflow_results.get("status") == "success":
            print(f"   - 공급사 연동: {workflow_results['suppliers_successful']}/{workflow_results['suppliers_tested']} 성공")
            print(f"   - 마켓플레이스 업로드: {workflow_results['marketplace_uploads']}개")
        
        if performance_results.get("status") == "success":
            print(f"   - 대량 처리: {performance_results['products_processed']}개 상품")
            print(f"   - 처리 시간: {performance_results['processing_time']:.2f}초")
        
        return {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests
            },
            "workflow_results": workflow_results,
            "performance_results": performance_results
        }


async def main():
    """메인 함수"""
    tester = SystemIntegrationTester()
    results = await tester.run_comprehensive_test()
    
    # 결과 저장
    with open("system_integration_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print("✅ 종합 테스트 완료 - 결과가 system_integration_test_results.json에 저장됨")
    
    return results


if __name__ == "__main__":
    # 비동기 메인 함수 실행
    results = asyncio.run(main())
