from typing import Dict, Any, Optional, List
from loguru import logger

from src.services.database_service import DatabaseService
from src.services.supplier_account_manager import SupplierAccountManager
from src.utils.error_handler import ErrorHandler


class ZentradeAccountManager:
    """젠트레이드 계정 관리자"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
        self.account_manager = SupplierAccountManager()
    
    async def create_zentrade_account(self, account_name: str, 
                                    id: str, m_skey: str,
                                    description: str = "") -> Optional[str]:
        """젠트레이드 계정 생성"""
        try:
            logger.info(f"젠트레이드 계정 생성 시작: {account_name}")
            
            # 공급사 ID 조회
            supplier_id = await self._get_supplier_id("zentrade")
            
            # 계정 데이터 구성
            account_data = {
                "supplier_id": supplier_id,
                "account_name": account_name,
                "description": description,
                "credentials": {
                    "id": id,
                    "m_skey": m_skey
                },
                "is_active": True
            }
            
            # 계정 생성
            account_id = await self.account_manager.create_supplier_account(
                "zentrade", 
                account_name, 
                {
                    "id": id,
                    "m_skey": m_skey
                }
            )
            
            logger.info(f"젠트레이드 계정 생성 완료: {account_name} (ID: {account_id})")
            return account_id
            
        except Exception as e:
            self.error_handler.log_error(e, f"젠트레이드 계정 생성 실패: {account_name}")
            return None
    
    async def get_zentrade_account(self, account_name: str) -> Optional[Dict[str, Any]]:
        """젠트레이드 계정 조회"""
        try:
            return await self.account_manager.get_supplier_account("zentrade", account_name)
        except Exception as e:
            self.error_handler.log_error(e, f"젠트레이드 계정 조회 실패: {account_name}")
            return None
    
    async def update_zentrade_account(self, account_name: str, 
                                    updates: Dict[str, Any]) -> bool:
        """젠트레이드 계정 업데이트"""
        try:
            logger.info(f"젠트레이드 계정 업데이트 시작: {account_name}")
            
            # 공급사 ID 조회
            supplier_id = await self._get_supplier_id("zentrade")
            
            # 업데이트 실행
            result = await self.account_manager.update_supplier_account(
                supplier_id, account_name, updates
            )
            
            if result:
                logger.info(f"젠트레이드 계정 업데이트 완료: {account_name}")
            else:
                logger.warning(f"젠트레이드 계정 업데이트 실패: {account_name}")
            
            return result
            
        except Exception as e:
            self.error_handler.log_error(e, f"젠트레이드 계정 업데이트 실패: {account_name}")
            return False
    
    async def delete_zentrade_account(self, account_name: str) -> bool:
        """젠트레이드 계정 삭제"""
        try:
            logger.info(f"젠트레이드 계정 삭제 시작: {account_name}")
            
            # 공급사 ID 조회
            supplier_id = await self._get_supplier_id("zentrade")
            
            # 삭제 실행
            result = await self.account_manager.delete_supplier_account(
                supplier_id, account_name
            )
            
            if result:
                logger.info(f"젠트레이드 계정 삭제 완료: {account_name}")
            else:
                logger.warning(f"젠트레이드 계정 삭제 실패: {account_name}")
            
            return result
            
        except Exception as e:
            self.error_handler.log_error(e, f"젠트레이드 계정 삭제 실패: {account_name}")
            return False
    
    async def list_zentrade_accounts(self) -> List[Dict[str, Any]]:
        """젠트레이드 계정 목록 조회"""
        try:
            return await self.account_manager.list_supplier_accounts("zentrade")
        except Exception as e:
            self.error_handler.log_error(e, "젠트레이드 계정 목록 조회 실패")
            return []
    
    async def _get_supplier_id(self, supplier_code: str) -> str:
        """공급사 ID 조회"""
        try:
            result = await self.db_service.select_data(
                "suppliers",
                {"code": supplier_code}
            )
            if result:
                return result[0]["id"]
            else:
                raise ValueError(f"공급사를 찾을 수 없습니다: {supplier_code}")
        except Exception as e:
            self.error_handler.log_error(e, f"공급사 ID 조회 실패: {supplier_code}")
            raise
