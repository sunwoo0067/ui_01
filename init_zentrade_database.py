#!/usr/bin/env python3
"""
젠트레이드 데이터베이스 초기화 스크립트
"""

import asyncio
import sys
import os
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.services.zentrade_account_manager import ZentradeAccountManager


async def init_zentrade_database():
    """젠트레이드 데이터베이스 초기화"""
    try:
        logger.info("젠트레이드 데이터베이스 초기화 시작")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 젠트레이드 계정 관리자 초기화
        account_manager = ZentradeAccountManager(db_service)
        
        # 젠트레이드 공급사 등록 (이미 있다면 무시)
        try:
            suppliers_data = {
                "name": "젠트레이드",
                "code": "zentrade",
                "type": "api",
                "api_endpoint": "https://www.zentrade.co.kr/shop/proc/product_api.php",
                "is_active": True
            }
            
            # 공급사 등록
            await db_service.insert_data("suppliers", suppliers_data)
            logger.info("젠트레이드 공급사 등록 완료")
            
        except Exception as e:
            if "duplicate key" in str(e).lower():
                logger.info("젠트레이드 공급사가 이미 등록되어 있습니다")
            else:
                logger.error(f"젠트레이드 공급사 등록 실패: {e}")
        
        # 테스트 계정 생성
        test_account_data = {
            "account_name": "test_account",
            "id": "b00679540",
            "m_skey": "5284c44b0fcf0f877e6791c5884d6ea9",
            "description": "젠트레이드 테스트 계정"
        }
        
        account_id = await account_manager.create_zentrade_account(**test_account_data)
        
        if account_id:
            logger.info(f"젠트레이드 테스트 계정 생성 완료: {account_id}")
        else:
            logger.warning("젠트레이드 테스트 계정 생성 실패")
        
        # 계정 목록 확인
        accounts = await account_manager.list_zentrade_accounts()
        logger.info(f"젠트레이드 계정 목록: {len(accounts)}개")
        
        for account in accounts:
            logger.info(f"  - {account['account_name']}: {account['description']}")
        
        logger.info("젠트레이드 데이터베이스 초기화 완료")
        
    except Exception as e:
        logger.error(f"젠트레이드 데이터베이스 초기화 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_zentrade_database())
