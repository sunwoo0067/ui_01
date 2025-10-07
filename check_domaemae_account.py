#!/usr/bin/env python3
"""
도매꾹 계정 확인 스크립트
"""

import asyncio
import sys
import os
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.services.domaemae_account_manager import DomaemaeAccountManager


async def check_domaemae_account():
    """도매꾹 계정 확인"""
    try:
        logger.info("도매꾹 계정 확인 시작")
        
        # 서비스 초기화
        db_service = DatabaseService()
        account_manager = DomaemaeAccountManager(db_service)
        
        # 계정 목록 조회
        accounts = await account_manager.list_domaemae_accounts()
        
        if not accounts:
            logger.warning("도매꾹 계정이 등록되어 있지 않습니다")
            return
        
        logger.info(f"도매꾹 계정 목록: {len(accounts)}개")
        
        for account in accounts:
            logger.info(f"\n계정 정보:")
            logger.info(f"  - 계정명: {account.get('account_name', 'N/A')}")
            logger.info(f"  - 설명: {account.get('description', 'N/A')}")
            logger.info(f"  - 활성화: {'예' if account.get('is_active') else '아니오'}")
            logger.info(f"  - 생성일: {account.get('created_at', 'N/A')}")
            logger.info(f"  - 수정일: {account.get('updated_at', 'N/A')}")
            
            # 계정 인증 정보
            credentials = account.get('account_credentials', {})
            if credentials:
                logger.info(f"  - API 키: {credentials.get('api_key', 'N/A')}")
                logger.info(f"  - API 버전: {credentials.get('version', 'N/A')}")
            else:
                logger.warning("  - 인증 정보 없음")
        
        # 특정 계정 상세 조회
        test_account_name = "test_account"
        test_account = await account_manager.get_domaemae_account(test_account_name)
        
        if test_account:
            logger.info(f"\n테스트 계정 상세 정보: {test_account_name}")
            logger.info(f"  - 계정 ID: {test_account.get('id', 'N/A')}")
            logger.info(f"  - 공급사 ID: {test_account.get('supplier_id', 'N/A')}")
            
            credentials = test_account.get('account_credentials', {})
            logger.info(f"  - API 키: {credentials.get('api_key', 'N/A')}")
            logger.info(f"  - API 버전: {credentials.get('version', 'N/A')}")
            
            # API 키 검증
            api_key = credentials.get('api_key')
            if api_key:
                if len(api_key) == 32:
                    logger.info("  - API 키 형식: 올바름 (32자)")
                else:
                    logger.warning(f"  - API 키 형식: 이상함 (길이: {len(api_key)})")
            else:
                logger.error("  - API 키 없음")
        else:
            logger.warning(f"테스트 계정을 찾을 수 없습니다: {test_account_name}")
        
        # 공급사 정보 확인
        logger.info("\n공급사 정보 확인")
        supplier_result = await db_service.select_data(
            "suppliers",
            {"code": "domaemae"}
        )
        
        if supplier_result:
            supplier = supplier_result[0]
            logger.info(f"  - 공급사명: {supplier.get('name', 'N/A')}")
            logger.info(f"  - 공급사 코드: {supplier.get('code', 'N/A')}")
            logger.info(f"  - 공급사 타입: {supplier.get('type', 'N/A')}")
            logger.info(f"  - API 엔드포인트: {supplier.get('api_endpoint', 'N/A')}")
            logger.info(f"  - 활성화: {'예' if supplier.get('is_active') else '아니오'}")
        else:
            logger.error("도매꾹 공급사 정보를 찾을 수 없습니다")
        
        logger.info("✅ 도매꾹 계정 확인 완료")
        
    except Exception as e:
        logger.error(f"❌ 도매꾹 계정 확인 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(check_domaemae_account())
