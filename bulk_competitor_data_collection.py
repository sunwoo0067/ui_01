#!/usr/bin/env python3
"""
정규화된 상품 데이터 기반 대량 경쟁사 데이터 수집
67,535개 상품의 카테고리별 경쟁사 가격 분석
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Set
from loguru import logger

from src.services.database_service import DatabaseService
from src.services.coupang_search_service import CoupangSearchService
from src.services.naver_smartstore_search_service import NaverSmartStoreSearchService
from src.services.price_comparison_service import PriceComparisonService


async def bulk_collect_competitor_data(
    limit: int = None,
    categories: List[str] = None,
    batch_size: int = 100
):
    """대량 경쟁사 데이터 수집"""
    
    db = DatabaseService()
    coupang_service = CoupangSearchService()
    naver_service = NaverSmartStoreSearchService()
    price_comparison_service = PriceComparisonService()
    
    logger.info("="*70)
    logger.info("🔍 대량 경쟁사 데이터 수집 시작")
    logger.info(f"   대상: 정규화 상품 (오너클랜)")
    logger.info(f"   제한: {limit if limit else '전체'}")
    logger.info("="*70)
    
    start_time = datetime.now()
    
    # 1단계: 정규화 상품 조회
    logger.info("\n1️⃣ 정규화 상품 조회 중...")
    
    supplier_id = "e458e4e2-cb03-4fc2-bff1-b05aaffde00f"  # 오너클랜
    
    query_conditions = {"supplier_id": supplier_id}
    
    if categories:
        logger.info(f"   카테고리 필터: {categories}")
    
    products = await db.select_data(
        "normalized_products",
        query_conditions,
        limit=limit
    )
    
    logger.info(f"   정규화 상품: {len(products):,}개")
    
    # 2단계: 상품별 검색 키워드 생성
    logger.info("\n2️⃣ 검색 키워드 생성 중...")
    
    keyword_product_map = {}  # 키워드 -> 상품 목록 매핑
    
    for product in products:
        try:
            # 상품명에서 검색 키워드 생성 (브랜드명 제거, 모델명 추출)
            title = product.get('title', '')
            category = product.get('category', '')
            
            # 간단한 키워드 추출 (첫 3-4단어)
            keywords = title.split()[:4]
            keyword = ' '.join(keywords)
            
            if not keyword:
                continue
            
            if keyword not in keyword_product_map:
                keyword_product_map[keyword] = []
            
            keyword_product_map[keyword].append({
                'id': product['id'],
                'title': title,
                'price': product.get('price', 0),
                'category': category
            })
            
        except Exception as e:
            logger.warning(f"   키워드 생성 실패: {e}")
            continue
    
    # 중복 키워드 제거 및 상위 N개만 선택 (너무 많으면 API 제한)
    unique_keywords = list(keyword_product_map.keys())[:500]  # 상위 500개만
    
    logger.info(f"   고유 키워드: {len(unique_keywords):,}개 (총 {len(keyword_product_map)}개 중)")
    logger.info(f"   매핑된 상품: {sum(len(v) for v in keyword_product_map.values()):,}개")
    
    # 3단계: 마켓플레이스별 경쟁사 데이터 수집
    logger.info(f"\n3️⃣ 경쟁사 데이터 수집 시작...")
    logger.info(f"   플랫폼: 쿠팡, 네이버 스마트스토어")
    logger.info(f"   배치 크기: {batch_size}개")
    
    total_collected = {
        'coupang': 0,
        'naver': 0
    }
    
    batch_num = 0
    total_batches = (len(unique_keywords) + batch_size - 1) // batch_size
    
    for i in range(0, len(unique_keywords), batch_size):
        batch_keywords = unique_keywords[i:i + batch_size]
        batch_num += 1
        
        logger.info(f"\n   배치 {batch_num}/{total_batches} 수집 중... ({len(batch_keywords)}개 키워드)")
        
        for idx, keyword in enumerate(batch_keywords, 1):
            try:
                # 쿠팡 검색
                try:
                    coupang_products = await coupang_service.search_products(
                        keyword=keyword,
                        page=1
                    )
                    
                    # 상위 10개만 사용
                    if coupang_products:
                        coupang_products = coupang_products[:10]
                        saved = await coupang_service.save_competitor_products(
                            coupang_products,
                            keyword
                        )
                        total_collected['coupang'] += saved
                        
                except Exception as e:
                    logger.debug(f"      쿠팡 검색 실패: {keyword[:30]}, {e}")
                
                # 네이버 스마트스토어 검색
                try:
                    naver_products = await naver_service.search_products(
                        keyword=keyword,
                        page=1
                    )
                    
                    # 상위 10개만 사용
                    if naver_products:
                        naver_products = naver_products[:10]
                        saved = await naver_service.save_competitor_products(
                            naver_products,
                            keyword
                        )
                        total_collected['naver'] += saved
                        
                except Exception as e:
                    logger.debug(f"      네이버 검색 실패: {keyword[:30]}, {e}")
                
                # 진행률 표시 (10개마다)
                if idx % 10 == 0:
                    progress = ((i + idx) / len(unique_keywords)) * 100
                    logger.info(f"      진행: {idx}/{len(batch_keywords)} (전체: {progress:.1f}%)")
                
                # API 호출 간격 (과부하 방지)
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"      키워드 처리 실패: {keyword[:30]}, {e}")
                continue
        
        # 배치 완료
        batch_progress = (batch_num / total_batches) * 100
        logger.info(f"   배치 {batch_num} 완료 (진행률: {batch_progress:.1f}%)")
        logger.info(f"      누적 - 쿠팡: {total_collected['coupang']:,}개, 네이버: {total_collected['naver']:,}개")
        
        # 배치 간 휴식
        await asyncio.sleep(1)
    
    total_time = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"\n{'='*70}")
    logger.info("✅ 대량 경쟁사 데이터 수집 완료!")
    logger.info(f"{'='*70}")
    logger.info(f"   처리 키워드: {len(unique_keywords):,}개")
    logger.info(f"   쿠팡 수집: {total_collected['coupang']:,}개")
    logger.info(f"   네이버 수집: {total_collected['naver']:,}개")
    logger.info(f"   총 수집: {sum(total_collected.values()):,}개")
    logger.info(f"   총 시간: {total_time/60:.2f}분")
    logger.info(f"{'='*70}")
    
    result = {
        "status": "success",
        "keywords_processed": len(unique_keywords),
        "coupang_collected": total_collected['coupang'],
        "naver_collected": total_collected['naver'],
        "total_collected": sum(total_collected.values()),
        "total_time": total_time
    }
    
    with open('competitor_data_collection_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info("💾 결과가 competitor_data_collection_result.json에 저장되었습니다")
    
    return result


if __name__ == "__main__":
    import sys
    
    # 명령줄 인자로 제한 가능
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 1000  # 기본 1000개
    
    result = asyncio.run(bulk_collect_competitor_data(
        limit=limit,
        batch_size=50  # 50개 키워드씩 배치 처리
    ))

