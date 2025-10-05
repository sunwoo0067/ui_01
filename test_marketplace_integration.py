"""
마켓플레이스 연동 테스트
데이터베이스 마이그레이션 및 가격 규칙 시스템 통합 테스트
"""

import asyncio
import os
import sys
from decimal import Decimal
from typing import Dict, List, Any

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.services.supabase_client import SupabaseClient
from src.services.pricing_engine import (
    PricingEngine, 
    PricingRuleManager, 
    ProductPricingData, 
    PricingRule,
    PricingRuleType
)
from src.utils.error_handler import ErrorHandler


class MarketplaceIntegrationTester:
    """마켓플레이스 연동 테스트 클래스"""
    
    def __init__(self):
        self.supabase = SupabaseClient()
        self.pricing_manager = PricingRuleManager()
        self.pricing_engine = self.pricing_manager.pricing_engine
    
    async def test_database_migration(self) -> Dict[str, Any]:
        """데이터베이스 마이그레이션 테스트"""
        print("🔄 데이터베이스 마이그레이션 테스트 시작...")
        
        try:
            # 마이그레이션 파일 실행
            migration_file = "database/migrations/003_marketplace_fees_schema.sql"
            
            if not os.path.exists(migration_file):
                return {
                    "status": "error",
                    "message": f"마이그레이션 파일을 찾을 수 없습니다: {migration_file}"
                }
            
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # SQL 실행 (실제 환경에서는 서비스 키 사용)
            result = self.supabase.client.rpc('exec_sql', {'sql': migration_sql})
            
            print("✅ 데이터베이스 마이그레이션 완료")
            
            return {
                "status": "success",
                "message": "마이그레이션 성공",
                "result": result
            }
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "database_migration"})
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def test_marketplace_fees_setup(self) -> Dict[str, Any]:
        """마켓플레이스 수수료 설정 테스트"""
        print("🔄 마켓플레이스 수수료 설정 테스트...")
        
        try:
            # 기본 수수료 설정
            fees = self.pricing_manager.setup_default_marketplace_fees()
            self.pricing_engine.set_marketplace_fees(fees)
            
            # 기본 가격 규칙 설정
            rules = self.pricing_manager.create_default_rules()
            for rule in rules:
                self.pricing_engine.add_pricing_rule(rule)
            
            print(f"✅ {len(fees)}개 마켓플레이스 수수료 설정 완료")
            print(f"✅ {len(rules)}개 가격 규칙 설정 완료")
            
            return {
                "status": "success",
                "marketplaces": len(fees),
                "rules": len(rules),
                "fees_summary": {
                    marketplace: {
                        category: float(rate) for category, rate in categories.items()
                    } for marketplace, categories in fees.items()
                }
            }
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "marketplace_fees_setup"})
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def test_pricing_calculation(self) -> Dict[str, Any]:
        """가격 계산 테스트"""
        print("🔄 가격 계산 테스트...")
        
        try:
            # 테스트 상품 데이터
            test_products = [
                ProductPricingData(
                    product_id="test_fashion_001",
                    cost_price=Decimal("10000"),
                    category="fashion",
                    brand="Test Brand"
                ),
                ProductPricingData(
                    product_id="test_beauty_001",
                    cost_price=Decimal("15000"),
                    category="beauty",
                    brand="Beauty Brand"
                ),
                ProductPricingData(
                    product_id="test_digital_001",
                    cost_price=Decimal("50000"),
                    category="digital",
                    brand="Tech Brand"
                ),
                ProductPricingData(
                    product_id="test_food_001",
                    cost_price=Decimal("5000"),
                    category="food",
                    brand="Food Brand"
                ),
                ProductPricingData(
                    product_id="test_home_001",
                    cost_price=Decimal("25000"),
                    category="home_living",
                    brand="Home Brand"
                )
            ]
            
            # 각 마켓플레이스별 가격 계산
            marketplaces = ["coupang", "naver_smartstore", "11st", "gmarket", "auction"]
            results = {}
            
            for marketplace in marketplaces:
                marketplace_results = self.pricing_engine.calculate_bulk_prices(
                    test_products, marketplace
                )
                summary = self.pricing_engine.get_pricing_summary(marketplace_results)
                
                results[marketplace] = {
                    "summary": summary,
                    "products": [
                        {
                            "product_id": r.product_id,
                            "calculated_price": float(r.calculated_price),
                            "margin_rate": float(r.margin_rate),
                            "fee_rate": float(r.fee_rate),
                            "net_profit": float(r.net_profit)
                        } for r in marketplace_results
                    ]
                }
            
            print("✅ 가격 계산 테스트 완료")
            
            return {
                "status": "success",
                "results": results
            }
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "pricing_calculation"})
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def test_database_integration(self) -> Dict[str, Any]:
        """데이터베이스 통합 테스트"""
        print("🔄 데이터베이스 통합 테스트...")
        
        try:
            # 마켓플레이스 데이터 조회
            marketplaces_result = self.supabase.client.table("marketplaces").select("*").execute()
            
            # 수수료 데이터 조회
            fees_result = self.supabase.client.table("marketplace_fees").select("*").execute()
            
            # 가격 규칙 데이터 조회
            rules_result = self.supabase.client.table("pricing_rules_v2").select("*").execute()
            
            print(f"✅ {len(marketplaces_result.data)}개 마켓플레이스 조회")
            print(f"✅ {len(fees_result.data)}개 수수료 정보 조회")
            print(f"✅ {len(rules_result.data)}개 가격 규칙 조회")
            
            return {
                "status": "success",
                "marketplaces": len(marketplaces_result.data),
                "fees": len(fees_result.data),
                "rules": len(rules_result.data),
                "data": {
                    "marketplaces": marketplaces_result.data,
                    "fees": fees_result.data,
                    "rules": rules_result.data
                }
            }
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "database_integration"})
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def test_custom_pricing_rules(self) -> Dict[str, Any]:
        """커스텀 가격 규칙 테스트"""
        print("🔄 커스텀 가격 규칙 테스트...")
        
        try:
            # 특정 공급사용 고가격 규칙 추가
            high_margin_rule = PricingRule(
                id="high_margin_supplier",
                supplier_id="test_supplier_001",
                marketplace_id="coupang",
                rule_name="고가격 공급사 60% 마진",
                calculation_type=PricingRuleType.PERCENTAGE_MARGIN,
                calculation_value=Decimal("0.60"),
                conditions={"category": "fashion"},
                priority=1
            )
            
            self.pricing_engine.add_pricing_rule(high_margin_rule)
            
            # 테스트 상품 (특정 공급사)
            test_product = ProductPricingData(
                product_id="test_high_margin_001",
                cost_price=Decimal("20000"),
                category="fashion",
                supplier_id="test_supplier_001"
            )
            
            # 가격 계산
            result = self.pricing_engine.calculate_price(test_product, "coupang")
            
            print(f"✅ 고가격 규칙 적용: {result.calculated_price:,.0f}원")
            print(f"   마진율: {result.margin_rate*100:.1f}%")
            print(f"   순이익: {result.net_profit:,.0f}원")
            
            return {
                "status": "success",
                "rule_applied": result.pricing_rule_id,
                "calculated_price": float(result.calculated_price),
                "margin_rate": float(result.margin_rate),
                "net_profit": float(result.net_profit)
            }
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": "custom_pricing_rules"})
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        print("🚀 마켓플레이스 연동 전체 테스트 시작...")
        
        results = {}
        
        # 1. 데이터베이스 마이그레이션 테스트
        results["migration"] = await self.test_database_migration()
        
        # 2. 마켓플레이스 수수료 설정 테스트
        results["fees_setup"] = await self.test_marketplace_fees_setup()
        
        # 3. 가격 계산 테스트
        results["pricing_calculation"] = await self.test_pricing_calculation()
        
        # 4. 데이터베이스 통합 테스트
        results["database_integration"] = await self.test_database_integration()
        
        # 5. 커스텀 가격 규칙 테스트
        results["custom_rules"] = await self.test_custom_pricing_rules()
        
        # 결과 요약
        success_count = sum(1 for r in results.values() if r.get("status") == "success")
        total_count = len(results)
        
        print(f"\n📊 테스트 결과: {success_count}/{total_count} 성공")
        
        return {
            "summary": {
                "total_tests": total_count,
                "successful": success_count,
                "failed": total_count - success_count
            },
            "results": results
        }


async def main():
    """메인 함수"""
    tester = MarketplaceIntegrationTester()
    results = await tester.run_all_tests()
    
    # 결과 저장
    import json
    with open("marketplace_integration_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print("✅ 테스트 완료 - 결과가 marketplace_integration_test_results.json에 저장됨")
    
    return results


if __name__ == "__main__":
    # 비동기 메인 함수 실행
    results = asyncio.run(main())
