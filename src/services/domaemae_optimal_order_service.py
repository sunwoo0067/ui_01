#!/usr/bin/env python3
"""
도매꾹 최적 주문 로직 서비스
"""

import asyncio
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.database_service import DatabaseService
from src.utils.error_handler import ErrorHandler


class DomaemaeOptimalOrderService:
    """도매꾹 최적 주문 로직 서비스"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
        
        # 시장별 특성
        self.market_characteristics = {
            "dome": {
                "name": "도매꾹",
                "min_order_type": "bulk",
                "supplier_type": "wholesale",
                "min_quantity": 10,  # 최소 주문 수량
                "price_advantage": 0.7,  # 도매가격 할인율 (30% 할인)
                "shipping_cost_per_unit": 500,  # 단위당 배송비
                "bulk_discount_threshold": 50,  # 대량 할인 임계값
                "bulk_discount_rate": 0.1  # 대량 할인율 (10% 추가 할인)
            },
            "supply": {
                "name": "도매매",
                "min_order_type": "single",
                "supplier_type": "retail",
                "min_quantity": 1,  # 최소 주문 수량
                "price_advantage": 1.0,  # 소매가격 (할인 없음)
                "shipping_cost_per_unit": 3000,  # 단위당 배송비
                "bulk_discount_threshold": 10,  # 소량 할인 임계값
                "bulk_discount_rate": 0.05  # 소량 할인율 (5% 할인)
            }
        }
    
    async def analyze_order_requirements(self, order_quantity: int, 
                                       product_price: float,
                                       product_category: str = "general") -> Dict[str, Any]:
        """주문 요구사항 분석"""
        try:
            logger.info(f"주문 요구사항 분석: 수량 {order_quantity}, 가격 {product_price:,.0f}원")
            
            analysis = {
                "order_quantity": order_quantity,
                "product_price": product_price,
                "product_category": product_category,
                "market_recommendations": {},
                "cost_analysis": {},
                "optimal_strategy": None
            }
            
            # 각 시장별 비용 분석
            for market_code, characteristics in self.market_characteristics.items():
                market_analysis = await self._analyze_market_cost(
                    order_quantity, product_price, market_code, characteristics
                )
                analysis["market_recommendations"][market_code] = market_analysis
            
            # 최적 전략 결정
            optimal_strategy = self._determine_optimal_strategy(analysis["market_recommendations"])
            analysis["optimal_strategy"] = optimal_strategy
            
            logger.info(f"최적 전략: {optimal_strategy['market_name']} (총 비용: {optimal_strategy['total_cost']:,.0f}원)")
            
            return analysis
            
        except Exception as e:
            self.error_handler.log_error(e, "주문 요구사항 분석 실패")
            return {}
    
    async def _analyze_market_cost(self, quantity: int, base_price: float, 
                                 market_code: str, characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """시장별 비용 분석"""
        try:
            market_name = characteristics["name"]
            min_quantity = characteristics["min_quantity"]
            price_advantage = characteristics["price_advantage"]
            shipping_cost_per_unit = characteristics["shipping_cost_per_unit"]
            bulk_threshold = characteristics["bulk_discount_threshold"]
            bulk_discount_rate = characteristics["bulk_discount_rate"]
            
            # 최소 주문 수량 확인
            if quantity < min_quantity:
                return {
                    "market_code": market_code,
                    "market_name": market_name,
                    "feasible": False,
                    "reason": f"최소 주문 수량 {min_quantity}개 미만",
                    "total_cost": float('inf')
                }
            
            # 기본 가격 계산
            unit_price = base_price * price_advantage
            
            # 대량 할인 적용
            if quantity >= bulk_threshold:
                unit_price *= (1 - bulk_discount_rate)
                discount_applied = True
                discount_rate = bulk_discount_rate
            else:
                discount_applied = False
                discount_rate = 0
            
            # 총 비용 계산
            subtotal = unit_price * quantity
            shipping_cost = shipping_cost_per_unit * quantity
            total_cost = subtotal + shipping_cost
            
            # 단위당 비용
            cost_per_unit = total_cost / quantity
            
            return {
                "market_code": market_code,
                "market_name": market_name,
                "feasible": True,
                "unit_price": unit_price,
                "quantity": quantity,
                "subtotal": subtotal,
                "shipping_cost": shipping_cost,
                "total_cost": total_cost,
                "cost_per_unit": cost_per_unit,
                "discount_applied": discount_applied,
                "discount_rate": discount_rate,
                "savings_vs_retail": (base_price * quantity) - total_cost,
                "characteristics": characteristics
            }
            
        except Exception as e:
            self.error_handler.log_error(e, f"{market_code} 시장 비용 분석 실패")
            return {"feasible": False, "reason": str(e)}
    
    def _determine_optimal_strategy(self, market_recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """최적 전략 결정"""
        try:
            feasible_markets = {
                k: v for k, v in market_recommendations.items() 
                if v.get("feasible", False)
            }
            
            if not feasible_markets:
                return {
                    "market_code": None,
                    "market_name": "해당 없음",
                    "total_cost": float('inf'),
                    "reason": "주문 가능한 시장이 없습니다"
                }
            
            # 가장 저렴한 시장 선택
            optimal_market = min(feasible_markets.items(), key=lambda x: x[1]["total_cost"])
            market_code, market_data = optimal_market
            
            return {
                "market_code": market_code,
                "market_name": market_data["market_name"],
                "total_cost": market_data["total_cost"],
                "cost_per_unit": market_data["cost_per_unit"],
                "savings_vs_retail": market_data["savings_vs_retail"],
                "recommendation": self._generate_recommendation(market_data)
            }
            
        except Exception as e:
            self.error_handler.log_error(e, "최적 전략 결정 실패")
            return {"market_code": None, "reason": str(e)}
    
    def _generate_recommendation(self, market_data: Dict[str, Any]) -> str:
        """추천 메시지 생성"""
        try:
            market_name = market_data["market_name"]
            total_cost = market_data["total_cost"]
            cost_per_unit = market_data["cost_per_unit"]
            savings = market_data["savings_vs_retail"]
            
            if market_name == "도매꾹":
                recommendation = f"도매꾹에서 주문하세요. 대량 구매로 단위당 {cost_per_unit:,.0f}원에 구매 가능하며, 소매 대비 {savings:,.0f}원 절약됩니다."
            else:
                recommendation = f"도매매에서 주문하세요. 소량 구매에 최적화되어 단위당 {cost_per_unit:,.0f}원에 구매 가능합니다."
            
            if market_data.get("discount_applied", False):
                discount_rate = market_data["discount_rate"] * 100
                recommendation += f" 대량 할인 {discount_rate:.0f}%가 적용되었습니다."
            
            return recommendation
            
        except Exception as e:
            self.error_handler.log_error(e, "추천 메시지 생성 실패")
            return "추천 메시지를 생성할 수 없습니다."
    
    async def get_market_comparison(self, order_quantity: int, 
                                  product_price: float) -> Dict[str, Any]:
        """시장 비교 분석"""
        try:
            logger.info(f"시장 비교 분석: 수량 {order_quantity}, 가격 {product_price:,.0f}원")
            
            comparison = {
                "order_quantity": order_quantity,
                "product_price": product_price,
                "markets": {},
                "summary": {}
            }
            
            # 각 시장별 분석
            for market_code, characteristics in self.market_characteristics.items():
                market_analysis = await self._analyze_market_cost(
                    order_quantity, product_price, market_code, characteristics
                )
                comparison["markets"][market_code] = market_analysis
            
            # 요약 정보
            feasible_markets = {
                k: v for k, v in comparison["markets"].items() 
                if v.get("feasible", False)
            }
            
            if feasible_markets:
                cheapest = min(feasible_markets.items(), key=lambda x: x[1]["total_cost"])
                most_expensive = max(feasible_markets.items(), key=lambda x: x[1]["total_cost"])
                
                comparison["summary"] = {
                    "cheapest_market": cheapest[0],
                    "cheapest_cost": cheapest[1]["total_cost"],
                    "most_expensive_market": most_expensive[0],
                    "most_expensive_cost": most_expensive[1]["total_cost"],
                    "cost_difference": most_expensive[1]["total_cost"] - cheapest[1]["total_cost"],
                    "feasible_markets_count": len(feasible_markets)
                }
            
            return comparison
            
        except Exception as e:
            self.error_handler.log_error(e, "시장 비교 분석 실패")
            return {}
    
    async def recommend_order_strategy(self, order_quantity: int, 
                                     product_price: float,
                                     budget_limit: Optional[float] = None) -> Dict[str, Any]:
        """주문 전략 추천"""
        try:
            logger.info(f"주문 전략 추천: 수량 {order_quantity}, 가격 {product_price:,.0f}원")
            
            # 기본 분석 수행
            analysis = await self.analyze_order_requirements(order_quantity, product_price)
            
            if not analysis.get("optimal_strategy"):
                return {
                    "recommendation": "주문할 수 있는 시장이 없습니다.",
                    "reason": "최소 주문 수량을 확인해주세요."
                }
            
            optimal = analysis["optimal_strategy"]
            recommendation = {
                "recommended_market": optimal["market_code"],
                "recommended_market_name": optimal["market_name"],
                "total_cost": optimal["total_cost"],
                "cost_per_unit": optimal["cost_per_unit"],
                "recommendation_message": optimal["recommendation"],
                "budget_check": None
            }
            
            # 예산 제한 확인
            if budget_limit:
                if optimal["total_cost"] <= budget_limit:
                    recommendation["budget_check"] = {
                        "within_budget": True,
                        "remaining_budget": budget_limit - optimal["total_cost"]
                    }
                else:
                    recommendation["budget_check"] = {
                        "within_budget": False,
                        "excess_amount": optimal["total_cost"] - budget_limit,
                        "suggestion": "예산을 초과합니다. 수량을 줄이거나 다른 시장을 고려해보세요."
                    }
            
            return recommendation
            
        except Exception as e:
            self.error_handler.log_error(e, "주문 전략 추천 실패")
            return {"error": str(e)}


async def test_optimal_order_service():
    """최적 주문 서비스 테스트"""
    try:
        logger.info("도매꾹 최적 주문 서비스 테스트 시작")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 최적 주문 서비스 초기화
        order_service = DomaemaeOptimalOrderService(db_service)
        
        # 테스트 케이스들
        test_cases = [
            {"quantity": 1, "price": 10000, "description": "소량 주문 (1개)"},
            {"quantity": 5, "price": 10000, "description": "소량 주문 (5개)"},
            {"quantity": 15, "price": 10000, "description": "중간 주문 (15개)"},
            {"quantity": 50, "price": 10000, "description": "대량 주문 (50개)"},
            {"quantity": 100, "price": 10000, "description": "대량 주문 (100개)"},
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n=== 테스트 케이스 {i}: {test_case['description']} ===")
            
            # 주문 요구사항 분석
            analysis = await order_service.analyze_order_requirements(
                test_case["quantity"], test_case["price"]
            )
            
            if analysis.get("optimal_strategy"):
                optimal = analysis["optimal_strategy"]
                logger.info(f"최적 시장: {optimal['market_name']}")
                logger.info(f"총 비용: {optimal['total_cost']:,.0f}원")
                logger.info(f"단위당 비용: {optimal['cost_per_unit']:,.0f}원")
                logger.info(f"추천: {optimal['recommendation']}")
            
            # 시장 비교
            comparison = await order_service.get_market_comparison(
                test_case["quantity"], test_case["price"]
            )
            
            if comparison.get("summary"):
                summary = comparison["summary"]
                logger.info(f"가장 저렴한 시장: {summary['cheapest_market']} ({summary['cheapest_cost']:,.0f}원)")
                logger.info(f"가장 비싼 시장: {summary['most_expensive_market']} ({summary['most_expensive_cost']:,.0f}원)")
                logger.info(f"비용 차이: {summary['cost_difference']:,.0f}원")
            
            # 주문 전략 추천
            recommendation = await order_service.recommend_order_strategy(
                test_case["quantity"], test_case["price"], budget_limit=500000
            )
            
            if recommendation.get("recommended_market"):
                logger.info(f"추천 시장: {recommendation['recommended_market_name']}")
                logger.info(f"추천 메시지: {recommendation['recommendation_message']}")
                
                if recommendation.get("budget_check"):
                    budget_check = recommendation["budget_check"]
                    if budget_check["within_budget"]:
                        logger.info(f"예산 내 주문 가능 (잔여: {budget_check['remaining_budget']:,.0f}원)")
                    else:
                        logger.warning(f"예산 초과: {budget_check['excess_amount']:,.0f}원")
        
        logger.info("\n도매꾹 최적 주문 서비스 테스트 완료")
        
    except Exception as e:
        logger.error(f"테스트 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_optimal_order_service())
