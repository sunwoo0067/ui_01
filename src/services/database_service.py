"""
데이터베이스 서비스

Supabase를 사용한 데이터베이스 작업을 위한 서비스 클래스
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
from loguru import logger

from src.services.supabase_client import SupabaseClient


class DatabaseService:
    """데이터베이스 서비스"""
    
    def __init__(self):
        self.supabase = SupabaseClient()
    
    async def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        SQL 쿼리 실행 (Supabase RPC 함수 사용)
        
        Args:
            query: SQL 쿼리
            params: 쿼리 파라미터
            
        Returns:
            쿼리 결과
        """
        try:
            # Supabase는 직접 SQL 쿼리를 지원하지 않으므로
            # 테이블 API를 사용하거나 RPC 함수를 호출해야 합니다
            # 여기서는 간단한 구현을 제공합니다
            
            # 실제 구현에서는 Supabase의 RPC 함수를 사용하거나
            # 테이블 API를 직접 사용해야 합니다
            logger.warning("execute_query는 Supabase에서 직접 지원되지 않습니다. 테이블 API를 사용하세요.")
            return []
            
        except Exception as e:
            logger.error(f"쿼리 실행 실패: {e}")
            raise
    
    async def insert_data(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        데이터 삽입
        
        Args:
            table_name: 테이블 이름
            data: 삽입할 데이터
            
        Returns:
            삽입된 데이터
        """
        try:
            table = self.supabase.get_table(table_name, use_service_key=True)
            result = table.insert(data).execute()
            
            if result.data:
                logger.info(f"데이터 삽입 성공: {table_name}")
                return result.data[0]
            else:
                raise Exception("데이터 삽입 실패")
                
        except Exception as e:
            logger.error(f"데이터 삽입 실패: {e}")
            raise
    
    async def update_data(self, table_name: str, data: Dict[str, Any], 
                        conditions: Dict[str, Any]) -> Dict[str, Any]:
        """
        데이터 업데이트
        
        Args:
            table_name: 테이블 이름
            data: 업데이트할 데이터
            conditions: 업데이트 조건
            
        Returns:
            업데이트된 데이터
        """
        try:
            table = self.supabase.get_table(table_name, use_service_key=True)
            
            # 조건 적용
            query = table.update(data)
            for key, value in conditions.items():
                query = query.eq(key, value)
            
            result = query.execute()
            
            if result.data:
                logger.info(f"데이터 업데이트 성공: {table_name}")
                return result.data[0]
            else:
                logger.warning(f"데이터 업데이트 실패: {table_name}, 조건: {conditions}, 데이터: {data}")
                # 업데이트할 레코드가 없을 수도 있으므로 None 반환
                return None
                
        except Exception as e:
            logger.error(f"데이터 업데이트 실패: {e}")
            raise
    
    async def select_data(self, table_name: str, conditions: Optional[Dict[str, Any]] = None,
                         limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        데이터 조회
        
        Args:
            table_name: 테이블 이름
            conditions: 조회 조건
            limit: 조회 개수 제한
            
        Returns:
            조회된 데이터 목록
        """
        try:
            table = self.supabase.get_table(table_name, use_service_key=True)
            
            # 조건 적용
            query = table.select("*")
            if conditions:
                for key, value in conditions.items():
                    query = query.eq(key, value)
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            
            if result.data is not None:
                logger.info(f"데이터 조회 성공: {table_name}, {len(result.data)}개")
                return result.data
            else:
                return []
                
        except Exception as e:
            logger.error(f"데이터 조회 실패: {e}")
            raise
    
    async def delete_data(self, table_name: str, conditions: Dict[str, Any]) -> bool:
        """
        데이터 삭제
        
        Args:
            table_name: 테이블 이름
            conditions: 삭제 조건
            
        Returns:
            삭제 성공 여부
        """
        try:
            table = self.supabase.get_table(table_name, use_service_key=True)
            
            # 조건 적용
            query = table.delete()
            for key, value in conditions.items():
                query = query.eq(key, value)
            
            result = query.execute()
            
            logger.info(f"데이터 삭제 성공: {table_name}")
            return True
                
        except Exception as e:
            logger.error(f"데이터 삭제 실패: {e}")
            raise
    
    async def upsert_data(self, table_name: str, data: Dict[str, Any], 
                         conflict_columns: List[str]) -> Dict[str, Any]:
        """
        데이터 삽입 또는 업데이트 (upsert)
        
        Args:
            table_name: 테이블 이름
            data: 데이터
            conflict_columns: 충돌 컬럼 목록
            
        Returns:
            처리된 데이터
        """
        try:
            table = self.supabase.get_table(table_name, use_service_key=True)
            result = table.upsert(data, on_conflict=','.join(conflict_columns)).execute()
            
            if result.data:
                logger.info(f"데이터 upsert 성공: {table_name}")
                return result.data[0]
            else:
                raise Exception("데이터 upsert 실패")
                
        except Exception as e:
            logger.error(f"데이터 upsert 실패: {e}")
            raise


# 전역 인스턴스
database_service = DatabaseService()
