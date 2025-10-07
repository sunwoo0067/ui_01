#!/usr/bin/env python3
"""
젠트레이드 계정 정보 확인 스크립트
"""

import asyncio
import sys
import os
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.services.zentrade_account_manager import ZentradeAccountManager


async def check_zentrade_account():
    """젠트레이드 계정 정보 확인"""
    try:
        logger.info("젠트레이드 계정 정보 확인 시작")
        
        # 서비스 초기화
        db_service = DatabaseService()
        account_manager = ZentradeAccountManager(db_service)
        
        # 계정 조회
        account = await account_manager.get_zentrade_account("test_account")
        
        if account:
            logger.info(f"계정 정보: {account}")
            
            # 인증 정보 확인
            credentials = account.get("credentials", {})
            logger.info(f"인증 정보: {credentials}")
            
            # ID와 m_skey 확인
            id_value = credentials.get("id")
            m_skey_value = credentials.get("m_skey")
            
            logger.info(f"ID: {id_value}")
            logger.info(f"m_skey: {m_skey_value}")
            
            # 올바른 값과 비교
            expected_id = "b00679540"
            expected_m_skey = "5284c44b0fcf0f877e6791c5884d6ea9"
            
            if id_value == expected_id:
                logger.info("✅ ID가 올바릅니다")
            else:
                logger.error(f"❌ ID가 잘못되었습니다. 예상: {expected_id}, 실제: {id_value}")
            
            if m_skey_value == expected_m_skey:
                logger.info("✅ m_skey가 올바릅니다")
            else:
                logger.error(f"❌ m_skey가 잘못되었습니다. 예상: {expected_m_skey}, 실제: {m_skey_value}")
                
        else:
            logger.error("계정을 찾을 수 없습니다")
        
        logger.info("젠트레이드 계정 정보 확인 완료")
        
    except Exception as e:
        logger.error(f"젠트레이드 계정 정보 확인 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(check_zentrade_account())
