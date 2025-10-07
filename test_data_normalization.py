#!/usr/bin/env python3
"""
데이터 정규화 테스트 스크립트
수집된 원본 데이터를 정규화된 상품 데이터로 변환
"""

import asyncio
import sys
import os
from loguru import logger
from uuid import UUID

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.services.product_pipeline import ProductPipeline


async def test_data_normalization():
    """데이터 정규화 테스트"""
    try:
        logger.info("데이터 정규화 테스트 시작")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 상품 파이프라인 초기화
        pipeline = ProductPipeline()
        
        # 1. 미처리 원본 데이터 확인
        logger.info("=== 미처리 원본 데이터 확인 ===")
        
        raw_data_result = await db_service.select_data(
            "raw_product_data",
            {"is_processed": False},
            limit=10
        )
        
        logger.info(f"미처리 원본 데이터: {len(raw_data_result)}개")
        
        if len(raw_data_result) == 0:
            logger.warning("처리할 원본 데이터가 없습니다")
            return
        
        # 2. 첫 번째 원본 데이터 처리 테스트
        logger.info("=== 첫 번째 원본 데이터 처리 테스트 ===")
        
        first_raw_data = raw_data_result[0]
        raw_data_id = UUID(first_raw_data["id"])
        
        logger.info(f"처리할 원본 데이터 ID: {raw_data_id}")
        logger.info(f"공급사 ID: {first_raw_data['supplier_id']}")
        logger.info(f"상품 ID: {first_raw_data['supplier_product_id']}")
        
        # 3. 데이터 정규화 실행
        logger.info("=== 데이터 정규화 실행 ===")
        
        result = await pipeline.process_raw_data(raw_data_id, auto_list=False)
        
        logger.info(f"정규화 결과: {result}")
        
        # 4. 정규화된 데이터 확인
        logger.info("=== 정규화된 데이터 확인 ===")
        
        normalized_result = await db_service.select_data(
            "normalized_products",
            {"supplier_id": first_raw_data["supplier_id"]},
            limit=5
        )
        
        logger.info(f"정규화된 상품 데이터: {len(normalized_result)}개")
        
        if len(normalized_result) > 0:
            logger.info("정규화된 상품 예시:")
            for product in normalized_result[:2]:
                logger.info(f"  - 상품명: {product.get('title', 'N/A')}")
                logger.info(f"    가격: {product.get('price', 'N/A')}")
                logger.info(f"    카테고리: {product.get('category', 'N/A')}")
        
        # 5. 배치 처리 테스트 (소량)
        logger.info("=== 배치 처리 테스트 (5개) ===")
        
        batch_result = await pipeline.process_all_unprocessed(limit=5)
        
        logger.info(f"배치 처리 결과: {batch_result}")
        
        # 6. 최종 통계
        logger.info("=== 최종 통계 ===")
        
        # 원본 데이터 통계
        total_raw = await db_service.select_data("raw_product_data", {})
        processed_raw = await db_service.select_data("raw_product_data", {"is_processed": True})
        
        # 정규화된 데이터 통계
        total_normalized = await db_service.select_data("normalized_products", {})
        
        logger.info(f"총 원본 데이터: {len(total_raw)}개")
        logger.info(f"처리된 원본 데이터: {len(processed_raw)}개")
        logger.info(f"총 정규화된 데이터: {len(total_normalized)}개")
        
        logger.info("✅ 데이터 정규화 테스트 완료")
        
    except Exception as e:
        logger.error(f"데이터 정규화 테스트 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_data_normalization())
