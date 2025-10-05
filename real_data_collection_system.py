"""
실제 데이터 수집 및 모델 재훈련 시스템

경쟁사 데이터를 실제로 수집하고 AI 모델을 재훈련하는 시스템입니다.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
import pandas as pd
import numpy as np

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.database_service import DatabaseService
from src.services.unified_marketplace_search_service import UnifiedMarketplaceSearchService
from src.services.ai_price_prediction_service import AIPricePredictionService
from src.services.price_comparison_service import PriceComparisonService
from src.services.competitor_data_scheduler import CompetitorDataScheduler


class RealDataCollectionSystem:
    """실제 데이터 수집 및 모델 재훈련 시스템"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.unified_service = UnifiedMarketplaceSearchService()
        self.ai_service = AIPricePredictionService()
        self.price_comparison_service = PriceComparisonService()
        self.scheduler = CompetitorDataScheduler()
        
        # 수집할 키워드 목록
        self.collection_keywords = [
            "스마트폰", "노트북", "태블릿", "이어폰", "스마트워치",
            "게이밍마우스", "키보드", "모니터", "웹캠", "스피커",
            "충전기", "케이스", "보호필름", "거치대", "블루투스"
        ]
        
        # 수집할 카테고리
        self.categories = [
            "electronics", "computers", "mobile", "audio", "gaming"
        ]
    
    async def collect_competitor_data(self) -> Dict[str, Any]:
        """경쟁사 데이터 수집"""
        try:
            logger.info("🚀 경쟁사 데이터 수집 시작")
            
            collection_results = {
                "total_products": 0,
                "platforms": {},
                "categories": {},
                "collection_time": datetime.now().isoformat(),
                "errors": []
            }
            
            # 각 키워드별로 데이터 수집
            for keyword in self.collection_keywords:
                logger.info(f"📦 '{keyword}' 키워드 데이터 수집 중...")
                
                try:
                    # 통합 검색 실행
                    search_results = await self.unified_service.search_all_platforms(
                        keyword=keyword,
                        page=1
                    )
                    
                    keyword_total = 0
                    for platform, products in search_results.items():
                        if products:
                            keyword_total += len(products)
                            
                            # 플랫폼별 통계
                            if platform not in collection_results["platforms"]:
                                collection_results["platforms"][platform] = 0
                            collection_results["platforms"][platform] += len(products)
                            
                            # 데이터베이스에 저장 시도
                            await self._save_products_to_database(products, keyword)
                    
                    collection_results["total_products"] += keyword_total
                    logger.info(f"✅ '{keyword}': {keyword_total}개 상품 수집 완료")
                    
                    # 요청 간격 조절 (Rate Limiting)
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    error_msg = f"키워드 '{keyword}' 수집 실패: {str(e)}"
                    logger.error(error_msg)
                    collection_results["errors"].append(error_msg)
                    continue
            
            logger.info(f"🎉 데이터 수집 완료: 총 {collection_results['total_products']}개 상품")
            return collection_results
            
        except Exception as e:
            logger.error(f"데이터 수집 시스템 오류: {e}")
            return {"error": str(e)}
    
    async def _save_products_to_database(self, products: List[Any], keyword: str) -> bool:
        """상품 데이터를 데이터베이스에 저장"""
        try:
            # 기존 테이블 활용 (normalized_products)
            for product in products:
                product_data = {
                    "name": product.name,
                    "price": product.price,
                    "original_price": product.original_price,
                    "platform": product.platform,
                    "seller": product.seller,
                    "product_url": product.product_url,
                    "image_url": product.image_url,
                    "rating": product.rating,
                    "review_count": product.review_count,
                    "shipping_info": product.shipping_info,
                    "category": self._categorize_product(product.name),
                    "collection_keyword": keyword,
                    "collected_at": datetime.now().isoformat(),
                    "is_competitor": True
                }
                
                # 데이터베이스에 저장 시도
                await self.db_service.insert_data("normalized_products", product_data)
            
            return True
            
        except Exception as e:
            logger.warning(f"상품 저장 실패: {e}")
            return False
    
    def _categorize_product(self, product_name: str) -> str:
        """상품명을 기반으로 카테고리 분류"""
        product_name_lower = product_name.lower()
        
        if any(word in product_name_lower for word in ["스마트폰", "폰", "phone", "galaxy", "iphone"]):
            return "mobile"
        elif any(word in product_name_lower for word in ["노트북", "laptop", "macbook", "컴퓨터"]):
            return "computers"
        elif any(word in product_name_lower for word in ["이어폰", "헤드폰", "earphone", "headphone"]):
            return "audio"
        elif any(word in product_name_lower for word in ["마우스", "키보드", "mouse", "keyboard"]):
            return "gaming"
        else:
            return "electronics"
    
    async def train_ai_models_with_real_data(self) -> Dict[str, Any]:
        """실제 데이터로 AI 모델 재훈련"""
        try:
            logger.info("🤖 실제 데이터로 AI 모델 재훈련 시작")
            
            # 실제 데이터 조회
            real_data = await self.db_service.select_data(
                "normalized_products",
                {"is_competitor": True},
                limit=1000  # 최대 1000개 샘플
            )
            
            if not real_data:
                logger.warning("⚠️ 훈련할 실제 데이터가 없습니다")
                return {"error": "훈련 데이터 없음"}
            
            logger.info(f"📊 훈련 데이터: {len(real_data)}개 샘플")
            
            # 데이터를 DataFrame으로 변환
            df = pd.DataFrame(real_data)
            
            # 특성 엔지니어링
            df = self._engineer_features_for_training(df)
            
            # 모델 훈련 실행
            model_scores = await self.ai_service.train_models_with_dataframe(df)
            
            logger.info("✅ AI 모델 재훈련 완료")
            return {
                "training_samples": len(df),
                "model_scores": model_scores,
                "trained_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"AI 모델 재훈련 실패: {e}")
            return {"error": str(e)}
    
    def _engineer_features_for_training(self, df: pd.DataFrame) -> pd.DataFrame:
        """훈련용 특성 엔지니어링"""
        try:
            # 기본 특성
            df['price_numeric'] = pd.to_numeric(df['price'], errors='coerce')
            df['original_price_numeric'] = pd.to_numeric(df.get('original_price', 0), errors='coerce')
            
            # 할인율 계산
            df['discount_rate'] = np.where(
                df['original_price_numeric'] > 0,
                (df['original_price_numeric'] - df['price_numeric']) / df['original_price_numeric'] * 100,
                0
            )
            
            # 플랫폼별 특성
            platforms = ['coupang', 'naver', '11st', 'gmarket', 'auction']
            for platform in platforms:
                df[f'platform_{platform}'] = (df['platform'] == platform).astype(int)
            
            # 카테고리 특성
            if 'category' in df.columns:
                df['category_encoded'] = df['category'].astype('category').cat.codes
            
            # 리뷰 점수 특성
            if 'rating' in df.columns:
                df['rating_numeric'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)
            
            # 리뷰 수 특성
            if 'review_count' in df.columns:
                df['review_count_numeric'] = pd.to_numeric(df['review_count'], errors='coerce').fillna(0)
            
            # 결측값 처리
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].median())
            
            return df
            
        except Exception as e:
            logger.error(f"특성 엔지니어링 실패: {e}")
            return df
    
    async def analyze_market_trends(self) -> Dict[str, Any]:
        """시장 트렌드 분석"""
        try:
            logger.info("📈 시장 트렌드 분석 시작")
            
            # 최근 수집된 데이터로 트렌드 분석
            recent_data = await self.db_service.select_data(
                "normalized_products",
                {"is_competitor": True},
                limit=500
            )
            
            if not recent_data:
                return {"error": "분석할 데이터 없음"}
            
            df = pd.DataFrame(recent_data)
            
            # 카테고리별 분석
            category_analysis = {}
            for category in df['category'].unique():
                category_data = df[df['category'] == category]
                category_analysis[category] = {
                    "product_count": len(category_data),
                    "avg_price": category_data['price'].mean(),
                    "price_range": {
                        "min": category_data['price'].min(),
                        "max": category_data['price'].max()
                    },
                    "platforms": category_data['platform'].value_counts().to_dict()
                }
            
            # 플랫폼별 분석
            platform_analysis = {}
            for platform in df['platform'].unique():
                platform_data = df[df['platform'] == platform]
                platform_analysis[platform] = {
                    "product_count": len(platform_data),
                    "avg_price": platform_data['price'].mean(),
                    "avg_rating": platform_data['rating'].mean() if 'rating' in platform_data.columns else 0
                }
            
            logger.info("✅ 시장 트렌드 분석 완료")
            return {
                "total_products_analyzed": len(df),
                "category_analysis": category_analysis,
                "platform_analysis": platform_analysis,
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"시장 트렌드 분석 실패: {e}")
            return {"error": str(e)}
    
    async def generate_price_recommendations(self) -> Dict[str, Any]:
        """가격 추천 생성"""
        try:
            logger.info("💰 가격 추천 생성 시작")
            
            # 최근 수집된 데이터로 가격 추천
            recent_products = await self.db_service.select_data(
                "normalized_products",
                {"is_competitor": True},
                limit=100
            )
            
            recommendations = []
            
            for product in recent_products[:10]:  # 상위 10개만 분석
                try:
                    # AI 가격 예측
                    predictions = await self.ai_service.predict_price({
                        "platform": product.get("platform", "coupang"),
                        "category": product.get("category", "electronics"),
                        "price": product.get("price", 0),
                        "original_price": product.get("original_price", 0),
                        "rating": product.get("rating", 0),
                        "review_count": product.get("review_count", 0)
                    })
                    
                    if predictions:
                        best_prediction = predictions[0]
                        recommendations.append({
                            "product_name": product.get("name", "Unknown"),
                            "current_price": product.get("price", 0),
                            "recommended_price": best_prediction.predicted_price,
                            "confidence": best_prediction.confidence_score,
                            "strategy": "AI_predicted",
                            "platform": product.get("platform", "unknown")
                        })
                
                except Exception as e:
                    logger.warning(f"상품 '{product.get('name', 'Unknown')}' 가격 추천 실패: {e}")
                    continue
            
            logger.info(f"✅ 가격 추천 생성 완료: {len(recommendations)}개")
            return {
                "recommendations": recommendations,
                "generated_at": datetime.now().isoformat(),
                "total_recommendations": len(recommendations)
            }
            
        except Exception as e:
            logger.error(f"가격 추천 생성 실패: {e}")
            return {"error": str(e)}
    
    async def run_complete_analysis(self) -> Dict[str, Any]:
        """완전한 분석 실행"""
        try:
            logger.info("🎯 완전한 데이터 수집 및 분석 시작")
            
            results = {
                "collection": {},
                "training": {},
                "trend_analysis": {},
                "price_recommendations": {},
                "summary": {}
            }
            
            # 1. 데이터 수집
            logger.info("1️⃣ 경쟁사 데이터 수집")
            collection_result = await self.collect_competitor_data()
            results["collection"] = collection_result
            
            # 2. AI 모델 재훈련
            logger.info("2️⃣ AI 모델 재훈련")
            training_result = await self.train_ai_models_with_real_data()
            results["training"] = training_result
            
            # 3. 시장 트렌드 분석
            logger.info("3️⃣ 시장 트렌드 분석")
            trend_result = await self.analyze_market_trends()
            results["trend_analysis"] = trend_result
            
            # 4. 가격 추천 생성
            logger.info("4️⃣ 가격 추천 생성")
            recommendation_result = await self.generate_price_recommendations()
            results["price_recommendations"] = recommendation_result
            
            # 5. 요약 생성
            results["summary"] = {
                "total_products_collected": collection_result.get("total_products", 0),
                "platforms_monitored": len(collection_result.get("platforms", {})),
                "training_samples": training_result.get("training_samples", 0),
                "recommendations_generated": len(recommendation_result.get("recommendations", [])),
                "analysis_completed_at": datetime.now().isoformat(),
                "status": "success"
            }
            
            logger.info("🎉 완전한 분석 완료!")
            return results
            
        except Exception as e:
            logger.error(f"완전한 분석 실패: {e}")
            return {"error": str(e), "status": "failed"}


async def main():
    """메인 함수"""
    system = RealDataCollectionSystem()
    
    logger.info("🚀 실제 데이터 수집 및 모델 재훈련 시스템 시작")
    
    # 완전한 분석 실행
    results = await system.run_complete_analysis()
    
    # 결과 출력
    logger.info("\n📊 분석 결과 요약:")
    logger.info("=" * 50)
    
    if "error" in results:
        logger.error(f"❌ 분석 실패: {results['error']}")
        return
    
    summary = results.get("summary", {})
    logger.info(f"📦 수집된 상품 수: {summary.get('total_products_collected', 0)}개")
    logger.info(f"🏪 모니터링 플랫폼: {summary.get('platforms_monitored', 0)}개")
    logger.info(f"🤖 훈련 샘플 수: {summary.get('training_samples', 0)}개")
    logger.info(f"💰 가격 추천 수: {summary.get('recommendations_generated', 0)}개")
    logger.info(f"✅ 분석 상태: {summary.get('status', 'unknown')}")
    
    logger.info("\n🎯 다음 단계:")
    logger.info("  1. 수집된 데이터 검토 및 품질 확인")
    logger.info("  2. AI 모델 성능 평가 및 개선")
    logger.info("  3. 가격 추천 시스템 운영 테스트")
    logger.info("  4. 자동화된 데이터 수집 스케줄러 설정")


if __name__ == "__main__":
    asyncio.run(main())
