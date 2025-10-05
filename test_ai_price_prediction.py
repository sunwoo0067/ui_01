"""
AI 가격 예측 시스템 테스트

머신러닝 모델 훈련, 가격 예측, 시장 트렌드 분석을 테스트합니다.
"""

import asyncio
import sys
import os
from datetime import datetime
from loguru import logger

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.ai_price_prediction_service import AIPricePredictionService
from src.services.database_service import DatabaseService


class AIPricePredictionTester:
    """AI 가격 예측 시스템 테스터"""
    
    def __init__(self):
        self.ai_service = AIPricePredictionService()
        self.db_service = DatabaseService()
        self.test_results = {}
    
    async def test_model_training(self) -> bool:
        """모델 훈련 테스트"""
        try:
            logger.info("\n=== 모델 훈련 테스트 시작 ===")
            
            # 모델 훈련 실행
            model_scores = await self.ai_service.train_models()
            
            if not model_scores:
                logger.warning("⚠️ 모델 훈련 결과가 없습니다")
                return False
            
            logger.info("✅ 모델 훈련 완료")
            
            # 결과 출력
            for model_name, scores in model_scores.items():
                logger.info(f"  {model_name}:")
                logger.info(f"    R² Score: {scores['r2']:.3f}")
                logger.info(f"    MAE: {scores['mae']:.2f}")
                logger.info(f"    RMSE: {scores['rmse']:.2f}")
            
            self.test_results['model_training'] = model_scores
            return True
            
        except Exception as e:
            logger.error(f"❌ 모델 훈련 테스트 실패: {e}")
            return False
    
    async def test_price_prediction(self) -> bool:
        """가격 예측 테스트"""
        try:
            logger.info("\n=== 가격 예측 테스트 시작 ===")
            
            # 테스트 상품 특성
            test_product = {
                'platform': 'coupang',
                'category': 'electronics',
                'price': 50000,
                'original_price': 60000,
                'rating': 4.5,
                'review_count': 150
            }
            
            # 가격 예측 실행
            predictions = await self.ai_service.predict_price(test_product)
            
            if not predictions:
                logger.warning("⚠️ 가격 예측 결과가 없습니다")
                return False
            
            logger.info("✅ 가격 예측 완료")
            
            # 결과 출력
            for i, prediction in enumerate(predictions[:3]):  # 상위 3개만
                logger.info(f"  예측 {i+1} ({prediction.model_name}):")
                logger.info(f"    예측 가격: {prediction.predicted_price:,.0f}원")
                logger.info(f"    신뢰도: {prediction.confidence_score:.3f}")
                logger.info(f"    사용 특성: {len(prediction.features_used)}개")
            
            self.test_results['price_prediction'] = predictions
            return True
            
        except Exception as e:
            logger.error(f"❌ 가격 예측 테스트 실패: {e}")
            return False
    
    async def test_market_trend_analysis(self) -> bool:
        """시장 트렌드 분석 테스트"""
        try:
            logger.info("\n=== 시장 트렌드 분석 테스트 시작 ===")
            
            # 시장 트렌드 분석 실행
            market_trend = await self.ai_service.analyze_market_trend()
            
            logger.info("✅ 시장 트렌드 분석 완료")
            logger.info(f"  트렌드 방향: {market_trend.trend_direction}")
            logger.info(f"  트렌드 강도: {market_trend.trend_strength:.3f}")
            logger.info(f"  변동성: {market_trend.volatility:.3f}")
            logger.info(f"  경쟁사 수: {market_trend.competitor_count}개")
            logger.info(f"  가격 범위: {market_trend.price_range[0]:,.0f}원 ~ {market_trend.price_range[1]:,.0f}원")
            
            if market_trend.seasonal_pattern:
                logger.info(f"  계절성 패턴: {market_trend.seasonal_pattern}")
            
            self.test_results['market_trend'] = market_trend
            return True
            
        except Exception as e:
            logger.error(f"❌ 시장 트렌드 분석 테스트 실패: {e}")
            return False
    
    async def test_optimal_pricing_strategy(self) -> bool:
        """최적 가격 전략 테스트"""
        try:
            logger.info("\n=== 최적 가격 전략 테스트 시작 ===")
            
            # 테스트 상품 특성
            test_product = {
                'platform': 'coupang',
                'category': 'electronics',
                'price': 50000,
                'original_price': 60000,
                'rating': 4.5,
                'review_count': 150
            }
            
            # 최적 가격 전략 분석
            strategy_result = await self.ai_service.get_optimal_pricing_strategy(test_product)
            
            logger.info("✅ 최적 가격 전략 분석 완료")
            logger.info(f"  권장 가격: {strategy_result['recommended_price']:,.0f}원")
            logger.info(f"  전략: {strategy_result['strategy']}")
            logger.info(f"  신뢰도: {strategy_result['confidence']:.3f}")
            logger.info(f"  근거: {strategy_result['reasoning']}")
            
            # 시장 트렌드 정보
            if 'market_trend' in strategy_result:
                trend = strategy_result['market_trend']
                logger.info(f"  시장 트렌드:")
                logger.info(f"    방향: {trend['direction']}")
                logger.info(f"    강도: {trend['strength']:.3f}")
                logger.info(f"    변동성: {trend['volatility']:.3f}")
                logger.info(f"    경쟁사 수: {trend['competitor_count']}개")
            
            # 모델 예측 결과
            if 'predictions' in strategy_result:
                logger.info(f"  모델 예측 결과:")
                for pred in strategy_result['predictions']:
                    logger.info(f"    {pred['model']}: {pred['price']:,.0f}원 (신뢰도: {pred['confidence']:.3f})")
            
            self.test_results['pricing_strategy'] = strategy_result
            return True
            
        except Exception as e:
            logger.error(f"❌ 최적 가격 전략 테스트 실패: {e}")
            return False
    
    async def test_database_operations(self) -> bool:
        """데이터베이스 작업 테스트"""
        try:
            logger.info("\n=== 데이터베이스 작업 테스트 시작 ===")
            
            # 테스트 상품 ID
            test_product_id = "test_product_001"
            
            # 가격 전략 결과 저장 테스트
            if 'pricing_strategy' in self.test_results:
                strategy_result = self.test_results['pricing_strategy']
                
                save_success = await self.ai_service.save_prediction_result(
                    test_product_id, 
                    strategy_result
                )
                
                if save_success:
                    logger.info("✅ 예측 결과 저장 성공")
                else:
                    logger.warning("⚠️ 예측 결과 저장 실패")
                    return False
            
            # 저장된 데이터 조회 테스트
            try:
                saved_predictions = await self.db_service.select_data(
                    "price_predictions",
                    {"product_id": test_product_id}
                )
                
                if saved_predictions:
                    logger.info(f"✅ 저장된 예측 결과 조회 성공: {len(saved_predictions)}개")
                else:
                    logger.warning("⚠️ 저장된 예측 결과가 없습니다")
                
            except Exception as e:
                logger.warning(f"⚠️ 데이터 조회 실패 (테이블이 없을 수 있음): {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 데이터베이스 작업 테스트 실패: {e}")
            return False
    
    async def test_feature_engineering(self) -> bool:
        """특성 엔지니어링 테스트"""
        try:
            logger.info("\n=== 특성 엔지니어링 테스트 시작 ===")
            
            # 테스트 데이터프레임 생성
            import pandas as pd
            
            test_data = {
                'platform': ['coupang', 'naver', '11st', 'gmarket', 'auction'],
                'price': ['50000', '45000', '48000', '52000', '47000'],
                'original_price': ['60000', '55000', '58000', '62000', '57000'],
                'rating': ['4.5', '4.2', '4.3', '4.6', '4.1'],
                'review_count': ['150', '200', '120', '180', '90'],
                'category': ['electronics', 'electronics', 'electronics', 'electronics', 'electronics'],
                'created_at': [datetime.now().isoformat()] * 5
            }
            
            df = pd.DataFrame(test_data)
            
            # 특성 엔지니어링 실행
            engineered_df = self.ai_service._engineer_features(df)
            
            logger.info("✅ 특성 엔지니어링 완료")
            logger.info(f"  원본 특성 수: {len(df.columns)}")
            logger.info(f"  엔지니어링 후 특성 수: {len(engineered_df.columns)}")
            
            # 새로운 특성들 확인
            new_features = set(engineered_df.columns) - set(df.columns)
            if new_features:
                logger.info(f"  새로 생성된 특성: {list(new_features)}")
            
            # 특성 벡터 생성 테스트
            test_features = {
                'platform': 'coupang',
                'price': 50000,
                'original_price': 60000,
                'rating': 4.5,
                'review_count': 150,
                'category': 'electronics'
            }
            
            feature_vector = self.ai_service._create_feature_vector(test_features)
            logger.info(f"  특성 벡터 길이: {len(feature_vector)}")
            logger.info(f"  특성 벡터: {feature_vector[:5]}...")  # 처음 5개만 출력
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 특성 엔지니어링 테스트 실패: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """모든 테스트 실행"""
        logger.info("🚀 AI 가격 예측 시스템 테스트 시작")
        
        # 테스트 실행
        tests = [
            ("특성 엔지니어링", self.test_feature_engineering),
            ("모델 훈련", self.test_model_training),
            ("가격 예측", self.test_price_prediction),
            ("시장 트렌드 분석", self.test_market_trend_analysis),
            ("최적 가격 전략", self.test_optimal_pricing_strategy),
            ("데이터베이스 작업", self.test_database_operations)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                logger.error(f"❌ {test_name} 테스트 중 오류: {e}")
                results.append((test_name, False))
        
        # 결과 요약
        logger.info("\n📊 테스트 결과 요약:")
        successful_tests = 0
        for test_name, result in results:
            status = "✅ 성공" if result else "❌ 실패"
            logger.info(f"  {test_name}: {status}")
            if result:
                successful_tests += 1
        
        total_tests = len(results)
        success_rate = (successful_tests / total_tests) * 100
        
        logger.info(f"\n총 테스트: {total_tests}개")
        logger.info(f"성공: {successful_tests}개")
        logger.info(f"실패: {total_tests - successful_tests}개")
        logger.info(f"성공률: {success_rate:.1f}%")
        
        if successful_tests == total_tests:
            logger.info("🎉 모든 AI 가격 예측 시스템 테스트 성공!")
            return True
        else:
            logger.warning("⚠️ 일부 테스트 실패")
            return False


async def main():
    """메인 함수"""
    tester = AIPricePredictionTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("\n✅ AI 가격 예측 시스템이 성공적으로 구현되었습니다!")
        logger.info("\n🎯 다음 단계:")
        logger.info("  1. 실제 데이터로 모델 재훈련")
        logger.info("  2. 대시보드에 AI 예측 결과 통합")
        logger.info("  3. 자동화된 가격 조정 시스템 구축")
    else:
        logger.error("\n❌ AI 가격 예측 시스템 구현에 문제가 있습니다.")
        logger.error("  로그를 확인하여 문제를 해결해주세요.")


if __name__ == "__main__":
    asyncio.run(main())
