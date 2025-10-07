#!/usr/bin/env python3
"""
오너클랜 상품 status 값 확인
"""

import asyncio
from loguru import logger
from src.services.ownerclan_data_collector import OwnerClanDataCollector


async def check_status():
    """실제 status 값 확인"""
    collector = OwnerClanDataCollector()
    
    # 간단한 쿼리로 status 확인
    query = """
    query {
        allItems(first: 10) {
            edges {
                node {
                    key
                    name
                    status
                    price
                }
            }
        }
    }
    """
    
    result = await collector._make_graphql_request(query, "test_account")
    
    if result and "data" in result:
        items = result["data"]["allItems"]["edges"]
        
        logger.info(f"📦 샘플 10개 상품:")
        logger.info(f"{'='*70}")
        
        status_counts = {}
        
        for edge in items:
            node = edge["node"]
            status = node.get("status", "N/A")
            
            status_counts[status] = status_counts.get(status, 0) + 1
            
            logger.info(f"상품: {node.get('name', 'N/A')[:30]}...")
            logger.info(f"  status: {status}")
            logger.info(f"  가격: {node.get('price', 0):,}원\n")
        
        logger.info(f"{'='*70}")
        logger.info("📊 Status 통계:")
        for status, count in sorted(status_counts.items()):
            logger.info(f"  {status}: {count}개")


if __name__ == "__main__":
    asyncio.run(check_status())

