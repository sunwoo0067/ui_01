#!/usr/bin/env python3
"""
도매꾹 데이터베이스 초기화 스크립트
"""

import asyncio
import sys
import os
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.services.domaemae_account_manager import DomaemaeAccountManager


async def init_domaemae_database():
    """도매꾹 데이터베이스 초기화"""
    try:
        logger.info("도매꾹 데이터베이스 초기화 시작")
        
        # 데이터베이스 서비스 초기화
        db_service = DatabaseService()
        
        # 도매꾹 계정 관리자 초기화
        account_manager = DomaemaeAccountManager(db_service)
        
        # 도매꾹 공급사 등록 (이미 있다면 무시)
        try:
            suppliers_data = {
                "name": "도매꾹",
                "code": "domaemae",
                "type": "api",
                "api_endpoint": "https://domeggook.com/ssl/api/",
                "is_active": True
            }
            
            # 공급사 등록
            await db_service.insert_data("suppliers", suppliers_data)
            logger.info("도매꾹 공급사 등록 완료")
            
        except Exception as e:
            if "duplicate key" in str(e).lower():
                logger.info("도매꾹 공급사가 이미 등록되어 있습니다")
            else:
                logger.error(f"도매꾹 공급사 등록 실패: {e}")
        
        # 테스트 계정 생성
        test_account_data = {
            "account_name": "test_account",
            "api_key": "96ef1110327e9ce5be389e5eaa612f4a",
            "version": "4.1",
            "description": "도매꾹 테스트 계정"
        }
        
        account_id = await account_manager.create_domaemae_account(**test_account_data)
        
        if account_id:
            logger.info(f"도매꾹 테스트 계정 생성 완료: {account_id}")
        else:
            logger.warning("도매꾹 테스트 계정 생성 실패")
        
        # 계정 목록 확인
        accounts = await account_manager.list_domaemae_accounts()
        logger.info(f"도매꾹 계정 목록: {len(accounts)}개")
        
        for account in accounts:
            logger.info(f"  - {account['account_name']}: {account.get('description', '')}")
        
        logger.info("도매꾹 데이터베이스 초기화 완료")
        
    except Exception as e:
        logger.error(f"도매꾹 데이터베이스 초기화 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_domaemae_database())
