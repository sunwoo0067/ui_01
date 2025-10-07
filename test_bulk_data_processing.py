#!/usr/bin/env python3
"""
대량 데이터 처리 시스템 테스트
수집된 모든 원본 데이터를 정규화된 상품 데이터로 변환
"""

import asyncio
import sys
import os
from loguru import logger
from uuid import UUID
import time

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.services.product_pipeline import ProductPipeline


async def test_bulk_data_processing():
    """대량 데이터 처리 테스트"""
    try:
        logger.info("대량 데이터 처리 테스트 시작")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 상품 파이프라인 초기화
        pipeline = ProductPipeline()
        
        # 1. 전체 데이터 현황 확인
        logger.info("=== 전체 데이터 현황 ===")
        
        # 원본 데이터 통계
        total_raw = await db_service.select_data("raw_product_data", {})
        processed_raw = await db_service.select_data("raw_product_data", {"is_processed": True})
        unprocessed_raw = await db_service.select_data("raw_product_data", {"is_processed": False})
        
        # 정규화된 데이터 통계
        total_normalized = await db_service.select_data("normalized_products", {})
        
        logger.info(f"총 원본 데이터: {len(total_raw)}개")
        logger.info(f"처리된 원본 데이터: {len(processed_raw)}개")
        logger.info(f"미처리 원본 데이터: {len(unprocessed_raw)}개")
        logger.info(f"총 정규화된 데이터: {len(total_normalized)}개")
        
        if len(unprocessed_raw) == 0:
            logger.warning("처리할 원본 데이터가 없습니다")
            return
        
        # 2. 공급사별 처리 계획
        logger.info("=== 공급사별 처리 계획 ===")
        
        suppliers_result = await db_service.select_data("suppliers", {"is_active": True})
        
        for supplier in suppliers_result:
            supplier_id = supplier["id"]
            supplier_name = supplier["name"]
            
            # 해당 공급사의 미처리 데이터 수 확인
            supplier_unprocessed = await db_service.select_data(
                "raw_product_data", 
                {"supplier_id": supplier_id, "is_processed": False}
            )
            
            logger.info(f"  {supplier_name}: {len(supplier_unprocessed)}개 미처리")
        
        # 3. 배치 처리 실행 (젠트레이드부터 시작)
        logger.info("=== 배치 처리 실행 ===")
        
        start_time = time.time()
        
        # 젠트레이드 데이터 처리 (소량)
        zentrade_supplier = next((s for s in suppliers_result if s["code"] == "zentrade"), None)
        if zentrade_supplier:
            logger.info(f"젠트레이드 데이터 처리 시작...")
            
            batch_result = await pipeline.process_all_unprocessed(
                UUID(zentrade_supplier["id"]), 
                limit=50
            )
            
            logger.info(f"젠트레이드 배치 처리 결과: {batch_result}")
        
        # 오너클랜 데이터 처리 (중간량)
        ownerclan_supplier = next((s for s in suppliers_result if s["code"] == "ownerclan"), None)
        if ownerclan_supplier:
            logger.info(f"오너클랜 데이터 처리 시작...")
            
            batch_result = await pipeline.process_all_unprocessed(
                UUID(ownerclan_supplier["id"]), 
                limit=100
            )
            
            logger.info(f"오너클랜 배치 처리 결과: {batch_result}")
        
        # 도매꾹 데이터 처리 (대량)
        domaemae_supplier = next((s for s in suppliers_result if s["code"] == "domaemae_dome"), None)
        if domaemae_supplier:
            logger.info(f"도매꾹 데이터 처리 시작...")
            
            batch_result = await pipeline.process_all_unprocessed(
                UUID(domaemae_supplier["id"]), 
                limit=200
            )
            
            logger.info(f"도매꾹 배치 처리 결과: {batch_result}")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 4. 처리 결과 확인
        logger.info("=== 처리 결과 확인 ===")
        
        # 최종 통계
        final_processed_raw = await db_service.select_data("raw_product_data", {"is_processed": True})
        final_normalized = await db_service.select_data("normalized_products", {})
        
        logger.info(f"처리 완료된 원본 데이터: {len(final_processed_raw)}개")
        logger.info(f"총 정규화된 데이터: {len(final_normalized)}개")
        logger.info(f"처리 시간: {processing_time:.2f}초")
        
        # 처리 속도 계산
        processed_count = len(final_processed_raw) - len(processed_raw)
        if processing_time > 0:
            processing_rate = processed_count / processing_time
            logger.info(f"처리 속도: {processing_rate:.2f}개/초")
        
        # 5. 정규화된 상품 샘플 확인
        logger.info("=== 정규화된 상품 샘플 ===")
        
        sample_products = await db_service.select_data("normalized_products", {}, limit=5)
        
        for i, product in enumerate(sample_products, 1):
            logger.info(f"  {i}. 상품명: {product.get('title', 'N/A')}")
            logger.info(f"     가격: {product.get('price', 'N/A')}")
            logger.info(f"     카테고리: {product.get('category', 'N/A')}")
            logger.info(f"     브랜드: {product.get('brand', 'N/A')}")
            logger.info(f"     상태: {product.get('status', 'N/A')}")
        
        logger.info("✅ 대량 데이터 처리 테스트 완료")
        
    except Exception as e:
        logger.error(f"대량 데이터 처리 테스트 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_bulk_data_processing())
