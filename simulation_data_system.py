"""
시뮬레이션 데이터 기반 모델 재훈련 시스템

웹 스크래핑이 차단된 상황에서 시뮬레이션 데이터를 생성하여 
AI 모델을 재훈련하고 시스템을 검증합니다.
"""

import asyncio
import sys
import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.database_service import DatabaseService
from src.services.ai_price_prediction_service import AIPricePredictionService


class SimulationDataSystem:
    """시뮬레이션 데이터 기반 모델 재훈련 시스템"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.ai_service = AIPricePredictionService()
        
        # 시뮬레이션 데이터 생성 설정
        self.platforms = ['coupang', 'naver', '11st', 'gmarket', 'auction']
        self.categories = ['electronics', 'mobile', 'computers', 'audio', 'gaming']
        self.brands = ['Samsung', 'Apple', 'LG', 'Sony', 'Xiaomi', 'Huawei', 'OnePlus']
        
        # 가격 범위 설정 (카테고리별)
        self.price_ranges = {
            'mobile': (50000, 1500000),
            'computers': (300000, 3000000),
            'electronics': (10000, 500000),
            'audio': (20000, 500000),
            'gaming': (50000, 800000)
        }
    
    def generate_simulation_products(self, count: int = 1000) -> List[Dict[str, Any]]:
        """시뮬레이션 상품 데이터 생성"""
        logger.info(f"🎲 {count}개의 시뮬레이션 상품 데이터 생성 중...")
        
        products = []
        
        for i in range(count):
            # 기본 정보
            category = random.choice(self.categories)
            platform = random.choice(self.platforms)
            brand = random.choice(self.brands)
            
            # 가격 설정
            min_price, max_price = self.price_ranges[category]
            original_price = random.randint(min_price, max_price)
            
            # 할인율 설정 (0-50%)
            discount_rate = random.uniform(0, 0.5)
            current_price = int(original_price * (1 - discount_rate))
            
            # 리뷰 점수 및 개수
            rating = round(random.uniform(3.0, 5.0), 1)
            review_count = random.randint(10, 10000)
            
            # 상품명 생성
            product_name = f"{brand} {self._generate_product_name(category)}"
            
            product = {
                "name": product_name,
                "price": current_price,
                "original_price": original_price,
                "discount_rate": int(discount_rate * 100),
                "platform": platform,
                "seller": f"{platform}_seller_{random.randint(1, 100)}",
                "product_url": f"https://{platform}.com/product/{i+1}",
                "image_url": f"https://example.com/images/product_{i+1}.jpg",
                "rating": rating,
                "review_count": review_count,
                "shipping_info": random.choice(["무료배송", "착불", "당일배송"]),
                "category": category,
                "brand": brand,
                "collection_keyword": random.choice(["스마트폰", "노트북", "이어폰", "게이밍", "전자제품"]),
                "collected_at": datetime.now().isoformat(),
                "is_competitor": True,
                "is_simulation": True,
                "simulation_source": "random_generator",
                "data_quality_score": round(random.uniform(0.7, 1.0), 2),
                "metadata": {
                    "simulation": True,
                    "generation_method": "random",
                    "quality_score": round(random.uniform(0.7, 1.0), 2)
                }
            }
            
            products.append(product)
        
        logger.info(f"✅ {len(products)}개의 시뮬레이션 상품 생성 완료")
        return products
    
    def _generate_product_name(self, category: str) -> str:
        """카테고리별 상품명 생성"""
        product_names = {
            'mobile': ['Galaxy', 'iPhone', 'Pixel', 'Mate', 'Mi'],
            'computers': ['MacBook', 'ThinkPad', 'ZenBook', 'Inspiron', 'Pavilion'],
            'electronics': ['Smart TV', 'Monitor', 'Tablet', 'Smart Watch', 'Camera'],
            'audio': ['AirPods', 'Headphones', 'Speaker', 'Earbuds', 'Soundbar'],
            'gaming': ['Gaming Mouse', 'Keyboard', 'Controller', 'Headset', 'Mouse Pad']
        }
        
        return random.choice(product_names.get(category, ['Product']))
    
    async def save_simulation_data(self, products: List[Dict[str, Any]]) -> bool:
        """시뮬레이션 데이터를 데이터베이스에 저장"""
        try:
            logger.info("💾 시뮬레이션 데이터를 데이터베이스에 저장 중...")
            
            saved_count = 0
            for product in products:
                try:
                    # normalized_products 테이블에 저장
                    await self.db_service.insert_data("normalized_products", product)
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"상품 저장 실패: {e}")
                    continue
            
            logger.info(f"✅ {saved_count}개 상품 저장 완료")
            return saved_count > 0
            
        except Exception as e:
            logger.error(f"시뮬레이션 데이터 저장 실패: {e}")
            return False
    
    async def train_models_with_simulation_data(self) -> Dict[str, Any]:
        """시뮬레이션 데이터로 AI 모델 재훈련"""
        try:
            logger.info("🤖 시뮬레이션 데이터로 AI 모델 재훈련 시작")
            
            # 시뮬레이션 데이터 조회
            simulation_data = await self.db_service.select_data(
                "normalized_products",
                {"is_simulation": True},
                limit=1000
            )
            
            if not simulation_data:
                logger.warning("⚠️ 훈련할 시뮬레이션 데이터가 없습니다")
                return {"error": "훈련 데이터 없음"}
            
            logger.info(f"📊 훈련 데이터: {len(simulation_data)}개 샘플")
            
            # 데이터를 DataFrame으로 변환
            df = pd.DataFrame(simulation_data)
            
            # 특성 엔지니어링
            df = self._engineer_features_for_training(df)
            
            # 모델 훈련 실행
            model_scores = await self.ai_service.train_models_with_dataframe(df)
            
            logger.info("✅ AI 모델 재훈련 완료")
            return {
                "training_samples": len(df),
                "model_scores": model_scores,
                "trained_at": datetime.now().isoformat(),
                "data_type": "simulation"
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
            
            # 브랜드 특성
            if 'brand' in df.columns:
                df['brand_encoded'] = df['brand'].astype('category').cat.codes
            
            # 리뷰 점수 특성
            if 'rating' in df.columns:
                df['rating_numeric'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)
            
            # 리뷰 수 특성
            if 'review_count' in df.columns:
                df['review_count_numeric'] = pd.to_numeric(df['review_count'], errors='coerce').fillna(0)
            
            # 가격 대비 리뷰 점수 비율
            df['price_rating_ratio'] = df['rating_numeric'] / (df['price_numeric'] / 10000)
            
            # 결측값 처리
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].median())
            
            return df
            
        except Exception as e:
            logger.error(f"특성 엔지니어링 실패: {e}")
            return df
    
    async def analyze_simulation_trends(self) -> Dict[str, Any]:
        """시뮬레이션 데이터 트렌드 분석"""
        try:
            logger.info("📈 시뮬레이션 데이터 트렌드 분석 시작")
            
            # 시뮬레이션 데이터 조회
            simulation_data = await self.db_service.select_data(
                "normalized_products",
                {"is_simulation": True},
                limit=1000
            )
            
            if not simulation_data:
                return {"error": "분석할 데이터 없음"}
            
            df = pd.DataFrame(simulation_data)
            
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
                    "avg_rating": category_data['rating'].mean(),
                    "platforms": category_data['platform'].value_counts().to_dict()
                }
            
            # 플랫폼별 분석
            platform_analysis = {}
            for platform in df['platform'].unique():
                platform_data = df[df['platform'] == platform]
                platform_analysis[platform] = {
                    "product_count": len(platform_data),
                    "avg_price": platform_data['price'].mean(),
                    "avg_rating": platform_data['rating'].mean(),
                    "avg_discount": platform_data['discount_rate'].mean()
                }
            
            # 브랜드별 분석
            brand_analysis = {}
            if 'brand' in df.columns:
                for brand in df['brand'].unique():
                    brand_data = df[df['brand'] == brand]
                    brand_analysis[brand] = {
                        "product_count": len(brand_data),
                        "avg_price": brand_data['price'].mean(),
                        "avg_rating": brand_data['rating'].mean()
                    }
            
            logger.info("✅ 시뮬레이션 데이터 트렌드 분석 완료")
            return {
                "total_products_analyzed": len(df),
                "category_analysis": category_analysis,
                "platform_analysis": platform_analysis,
                "brand_analysis": brand_analysis,
                "analysis_date": datetime.now().isoformat(),
                "data_type": "simulation"
            }
            
        except Exception as e:
            logger.error(f"시뮬레이션 데이터 트렌드 분석 실패: {e}")
            return {"error": str(e)}
    
    async def generate_simulation_recommendations(self) -> Dict[str, Any]:
        """시뮬레이션 가격 추천 생성"""
        try:
            logger.info("💰 시뮬레이션 가격 추천 생성 시작")
            
            # 시뮬레이션 데이터 조회
            simulation_products = await self.db_service.select_data(
                "normalized_products",
                {"is_simulation": True},
                limit=100
            )
            
            recommendations = []
            
            for product in simulation_products[:10]:  # 상위 10개만 분석
                try:
                    # AI 가격 예측
                    predictions = await self.ai_service.predict_price({
                        "platform": product.get("platform", "coupang"),
                        "category": product.get("category", "electronics"),
                        "price": product.get("price", 0),
                        "original_price": product.get("original_price", 0),
                        "rating": product.get("rating", 0),
                        "review_count": product.get("review_count", 0),
                        "brand": product.get("brand", "Unknown")
                    })
                    
                    if predictions:
                        best_prediction = predictions[0]
                        recommendations.append({
                            "product_name": product.get("name", "Unknown"),
                            "current_price": product.get("price", 0),
                            "recommended_price": best_prediction.predicted_price,
                            "confidence": best_prediction.confidence_score,
                            "strategy": "AI_predicted",
                            "platform": product.get("platform", "unknown"),
                            "category": product.get("category", "unknown"),
                            "brand": product.get("brand", "unknown")
                        })
                
                except Exception as e:
                    logger.warning(f"상품 '{product.get('name', 'Unknown')}' 가격 추천 실패: {e}")
                    continue
            
            logger.info(f"✅ 시뮬레이션 가격 추천 생성 완료: {len(recommendations)}개")
            return {
                "recommendations": recommendations,
                "generated_at": datetime.now().isoformat(),
                "total_recommendations": len(recommendations),
                "data_type": "simulation"
            }
            
        except Exception as e:
            logger.error(f"시뮬레이션 가격 추천 생성 실패: {e}")
            return {"error": str(e)}
    
    async def run_simulation_analysis(self) -> Dict[str, Any]:
        """시뮬레이션 분석 실행"""
        try:
            logger.info("🎯 시뮬레이션 데이터 분석 시작")
            
            results = {
                "data_generation": {},
                "training": {},
                "trend_analysis": {},
                "price_recommendations": {},
                "summary": {}
            }
            
            # 1. 시뮬레이션 데이터 생성 및 저장
            logger.info("1️⃣ 시뮬레이션 데이터 생성")
            simulation_products = self.generate_simulation_products(1000)
            save_result = await self.save_simulation_data(simulation_products)
            results["data_generation"] = {
                "generated_count": len(simulation_products),
                "saved_successfully": save_result,
                "generated_at": datetime.now().isoformat()
            }
            
            # 2. AI 모델 재훈련
            logger.info("2️⃣ AI 모델 재훈련")
            training_result = await self.train_models_with_simulation_data()
            results["training"] = training_result
            
            # 3. 트렌드 분석
            logger.info("3️⃣ 트렌드 분석")
            trend_result = await self.analyze_simulation_trends()
            results["trend_analysis"] = trend_result
            
            # 4. 가격 추천 생성
            logger.info("4️⃣ 가격 추천 생성")
            recommendation_result = await self.generate_simulation_recommendations()
            results["price_recommendations"] = recommendation_result
            
            # 5. 요약 생성
            results["summary"] = {
                "simulation_products_generated": len(simulation_products),
                "training_samples": training_result.get("training_samples", 0),
                "recommendations_generated": len(recommendation_result.get("recommendations", [])),
                "analysis_completed_at": datetime.now().isoformat(),
                "status": "success",
                "data_type": "simulation"
            }
            
            logger.info("🎉 시뮬레이션 분석 완료!")
            return results
            
        except Exception as e:
            logger.error(f"시뮬레이션 분석 실패: {e}")
            return {"error": str(e), "status": "failed"}


async def main():
    """메인 함수"""
    system = SimulationDataSystem()
    
    logger.info("🚀 시뮬레이션 데이터 기반 모델 재훈련 시스템 시작")
    
    # 시뮬레이션 분석 실행
    results = await system.run_simulation_analysis()
    
    # 결과 출력
    logger.info("\n📊 시뮬레이션 분석 결과 요약:")
    logger.info("=" * 50)
    
    if "error" in results:
        logger.error(f"❌ 분석 실패: {results['error']}")
        return
    
    summary = results.get("summary", {})
    logger.info(f"🎲 생성된 시뮬레이션 상품: {summary.get('simulation_products_generated', 0)}개")
    logger.info(f"🤖 훈련 샘플 수: {summary.get('training_samples', 0)}개")
    logger.info(f"💰 가격 추천 수: {summary.get('recommendations_generated', 0)}개")
    logger.info(f"✅ 분석 상태: {summary.get('status', 'unknown')}")
    logger.info(f"📊 데이터 타입: {summary.get('data_type', 'unknown')}")
    
    logger.info("\n🎯 다음 단계:")
    logger.info("  1. 시뮬레이션 데이터 품질 검토")
    logger.info("  2. AI 모델 성능 평가")
    logger.info("  3. 실제 데이터 수집 방법 개선")
    logger.info("  4. 운영 환경 배포 준비")


if __name__ == "__main__":
    asyncio.run(main())
