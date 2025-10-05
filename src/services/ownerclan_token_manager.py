#!/usr/bin/env python3
"""
오너클랜 JWT 토큰 관리자
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from src.config.settings import settings
from src.utils.error_handler import ErrorHandler
from src.services.supplier_account_manager import supplier_account_manager


class OwnerClanTokenManager:
    """오너클랜 JWT 토큰 관리자"""
    
    def __init__(self):
        self.settings = settings
        self.error_handler = ErrorHandler()
        self.auth_endpoint = "https://auth.ownerclan.com/auth"
        self._token_cache: Dict[str, Dict[str, Any]] = {}
    
    async def get_auth_token(self, account_name: str, force_refresh: bool = False) -> Optional[str]:
        """
        오너클랜 인증 토큰 조회
        Args:
            account_name: 계정 이름
            force_refresh: 강제 토큰 갱신 여부
        Returns:
            JWT 토큰 문자열 또는 None
        """
        try:
            # 캐시된 토큰 확인
            if not force_refresh and account_name in self._token_cache:
                cached_token = self._token_cache[account_name]
                if datetime.now() < cached_token['expires_at']:
                    logger.debug(f"캐시된 토큰 사용: {account_name}")
                    return cached_token['token']
            
            # 계정 정보 조회
            credentials = await supplier_account_manager.get_ownerclan_credentials(account_name)
            if not credentials:
                logger.error(f"계정 정보를 찾을 수 없습니다: {account_name}")
                return None
            
            # 인증 요청
            auth_data = {
                "service": "ownerclan",
                "userType": "seller",
                "username": credentials["username"],
                "password": credentials["password"]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.auth_endpoint,
                    json=auth_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        if response_text.startswith("eyJ"):
                            token = response_text.strip()
                            
                            # 토큰 캐시 저장 (30일 유효)
                            expires_at = datetime.now() + timedelta(days=30)
                            self._token_cache[account_name] = {
                                'token': token,
                                'expires_at': expires_at
                            }
                            
                            logger.info(f"토큰 발급 성공: {account_name}")
                            return token
                        else:
                            logger.error(f"토큰 형식이 올바르지 않습니다: {account_name}")
                            return None
                    else:
                        logger.error(f"인증 실패: {response.status} - {account_name}")
                        return None
                        
        except Exception as e:
            self.error_handler.log_error(e, f"토큰 발급 실패: {account_name}")
            return None
    
    async def refresh_token(self, account_name: str) -> Optional[str]:
        """토큰 강제 갱신"""
        return await self.get_auth_token(account_name, force_refresh=True)
    
    def clear_token_cache(self, account_name: Optional[str] = None):
        """토큰 캐시 삭제"""
        if account_name:
            if account_name in self._token_cache:
                del self._token_cache[account_name]
                logger.info(f"토큰 캐시 삭제: {account_name}")
        else:
            self._token_cache.clear()
            logger.info("모든 토큰 캐시 삭제")
    
    def get_cached_token_info(self, account_name: str) -> Optional[Dict[str, Any]]:
        """캐시된 토큰 정보 조회"""
        if account_name in self._token_cache:
            token_info = self._token_cache[account_name].copy()
            token_info['expires_at'] = token_info['expires_at'].isoformat()
            return token_info
        return None


# 전역 인스턴스
ownerclan_token_manager = OwnerClanTokenManager()