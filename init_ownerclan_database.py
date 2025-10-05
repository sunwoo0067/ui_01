"""
오너클랜 데이터베이스 초기화 스크립트

오너클랜 공급사 정보를 데이터베이스에 추가하고 테스트 데이터를 설정
"""

import asyncio
from datetime import datetime
from loguru import logger

from src.services.database_service import database_service


async def initialize_ownerclan_supplier():
    """오너클랜 공급사 초기화"""
    
    try:
        logger.info("=== 오너클랜 공급사 초기화 시작 ===")
        
        # 1. 오너클랜 공급사 정보 확인/생성
        suppliers = await database_service.select_data(
            'suppliers',
            {'code': 'ownerclan'}
        )
        
        if not suppliers:
            # 오너클랜 공급사 생성
            supplier_data = {
                'name': '오너클랜',
                'code': 'ownerclan',
                'type': 'api',
                'api_endpoint': 'https://api.ownerclan.com/v1/graphql',
                'api_version': 'v1',
                'auth_type': 'jwt',
                'credentials': {
                    'auth_endpoint': 'https://auth.ownerclan.com/auth',
                    'service': 'ownerclan',
                    'userType': 'seller'
                },
                'field_mapping': {
                    'key': 'supplier_product_id',
                    'name': 'name',
                    'price': 'price',
                    'model': 'model',
                    'production': 'brand',
                    'origin': 'origin',
                    'category': 'category',
                    'images': 'images',
                    'options': 'options'
                },
                'is_active': True,
                'created_at': datetime.utcnow().isoformat()
            }
            
            supplier_result = await database_service.insert_data('suppliers', supplier_data)
            supplier_id = supplier_result['id']
            logger.info(f"오너클랜 공급사 생성 완료: {supplier_id}")
            
        else:
            supplier_id = suppliers[0]['id']
            logger.info(f"오너클랜 공급사 이미 존재: {supplier_id}")
        
        # 2. 테스트 계정 생성
        test_accounts = [
            {
                'account_name': 'test_account',
                'username': 'b00679540',
                'password': 'ehdgod1101*'
            },
            {
                'account_name': 'auth_test',
                'username': 'b00679540',
                'password': 'ehdgod1101*'
            }
        ]
        
        for account_info in test_accounts:
            # 기존 계정 확인
            existing_accounts = await database_service.select_data(
                'supplier_accounts',
                {'supplier_id': supplier_id, 'account_name': account_info['account_name']}
            )
            
            if not existing_accounts:
                # 새 계정 생성
                account_data = {
                    'supplier_id': supplier_id,
                    'account_name': account_info['account_name'],
                    'account_credentials': {
                        'service': 'ownerclan',
                        'userType': 'seller',
                        'username': account_info['username'],
                        'password': account_info['password'],
                        'auth_endpoint': 'https://auth.ownerclan.com/auth',
                        'api_endpoint': 'https://api.ownerclan.com/v1/graphql'
                    },
                    'is_active': True,
                    'created_at': datetime.utcnow().isoformat()
                }
                
                account_result = await database_service.insert_data('supplier_accounts', account_data)
                logger.info(f"테스트 계정 생성 완료: {account_info['account_name']} - {account_result['id']}")
            else:
                logger.info(f"테스트 계정 이미 존재: {account_info['account_name']}")
        
        logger.info("=== 오너클랜 공급사 초기화 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"오너클랜 공급사 초기화 실패: {e}")
        return False


async def test_database_connection():
    """데이터베이스 연결 테스트"""
    
    try:
        logger.info("=== 데이터베이스 연결 테스트 시작 ===")
        
        # suppliers 테이블 조회
        suppliers = await database_service.select_data('suppliers', limit=5)
        logger.info(f"Suppliers 테이블 조회 성공: {len(suppliers)}개")
        
        # supplier_accounts 테이블 조회
        accounts = await database_service.select_data('supplier_accounts', limit=5)
        logger.info(f"Supplier_accounts 테이블 조회 성공: {len(accounts)}개")
        
        logger.info("=== 데이터베이스 연결 테스트 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"데이터베이스 연결 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    print("오너클랜 데이터베이스 초기화를 시작합니다...")
    
    # 데이터베이스 연결 테스트
    result = asyncio.run(test_database_connection())
    print(f"데이터베이스 연결 테스트 결과: {result}")
    
    # 오너클랜 공급사 초기화
    result = asyncio.run(initialize_ownerclan_supplier())
    print(f"오너클랜 공급사 초기화 결과: {result}")
