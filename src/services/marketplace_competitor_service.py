#!/usr/bin/env python3
"""
마켓플레이스 경쟁사 데이터 수집 통합 서비스
"""

import asyncio
import sys
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.database_service import DatabaseService
from src.services.coupang_search_service import CoupangSearchService, CoupangProduct
from src.services.naver_smartstore_search_service import NaverSmartStoreSearchService, NaverSmartStoreProduct
from src.services.elevenstreet_search_service import ElevenStreetSearchService, ElevenStreetProduct
from src.services.gmarket_search_service import GmarketSearchService, GmarketProduct
from src.services.auction_search_service import AuctionSearchService, AuctionProduct
from src.utils.error_handler import ErrorHandler


class MarketplaceCompetitorService:
    """마켓플레이스 경쟁사 데이터 수집 통합 서비스"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
        
        # 마켓플레이스 서비스 초기화
        self.coupang_service = CoupangSearchService()
        self.naver_service = NaverSmartStoreSearchService()
        self.elevenstreet_service = ElevenStreetSearchService()
        self.gmarket_service = GmarketSearchService()
        self.auction_service = AuctionSearchService()
        
        # 마켓플레이스 정보
        self.marketplaces = {
            "coupang": {
                "name": "쿠팡",
                "service": self.coupang_service,
                "product_class": CoupangProduct,
                "description": "국내 최대 이커머스 플랫폼",
                "market_share": 0.35,  # 시장 점유율 추정
                "avg_delivery_days": 1.5,
                "free_shipping_threshold": 30000
            },
            "naver_smartstore": {
                "name": "네이버 스마트스토어",
                "service": self.naver_service,
                "product_class": NaverSmartStoreProduct,
                "description": "네이버 기반 쇼핑몰 플랫폼",
                "market_share": 0.25,
                "avg_delivery_days": 2.0,
                "free_shipping_threshold": 20000
            },
            "elevenstreet": {
                "name": "11번가",
                "service": self.elevenstreet_service,
                "product_class": ElevenStreetProduct,
                "description": "SK텔레콤 계열 이커머스",
                "market_share": 0.15,
                "avg_delivery_days": 2.5,
                "free_shipping_threshold": 25000
            },
            "gmarket": {
                "name": "G마켓",
                "service": self.gmarket_service,
                "product_class": GmarketProduct,
                "description": "eBay Korea 계열 이커머스",
                "market_share": 0.12,
                "avg_delivery_days": 3.0,
                "free_shipping_threshold": 30000
            },
            "auction": {
                "name": "옥션",
                "service": self.auction_service,
                "product_class": AuctionProduct,
                "description": "eBay Korea 계열 경매/이커머스",
                "market_share": 0.08,
                "avg_delivery_days": 3.5,
                "free_shipping_threshold": 30000
            }
        }
    
    async def search_competitors(self, keyword: str, 
                              marketplaces: Optional[List[str]] = None,
                              max_results_per_marketplace: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """경쟁사 상품 검색 (모든 마켓플레이스)"""
        try:
            logger.info(f"경쟁사 상품 검색 시작: '{keyword}'")
            
            if marketplaces is None:
                marketplaces = list(self.marketplaces.keys())
            
            results = {}
            
            for marketplace_code in marketplaces:
                if marketplace_code not in self.marketplaces:
                    logger.warning(f"지원하지 않는 마켓플레이스: {marketplace_code}")
                    continue
                
                marketplace_info = self.marketplaces[marketplace_code]
                marketplace_name = marketplace_info["name"]
                
                logger.info(f"{marketplace_name} 검색 시작...")
                
                try:
                    # 마켓플레이스별 검색 실행
                    products = await self._search_marketplace(
                        marketplace_code, keyword, max_results_per_marketplace
                    )
                    
                    results[marketplace_code] = products
                    logger.info(f"{marketplace_name} 검색 완료: {len(products)}개 상품")
                    
                except Exception as e:
                    self.error_handler.log_error(e, f"{marketplace_name} 검색 실패")
                    results[marketplace_code] = []
                    logger.error(f"{marketplace_name} 검색 실패: {e}")
                
                # API 호출 간격 조절
                await asyncio.sleep(1.0)
            
            total_products = sum(len(products) for products in results.values())
            logger.info(f"경쟁사 상품 검색 완료: 총 {total_products}개 상품")
            
            return results
            
        except Exception as e:
            self.error_handler.log_error(e, f"경쟁사 상품 검색 실패: {keyword}")
            return {}
    
    async def _search_marketplace(self, marketplace_code: str, 
                                keyword: str, max_results: int) -> List[Dict[str, Any]]:
        """개별 마켓플레이스 검색"""
        try:
            marketplace_info = self.marketplaces[marketplace_code]
            service = marketplace_info["service"]
            product_class = marketplace_info["product_class"]
            
            # 마켓플레이스별 검색 실행
            if marketplace_code == "coupang":
                products = await service.search_products(keyword)
            elif marketplace_code == "naver_smartstore":
                products = await service.search_products(keyword)
            elif marketplace_code == "elevenstreet":
                products = await service.search_products(keyword)
            elif marketplace_code == "gmarket":
                products = await service.search_products(keyword)
            elif marketplace_code == "auction":
                products = await service.search_products(keyword)
            else:
                logger.warning(f"지원하지 않는 마켓플레이스: {marketplace_code}")
                return []
            
            # 결과를 딕셔너리로 변환하고 마켓플레이스 정보 추가
            result_products = []
            for product in products[:max_results]:  # 결과 수 제한
                if isinstance(product, product_class):
                    product_dict = product.__dict__
                else:
                    product_dict = product
                
                # 마켓플레이스 메타데이터 추가
                product_dict.update({
                    "marketplace_code": marketplace_code,
                    "marketplace_name": marketplace_info["name"],
                    "market_share": marketplace_info["market_share"],
                    "avg_delivery_days": marketplace_info["avg_delivery_days"],
                    "free_shipping_threshold": marketplace_info["free_shipping_threshold"],
                    "collected_at": datetime.utcnow().isoformat()
                })
                
                result_products.append(product_dict)
            
            return result_products
            
        except Exception as e:
            self.error_handler.log_error(e, f"{marketplace_code} 마켓플레이스 검색 실패")
            return []
    
    async def analyze_price_competition(self, keyword: str, 
                                     our_price: float,
                                     marketplaces: Optional[List[str]] = None) -> Dict[str, Any]:
        """가격 경쟁 분석"""
        try:
            logger.info(f"가격 경쟁 분석 시작: '{keyword}' (우리 가격: {our_price:,.0f}원)")
            
            # 경쟁사 상품 검색
            competitor_data = await self.search_competitors(keyword, marketplaces)
            
            if not competitor_data:
                return {
                    "keyword": keyword,
                    "our_price": our_price,
                    "competitor_count": 0,
                    "analysis": "경쟁사 데이터를 찾을 수 없습니다."
                }
            
            # 가격 분석
            all_prices = []
            marketplace_stats = {}
            
            for marketplace_code, products in competitor_data.items():
                if not products:
                    continue
                
                marketplace_name = self.marketplaces[marketplace_code]["name"]
                prices = [p.get("price", 0) for p in products if p.get("price", 0) > 0]
                
                if prices:
                    marketplace_stats[marketplace_code] = {
                        "name": marketplace_name,
                        "product_count": len(products),
                        "avg_price": sum(prices) / len(prices),
                        "min_price": min(prices),
                        "max_price": max(prices),
                        "prices": prices
                    }
                    all_prices.extend(prices)
            
            if not all_prices:
                return {
                    "keyword": keyword,
                    "our_price": our_price,
                    "competitor_count": 0,
                    "analysis": "유효한 가격 데이터를 찾을 수 없습니다."
                }
            
            # 전체 통계 계산
            avg_competitor_price = sum(all_prices) / len(all_prices)
            min_competitor_price = min(all_prices)
            max_competitor_price = max(all_prices)
            
            # 경쟁력 분석
            price_position = self._analyze_price_position(our_price, all_prices)
            competitiveness = self._calculate_competitiveness(our_price, avg_competitor_price)
            
            analysis_result = {
                "keyword": keyword,
                "our_price": our_price,
                "competitor_count": len(all_prices),
                "marketplace_stats": marketplace_stats,
                "overall_stats": {
                    "avg_competitor_price": avg_competitor_price,
                    "min_competitor_price": min_competitor_price,
                    "max_competitor_price": max_competitor_price,
                    "price_range": max_competitor_price - min_competitor_price
                },
                "competitiveness": competitiveness,
                "price_position": price_position,
                "recommendations": self._generate_price_recommendations(
                    our_price, avg_competitor_price, min_competitor_price, competitiveness
                ),
                "collected_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"가격 경쟁 분석 완료: {len(all_prices)}개 경쟁사 상품 분석")
            
            return analysis_result
            
        except Exception as e:
            self.error_handler.log_error(e, f"가격 경쟁 분석 실패: {keyword}")
            return {}
    
    def _analyze_price_position(self, our_price: float, competitor_prices: List[float]) -> Dict[str, Any]:
        """가격 포지션 분석"""
        try:
            sorted_prices = sorted(competitor_prices)
            total_count = len(sorted_prices)
            
            # 우리 가격보다 저렴한 상품 수
            cheaper_count = sum(1 for price in sorted_prices if price < our_price)
            # 우리 가격보다 비싼 상품 수
            expensive_count = sum(1 for price in sorted_prices if price > our_price)
            # 같은 가격 상품 수
            same_price_count = sum(1 for price in sorted_prices if price == our_price)
            
            # 가격 순위 계산
            rank = cheaper_count + 1
            
            return {
                "rank": rank,
                "total_competitors": total_count,
                "cheaper_than_us": cheaper_count,
                "more_expensive_than_us": expensive_count,
                "same_price_as_us": same_price_count,
                "percentile": (cheaper_count / total_count) * 100 if total_count > 0 else 0,
                "position": "저가" if rank <= total_count * 0.25 else 
                           "중저가" if rank <= total_count * 0.5 else
                           "중고가" if rank <= total_count * 0.75 else "고가"
            }
            
        except Exception as e:
            self.error_handler.log_error(e, "가격 포지션 분석 실패")
            return {}
    
    def _calculate_competitiveness(self, our_price: float, avg_competitor_price: float) -> Dict[str, Any]:
        """경쟁력 계산"""
        try:
            if avg_competitor_price == 0:
                return {"score": 0, "level": "분석 불가", "description": "경쟁사 평균 가격이 0원입니다."}
            
            # 가격 차이 계산
            price_difference = our_price - avg_competitor_price
            price_difference_percent = (price_difference / avg_competitor_price) * 100
            
            # 경쟁력 점수 계산 (0-100점)
            if price_difference_percent <= -20:
                score = 90
                level = "매우 경쟁력 있음"
                description = "경쟁사 대비 20% 이상 저렴"
            elif price_difference_percent <= -10:
                score = 75
                level = "경쟁력 있음"
                description = "경쟁사 대비 10-20% 저렴"
            elif price_difference_percent <= 0:
                score = 60
                level = "경쟁력 보통"
                description = "경쟁사 평균가와 비슷하거나 저렴"
            elif price_difference_percent <= 10:
                score = 40
                level = "경쟁력 부족"
                description = "경쟁사 대비 10% 이내 비쌈"
            elif price_difference_percent <= 20:
                score = 25
                level = "경쟁력 매우 부족"
                description = "경쟁사 대비 10-20% 비쌈"
            else:
                score = 10
                level = "경쟁력 없음"
                description = "경쟁사 대비 20% 이상 비쌈"
            
            return {
                "score": score,
                "level": level,
                "description": description,
                "price_difference": price_difference,
                "price_difference_percent": price_difference_percent
            }
            
        except Exception as e:
            self.error_handler.log_error(e, "경쟁력 계산 실패")
            return {}
    
    def _generate_price_recommendations(self, our_price: float, 
                                      avg_competitor_price: float,
                                      min_competitor_price: float,
                                      competitiveness: Dict[str, Any]) -> List[str]:
        """가격 추천 생성"""
        try:
            recommendations = []
            
            if competitiveness.get("score", 0) >= 75:
                recommendations.append("현재 가격이 매우 경쟁력 있습니다. 가격 유지 권장")
            elif competitiveness.get("score", 0) >= 60:
                recommendations.append("현재 가격이 경쟁력 있습니다. 가격 유지 또는 소폭 인상 고려")
            elif competitiveness.get("score", 0) >= 40:
                recommendations.append("경쟁력을 높이기 위해 가격 인하 검토 필요")
            else:
                recommendations.append("경쟁력이 부족합니다. 가격 대폭 인하 또는 차별화 전략 필요")
            
            # 구체적인 가격 제안
            if our_price > avg_competitor_price:
                suggested_price = avg_competitor_price * 0.95  # 평균가의 95%
                recommendations.append(f"경쟁력 확보를 위한 제안 가격: {suggested_price:,.0f}원")
            
            if our_price > min_competitor_price * 1.1:
                competitive_price = min_competitor_price * 1.05  # 최저가의 105%
                recommendations.append(f"경쟁력 있는 가격: {competitive_price:,.0f}원")
            
            return recommendations
            
        except Exception as e:
            self.error_handler.log_error(e, "가격 추천 생성 실패")
            return ["가격 추천을 생성할 수 없습니다."]
    
    async def save_competitor_data(self, competitor_data: Dict[str, List[Dict[str, Any]]]) -> int:
        """경쟁사 데이터 저장"""
        try:
            if not competitor_data:
                logger.info("저장할 경쟁사 데이터가 없습니다")
                return 0
            
            total_saved = 0
            
            for marketplace_code, products in competitor_data.items():
                if not products:
                    continue
                
                marketplace_name = self.marketplaces[marketplace_code]["name"]
                logger.info(f"{marketplace_name} 경쟁사 데이터 저장 시작: {len(products)}개")
                
                saved_count = 0
                for product in products:
                    try:
                        # 경쟁사 상품 데이터 저장
                        raw_data = {
                            "marketplace_code": marketplace_code,
                            "marketplace_name": marketplace_name,
                            "product_id": product.get("product_id", ""),
                            "product_name": product.get("name", ""),
                            "price": product.get("price", 0),
                            "original_price": product.get("original_price", 0),
                            "discount_rate": product.get("discount_rate", 0),
                            "seller": product.get("seller", ""),
                            "rating": product.get("rating", 0.0),
                            "review_count": product.get("review_count", 0),
                            "image_url": product.get("image_url", ""),
                            "product_url": product.get("product_url", ""),
                            "category": product.get("category", ""),
                            "brand": product.get("brand", ""),
                            "market_share": product.get("market_share", 0),
                            "avg_delivery_days": product.get("avg_delivery_days", 0),
                            "free_shipping_threshold": product.get("free_shipping_threshold", 0),
                            "collected_at": product.get("collected_at", datetime.utcnow().isoformat()),
                            "raw_data": product
                        }
                        
                        # 데이터베이스에 저장 (competitor_products 테이블)
                        await self.db_service.insert_data("competitor_products", raw_data)
                        saved_count += 1
                        
                    except Exception as e:
                        self.error_handler.log_error(e, f"{marketplace_name} 상품 저장 실패: {product.get('product_id', 'Unknown')}")
                        continue
                
                logger.info(f"{marketplace_name} 경쟁사 데이터 저장 완료: {saved_count}개")
                total_saved += saved_count
            
            logger.info(f"경쟁사 데이터 저장 완료: 총 {total_saved}개")
            return total_saved
            
        except Exception as e:
            self.error_handler.log_error(e, "경쟁사 데이터 저장 실패")
            return 0


async def test_marketplace_competitor_service():
    """마켓플레이스 경쟁사 서비스 테스트"""
    try:
        logger.info("마켓플레이스 경쟁사 서비스 테스트 시작")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 경쟁사 서비스 초기화
        competitor_service = MarketplaceCompetitorService(db_service)
        
        # 테스트 키워드
        test_keywords = ["가방", "노트북", "스마트폰"]
        
        for keyword in test_keywords:
            logger.info(f"\n=== '{keyword}' 경쟁사 분석 ===")
            
            # 경쟁사 상품 검색
            competitor_data = await competitor_service.search_competitors(
                keyword=keyword,
                marketplaces=["coupang", "naver_smartstore"],  # 테스트용으로 2개만
                max_results_per_marketplace=10
            )
            
            # 결과 출력
            for marketplace_code, products in competitor_data.items():
                marketplace_name = competitor_service.marketplaces[marketplace_code]["name"]
                logger.info(f"{marketplace_name}: {len(products)}개 상품")
                
                if products:
                    sample = products[0]
                    logger.info(f"  샘플 상품: {sample.get('name', 'N/A')} - {sample.get('price', 0):,}원")
            
            # 가격 경쟁 분석
            our_price = 50000  # 테스트용 우리 가격
            analysis = await competitor_service.analyze_price_competition(
                keyword=keyword,
                our_price=our_price,
                marketplaces=["coupang", "naver_smartstore"]
            )
            
            if analysis.get("competitor_count", 0) > 0:
                logger.info(f"경쟁사 수: {analysis['competitor_count']}개")
                logger.info(f"평균 경쟁사 가격: {analysis['overall_stats']['avg_competitor_price']:,.0f}원")
                logger.info(f"경쟁력: {analysis['competitiveness']['level']} ({analysis['competitiveness']['score']}점)")
                logger.info(f"가격 포지션: {analysis['price_position']['position']}")
                
                for recommendation in analysis.get("recommendations", []):
                    logger.info(f"추천: {recommendation}")
            
            # 데이터 저장 테스트
            saved_count = await competitor_service.save_competitor_data(competitor_data)
            logger.info(f"저장된 경쟁사 데이터: {saved_count}개")
        
        logger.info("\n마켓플레이스 경쟁사 서비스 테스트 완료")
        
    except Exception as e:
        logger.error(f"테스트 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_marketplace_competitor_service())
