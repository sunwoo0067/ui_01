"""
공급사 계정 정보 관리 서비스

데이터베이스 중심 아키텍처에서 공급사 API 계정 정보를 관리하는 서비스
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import asyncio
from loguru import logger

from src.config.settings import settings
from src.utils.error_handler import ErrorHandler, BaseAPIError, DatabaseError
from src.services.database_service import database_service


class SupplierAccountManager:
    """공급사 계정 정보 관리자"""
    
    def __init__(self):
        self.settings = settings
        self.db_service = database_service
        self.error_handler = ErrorHandler()
    
    async def get_supplier_by_code(self, supplier_code: str) -> Optional[Dict[str, Any]]:
        """
        공급사 코드로 공급사 정보 조회
        
        Args:
            supplier_code: 공급사 코드 (예: 'ownerclan')
            
        Returns:
            공급사 정보 딕셔너리 또는 None
        """
        try:
            result = await self.db_service.select_data(
                'suppliers',
                {'code': supplier_code}
            )
            
            if result:
                return result[0]
            
            return None
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "공급사 정보 조회 실패",
                'supplier_code': supplier_code
            })
            raise DatabaseError(f"공급사 정보 조회 실패: {e}")
    
    async def get_supplier_account(self, supplier_code: str, account_name: str) -> Optional[Dict[str, Any]]:
        """
        공급사 계정 정보 조회
        
        Args:
            supplier_code: 공급사 코드 (예: 'ownerclan')
            account_name: 계정 이름
            
        Returns:
            계정 정보 딕셔너리 또는 None
        """
        try:
            # 먼저 공급사 정보 조회
            supplier = await self.get_supplier_by_code(supplier_code)
            if not supplier:
                return None
            
            supplier_id = supplier['id']
            
            result = await self.db_service.select_data(
                'supplier_accounts',
                {'supplier_id': supplier_id, 'account_name': account_name}
            )
            
            if result:
                account = result[0]
                # JSONB 필드를 파이썬 딕셔너리로 변환
                if isinstance(account['account_credentials'], str):
                    account['account_credentials'] = json.loads(account['account_credentials'])
                return account
            
            return None
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "공급사 계정 정보 조회 실패",
                'supplier_code': supplier_code,
                'account_name': account_name
            })
            raise DatabaseError(f"공급사 계정 정보 조회 실패: {e}")
    
    async def create_supplier_account(self, supplier_code: str, account_name: str, 
                                    credentials: Dict[str, Any]) -> str:
        """
        공급사 계정 정보 생성
        
        Args:
            supplier_code: 공급사 코드 (예: 'ownerclan')
            account_name: 계정 이름
            credentials: 인증 정보
            
        Returns:
            생성된 계정 ID
        """
        try:
            # 먼저 공급사 정보 조회
            supplier = await self.get_supplier_by_code(supplier_code)
            if not supplier:
                raise DatabaseError(f"공급사를 찾을 수 없습니다: {supplier_code}")
            
            supplier_id = supplier['id']
            
            # 인증 정보를 JSONB로 저장
            credentials_json = json.dumps(credentials)
            
            data = {
                'supplier_id': supplier_id,
                'account_name': account_name,
                'account_credentials': credentials_json,
                'is_active': True,
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = await self.db_service.insert_data('supplier_accounts', data)
            account_id = result['id']
            
            logger.info(f"공급사 계정 생성 완료: {account_id}")
            return account_id
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "공급사 계정 정보 생성 실패",
                'supplier_code': supplier_code,
                'account_name': account_name
            })
            raise DatabaseError(f"공급사 계정 정보 생성 실패: {e}")
    
    async def update_supplier_account(self, account_id: str, 
                                    credentials: Optional[Dict[str, Any]] = None,
                                    is_active: Optional[bool] = None) -> bool:
        """
        공급사 계정 정보 업데이트
        
        Args:
            account_id: 계정 ID
            credentials: 업데이트할 인증 정보
            is_active: 활성 상태
            
        Returns:
            업데이트 성공 여부
        """
        try:
            update_fields = []
            params = []
            
            if credentials is not None:
                update_fields.append("account_credentials = %s")
                params.append(json.dumps(credentials))
            
            if is_active is not None:
                update_fields.append("is_active = %s")
                params.append(is_active)
            
            if not update_fields:
                return False
            
            update_fields.append("updated_at = %s")
            params.append(datetime.utcnow())
            params.append(account_id)
            
            query = f"""
                UPDATE supplier_accounts 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            
            await self.db_service.execute_query(query, params)
            logger.info(f"공급사 계정 정보 업데이트 완료: {account_id}")
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "공급사 계정 정보 업데이트 실패",
                'account_id': account_id
            })
            raise DatabaseError(f"공급사 계정 정보 업데이트 실패: {e}")
    
    async def list_supplier_accounts(self, supplier_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        공급사 계정 목록 조회
        
        Args:
            supplier_id: 특정 공급사 ID (선택사항)
            
        Returns:
            계정 목록
        """
        try:
            if supplier_id:
                query = """
                    SELECT sa.*, s.name as supplier_name 
                    FROM supplier_accounts sa
                    JOIN suppliers s ON sa.supplier_id = s.id
                    WHERE sa.supplier_id = %s
                    ORDER BY sa.created_at DESC
                """
                result = await self.db_service.execute_query(query, (supplier_id,))
            else:
                query = """
                    SELECT sa.*, s.name as supplier_name 
                    FROM supplier_accounts sa
                    JOIN suppliers s ON sa.supplier_id = s.id
                    ORDER BY sa.created_at DESC
                """
                result = await self.db_service.execute_query(query)
            
            # JSONB 필드를 파이썬 딕셔너리로 변환
            for account in result:
                account['account_credentials'] = json.loads(account['account_credentials'])
            
            return result
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "공급사 계정 목록 조회 실패",
                'supplier_id': supplier_id
            })
            raise DatabaseError(f"공급사 계정 목록 조회 실패: {e}")
    
    async def get_ownerclan_credentials(self, account_name: str) -> Optional[Dict[str, Any]]:
        """
        오너클랜 계정 인증 정보 조회
        Args:
            account_name: 계정 이름
        Returns:
            인증 정보 딕셔너리 또는 None
        """
        try:
            account = await self.get_supplier_account("ownerclan", account_name)
            if account:
                return account['account_credentials']
            return None
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "오너클랜 인증 정보 조회 실패",
                'account_name': account_name
            })
            return None
    
    async def delete_supplier_account(self, account_id: str) -> bool:
        """
        공급사 계정 정보 삭제 (소프트 삭제)
        
        Args:
            account_id: 계정 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            query = """
                UPDATE supplier_accounts 
                SET is_active = false, updated_at = %s
                WHERE id = %s
            """
            
            await self.db_service.execute_query(query, (datetime.utcnow(), account_id))
            logger.info(f"공급사 계정 정보 삭제 완료: {account_id}")
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': "공급사 계정 정보 삭제 실패",
                'account_id': account_id
            })
            raise DatabaseError(f"공급사 계정 정보 삭제 실패: {e}")


class OwnerClanAccountManager(SupplierAccountManager):
    """오너클랜 전용 계정 관리자"""
    
    def __init__(self):
        super().__init__()
        self.supplier_id = "ownerclan"  # 오너클랜 공급사 ID
    
    async def create_ownerclan_account(self, account_name: str, 
                                     username: str, password: str) -> str:
        """
        오너클랜 계정 생성
        
        Args:
            account_name: 계정 이름
            username: 오너클랜 사용자명
            password: 오너클랜 비밀번호
            
        Returns:
            생성된 계정 ID
        """
        credentials = {
            'service': 'ownerclan',
            'userType': 'seller',
            'username': username,
            'password': password,
            'auth_endpoint': 'https://auth.ownerclan.com/auth',
            'api_endpoint': 'https://api.ownerclan.com/v1/graphql'
        }
        
        return await self.create_supplier_account(
            self.supplier_id, account_name, credentials
        )
    
    async def get_ownerclan_credentials(self, account_name: str) -> Optional[Dict[str, Any]]:
        """
        오너클랜 인증 정보 조회
        
        Args:
            account_name: 계정 이름
            
        Returns:
            인증 정보 딕셔너리 또는 None
        """
        account = await self.get_supplier_account(self.supplier_id, account_name)
        if account:
            return account['account_credentials']
        return None


    async def create_ownerclan_account(self, account_name: str, 
                                     username: str, password: str) -> str:
        """
        오너클랜 계정 생성
        
        Args:
            account_name: 계정 이름
            username: 오너클랜 사용자명
            password: 오너클랜 비밀번호
            
        Returns:
            생성된 계정 ID
        """
        credentials = {
            'service': 'ownerclan',
            'userType': 'seller',
            'username': username,
            'password': password,
            'auth_endpoint': 'https://auth.ownerclan.com/auth',
            'api_endpoint': 'https://api.ownerclan.com/v1/graphql'
        }
        
        return await self.create_supplier_account(
            'ownerclan', account_name, credentials
        )
    
    async def get_ownerclan_credentials(self, account_name: str) -> Optional[Dict[str, Any]]:
        """
        오너클랜 인증 정보 조회
        
        Args:
            account_name: 계정 이름
            
        Returns:
            인증 정보 딕셔너리 또는 None
        """
        account = await self.get_supplier_account('ownerclan', account_name)
        if account:
            return account['account_credentials']
        return None


# 전역 인스턴스
supplier_account_manager = SupplierAccountManager()
