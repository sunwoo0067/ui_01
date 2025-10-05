"""
가격 규칙 시스템 구현
마켓플레이스별 수수료를 고려한 가격 계산 엔진
"""

from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.error_handler import ValidationError, BusinessLogicError, validate_required_fields


class PricingRuleType(Enum):
    """가격 규칙 타입"""
    PERCENTAGE_MARGIN = "percentage_margin"  # 퍼센트 마진
    FIXED_MARGIN = "fixed_margin"           # 고정 마진
    COST_PLUS = "cost_plus"                 # 원가 플러스
    COMPETITIVE = "competitive"             # 경쟁사 가격 기반


class PricingCondition(Enum):
    """가격 조건"""
    CATEGORY = "category"
    BRAND = "brand"
    PRICE_RANGE = "price_range"
    SUPPLIER = "supplier"
    MARKETPLACE = "marketplace"


@dataclass
class PricingRule:
    """가격 규칙"""
    id: str
    supplier_id: str
    marketplace_id: str
    rule_name: str
    calculation_type: PricingRuleType
    calculation_value: Decimal
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    round_to: int = 100
    conditions: Optional[Dict[str, Any]] = None
    priority: int = 1
    is_active: bool = True


@dataclass
class ProductPricingData:
    """상품 가격 데이터"""
    product_id: str
    cost_price: Decimal
    category: str
    brand: Optional[str] = None
    supplier_id: Optional[str] = None
    original_price: Optional[Decimal] = None


@dataclass
class PricingResult:
    """가격 계산 결과"""
    product_id: str
    marketplace_id: str
    original_price: Decimal
    calculated_price: Decimal
    cost_price: Decimal
    margin_amount: Decimal
    margin_rate: Decimal
    fee_amount: Decimal
    fee_rate: Decimal
    net_profit: Decimal
    pricing_rule_id: str
    calculation_details: Dict[str, Any]


class PricingEngine:
    """가격 계산 엔진"""
    
    def __init__(self):
        self.marketplace_fees: Dict[str, Dict[str, Decimal]] = {}
        self.pricing_rules: List[PricingRule] = []
    
    def set_marketplace_fees(self, fees: Dict[str, Dict[str, Decimal]]):
        """마켓플레이스 수수료 설정"""
        self.marketplace_fees = fees
    
    def add_pricing_rule(self, rule: PricingRule):
        """가격 규칙 추가"""
        self.pricing_rules.append(rule)
        # 우선순위별로 정렬
        self.pricing_rules.sort(key=lambda x: x.priority)
    
    def get_marketplace_fee_rate(
        self, 
        marketplace_id: str, 
        category: str
    ) -> Decimal:
        """마켓플레이스별 카테고리 수수료율 조회"""
        if marketplace_id not in self.marketplace_fees:
            raise BusinessLogicError(
                f"마켓플레이스 수수료 정보를 찾을 수 없습니다: {marketplace_id}",
                details={"marketplace_id": marketplace_id}
            )
        
        marketplace_fees = self.marketplace_fees[marketplace_id]
        
        # 카테고리별 수수료 조회
        if category in marketplace_fees:
            return marketplace_fees[category]
        
        # 기본 수수료 (etc 카테고리)
        if "etc" in marketplace_fees:
            return marketplace_fees["etc"]
        
        # 기본값 10%
        return Decimal("0.10")
    
    def find_applicable_rule(
        self, 
        product_data: ProductPricingData, 
        marketplace_id: str
    ) -> Optional[PricingRule]:
        """적용 가능한 가격 규칙 찾기"""
        applicable_rules = []
        
        for rule in self.pricing_rules:
            if not rule.is_active:
                continue
            
            if rule.marketplace_id != marketplace_id:
                continue
            
            if rule.supplier_id and rule.supplier_id != product_data.supplier_id:
                continue
            
            # 조건 확인
            if rule.conditions:
                if not self._check_conditions(product_data, rule.conditions):
                    continue
            
            applicable_rules.append(rule)
        
        # 우선순위가 높은 규칙 반환 (priority가 낮을수록 높은 우선순위)
        if applicable_rules:
            return min(applicable_rules, key=lambda x: x.priority)
        
        return None
    
    def _check_conditions(
        self, 
        product_data: ProductPricingData, 
        conditions: Dict[str, Any]
    ) -> bool:
        """가격 규칙 조건 확인"""
        for condition_type, condition_value in conditions.items():
            if condition_type == PricingCondition.CATEGORY.value:
                if product_data.category != condition_value:
                    return False
            
            elif condition_type == PricingCondition.BRAND.value:
                if product_data.brand != condition_value:
                    return False
            
            elif condition_type == PricingCondition.PRICE_RANGE.value:
                min_price = condition_value.get("min")
                max_price = condition_value.get("max")
                
                if min_price and product_data.cost_price < Decimal(str(min_price)):
                    return False
                
                if max_price and product_data.cost_price > Decimal(str(max_price)):
                    return False
            
            elif condition_type == PricingCondition.SUPPLIER.value:
                if product_data.supplier_id != condition_value:
                    return False
        
        return True
    
    def calculate_price(
        self, 
        product_data: ProductPricingData, 
        marketplace_id: str
    ) -> PricingResult:
        """가격 계산"""
        # 입력 검증
        validate_required_fields(
            {
                "product_id": product_data.product_id,
                "cost_price": product_data.cost_price,
                "category": product_data.category
            },
            ["product_id", "cost_price", "category"],
            "상품 가격 데이터"
        )
        
        # 적용 가능한 가격 규칙 찾기
        rule = self.find_applicable_rule(product_data, marketplace_id)
        
        if not rule:
            # 기본 규칙: 30% 마진
            rule = PricingRule(
                id="default",
                supplier_id="",
                marketplace_id=marketplace_id,
                rule_name="기본 30% 마진",
                calculation_type=PricingRuleType.PERCENTAGE_MARGIN,
                calculation_value=Decimal("0.30")
            )
        
        # 가격 계산
        calculated_price = self._calculate_price_by_rule(
            product_data.cost_price, 
            rule
        )
        
        # 마켓플레이스 수수료율 조회
        fee_rate = self.get_marketplace_fee_rate(marketplace_id, product_data.category)
        
        # 수수료 금액 계산
        fee_amount = calculated_price * fee_rate
        
        # 마진 금액 및 비율 계산
        margin_amount = calculated_price - product_data.cost_price
        margin_rate = margin_amount / product_data.cost_price if product_data.cost_price > 0 else Decimal("0")
        
        # 순이익 계산
        net_profit = margin_amount - fee_amount
        
        # 최소/최대 가격 적용
        if rule.min_price and calculated_price < rule.min_price:
            calculated_price = rule.min_price
            margin_amount = calculated_price - product_data.cost_price
            margin_rate = margin_amount / product_data.cost_price if product_data.cost_price > 0 else Decimal("0")
            fee_amount = calculated_price * fee_rate
            net_profit = margin_amount - fee_amount
        
        if rule.max_price and calculated_price > rule.max_price:
            calculated_price = rule.max_price
            margin_amount = calculated_price - product_data.cost_price
            margin_rate = margin_amount / product_data.cost_price if product_data.cost_price > 0 else Decimal("0")
            fee_amount = calculated_price * fee_rate
            net_profit = margin_amount - fee_amount
        
        # 계산 상세 정보
        calculation_details = {
            "rule_name": rule.rule_name,
            "calculation_type": rule.calculation_type.value,
            "calculation_value": float(rule.calculation_value),
            "fee_rate": float(fee_rate),
            "round_to": rule.round_to,
            "conditions": rule.conditions
        }
        
        return PricingResult(
            product_id=product_data.product_id,
            marketplace_id=marketplace_id,
            original_price=product_data.original_price or product_data.cost_price,
            calculated_price=calculated_price,
            cost_price=product_data.cost_price,
            margin_amount=margin_amount,
            margin_rate=margin_rate,
            fee_amount=fee_amount,
            fee_rate=fee_rate,
            net_profit=net_profit,
            pricing_rule_id=rule.id,
            calculation_details=calculation_details
        )
    
    def _calculate_price_by_rule(
        self, 
        cost_price: Decimal, 
        rule: PricingRule
    ) -> Decimal:
        """규칙에 따른 가격 계산"""
        if rule.calculation_type == PricingRuleType.PERCENTAGE_MARGIN:
            # 퍼센트 마진: 원가 * (1 + 마진율)
            price = cost_price * (Decimal("1") + rule.calculation_value)
        
        elif rule.calculation_type == PricingRuleType.FIXED_MARGIN:
            # 고정 마진: 원가 + 고정 마진
            price = cost_price + rule.calculation_value
        
        elif rule.calculation_type == PricingRuleType.COST_PLUS:
            # 원가 플러스: 원가 + (원가 * 플러스율)
            price = cost_price + (cost_price * rule.calculation_value)
        
        elif rule.calculation_type == PricingRuleType.COMPETITIVE:
            # 경쟁사 가격 기반: 원가 * 경쟁사 배수
            price = cost_price * rule.calculation_value
        
        else:
            raise BusinessLogicError(
                f"지원하지 않는 가격 계산 타입: {rule.calculation_type}",
                details={"calculation_type": rule.calculation_type.value}
            )
        
        # 반올림 적용
        if rule.round_to > 0:
            price = self._round_price(price, rule.round_to)
        
        return price
    
    def _round_price(self, price: Decimal, round_to: int) -> Decimal:
        """가격 반올림"""
        if round_to <= 0:
            return price
        
        # 반올림 단위로 나누고 반올림한 후 다시 곱하기
        rounded = (price / Decimal(str(round_to))).quantize(
            Decimal('1'), 
            rounding=ROUND_HALF_UP
        ) * Decimal(str(round_to))
        
        return rounded
    
    def calculate_bulk_prices(
        self, 
        products: List[ProductPricingData], 
        marketplace_id: str
    ) -> List[PricingResult]:
        """대량 가격 계산"""
        results = []
        
        for product_data in products:
            try:
                result = self.calculate_price(product_data, marketplace_id)
                results.append(result)
            except Exception as e:
                # 개별 상품 오류는 로깅하고 계속 진행
                print(f"상품 {product_data.product_id} 가격 계산 오류: {e}")
                continue
        
        return results
    
    def get_pricing_summary(
        self, 
        results: List[PricingResult]
    ) -> Dict[str, Any]:
        """가격 계산 결과 요약"""
        if not results:
            return {
                "total_products": 0,
                "average_margin_rate": 0,
                "average_fee_rate": 0,
                "total_net_profit": 0
            }
        
        total_products = len(results)
        total_margin_rate = sum(float(r.margin_rate) for r in results)
        total_fee_rate = sum(float(r.fee_rate) for r in results)
        total_net_profit = sum(float(r.net_profit) for r in results)
        
        return {
            "total_products": total_products,
            "average_margin_rate": total_margin_rate / total_products,
            "average_fee_rate": total_fee_rate / total_products,
            "total_net_profit": total_net_profit,
            "average_margin_percentage": f"{(total_margin_rate / total_products) * 100:.1f}%",
            "average_fee_percentage": f"{(total_fee_rate / total_products) * 100:.1f}%"
        }


class PricingRuleManager:
    """가격 규칙 관리자"""
    
    def __init__(self):
        self.pricing_engine = PricingEngine()
    
    def create_default_rules(self) -> List[PricingRule]:
        """기본 가격 규칙 생성"""
        rules = [
            # 패션의류 기본 규칙
            PricingRule(
                id="fashion_default",
                supplier_id="",
                marketplace_id="",
                rule_name="패션의류 기본 40% 마진",
                calculation_type=PricingRuleType.PERCENTAGE_MARGIN,
                calculation_value=Decimal("0.40"),
                conditions={"category": "fashion"},
                priority=1
            ),
            
            # 뷰티 기본 규칙
            PricingRule(
                id="beauty_default",
                supplier_id="",
                marketplace_id="",
                rule_name="뷰티 기본 50% 마진",
                calculation_type=PricingRuleType.PERCENTAGE_MARGIN,
                calculation_value=Decimal("0.50"),
                conditions={"category": "beauty"},
                priority=1
            ),
            
            # 디지털 기본 규칙
            PricingRule(
                id="digital_default",
                supplier_id="",
                marketplace_id="",
                rule_name="디지털 기본 20% 마진",
                calculation_type=PricingRuleType.PERCENTAGE_MARGIN,
                calculation_value=Decimal("0.20"),
                conditions={"category": "digital"},
                priority=1
            ),
            
            # 식품 기본 규칙
            PricingRule(
                id="food_default",
                supplier_id="",
                marketplace_id="",
                rule_name="식품 기본 60% 마진",
                calculation_type=PricingRuleType.PERCENTAGE_MARGIN,
                calculation_value=Decimal("0.60"),
                conditions={"category": "food"},
                priority=1
            ),
            
            # 홈리빙 기본 규칙
            PricingRule(
                id="home_living_default",
                supplier_id="",
                marketplace_id="",
                rule_name="홈리빙 기본 35% 마진",
                calculation_type=PricingRuleType.PERCENTAGE_MARGIN,
                calculation_value=Decimal("0.35"),
                conditions={"category": "home_living"},
                priority=1
            ),
        ]
        
        return rules
    
    def setup_default_marketplace_fees(self) -> Dict[str, Dict[str, Decimal]]:
        """기본 마켓플레이스 수수료 설정"""
        fees = {
            "coupang": {
                "fashion": Decimal("0.105"),  # 8% + 2.5%
                "beauty": Decimal("0.125"),    # 10% + 2.5%
                "home_living": Decimal("0.105"), # 8% + 2.5%
                "digital": Decimal("0.075"),   # 5% + 2.5%
                "food": Decimal("0.145"),     # 12% + 2.5%
                "etc": Decimal("0.105")       # 기본 + 2.5%
            },
            "naver_smartstore": {
                "fashion": Decimal("0.07"),    # 5% + 2%
                "beauty": Decimal("0.08"),    # 6% + 2%
                "home_living": Decimal("0.07"), # 5% + 2%
                "digital": Decimal("0.05"),   # 3% + 2%
                "food": Decimal("0.10"),     # 8% + 2%
                "etc": Decimal("0.07")        # 기본 + 2%
            },
            "11st": {
                "fashion": Decimal("0.092"),  # 7% + 2.2%
                "beauty": Decimal("0.102"),   # 8% + 2.2%
                "home_living": Decimal("0.092"), # 7% + 2.2%
                "digital": Decimal("0.062"),  # 4% + 2.2%
                "food": Decimal("0.122"),     # 10% + 2.2%
                "etc": Decimal("0.092")      # 기본 + 2.2%
            },
            "gmarket": {
                "fashion": Decimal("0.08"),   # 6% + 2%
                "beauty": Decimal("0.09"),   # 7% + 2%
                "home_living": Decimal("0.08"), # 6% + 2%
                "digital": Decimal("0.05"),  # 3% + 2%
                "food": Decimal("0.11"),     # 9% + 2%
                "etc": Decimal("0.08")       # 기본 + 2%
            },
            "auction": {
                "fashion": Decimal("0.08"),   # 6% + 2%
                "beauty": Decimal("0.09"),   # 7% + 2%
                "home_living": Decimal("0.08"), # 6% + 2%
                "digital": Decimal("0.05"),   # 3% + 2%
                "food": Decimal("0.11"),     # 9% + 2%
                "etc": Decimal("0.08")       # 기본 + 2%
            }
        }
        
        return fees


# 사용 예시
def example_usage():
    """가격 규칙 시스템 사용 예시"""
    
    # 가격 규칙 관리자 생성
    manager = PricingRuleManager()
    
    # 기본 규칙 및 수수료 설정
    rules = manager.create_default_rules()
    fees = manager.setup_default_marketplace_fees()
    
    # 가격 엔진에 설정 적용
    pricing_engine = manager.pricing_engine
    pricing_engine.set_marketplace_fees(fees)
    
    for rule in rules:
        pricing_engine.add_pricing_rule(rule)
    
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
        )
    ]
    
    # 각 마켓플레이스별 가격 계산
    marketplaces = ["coupang", "naver_smartstore", "11st", "gmarket", "auction"]
    
    for marketplace in marketplaces:
        print(f"\n=== {marketplace.upper()} ===")
        
        results = pricing_engine.calculate_bulk_prices(test_products, marketplace)
        summary = pricing_engine.get_pricing_summary(results)
        
        print(f"총 상품 수: {summary['total_products']}")
        print(f"평균 마진율: {summary['average_margin_percentage']}")
        print(f"평균 수수료율: {summary['average_fee_percentage']}")
        print(f"총 순이익: {summary['total_net_profit']:,.0f}원")
        
        for result in results:
            print(f"  {result.product_id}: {result.calculated_price:,.0f}원 "
                  f"(마진: {result.margin_rate*100:.1f}%, "
                  f"순이익: {result.net_profit:,.0f}원)")


if __name__ == "__main__":
    example_usage()
