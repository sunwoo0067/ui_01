#!/usr/bin/env python3
"""
REST API 포괄적 테스트
72,376개 정규화 상품 기반 API 테스트
"""

import asyncio
import aiohttp
from loguru import logger


API_BASE = "http://localhost:8000"


async def test_api_endpoints():
    """API 엔드포인트 테스트"""
    
    logger.info("="*70)
    logger.info("🧪 REST API 포괄적 테스트")
    logger.info(f"   API 서버: {API_BASE}")
    logger.info("="*70)
    
    async with aiohttp.ClientSession() as session:
        
        # 1. 헬스 체크
        logger.info("\n1️⃣ 헬스 체크...")
        try:
            async with session.get(f"{API_BASE}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"   ✅ 헬스 체크: {data}")
                else:
                    logger.error(f"   ❌ 헬스 체크 실패: {resp.status}")
        except Exception as e:
            logger.error(f"   ❌ 헬스 체크 오류: {e}")
        
        # 2. 공급사 목록 조회
        logger.info("\n2️⃣ 공급사 목록 조회...")
        try:
            async with session.get(f"{API_BASE}/api/suppliers") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"   ✅ 공급사: {len(data)}개")
                    for supplier in data:
                        logger.info(f"      - {supplier.get('name')} ({supplier.get('code')})")
                else:
                    logger.error(f"   ❌ 공급사 조회 실패: {resp.status}")
        except Exception as e:
            logger.error(f"   ❌ 공급사 조회 오류: {e}")
        
        # 3. 상품 목록 조회 (페이징)
        logger.info("\n3️⃣ 상품 목록 조회...")
        try:
            async with session.get(f"{API_BASE}/api/products?page=1&size=20") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get('items', [])
                    total = data.get('total', 0)
                    logger.info(f"   ✅ 상품 목록: {len(items)}개 (전체: {total:,}개)")
                    if items:
                        logger.info(f"      첫 상품: {items[0].get('title', 'N/A')[:50]}...")
                else:
                    logger.error(f"   ❌ 상품 목록 조회 실패: {resp.status}")
        except Exception as e:
            logger.error(f"   ❌ 상품 목록 조회 오류: {e}")
        
        # 4. 공급사별 상품 조회
        logger.info("\n4️⃣ 공급사별 상품 조회 (오너클랜)...")
        try:
            async with session.get(
                f"{API_BASE}/api/products/by-supplier/e458e4e2-cb03-4fc2-bff1-b05aaffde00f?page=1&size=10"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get('items', [])
                    logger.info(f"   ✅ 오너클랜 상품: {len(items)}개")
                else:
                    logger.error(f"   ❌ 공급사별 상품 조회 실패: {resp.status}")
        except Exception as e:
            logger.error(f"   ❌ 공급사별 상품 조회 오류: {e}")
        
        # 5. 카테고리별 상품 조회
        logger.info("\n5️⃣ 카테고리별 상품 조회...")
        try:
            async with session.get(f"{API_BASE}/api/products/by-category?category=&page=1&size=10") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get('items', [])
                    logger.info(f"   ✅ 카테고리 상품: {len(items)}개")
                else:
                    logger.error(f"   ❌ 카테고리 상품 조회 실패: {resp.status}")
        except Exception as e:
            logger.error(f"   ❌ 카테고리 상품 조회 오류: {e}")
        
        # 6. 통계 조회
        logger.info("\n6️⃣ 통계 조회...")
        try:
            async with session.get(f"{API_BASE}/api/statistics/overview") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"   ✅ 통계:")
                    logger.info(f"      총 상품: {data.get('total_products', 0):,}개")
                    logger.info(f"      활성 상품: {data.get('active_products', 0):,}개")
                    logger.info(f"      공급사: {data.get('suppliers', 0)}개")
                else:
                    logger.error(f"   ❌ 통계 조회 실패: {resp.status}")
        except Exception as e:
            logger.error(f"   ❌ 통계 조회 오류: {e}")
    
    logger.info(f"\n{'='*70}")
    logger.info("✅ REST API 테스트 완료!")
    logger.info(f"{'='*70}")
    logger.info(f"\n💡 API 문서: {API_BASE}/api/docs")
    logger.info(f"💡 대시보드: file:///{os.path.abspath('dashboard.html')}")


if __name__ == "__main__":
    import os
    asyncio.run(test_api_endpoints())

