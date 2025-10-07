#!/usr/bin/env python3
"""
AI 가격 예측 서비스 테스트
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.ai_price_prediction_service import AIPricePredictionService
from src.services.database_service import DatabaseService


async def test_ai_prediction_service():
    """AI 가격 예측 서비스 테스트"""
    try:
        logger.info("=== AI 가격 예측 서비스 테스트 시작 ===")
        
        # AI 서비스 초기화
        ai_service = AIPricePredictionService()
        
        # 테스트 상품 특성 생성
        test_product_features = {
            "platform": "coupang",
            "price": 50000,
            "original_price": 65000,
            "rating": 4.3,
            "review_count": 850,
            "category": "전자제품",
            "brand": "TestBrand"
        }
        
        logger.info(f"테스트 상품 특성: {test_product_features}")
        
        # 가격 예측 테스트
        logger.info("가격 예측 실행 중...")
        predictions = await ai_service.predict_price(
            product_features=test_product_features,
            category="전자제품"
        )
        
        if predictions:
            logger.info(f"✅ 가격 예측 성공: {len(predictions)}개 모델")
            
            # 예측 결과 출력
            for i, prediction in enumerate(predictions[:3]):
                logger.info(f"  {i+1}. {prediction.model_name}:")
                logger.info(f"     예측 가격: {prediction.predicted_price:,.0f}원")
                logger.info(f"     신뢰도: {prediction.confidence_score:.2f}")
                logger.info(f"     사용된 특성: {len(prediction.features_used)}개")
        else:
            logger.warning("⚠️ 가격 예측 결과가 없습니다")
        
        # 시장 트렌드 분석 테스트
        logger.info("\n시장 트렌드 분석 실행 중...")
        market_trend = await ai_service.analyze_market_trend(category="전자제품")
        
        logger.info("✅ 시장 트렌드 분석 완료")
        logger.info(f"  트렌드 방향: {market_trend.trend_direction}")
        logger.info(f"  트렌드 강도: {market_trend.trend_strength:.2f}")
        logger.info(f"  변동성: {market_trend.volatility:.2f}")
        logger.info(f"  경쟁사 수: {market_trend.competitor_count}개")
        logger.info(f"  가격 범위: {market_trend.price_range[0]:,.0f}원 ~ {market_trend.price_range[1]:,.0f}원")
        
        # 최적 가격 전략 분석 테스트
        logger.info("\n최적 가격 전략 분석 실행 중...")
        pricing_strategy = await ai_service.get_optimal_pricing_strategy(
            product_features=test_product_features,
            category="전자제품"
        )
        
        logger.info("✅ 최적 가격 전략 분석 완료")
        logger.info(f"  추천 가격: {pricing_strategy['recommended_price']:,.0f}원")
        logger.info(f"  전략: {pricing_strategy['strategy']}")
        logger.info(f"  신뢰도: {pricing_strategy['confidence']:.2f}")
        logger.info(f"  추천 이유: {pricing_strategy['reasoning']}")
        
        # 시장 트렌드 정보
        if 'market_trend' in pricing_strategy:
            market_info = pricing_strategy['market_trend']
            logger.info(f"  시장 정보:")
            logger.info(f"    방향: {market_info['direction']}")
            logger.info(f"    강도: {market_info['strength']:.2f}")
            logger.info(f"    변동성: {market_info['volatility']:.2f}")
            logger.info(f"    경쟁사 수: {market_info['competitor_count']}개")
        
        # 모델 예측 결과
        if 'predictions' in pricing_strategy:
            logger.info(f"  모델 예측 결과:")
            for pred in pricing_strategy['predictions']:
                logger.info(f"    {pred['model']}: {pred['price']:,.0f}원 (신뢰도: {pred['confidence']:.2f})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ AI 가격 예측 서비스 테스트 실패: {e}")
        return False


async def test_model_training():
    """모델 훈련 테스트"""
    try:
        logger.info("\n=== 모델 훈련 테스트 시작 ===")
        
        # AI 서비스 초기화
        ai_service = AIPricePredictionService()
        
        # 모델 훈련 실행
        logger.info("모델 훈련 실행 중...")
        model_scores = await ai_service.train_models(category="전자제품")
        
        if model_scores:
            logger.info(f"✅ 모델 훈련 완료: {len(model_scores)}개 모델")
            
            # 모델 성능 출력
            for model_name, scores in model_scores.items():
                logger.info(f"  {model_name}:")
                logger.info(f"    R² 점수: {scores['r2']:.3f}")
                logger.info(f"    MAE: {scores['mae']:.2f}")
                logger.info(f"    RMSE: {scores['rmse']:.2f}")
            
            # 최고 성능 모델 찾기
            best_model = max(model_scores.items(), key=lambda x: x[1]['r2'])
            logger.info(f"  최고 성능 모델: {best_model[0]} (R²: {best_model[1]['r2']:.3f})")
            
            return True
        else:
            logger.warning("⚠️ 모델 훈련 결과가 없습니다")
            return False
            
    except Exception as e:
        logger.error(f"❌ 모델 훈련 테스트 실패: {e}")
        return False


async def test_prediction_save():
    """예측 결과 저장 테스트"""
    try:
        logger.info("\n=== 예측 결과 저장 테스트 시작 ===")
        
        # AI 서비스 초기화
        ai_service = AIPricePredictionService()
        
        # 테스트 상품 특성
        test_features = {
            "platform": "coupang",
            "price": 45000,
            "original_price": 60000,
            "rating": 4.5,
            "review_count": 1200,
            "category": "전자제품",
            "brand": "TestBrand"
        }
        
        # 가격 전략 분석
        pricing_strategy = await ai_service.get_optimal_pricing_strategy(
            product_features=test_features,
            category="전자제품"
        )
        
        # 예측 결과 저장
        product_id = "ai_test_prediction_001"
        save_result = await ai_service.save_prediction_result(
            product_id=product_id,
            prediction_result=pricing_strategy
        )
        
        if save_result:
            logger.info(f"✅ 예측 결과 저장 성공: {product_id}")
            
            # 저장된 데이터 확인
            db_service = DatabaseService()
            saved_predictions = await db_service.select_data(
                "price_predictions",
                {"product_id": product_id}
            )
            
            if saved_predictions:
                prediction = saved_predictions[0]
                logger.info(f"  저장된 예측 가격: {prediction['predicted_price']:,.0f}원")
                logger.info(f"  전략: {prediction['strategy']}")
                logger.info(f"  신뢰도: {prediction['confidence_score']:.2f}")
                return True
            else:
                logger.error("❌ 저장된 예측 결과 조회 실패")
                return False
        else:
            logger.error("❌ 예측 결과 저장 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 예측 결과 저장 테스트 실패: {e}")
        return False


async def main():
    """메인 함수"""
    try:
        logger.info("🚀 AI 가격 예측 서비스 통합 테스트 시작")
        
        test_results = []
        
        # 1. AI 가격 예측 서비스 테스트
        test_results.append(await test_ai_prediction_service())
        
        # 2. 모델 훈련 테스트
        test_results.append(await test_model_training())
        
        # 3. 예측 결과 저장 테스트
        test_results.append(await test_prediction_save())
        
        # 결과 요약
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        logger.info(f"\n📊 테스트 결과 요약:")
        logger.info(f"  총 테스트: {total_tests}개")
        logger.info(f"  성공: {passed_tests}개")
        logger.info(f"  실패: {total_tests - passed_tests}개")
        logger.info(f"  성공률: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 모든 테스트 통과!")
        else:
            logger.warning("⚠️ 일부 테스트 실패")
            
    except Exception as e:
        logger.error(f"❌ 테스트 실행 중 오류: {e}")


if __name__ == "__main__":
    asyncio.run(main())
