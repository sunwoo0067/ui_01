"""
AI 기반 가격 예측 서비스

머신러닝을 활용하여 경쟁사 데이터를 기반으로 최적 가격을 예측합니다.
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb

from src.services.database_service import DatabaseService
from src.config.settings import settings


@dataclass
class PricePredictionResult:
    """가격 예측 결과"""
    predicted_price: float
    confidence_score: float
    model_name: str
    features_used: List[str]
    prediction_date: datetime
    market_analysis: Dict[str, Any]


@dataclass
class MarketTrend:
    """시장 트렌드 분석"""
    trend_direction: str  # "up", "down", "stable"
    trend_strength: float  # 0.0 ~ 1.0
    volatility: float
    seasonal_pattern: Optional[str]
    competitor_count: int
    price_range: Tuple[float, float]


class AIPricePredictionService:
    """AI 기반 가격 예측 서비스"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.feature_importance = {}
        
        # 모델 초기화
        self._initialize_models()
    
    def _initialize_models(self) -> None:
        """머신러닝 모델들을 초기화"""
        self.models = {
            'random_forest': RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            ),
            'xgboost': xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1
            ),
            'lightgbm': lgb.LGBMRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1,
                verbose=-1
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            ),
            'linear_regression': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'lasso': Lasso(alpha=0.1)
        }
        
        # 스케일러 초기화
        for model_name in self.models.keys():
            self.scalers[model_name] = StandardScaler()
            self.label_encoders[model_name] = LabelEncoder()
    
    async def prepare_training_data(self, category: Optional[str] = None) -> pd.DataFrame:
        """훈련 데이터 준비"""
        try:
            logger.info("훈련 데이터 준비 시작")
            
            # 경쟁사 상품 데이터 조회
            competitor_data = await self.db_service.select_data(
                "competitor_products",
                {"category": category} if category else {}
            )
            
            # 가격 히스토리 데이터 조회 (category 컬럼이 없으므로 전체 조회)
            price_history = await self.db_service.select_data(
                "price_history",
                {}
            )
            
            if not competitor_data:
                logger.warning("경쟁사 데이터가 없습니다")
                return pd.DataFrame()
            
            # 데이터프레임 생성
            df = pd.DataFrame(competitor_data)
            
            if price_history:
                price_df = pd.DataFrame(price_history)
                # 가격 히스토리와 병합
                df = df.merge(price_df, on='product_id', how='left', suffixes=('', '_history'))
            
            # 특성 엔지니어링
            df = self._engineer_features(df)
            
            logger.info(f"훈련 데이터 준비 완료: {len(df)}개 샘플")
            return df
            
        except Exception as e:
            logger.error(f"훈련 데이터 준비 실패: {e}")
            return pd.DataFrame()
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """특성 엔지니어링"""
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
            df['platform_coupang'] = (df['platform'] == 'coupang').astype(int)
            df['platform_naver'] = (df['platform'] == 'naver').astype(int)
            df['platform_11st'] = (df['platform'] == '11st').astype(int)
            df['platform_gmarket'] = (df['platform'] == 'gmarket').astype(int)
            df['platform_auction'] = (df['platform'] == 'auction').astype(int)
            
            # 시간 특성
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'])
                df['hour'] = df['created_at'].dt.hour
                df['day_of_week'] = df['created_at'].dt.dayofweek
                df['month'] = df['created_at'].dt.month
                df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            
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
    
    async def train_models(self, category: Optional[str] = None) -> Dict[str, float]:
        """모든 모델 훈련"""
        try:
            logger.info("모델 훈련 시작")
            
            # 훈련 데이터 준비
            df = await self.prepare_training_data(category)
            
            if df.empty:
                logger.warning("훈련 데이터가 없습니다")
                return {}
            
            # 특성과 타겟 분리
            feature_columns = [
                'platform_coupang', 'platform_naver', 'platform_11st', 
                'platform_gmarket', 'platform_auction', 'discount_rate',
                'hour', 'day_of_week', 'month', 'is_weekend', 'category_encoded',
                'rating_numeric', 'review_count_numeric'
            ]
            
            # 존재하는 특성만 선택
            available_features = [col for col in feature_columns if col in df.columns]
            
            if not available_features:
                logger.warning("사용 가능한 특성이 없습니다")
                return {}
            
            X = df[available_features]
            y = df['price_numeric']
            
            # 결측값 제거
            mask = ~(X.isnull().any(axis=1) | y.isnull())
            X = X[mask]
            y = y[mask]
            
            if len(X) < 10:
                logger.warning("훈련 데이터가 너무 적습니다")
                return {}
            
            # 훈련/테스트 분할
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            model_scores = {}
            
            # 각 모델 훈련
            for model_name, model in self.models.items():
                try:
                    logger.info(f"{model_name} 모델 훈련 중...")
                    
                    # 스케일링
                    X_train_scaled = self.scalers[model_name].fit_transform(X_train)
                    X_test_scaled = self.scalers[model_name].transform(X_test)
                    
                    # 모델 훈련
                    model.fit(X_train_scaled, y_train)
                    
                    # 예측
                    y_pred = model.predict(X_test_scaled)
                    
                    # 평가
                    mae = mean_absolute_error(y_test, y_pred)
                    mse = mean_squared_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)
                    
                    model_scores[model_name] = {
                        'mae': mae,
                        'mse': mse,
                        'r2': r2,
                        'rmse': np.sqrt(mse)
                    }
                    
                    # 특성 중요도 저장
                    if hasattr(model, 'feature_importances_'):
                        self.feature_importance[model_name] = dict(
                            zip(available_features, model.feature_importances_)
                        )
                    
                    logger.info(f"{model_name} 훈련 완료 - R²: {r2:.3f}, MAE: {mae:.2f}")
                    
                except Exception as e:
                    logger.error(f"{model_name} 모델 훈련 실패: {e}")
                    continue
            
            logger.info("모든 모델 훈련 완료")
            return model_scores
            
        except Exception as e:
            logger.error(f"모델 훈련 실패: {e}")
            return {}
    
    async def predict_price(self, 
                          product_features: Dict[str, Any],
                          category: Optional[str] = None) -> List[PricePredictionResult]:
        """상품 가격 예측"""
        try:
            logger.info("가격 예측 시작")
            
            # 모델이 훈련되지 않은 경우 훈련
            if not self.models or not any(hasattr(model, 'feature_importances_') for model in self.models.values()):
                logger.info("모델이 훈련되지 않음. 훈련을 시작합니다.")
                await self.train_models(category)
            
            # 특성 벡터 생성
            feature_vector = self._create_feature_vector(product_features)
            
            predictions = []
            
            # 각 모델로 예측
            for model_name, model in self.models.items():
                try:
                    if not hasattr(model, 'predict'):
                        continue
                    
                    # 특성 스케일링
                    feature_scaled = self.scalers[model_name].transform([feature_vector])
                    
                    # 예측
                    predicted_price = model.predict(feature_scaled)[0]
                    
                    # 신뢰도 점수 계산 (간단한 방법)
                    confidence = min(0.95, max(0.1, abs(predicted_price) / 100000))
                    
                    prediction = PricePredictionResult(
                        predicted_price=float(predicted_price),
                        confidence_score=confidence,
                        model_name=model_name,
                        features_used=list(product_features.keys()),
                        prediction_date=datetime.now(),
                        market_analysis={}
                    )
                    
                    predictions.append(prediction)
                    
                except Exception as e:
                    logger.error(f"{model_name} 예측 실패: {e}")
                    continue
            
            # 예측 결과 정렬 (신뢰도 기준)
            predictions.sort(key=lambda x: x.confidence_score, reverse=True)
            
            logger.info(f"가격 예측 완료: {len(predictions)}개 모델")
            return predictions
            
        except Exception as e:
            logger.error(f"가격 예측 실패: {e}")
            return []
    
    def _create_feature_vector(self, product_features: Dict[str, Any]) -> List[float]:
        """상품 특성을 특성 벡터로 변환"""
        try:
            # 기본 특성 벡터 (모든 특성을 0으로 초기화)
            feature_vector = [0.0] * 13  # 사용 가능한 특성 수
            
            # 플랫폼 특성
            platform = product_features.get('platform', '').lower()
            if platform == 'coupang':
                feature_vector[0] = 1.0
            elif platform == 'naver':
                feature_vector[1] = 1.0
            elif platform == '11st':
                feature_vector[2] = 1.0
            elif platform == 'gmarket':
                feature_vector[3] = 1.0
            elif platform == 'auction':
                feature_vector[4] = 1.0
            
            # 할인율
            original_price = product_features.get('original_price', 0)
            price = product_features.get('price', 0)
            if original_price > 0:
                feature_vector[5] = (original_price - price) / original_price * 100
            
            # 시간 특성
            now = datetime.now()
            feature_vector[6] = now.hour
            feature_vector[7] = now.weekday()
            feature_vector[8] = now.month
            feature_vector[9] = 1.0 if now.weekday() >= 5 else 0.0
            
            # 카테고리 (간단한 해시)
            category = product_features.get('category', '')
            feature_vector[10] = hash(category) % 100
            
            # 리뷰 점수
            feature_vector[11] = product_features.get('rating', 0)
            
            # 리뷰 수
            feature_vector[12] = product_features.get('review_count', 0)
            
            return feature_vector
            
        except Exception as e:
            logger.error(f"특성 벡터 생성 실패: {e}")
            return [0.0] * 13
    
    async def analyze_market_trend(self, category: Optional[str] = None) -> MarketTrend:
        """시장 트렌드 분석"""
        try:
            logger.info("시장 트렌드 분석 시작")
            
            # 경쟁사 데이터 조회
            competitor_data = await self.db_service.select_data(
                "competitor_products",
                {"category": category} if category else {}
            )
            
            if not competitor_data:
                return MarketTrend(
                    trend_direction="stable",
                    trend_strength=0.0,
                    volatility=0.0,
                    seasonal_pattern=None,
                    competitor_count=0,
                    price_range=(0.0, 0.0)
                )
            
            df = pd.DataFrame(competitor_data)
            df['price_numeric'] = pd.to_numeric(df['price'], errors='coerce')
            df = df.dropna(subset=['price_numeric'])
            
            if len(df) < 2:
                return MarketTrend(
                    trend_direction="stable",
                    trend_strength=0.0,
                    volatility=0.0,
                    seasonal_pattern=None,
                    competitor_count=len(df),
                    price_range=(df['price_numeric'].min(), df['price_numeric'].max())
                )
            
            # 가격 범위
            price_min = df['price_numeric'].min()
            price_max = df['price_numeric'].max()
            
            # 변동성 계산
            volatility = df['price_numeric'].std() / df['price_numeric'].mean()
            
            # 트렌드 분석 (간단한 방법)
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'])
                df_sorted = df.sort_values('created_at')
                
                if len(df_sorted) > 1:
                    # 최근 가격과 이전 가격 비교
                    recent_prices = df_sorted.tail(len(df_sorted)//2)['price_numeric'].mean()
                    older_prices = df_sorted.head(len(df_sorted)//2)['price_numeric'].mean()
                    
                    price_change = (recent_prices - older_prices) / older_prices
                    
                    if price_change > 0.05:
                        trend_direction = "up"
                        trend_strength = min(1.0, abs(price_change))
                    elif price_change < -0.05:
                        trend_direction = "down"
                        trend_strength = min(1.0, abs(price_change))
                    else:
                        trend_direction = "stable"
                        trend_strength = 0.0
                else:
                    trend_direction = "stable"
                    trend_strength = 0.0
            else:
                trend_direction = "stable"
                trend_strength = 0.0
            
            # 계절성 패턴 분석 (간단한 방법)
            seasonal_pattern = None
            if 'created_at' in df.columns and len(df) > 12:
                df['month'] = pd.to_datetime(df['created_at']).dt.month
                monthly_avg = df.groupby('month')['price_numeric'].mean()
                
                # 계절성 패턴 감지
                if monthly_avg.std() / monthly_avg.mean() > 0.1:
                    seasonal_pattern = "seasonal"
            
            return MarketTrend(
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                volatility=volatility,
                seasonal_pattern=seasonal_pattern,
                competitor_count=len(df),
                price_range=(price_min, price_max)
            )
            
        except Exception as e:
            logger.error(f"시장 트렌드 분석 실패: {e}")
            return MarketTrend(
                trend_direction="stable",
                trend_strength=0.0,
                volatility=0.0,
                seasonal_pattern=None,
                competitor_count=0,
                price_range=(0.0, 0.0)
            )
    
    async def get_optimal_pricing_strategy(self, 
                                         product_features: Dict[str, Any],
                                         category: Optional[str] = None) -> Dict[str, Any]:
        """최적 가격 전략 제안"""
        try:
            logger.info("최적 가격 전략 분석 시작")
            
            # 가격 예측
            predictions = await self.predict_price(product_features, category)
            
            # 시장 트렌드 분석
            market_trend = await self.analyze_market_trend(category)
            
            if not predictions:
                return {
                    "recommended_price": product_features.get('price', 0),
                    "strategy": "manual_review",
                    "confidence": 0.0,
                    "reasoning": "예측 모델이 준비되지 않음"
                }
            
            # 최고 신뢰도 예측 선택
            best_prediction = predictions[0]
            
            # 가격 전략 결정
            strategy = "competitive"
            reasoning = []
            
            if market_trend.trend_direction == "up":
                strategy = "premium"
                reasoning.append("시장 가격 상승 추세")
            elif market_trend.trend_direction == "down":
                strategy = "aggressive"
                reasoning.append("시장 가격 하락 추세")
            
            if market_trend.volatility > 0.2:
                strategy = "conservative"
                reasoning.append("높은 가격 변동성")
            
            if market_trend.competitor_count < 3:
                strategy = "premium"
                reasoning.append("경쟁사 부족")
            
            # 최종 가격 조정
            recommended_price = best_prediction.predicted_price
            
            if strategy == "aggressive":
                recommended_price *= 0.95  # 5% 할인
            elif strategy == "premium":
                recommended_price *= 1.05  # 5% 프리미엄
            elif strategy == "conservative":
                recommended_price *= 0.98  # 2% 할인
            
            return {
                "recommended_price": round(recommended_price, 2),
                "strategy": strategy,
                "confidence": best_prediction.confidence_score,
                "reasoning": "; ".join(reasoning) if reasoning else "균형 잡힌 가격",
                "market_trend": {
                    "direction": market_trend.trend_direction,
                    "strength": market_trend.trend_strength,
                    "volatility": market_trend.volatility,
                    "competitor_count": market_trend.competitor_count
                },
                "predictions": [
                    {
                        "model": p.model_name,
                        "price": p.predicted_price,
                        "confidence": p.confidence_score
                    }
                    for p in predictions[:3]  # 상위 3개만
                ]
            }
            
        except Exception as e:
            logger.error(f"최적 가격 전략 분석 실패: {e}")
            return {
                "recommended_price": product_features.get('price', 0),
                "strategy": "manual_review",
                "confidence": 0.0,
                "reasoning": f"분석 실패: {str(e)}"
            }
    
    async def save_prediction_result(self, 
                                   product_id: str,
                                   prediction_result: Dict[str, Any]) -> bool:
        """예측 결과를 데이터베이스에 저장"""
        try:
            prediction_data = {
                "product_id": product_id,
                "predicted_price": prediction_result["recommended_price"],
                "strategy": prediction_result["strategy"],
                "confidence_score": prediction_result["confidence"],
                "reasoning": prediction_result["reasoning"],
                "market_trend": prediction_result.get("market_trend", {}),
                "model_predictions": prediction_result.get("predictions", []),
                "created_at": datetime.now().isoformat()
            }
            
            result = await self.db_service.insert_data("price_predictions", prediction_data)
            
            if result:
                logger.info(f"예측 결과 저장 완료: {product_id}")
                return True
            else:
                logger.error(f"예측 결과 저장 실패: {product_id}")
                return False
                
        except Exception as e:
            logger.error(f"예측 결과 저장 실패: {e}")
            return False
