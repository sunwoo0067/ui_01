"""
자동 가격 비교 시스템
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timezone, timedelta
import asyncio
import json
from loguru import logger

from src.config.settings import settings
from src.utils.error_handler import ErrorHandler, BaseAPIError, DatabaseError
from src.services.database_service import DatabaseService
from src.services.coupang_search_service import CoupangSearchService
from src.services.naver_smartstore_search_service import NaverSmartStoreSearchService


class PriceComparisonResult:
    """가격 비교 결과 클래스"""
    
    def __init__(self, data: Dict[str, Any]):
        self.keyword = data.get('keyword', '')
        self.our_product_id = data.get('our_product_id', '')
        self.our_price = data.get('our_price', 0)
        self.competitor_products = data.get('competitor_products', [])
        self.price_analysis = data.get('price_analysis', {})
        self.recommendations = data.get('recommendations', [])
        self.analyzed_at = data.get('analyzed_at', datetime.now(timezone.utc).isoformat())


class PriceComparisonService:
    """자동 가격 비교 서비스"""

    def __init__(self):
        self.settings = settings
        self.error_handler = ErrorHandler()
        self.db_service = DatabaseService()
        self.coupang_service = CoupangSearchService()
        self.naver_service = NaverSmartStoreSearchService()
        
        # 테이블명
        self.competitor_products_table = "competitor_products"
        self.price_history_table = "price_history"
        self.competitor_analysis_table = "competitor_analysis"

    async def compare_prices(self, keyword: str, 
                           our_product_id: str, 
                           our_price: int,
                           platforms: List[str] = None) -> PriceComparisonResult:
        """
        가격 비교 분석
        
        Args:
            keyword: 비교할 상품 키워드
            our_product_id: 우리 상품 ID
            our_price: 우리 상품 가격
            platforms: 비교할 플랫폼 목록
            
        Returns:
            PriceComparisonResult: 가격 비교 결과
        """
        try:
            logger.info(f"가격 비교 분석 시작: {keyword}, 우리 가격: {our_price}원")
            
            if platforms is None:
                platforms = ['coupang', 'naver_smartstore']
            
            # 1. 경쟁사 상품 데이터 수집
            competitor_products = await self._collect_competitor_data(keyword, platforms)
            
            # 2. 가격 분석 수행
            price_analysis = await self._analyze_prices(our_price, competitor_products)
            
            # 3. 추천사항 생성
            recommendations = await self._generate_recommendations(our_price, price_analysis)
            
            # 4. 결과 구성
            result_data = {
                'keyword': keyword,
                'our_product_id': our_product_id,
                'our_price': our_price,
                'competitor_products': competitor_products,
                'price_analysis': price_analysis,
                'recommendations': recommendations,
                'analyzed_at': datetime.now(timezone.utc).isoformat()
            }
            
            # 5. 분석 결과 저장
            await self._save_comparison_result(result_data)
            
            logger.info(f"가격 비교 분석 완료: {keyword}")
            
            return PriceComparisonResult(result_data)
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "가격 비교 분석 실패",
                'keyword': keyword,
                'our_product_id': our_product_id
            })
            return PriceComparisonResult({
                'keyword': keyword,
                'our_product_id': our_product_id,
                'our_price': our_price,
                'competitor_products': [],
                'price_analysis': {},
                'recommendations': [],
                'analyzed_at': datetime.now(timezone.utc).isoformat()
            })

    async def monitor_price_changes(self, keyword: str, 
                                  alert_threshold: float = 10.0) -> List[Dict[str, Any]]:
        """
        가격 변동 모니터링
        
        Args:
            keyword: 모니터링 키워드
            alert_threshold: 알림 임계값 (%)
            
        Returns:
            List[Dict]: 가격 변동 알림 목록
        """
        try:
            logger.info(f"가격 변동 모니터링 시작: {keyword}")
            
            # 최근 가격 변동 조회
            recent_changes = await self.db_service.select_data(
                self.price_history_table,
                {
                    "timestamp__gte": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
                }
            )
            
            alerts = []
            
            if recent_changes:
                for change in recent_changes:
                    # 임계값 초과 변동 확인
                    if abs(change['price_change_rate']) >= alert_threshold:
                        alert = {
                            'product_id': change['product_id'],
                            'platform': change['platform'],
                            'old_price': change['old_price'],
                            'new_price': change['new_price'],
                            'price_change': change['price_change'],
                            'price_change_rate': change['price_change_rate'],
                            'timestamp': change['timestamp'],
                            'alert_type': 'price_change',
                            'severity': 'high' if abs(change['price_change_rate']) >= 20 else 'medium'
                        }
                        alerts.append(alert)
            
            logger.info(f"가격 변동 모니터링 완료: {len(alerts)}개 알림")
            
            return alerts
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "가격 변동 모니터링 실패",
                'keyword': keyword
            })
            return []

    async def get_market_insights(self, keyword: str, days: int = 7) -> Dict[str, Any]:
        """
        시장 인사이트 분석
        
        Args:
            keyword: 분석 키워드
            days: 분석 기간 (일)
            
        Returns:
            Dict: 시장 인사이트
        """
        try:
            logger.info(f"시장 인사이트 분석 시작: {keyword}")
            
            # 분석 기간 설정
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # 경쟁사 상품 데이터 조회
            competitor_products = await self.db_service.select_data(
                self.competitor_products_table,
                {
                    "search_keyword": keyword,
                    "collected_at__gte": start_date.isoformat(),
                    "is_active": True
                }
            )
            
            if not competitor_products:
                return {
                    "keyword": keyword,
                    "analysis_period": f"{days}일",
                    "insights": {}
                }
            
            # 인사이트 분석
            insights = {
                "market_overview": await self._analyze_market_overview(competitor_products),
                "price_trends": await self._analyze_price_trends(competitor_products, days),
                "competitor_analysis": await self._analyze_competitors(competitor_products),
                "opportunities": await self._identify_opportunities(competitor_products)
            }
            
            logger.info(f"시장 인사이트 분석 완료: {keyword}")
            
            return {
                "keyword": keyword,
                "analysis_period": f"{days}일",
                "total_products": len(competitor_products),
                "insights": insights
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "시장 인사이트 분석 실패",
                'keyword': keyword
            })
            return {}

    async def _collect_competitor_data(self, keyword: str, platforms: List[str]) -> List[Dict[str, Any]]:
        """경쟁사 데이터 수집"""
        try:
            competitor_products = []
            
            # 기존 데이터 조회
            existing_products = await self.db_service.select_data(
                self.competitor_products_table,
                {
                    "search_keyword": keyword,
                    "platform__in": platforms,
                    "is_active": True
                }
            )
            
            if existing_products:
                competitor_products.extend(existing_products)
            
            # 최신 데이터 수집 (필요시)
            for platform in platforms:
                if platform == 'coupang':
                    products = await self.coupang_service.search_products(keyword, limit=20)
                    if products:
                        await self.coupang_service.save_competitor_products(products, keyword)
                elif platform == 'naver_smartstore':
                    products = await self.naver_service.search_products(keyword, limit=20)
                    if products:
                        await self.naver_service.save_competitor_products(products, keyword)
            
            return competitor_products
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "경쟁사 데이터 수집 실패",
                'keyword': keyword
            })
            return []

    async def _analyze_prices(self, our_price: int, competitor_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """가격 분석"""
        try:
            if not competitor_products:
                return {}
            
            # 가격 데이터 추출
            prices = [p['price'] for p in competitor_products if p['price'] > 0]
            
            if not prices:
                return {}
            
            # 기본 통계
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            median_price = sorted(prices)[len(prices) // 2]
            
            # 우리 가격과 비교
            price_position = self._calculate_price_position(our_price, prices)
            
            # 가격대별 분포
            price_distribution = self._calculate_price_distribution(prices)
            
            return {
                "market_statistics": {
                    "min_price": min_price,
                    "max_price": max_price,
                    "avg_price": round(avg_price, 2),
                    "median_price": median_price,
                    "total_products": len(prices)
                },
                "our_price_analysis": {
                    "our_price": our_price,
                    "price_position": price_position,
                    "vs_min_price": our_price - min_price,
                    "vs_max_price": our_price - max_price,
                    "vs_avg_price": our_price - avg_price,
                    "vs_median_price": our_price - median_price
                },
                "price_distribution": price_distribution
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "가격 분석 실패"
            })
            return {}

    def _calculate_price_position(self, our_price: int, competitor_prices: List[int]) -> str:
        """우리 가격의 시장 내 위치 계산"""
        sorted_prices = sorted(competitor_prices)
        our_position = 0
        
        for price in sorted_prices:
            if our_price >= price:
                our_position += 1
            else:
                break
        
        position_percentage = (our_position / len(sorted_prices)) * 100
        
        if position_percentage <= 25:
            return "저가"
        elif position_percentage <= 50:
            return "중저가"
        elif position_percentage <= 75:
            return "중고가"
        else:
            return "고가"

    def _calculate_price_distribution(self, prices: List[int]) -> Dict[str, int]:
        """가격대별 분포 계산"""
        if not prices:
            return {}
        
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price
        
        if price_range == 0:
            return {"single_price": len(prices)}
        
        # 4개 구간으로 나누기
        interval_size = price_range / 4
        
        distribution = {
            "low": 0,      # 하위 25%
            "medium_low": 0,  # 25-50%
            "medium_high": 0, # 50-75%
            "high": 0      # 상위 25%
        }
        
        for price in prices:
            if price <= min_price + interval_size:
                distribution["low"] += 1
            elif price <= min_price + interval_size * 2:
                distribution["medium_low"] += 1
            elif price <= min_price + interval_size * 3:
                distribution["medium_high"] += 1
            else:
                distribution["high"] += 1
        
        return distribution

    async def _generate_recommendations(self, our_price: int, price_analysis: Dict[str, Any]) -> List[str]:
        """가격 조정 추천사항 생성"""
        try:
            recommendations = []
            
            if not price_analysis or 'our_price_analysis' not in price_analysis:
                return ["가격 분석 데이터가 부족합니다."]
            
            our_analysis = price_analysis['our_price_analysis']
            market_stats = price_analysis.get('market_statistics', {})
            
            # 평균 가격 대비 분석
            avg_price = market_stats.get('avg_price', 0)
            if avg_price > 0:
                price_diff_percentage = ((our_price - avg_price) / avg_price) * 100
                
                if price_diff_percentage > 20:
                    recommendations.append(f"현재 가격이 시장 평균보다 {price_diff_percentage:.1f}% 높습니다. 가격 인하를 고려해보세요.")
                elif price_diff_percentage < -20:
                    recommendations.append(f"현재 가격이 시장 평균보다 {abs(price_diff_percentage):.1f}% 낮습니다. 가격 인상을 고려해보세요.")
                else:
                    recommendations.append("현재 가격이 시장 평균과 유사합니다. 경쟁력 있는 가격입니다.")
            
            # 최저가 대비 분석
            min_price = market_stats.get('min_price', 0)
            if min_price > 0 and our_price > min_price:
                min_price_diff = our_price - min_price
                recommendations.append(f"최저가 대비 {min_price_diff:,}원 높습니다. 차별화 포인트를 강조하세요.")
            
            # 가격 포지션 분석
            price_position = our_analysis.get('price_position', '')
            if price_position == '고가':
                recommendations.append("고가 포지션입니다. 프리미엄 브랜드 이미지와 품질을 강조하세요.")
            elif price_position == '저가':
                recommendations.append("저가 포지션입니다. 가격 경쟁력을 강조하세요.")
            
            return recommendations
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "추천사항 생성 실패"
            })
            return ["추천사항을 생성할 수 없습니다."]

    async def _save_comparison_result(self, result_data: Dict[str, Any]) -> None:
        """가격 비교 결과 저장"""
        try:
            analysis_data = {
                "analysis_type": "price_comparison",
                "target_keyword": result_data['keyword'],
                "platform": "all",
                "analysis_data": result_data,
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db_service.insert_data(self.competitor_analysis_table, analysis_data)
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "가격 비교 결과 저장 실패"
            })

    async def _analyze_market_overview(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """시장 개요 분석"""
        try:
            platforms = {}
            categories = {}
            
            for product in products:
                platform = product.get('platform', 'unknown')
                category = product.get('category', 'unknown')
                
                platforms[platform] = platforms.get(platform, 0) + 1
                categories[category] = categories.get(category, 0) + 1
            
            return {
                "total_products": len(products),
                "platform_distribution": platforms,
                "category_distribution": categories
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "시장 개요 분석 실패"
            })
            return {}

    async def _analyze_price_trends(self, products: List[Dict[str, Any]], days: int) -> Dict[str, Any]:
        """가격 동향 분석"""
        try:
            # 최근 가격 변동 조회
            recent_changes = await self.db_service.select_data(
                self.price_history_table,
                {
                    "timestamp__gte": (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
                }
            )
            
            if not recent_changes:
                return {"trend": "stable", "changes_count": 0}
            
            # 가격 변동 분석
            price_increases = len([c for c in recent_changes if c['price_change'] > 0])
            price_decreases = len([c for c in recent_changes if c['price_change'] < 0])
            
            if price_increases > price_decreases * 1.5:
                trend = "increasing"
            elif price_decreases > price_increases * 1.5:
                trend = "decreasing"
            else:
                trend = "stable"
            
            return {
                "trend": trend,
                "changes_count": len(recent_changes),
                "price_increases": price_increases,
                "price_decreases": price_decreases
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "가격 동향 분석 실패"
            })
            return {}

    async def _analyze_competitors(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """경쟁사 분석"""
        try:
            sellers = {}
            ratings = []
            
            for product in products:
                seller = product.get('seller', 'unknown')
                rating = product.get('rating', 0)
                
                sellers[seller] = sellers.get(seller, 0) + 1
                if rating > 0:
                    ratings.append(rating)
            
            # 상위 판매자
            top_sellers = sorted(sellers.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # 평점 분석
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            return {
                "total_sellers": len(sellers),
                "top_sellers": top_sellers,
                "avg_rating": round(avg_rating, 2),
                "high_rated_products": len([r for r in ratings if r >= 4.0])
            }
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "경쟁사 분석 실패"
            })
            return {}

    async def _identify_opportunities(self, products: List[Dict[str, Any]]) -> List[str]:
        """기회 요소 식별"""
        try:
            opportunities = []
            
            # 저평가 상품 찾기
            low_rated_products = [p for p in products if p.get('rating', 0) < 3.0 and p.get('price', 0) > 0]
            if low_rated_products:
                opportunities.append(f"저평가 상품 {len(low_rated_products)}개 발견 - 품질 개선 기회")
            
            # 고가 상품 찾기
            prices = [p['price'] for p in products if p.get('price', 0) > 0]
            if prices:
                avg_price = sum(prices) / len(prices)
                high_price_products = [p for p in products if p.get('price', 0) > avg_price * 1.5]
                if high_price_products:
                    opportunities.append(f"고가 상품 {len(high_price_products)}개 발견 - 프리미엄 시장 기회")
            
            # 리뷰 부족 상품 찾기
            low_review_products = [p for p in products if p.get('review_count', 0) < 10]
            if low_review_products:
                opportunities.append(f"리뷰 부족 상품 {len(low_review_products)}개 발견 - 마케팅 기회")
            
            return opportunities
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "기회 요소 식별 실패"
            })
            return []


# 전역 인스턴스
price_comparison_service = PriceComparisonService()
