"""
API 연동 서비스 구현
외부 API와의 통합을 위한 서비스
"""

import asyncio
import json
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from src.services.database_service import DatabaseService
from src.utils.error_handler import ErrorHandler


class APIType(Enum):
    """API 타입"""
    REST = "rest"
    GRAPHQL = "graphql"
    SOAP = "soap"
    WEBHOOK = "webhook"


class AuthType(Enum):
    """인증 타입"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"
    JWT = "jwt"


@dataclass
class APIConfig:
    """API 설정"""
    id: str
    name: str
    base_url: str
    api_type: APIType
    auth_type: AuthType
    auth_config: Dict[str, Any]
    headers: Dict[str, str]
    timeout: int = 30
    retry_count: int = 3
    rate_limit: Optional[int] = None  # requests per minute
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class APIRequest:
    """API 요청"""
    method: str
    endpoint: str
    params: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None


@dataclass
class APIResponse:
    """API 응답"""
    status_code: int
    data: Any
    headers: Dict[str, str]
    success: bool
    error_message: Optional[str] = None
    response_time: float = 0.0


class APIConnector:
    """API 연결자"""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time: Optional[datetime] = None
        self.request_count = 0
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """인증 헤더 생성"""
        headers = {}
        
        if self.config.auth_type == AuthType.API_KEY:
            api_key = self.config.auth_config.get("api_key")
            key_name = self.config.auth_config.get("key_name", "X-API-Key")
            if api_key:
                headers[key_name] = api_key
                
        elif self.config.auth_type == AuthType.BEARER_TOKEN:
            token = self.config.auth_config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
                
        elif self.config.auth_type == AuthType.BASIC_AUTH:
            username = self.config.auth_config.get("username")
            password = self.config.auth_config.get("password")
            if username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
                
        elif self.config.auth_type == AuthType.JWT:
            token = self.config.auth_config.get("jwt_token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    async def _check_rate_limit(self):
        """레이트 리미트 확인"""
        if not self.config.rate_limit:
            return
            
        now = datetime.now()
        
        # 1분 단위로 리셋
        if self.last_request_time and (now - self.last_request_time).seconds >= 60:
            self.request_count = 0
            
        if self.request_count >= self.config.rate_limit:
            wait_time = 60 - (now - self.last_request_time).seconds
            logger.warning(f"⏰ 레이트 리미트 도달, {wait_time}초 대기")
            await asyncio.sleep(wait_time)
            self.request_count = 0
    
    async def make_request(self, request: APIRequest) -> APIResponse:
        """API 요청 실행"""
        start_time = datetime.now()
        
        try:
            # 레이트 리미트 확인
            await self._check_rate_limit()
            
            # 기본 헤더와 인증 헤더 병합
            headers = {**self.config.headers, **self._get_auth_headers()}
            if request.headers:
                headers.update(request.headers)
            
            # URL 구성
            url = f"{self.config.base_url.rstrip('/')}/{request.endpoint.lstrip('/')}"
            
            # 타임아웃 설정
            timeout = aiohttp.ClientTimeout(total=request.timeout or self.config.timeout)
            
            # 요청 실행
            async with self.session.request(
                method=request.method.upper(),
                url=url,
                params=request.params,
                json=request.data,
                headers=headers,
                timeout=timeout
            ) as response:
                
                # 응답 데이터 파싱
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                # 요청 카운트 업데이트
                self.request_count += 1
                self.last_request_time = datetime.now()
                
                return APIResponse(
                    status_code=response.status,
                    data=response_data,
                    headers=dict(response.headers),
                    success=200 <= response.status < 300,
                    response_time=response_time
                )
                
        except asyncio.TimeoutError:
            response_time = (datetime.now() - start_time).total_seconds()
            return APIResponse(
                status_code=408,
                data=None,
                headers={},
                success=False,
                error_message="Request timeout",
                response_time=response_time
            )
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return APIResponse(
                status_code=500,
                data=None,
                headers={},
                success=False,
                error_message=str(e),
                response_time=response_time
            )


class APIIntegrationService:
    """API 연동 서비스"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.connectors: Dict[str, APIConnector] = {}
        
    async def load_configs(self):
        """API 설정 로드"""
        try:
            configs_data = await self.db_service.select_data(
                "api_integrations"
            )
            
            for config_data in configs_data:
                config = APIConfig(
                    id=config_data["id"],
                    name=config_data["name"],
                    base_url=config_data["base_url"],
                    api_type=APIType(config_data["api_type"]),
                    auth_type=AuthType(config_data["auth_type"]),
                    auth_config=config_data["auth_config"],
                    headers=config_data["headers"],
                    timeout=config_data.get("timeout", 30),
                    retry_count=config_data.get("retry_count", 3),
                    rate_limit=config_data.get("rate_limit"),
                    is_active=config_data["is_active"],
                    created_at=config_data.get("created_at"),
                    updated_at=config_data.get("updated_at")
                )
                
                self.connectors[config.id] = APIConnector(config)
                
            logger.info(f"✅ {len(self.connectors)}개 API 연동 설정 로드 완료")
            
        except Exception as e:
            ErrorHandler.log_error(e, "API 연동 설정 로드 실패")
    
    async def create_config(self, config: APIConfig) -> bool:
        """API 설정 생성"""
        try:
            config_data = {
                "id": config.id,
                "name": config.name,
                "base_url": config.base_url,
                "api_type": config.api_type.value,
                "auth_type": config.auth_type.value,
                "auth_config": config.auth_config,
                "headers": config.headers,
                "timeout": config.timeout,
                "retry_count": config.retry_count,
                "rate_limit": config.rate_limit,
                "is_active": config.is_active,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            await self.db_service.insert_data("api_integrations", config_data)
            self.connectors[config.id] = APIConnector(config)
            
            logger.info(f"✅ API 연동 설정 생성: {config.name}")
            return True
            
        except Exception as e:
            ErrorHandler.log_error(e, f"API 연동 설정 생성 실패: {config.name}")
            return False
    
    async def make_api_call(self, config_id: str, request: APIRequest) -> APIResponse:
        """API 호출"""
        if config_id not in self.connectors:
            return APIResponse(
                status_code=404,
                data=None,
                headers={},
                success=False,
                error_message=f"API 설정을 찾을 수 없습니다: {config_id}"
            )
        
        connector = self.connectors[config_id]
        
        async with connector as conn:
            return await conn.make_request(request)
    
    async def test_connection(self, config_id: str) -> Dict[str, Any]:
        """연결 테스트"""
        try:
            # 간단한 GET 요청으로 연결 테스트
            test_request = APIRequest(
                method="GET",
                endpoint="/health"  # 또는 "/" 또는 API별 헬스체크 엔드포인트
            )
            
            response = await self.make_api_call(config_id, test_request)
            
            return {
                "success": response.success,
                "status_code": response.status_code,
                "response_time": response.response_time,
                "error_message": response.error_message
            }
            
        except Exception as e:
            ErrorHandler.log_error(e, f"API 연결 테스트 실패: {config_id}")
            return {
                "success": False,
                "error_message": str(e)
            }
    
    async def get_integration_stats(self) -> Dict[str, Any]:
        """연동 통계 조회"""
        try:
            stats = {
                "total_integrations": len(self.connectors),
                "active_integrations": len([c for c in self.connectors.values() if c.config.is_active]),
                "api_types": {},
                "auth_types": {}
            }
            
            # API 타입별 통계
            for connector in self.connectors.values():
                api_type = connector.config.api_type.value
                stats["api_types"][api_type] = stats["api_types"].get(api_type, 0) + 1
                
                auth_type = connector.config.auth_type.value
                stats["auth_types"][auth_type] = stats["auth_types"].get(auth_type, 0) + 1
            
            return stats
            
        except Exception as e:
            ErrorHandler.log_error(e, "API 연동 통계 조회 실패")
            return {}


class ExternalSystemManager:
    """외부 시스템 매니저"""
    
    def __init__(self, api_service: APIIntegrationService):
        self.api_service = api_service
    
    async def sync_products_to_marketplace(self, marketplace_id: str, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """마켓플레이스에 상품 동기화"""
        results = {
            "total_products": len(products),
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for product in products:
            try:
                request = APIRequest(
                    method="POST",
                    endpoint="/products",
                    data=product
                )
                
                response = await self.api_service.make_api_call(marketplace_id, request)
                
                if response.success:
                    results["successful"] += 1
                    results["details"].append({
                        "product_id": product.get("id"),
                        "status": "success",
                        "marketplace_response": response.data
                    })
                else:
                    results["failed"] += 1
                    results["details"].append({
                        "product_id": product.get("id"),
                        "status": "failed",
                        "error": response.error_message
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "product_id": product.get("id"),
                    "status": "error",
                    "error": str(e)
                })
        
        logger.info(f"📤 마켓플레이스 상품 동기화 완료: {marketplace_id} - 성공: {results['successful']}, 실패: {results['failed']}")
        return results
    
    async def fetch_orders_from_supplier(self, supplier_id: str, date_from: datetime = None) -> Dict[str, Any]:
        """공급사에서 주문 정보 가져오기"""
        try:
            params = {}
            if date_from:
                params["date_from"] = date_from.isoformat()
            
            request = APIRequest(
                method="GET",
                endpoint="/orders",
                params=params
            )
            
            response = await self.api_service.make_api_call(supplier_id, request)
            
            if response.success:
                logger.info(f"✅ 공급사 주문 정보 조회 성공: {supplier_id}")
                return {
                    "success": True,
                    "orders": response.data,
                    "total_count": len(response.data) if isinstance(response.data, list) else 1
                }
            else:
                logger.error(f"❌ 공급사 주문 정보 조회 실패: {supplier_id}")
                return {
                    "success": False,
                    "error": response.error_message
                }
                
        except Exception as e:
            ErrorHandler.log_error(e, f"공급사 주문 정보 조회 실패: {supplier_id}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_inventory_to_supplier(self, supplier_id: str, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """공급사에 재고 정보 업데이트"""
        try:
            request = APIRequest(
                method="PUT",
                endpoint="/inventory",
                data=inventory_data
            )
            
            response = await self.api_service.make_api_call(supplier_id, request)
            
            if response.success:
                logger.info(f"✅ 공급사 재고 정보 업데이트 성공: {supplier_id}")
                return {
                    "success": True,
                    "response": response.data
                }
            else:
                logger.error(f"❌ 공급사 재고 정보 업데이트 실패: {supplier_id}")
                return {
                    "success": False,
                    "error": response.error_message
                }
                
        except Exception as e:
            ErrorHandler.log_error(e, f"공급사 재고 정보 업데이트 실패: {supplier_id}")
            return {
                "success": False,
                "error": str(e)
            }


# 테스트 함수
async def test_api_integration():
    """API 연동 테스트"""
    logger.info("🧪 API 연동 시스템 테스트 시작")
    
    db_service = DatabaseService()
    api_service = APIIntegrationService(db_service)
    
    # 테스트 API 설정 생성
    test_config = APIConfig(
        id="test_api_1",
        name="테스트 API",
        base_url="https://jsonplaceholder.typicode.com",
        api_type=APIType.REST,
        auth_type=AuthType.NONE,
        auth_config={},
        headers={"User-Agent": "DropshippingBot/1.0"},
        timeout=30,
        retry_count=3
    )
    
    # 설정 생성
    await api_service.create_config(test_config)
    
    # 연결 테스트
    test_result = await api_service.test_connection("test_api_1")
    logger.info(f"📊 API 연결 테스트 결과: {test_result}")
    
    # API 호출 테스트
    request = APIRequest(
        method="GET",
        endpoint="/posts/1"
    )
    
    response = await api_service.make_api_call("test_api_1", request)
    logger.info(f"📤 API 호출 결과: {response.status_code} - {response.success}")
    
    # 통계 조회
    stats = await api_service.get_integration_stats()
    logger.info(f"📈 API 연동 통계: {stats}")


if __name__ == "__main__":
    asyncio.run(test_api_integration())
