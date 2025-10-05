#!/usr/bin/env python3
"""
OwnerClan 날짜 필터 기능 테스트
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.ownerclan_data_collector import OwnerClanDataCollector
from src.services.supplier_account_manager import OwnerClanAccountManager
from src.utils.error_handler import ErrorHandler

async def test_date_filter():
    """날짜 필터 기능 테스트"""
    try:
        logger.info("=== OwnerClan 날짜 필터 기능 테스트 시작 ===")
        
        # 서비스 초기화
        error_handler = ErrorHandler()
        account_manager = OwnerClanAccountManager()
        collector = OwnerClanDataCollector()
        
        # 테스트 계정 확인
        account_name = "test_account"
        account = await account_manager.get_supplier_account("ownerclan", account_name)
        if not account:
            logger.error(f"테스트 계정이 없습니다: {account_name}")
            return
        
        logger.info(f"테스트 계정 사용: {account_name}")
        
        # 다양한 날짜 범위로 테스트
        test_cases = [
            {
                "name": "최근 7일",
                "start_date": datetime.now() - timedelta(days=7),
                "end_date": datetime.now()
            },
            {
                "name": "최근 30일",
                "start_date": datetime.now() - timedelta(days=30),
                "end_date": datetime.now()
            },
            {
                "name": "특정 기간 (2024년 1월)",
                "start_date": datetime(2024, 1, 1),
                "end_date": datetime(2024, 1, 31)
            },
            {
                "name": "배송일 기준 (최근 15일)",
                "shipped_after": datetime.now() - timedelta(days=15),
                "shipped_before": datetime.now()
            },
            {
                "name": "복합 필터 (주문일 + 배송일)",
                "start_date": datetime.now() - timedelta(days=30),
                "end_date": datetime.now(),
                "shipped_after": datetime.now() - timedelta(days=7)
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n--- 테스트 {i}: {test_case['name']} ---")
            
            try:
                # 주문 데이터 수집
                orders = await collector.collect_orders(
                    account_name=account_name,
                    limit=50,
                    start_date=test_case.get('start_date'),
                    end_date=test_case.get('end_date'),
                    shipped_after=test_case.get('shipped_after'),
                    shipped_before=test_case.get('shipped_before')
                )
                
                logger.info(f"수집된 주문 수: {len(orders)}")
                
                if orders:
                    # 첫 번째 주문 정보 출력
                    first_order = orders[0]
                    logger.info(f"첫 번째 주문:")
                    logger.info(f"  - 주문 키: {first_order.get('supplier_key', 'N/A')}")
                    logger.info(f"  - 주문 ID: {first_order.get('supplier_id', 'N/A')}")
                    logger.info(f"  - 주문 상태: {first_order.get('status', 'N/A')}")
                    logger.info(f"  - 주문일: {first_order.get('created_at', 'N/A')}")
                    logger.info(f"  - 상품 수: {len(first_order.get('products', []))}")
                    
                    # 날짜 필터링 검증
                    if test_case.get('start_date') or test_case.get('end_date'):
                        logger.info("주문일 필터링 검증:")
                        for order in orders[:5]:  # 처음 5개 주문만 검증
                            created_at = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                            logger.info(f"  - 주문일: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    logger.info("수집된 주문이 없습니다.")
                    
            except Exception as e:
                logger.error(f"테스트 {i} 실패: {e}")
                error_handler.log_error(e, f"날짜 필터 테스트 실패: {test_case['name']}")
        
        logger.info("\n=== 날짜 필터 기능 테스트 완료 ===")
        
    except Exception as e:
        logger.error(f"테스트 실행 실패: {e}")
        error_handler.log_error(e, "날짜 필터 테스트 실행 실패")

async def test_edge_cases():
    """엣지 케이스 테스트"""
    try:
        logger.info("\n=== 엣지 케이스 테스트 시작 ===")
        
        # 서비스 초기화
        error_handler = ErrorHandler()
        collector = OwnerClanDataCollector()
        account_name = "test_account"
        
        edge_cases = [
            {
                "name": "90일 초과 범위 (자동 제한)",
                "start_date": datetime.now() - timedelta(days=120),
                "end_date": datetime.now()
            },
            {
                "name": "미래 날짜 범위",
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=7)
            },
            {
                "name": "동일한 시작일과 종료일",
                "start_date": datetime.now(),
                "end_date": datetime.now()
            },
            {
                "name": "매개변수 없음 (기본값 사용)",
                "start_date": None,
                "end_date": None
            }
        ]
        
        for i, test_case in enumerate(edge_cases, 1):
            logger.info(f"\n--- 엣지 케이스 {i}: {test_case['name']} ---")
            
            try:
                orders = await collector.collect_orders(
                    account_name=account_name,
                    limit=10,
                    start_date=test_case.get('start_date'),
                    end_date=test_case.get('end_date')
                )
                
                logger.info(f"수집된 주문 수: {len(orders)}")
                logger.info("엣지 케이스 처리 성공")
                
            except Exception as e:
                logger.error(f"엣지 케이스 {i} 실패: {e}")
                error_handler.log_error(e, f"엣지 케이스 테스트 실패: {test_case['name']}")
        
        logger.info("\n=== 엣지 케이스 테스트 완료 ===")
        
    except Exception as e:
        logger.error(f"엣지 케이스 테스트 실행 실패: {e}")
        error_handler.log_error(e, "엣지 케이스 테스트 실행 실패")

if __name__ == "__main__":
    # 로거 설정
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # 테스트 실행
    asyncio.run(test_date_filter())
    asyncio.run(test_edge_cases())
