#!/usr/bin/env python3
"""
AI 가격 예측 시스템 간단 테스트
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService


async def create_mock_training_data():
    """모의 훈련 데이터 생성"""
    try:
        logger.info("=== 모의 훈련 데이터 생성 시작 ===")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 모의 경쟁사 상품 데이터 생성
        mock_products = [
            {
                "platform": "coupang",
                "product_id": "ai_test_001",
                "name": "AI 테스트 무선 이어폰",
                "price": 45000,
                "original_price": 60000,
                "discount_rate": 25,
                "seller": "테스트 셀러",
                "rating": 4.5,
                "review_count": 1250,
                "image_url": "https://example.com/test1.jpg",
                "product_url": "https://coupang.com/test1",
                "category": "전자제품",
                "brand": "TestBrand",
                "search_keyword": "무선 이어폰",
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True,
                "marketplace_code": "coupang",
                "marketplace_name": "쿠팡",
                "market_share": 0.35,
                "avg_delivery_days": 1.5,
                "free_shipping_threshold": 30000,
                "raw_data": {"test": "data1"}
            },
            {
                "platform": "naver_smartstore",
                "product_id": "ai_test_002",
                "name": "AI 테스트 스마트워치",
                "price": 89000,
                "original_price": 120000,
                "discount_rate": 26,
                "seller": "테스트 셀러2",
                "rating": 4.3,
                "review_count": 890,
                "image_url": "https://example.com/test2.jpg",
                "product_url": "https://smartstore.naver.com/test2",
                "category": "전자제품",
                "brand": "SmartTech",
                "search_keyword": "스마트워치",
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True,
                "marketplace_code": "naver_smartstore",
                "marketplace_name": "네이버 스마트스토어",
                "market_share": 0.25,
                "avg_delivery_days": 2.0,
                "free_shipping_threshold": 20000,
                "raw_data": {"test": "data2"}
            },
            {
                "platform": "coupang",
                "product_id": "ai_test_003",
                "name": "AI 테스트 블루투스 스피커",
                "price": 32000,
                "original_price": 45000,
                "discount_rate": 29,
                "seller": "테스트 셀러3",
                "rating": 4.2,
                "review_count": 567,
                "image_url": "https://example.com/test3.jpg",
                "product_url": "https://coupang.com/test3",
                "category": "전자제품",
                "brand": "SoundMax",
                "search_keyword": "블루투스 스피커",
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True,
                "marketplace_code": "coupang",
                "marketplace_name": "쿠팡",
                "market_share": 0.35,
                "avg_delivery_days": 1.5,
                "free_shipping_threshold": 30000,
                "raw_data": {"test": "data3"}
            }
        ]
        
        # 데이터 저장
        saved_count = 0
        for product in mock_products:
            try:
                await db_service.insert_data("competitor_products", product)
                saved_count += 1
                logger.info(f"상품 데이터 저장: {product['name']}")
            except Exception as e:
                logger.error(f"상품 데이터 저장 실패: {e}")
        
        if saved_count > 0:
            logger.info(f"✅ 모의 훈련 데이터 생성 완료: {saved_count}개")
            return True
        else:
            logger.error("❌ 모의 훈련 데이터 생성 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 모의 훈련 데이터 생성 실패: {e}")
        return False


async def test_price_prediction_storage():
    """가격 예측 결과 저장 테스트"""
    try:
        logger.info("\n=== 가격 예측 결과 저장 테스트 시작 ===")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 모의 예측 결과 생성
        prediction_data = {
            "product_id": "ai_test_001",
            "predicted_price": 47000.0,
            "strategy": "competitive",
            "confidence_score": 0.85,
            "reasoning": "시장 평균가 대비 경쟁력 있는 가격",
            "market_trend": {
                "direction": "stable",
                "strength": 0.3,
                "volatility": 0.15,
                "competitor_count": 5
            },
            "model_predictions": [
                {"model": "random_forest", "price": 46000.0, "confidence": 0.82},
                {"model": "xgboost", "price": 47000.0, "confidence": 0.88},
                {"model": "lightgbm", "price": 47500.0, "confidence": 0.85}
            ],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # 데이터 저장
        await db_service.insert_data("price_predictions", prediction_data)
        logger.info("✅ 가격 예측 결과 저장 성공")
        
        # 저장된 데이터 조회
        stored_predictions = await db_service.select_data(
            "price_predictions",
            {"product_id": "ai_test_001"}
        )
        
        if stored_predictions:
            logger.info(f"✅ 가격 예측 결과 조회 성공: {len(stored_predictions)}개")
            prediction = stored_predictions[0]
            logger.info(f"  예측 가격: {prediction['predicted_price']:,}원")
            logger.info(f"  전략: {prediction['strategy']}")
            logger.info(f"  신뢰도: {prediction['confidence_score']:.2f}")
            return True
        else:
            logger.error("❌ 가격 예측 결과 조회 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 가격 예측 결과 저장 테스트 실패: {e}")
        return False


async def test_model_performance_storage():
    """모델 성능 데이터 저장 테스트"""
    try:
        logger.info("\n=== 모델 성능 데이터 저장 테스트 시작 ===")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 모의 모델 성능 데이터 생성
        performance_data = {
            "model_name": "random_forest",
            "category": "전자제품",
            "mae": 2500.0,
            "mse": 8500000.0,
            "r2_score": 0.85,
            "rmse": 2915.5,
            "training_samples": 100,
            "test_samples": 25,
            "feature_importance": {
                "price_numeric": 0.35,
                "platform_coupang": 0.25,
                "discount_rate": 0.20,
                "rating_numeric": 0.15,
                "review_count_numeric": 0.05
            },
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # 데이터 저장
        await db_service.insert_data("model_performance", performance_data)
        logger.info("✅ 모델 성능 데이터 저장 성공")
        
        # 저장된 데이터 조회
        stored_performance = await db_service.select_data(
            "model_performance",
            {"model_name": "random_forest"}
        )
        
        if stored_performance:
            logger.info(f"✅ 모델 성능 데이터 조회 성공: {len(stored_performance)}개")
            performance = stored_performance[0]
            logger.info(f"  모델명: {performance['model_name']}")
            logger.info(f"  R² 점수: {performance['r2_score']:.3f}")
            logger.info(f"  MAE: {performance['mae']:.2f}")
            logger.info(f"  훈련 샘플: {performance['training_samples']}개")
            return True
        else:
            logger.error("❌ 모델 성능 데이터 조회 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 모델 성능 데이터 저장 테스트 실패: {e}")
        return False


async def test_market_trend_analysis():
    """시장 트렌드 분석 데이터 저장 테스트"""
    try:
        logger.info("\n=== 시장 트렌드 분석 데이터 저장 테스트 시작 ===")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 모의 시장 트렌드 분석 데이터 생성
        trend_data = {
            "category": "전자제품",
            "trend_direction": "up",
            "trend_strength": 0.6,
            "volatility": 0.15,
            "seasonal_pattern": "spring_peak",
            "competitor_count": 8,
            "price_range_min": 25000.0,
            "price_range_max": 120000.0,
            "analysis_period_start": datetime.now(timezone.utc).isoformat(),
            "analysis_period_end": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # 데이터 저장
        await db_service.insert_data("market_trend_analysis", trend_data)
        logger.info("✅ 시장 트렌드 분석 데이터 저장 성공")
        
        # 저장된 데이터 조회
        stored_trends = await db_service.select_data(
            "market_trend_analysis",
            {"category": "전자제품"}
        )
        
        if stored_trends:
            logger.info(f"✅ 시장 트렌드 분석 데이터 조회 성공: {len(stored_trends)}개")
            trend = stored_trends[0]
            logger.info(f"  카테고리: {trend['category']}")
            logger.info(f"  트렌드 방향: {trend['trend_direction']}")
            logger.info(f"  트렌드 강도: {trend['trend_strength']:.2f}")
            logger.info(f"  경쟁사 수: {trend['competitor_count']}개")
            return True
        else:
            logger.error("❌ 시장 트렌드 분석 데이터 조회 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 시장 트렌드 분석 데이터 저장 테스트 실패: {e}")
        return False


async def main():
    """메인 함수"""
    try:
        logger.info("🚀 AI 가격 예측 시스템 간단 테스트 시작")
        
        test_results = []
        
        # 1. 모의 훈련 데이터 생성
        test_results.append(await create_mock_training_data())
        
        # 2. 가격 예측 결과 저장 테스트
        test_results.append(await test_price_prediction_storage())
        
        # 3. 모델 성능 데이터 저장 테스트
        test_results.append(await test_model_performance_storage())
        
        # 4. 시장 트렌드 분석 데이터 저장 테스트
        test_results.append(await test_market_trend_analysis())
        
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
