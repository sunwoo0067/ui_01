"""
웹훅 시스템 구현
외부 시스템과의 실시간 데이터 동기화를 위한 웹훅 서비스
"""

import asyncio
import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import aiohttp
from loguru import logger

from src.services.database_service import DatabaseService
from src.utils.error_handler import ErrorHandler


class WebhookEventType(Enum):
    """웹훅 이벤트 타입"""
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_CANCELLED = "order.cancelled"
    PRICE_CHANGED = "price.changed"
    INVENTORY_UPDATED = "inventory.updated"
    MARKETPLACE_SYNC = "marketplace.sync"
    AI_PREDICTION = "ai.prediction"


@dataclass
class WebhookEndpoint:
    """웹훅 엔드포인트 정보"""
    id: str
    url: str
    secret: str
    events: List[WebhookEventType]
    is_active: bool = True
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 30
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class WebhookPayload:
    """웹훅 페이로드"""
    event_type: WebhookEventType
    data: Dict[str, Any]
    timestamp: datetime
    webhook_id: str
    signature: Optional[str] = None


class WebhookService:
    """웹훅 서비스"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession()
        await self.load_endpoints()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
    
    async def load_endpoints(self):
        """데이터베이스에서 웹훅 엔드포인트 로드"""
        try:
            endpoints_data = await self.db_service.select_data(
                "webhook_endpoints"
            )
            
            for endpoint_data in endpoints_data:
                endpoint = WebhookEndpoint(
                    id=endpoint_data["id"],
                    url=endpoint_data["url"],
                    secret=endpoint_data["secret"],
                    events=[WebhookEventType(e) for e in endpoint_data["events"]],
                    is_active=endpoint_data["is_active"],
                    retry_count=endpoint_data.get("retry_count", 0),
                    max_retries=endpoint_data.get("max_retries", 3),
                    timeout=endpoint_data.get("timeout", 30),
                    created_at=endpoint_data.get("created_at"),
                    updated_at=endpoint_data.get("updated_at")
                )
                self.endpoints[endpoint.id] = endpoint
                
            logger.info(f"✅ {len(self.endpoints)}개 웹훅 엔드포인트 로드 완료")
            
        except Exception as e:
            ErrorHandler.log_error(e, "웹훅 엔드포인트 로드 실패")
    
    async def create_endpoint(self, endpoint: WebhookEndpoint) -> bool:
        """웹훅 엔드포인트 생성"""
        try:
            endpoint_data = {
                "id": endpoint.id,
                "url": endpoint.url,
                "secret": endpoint.secret,
                "events": [e.value for e in endpoint.events],
                "is_active": endpoint.is_active,
                "retry_count": endpoint.retry_count,
                "max_retries": endpoint.max_retries,
                "timeout": endpoint.timeout,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            await self.db_service.insert_data("webhook_endpoints", endpoint_data)
            self.endpoints[endpoint.id] = endpoint
            
            logger.info(f"✅ 웹훅 엔드포인트 생성: {endpoint.url}")
            return True
            
        except Exception as e:
            ErrorHandler.log_error(e, f"웹훅 엔드포인트 생성 실패: {endpoint.url}")
            return False
    
    async def update_endpoint(self, endpoint_id: str, updates: Dict[str, Any]) -> bool:
        """웹훅 엔드포인트 업데이트"""
        try:
            updates["updated_at"] = datetime.now().isoformat()
            
            await self.db_service.update_data(
                "webhook_endpoints",
                filters={"id": endpoint_id},
                updates=updates
            )
            
            if endpoint_id in self.endpoints:
                for key, value in updates.items():
                    if hasattr(self.endpoints[endpoint_id], key):
                        setattr(self.endpoints[endpoint_id], key, value)
            
            logger.info(f"✅ 웹훅 엔드포인트 업데이트: {endpoint_id}")
            return True
            
        except Exception as e:
            ErrorHandler.log_error(e, f"웹훅 엔드포인트 업데이트 실패: {endpoint_id}")
            return False
    
    async def delete_endpoint(self, endpoint_id: str) -> bool:
        """웹훅 엔드포인트 삭제"""
        try:
            await self.db_service.update_data(
                "webhook_endpoints",
                filters={"id": endpoint_id},
                updates={"is_active": False, "updated_at": datetime.now().isoformat()}
            )
            
            if endpoint_id in self.endpoints:
                del self.endpoints[endpoint_id]
            
            logger.info(f"✅ 웹훅 엔드포인트 삭제: {endpoint_id}")
            return True
            
        except Exception as e:
            ErrorHandler.log_error(e, f"웹훅 엔드포인트 삭제 실패: {endpoint_id}")
            return False
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """웹훅 서명 생성"""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def send_webhook(self, endpoint: WebhookEndpoint, payload: WebhookPayload) -> bool:
        """웹훅 전송"""
        try:
            payload_json = json.dumps({
                "event_type": payload.event_type.value,
                "data": payload.data,
                "timestamp": payload.timestamp.isoformat(),
                "webhook_id": payload.webhook_id
            }, ensure_ascii=False)
            
            signature = self._generate_signature(payload_json, endpoint.secret)
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": f"sha256={signature}",
                "X-Webhook-Event": payload.event_type.value,
                "User-Agent": "DropshippingBot/1.0"
            }
            
            timeout = aiohttp.ClientTimeout(total=endpoint.timeout)
            
            async with self.session.post(
                endpoint.url,
                data=payload_json,
                headers=headers,
                timeout=timeout
            ) as response:
                
                if response.status in [200, 201, 202]:
                    logger.info(f"✅ 웹훅 전송 성공: {endpoint.url} ({response.status})")
                    return True
                else:
                    logger.warning(f"⚠️ 웹훅 전송 실패: {endpoint.url} ({response.status})")
                    return False
                    
        except asyncio.TimeoutError:
            logger.error(f"⏰ 웹훅 전송 타임아웃: {endpoint.url}")
            return False
        except Exception as e:
            ErrorHandler.log_error(e, f"웹훅 전송 오류: {endpoint.url}")
            return False
    
    async def trigger_webhook(self, event_type: WebhookEventType, data: Dict[str, Any]) -> Dict[str, Any]:
        """웹훅 트리거"""
        results = {
            "total_endpoints": 0,
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        payload = WebhookPayload(
            event_type=event_type,
            data=data,
            timestamp=datetime.now(),
            webhook_id=f"wh_{int(datetime.now().timestamp())}"
        )
        
        # 해당 이벤트를 구독하는 엔드포인트 찾기
        target_endpoints = [
            endpoint for endpoint in self.endpoints.values()
            if event_type in endpoint.events and endpoint.is_active
        ]
        
        results["total_endpoints"] = len(target_endpoints)
        
        if not target_endpoints:
            logger.info(f"📭 {event_type.value} 이벤트 구독 엔드포인트 없음")
            return results
        
        # 각 엔드포인트로 웹훅 전송
        tasks = []
        for endpoint in target_endpoints:
            task = asyncio.create_task(self._send_with_retry(endpoint, payload))
            tasks.append((endpoint.id, task))
        
        # 모든 웹훅 전송 완료 대기
        for endpoint_id, task in tasks:
            try:
                success = await task
                if success:
                    results["successful"] += 1
                    results["details"].append({
                        "endpoint_id": endpoint_id,
                        "status": "success"
                    })
                else:
                    results["failed"] += 1
                    results["details"].append({
                        "endpoint_id": endpoint_id,
                        "status": "failed"
                    })
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "endpoint_id": endpoint_id,
                    "status": "error",
                    "error": str(e)
                })
        
        logger.info(f"📤 웹훅 전송 완료: {event_type.value} - 성공: {results['successful']}, 실패: {results['failed']}")
        return results
    
    async def _send_with_retry(self, endpoint: WebhookEndpoint, payload: WebhookPayload) -> bool:
        """재시도 로직이 포함된 웹훅 전송"""
        for attempt in range(endpoint.max_retries + 1):
            try:
                success = await self.send_webhook(endpoint, payload)
                if success:
                    # 성공 시 재시도 카운트 리셋
                    if endpoint.retry_count > 0:
                        await self.update_endpoint(endpoint.id, {"retry_count": 0})
                    return True
                else:
                    # 실패 시 재시도 카운트 증가
                    await self.update_endpoint(endpoint.id, {"retry_count": endpoint.retry_count + 1})
                    
            except Exception as e:
                logger.error(f"웹훅 전송 시도 {attempt + 1} 실패: {endpoint.url} - {e}")
                
            if attempt < endpoint.max_retries:
                # 지수 백오프 대기
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
        
        logger.error(f"❌ 웹훅 전송 최종 실패: {endpoint.url} (최대 재시도 횟수 초과)")
        return False
    
    async def get_endpoint_stats(self) -> Dict[str, Any]:
        """웹훅 엔드포인트 통계 조회"""
        try:
            stats = {
                "total_endpoints": len(self.endpoints),
                "active_endpoints": len([e for e in self.endpoints.values() if e.is_active]),
                "inactive_endpoints": len([e for e in self.endpoints.values() if not e.is_active]),
                "endpoints_with_retries": len([e for e in self.endpoints.values() if e.retry_count > 0]),
                "event_subscriptions": {}
            }
            
            # 이벤트별 구독 수 계산
            for event_type in WebhookEventType:
                count = len([
                    e for e in self.endpoints.values()
                    if event_type in e.events and e.is_active
                ])
                stats["event_subscriptions"][event_type.value] = count
            
            return stats
            
        except Exception as e:
            ErrorHandler.log_error(e, "웹훅 통계 조회 실패")
            return {}


class WebhookManager:
    """웹훅 매니저 - 비즈니스 로직과 웹훅 서비스 연결"""
    
    def __init__(self, webhook_service: WebhookService):
        self.webhook_service = webhook_service
    
    async def notify_product_created(self, product_data: Dict[str, Any]):
        """상품 생성 알림"""
        await self.webhook_service.trigger_webhook(
            WebhookEventType.PRODUCT_CREATED,
            product_data
        )
    
    async def notify_product_updated(self, product_data: Dict[str, Any]):
        """상품 업데이트 알림"""
        await self.webhook_service.trigger_webhook(
            WebhookEventType.PRODUCT_UPDATED,
            product_data
        )
    
    async def notify_order_created(self, order_data: Dict[str, Any]):
        """주문 생성 알림"""
        await self.webhook_service.trigger_webhook(
            WebhookEventType.ORDER_CREATED,
            order_data
        )
    
    async def notify_price_changed(self, price_data: Dict[str, Any]):
        """가격 변경 알림"""
        await self.webhook_service.trigger_webhook(
            WebhookEventType.PRICE_CHANGED,
            price_data
        )
    
    async def notify_ai_prediction(self, prediction_data: Dict[str, Any]):
        """AI 예측 결과 알림"""
        await self.webhook_service.trigger_webhook(
            WebhookEventType.AI_PREDICTION,
            prediction_data
        )
    
    async def notify_marketplace_sync(self, sync_data: Dict[str, Any]):
        """마켓플레이스 동기화 알림"""
        await self.webhook_service.trigger_webhook(
            WebhookEventType.MARKETPLACE_SYNC,
            sync_data
        )
    
    async def notify_inventory_updated(self, inventory_data: Dict[str, Any]):
        """재고 업데이트 알림"""
        await self.webhook_service.trigger_webhook(
            WebhookEventType.INVENTORY_UPDATED,
            inventory_data
        )


# 테스트 함수
async def test_webhook_system():
    """웹훅 시스템 테스트"""
    logger.info("🧪 웹훅 시스템 테스트 시작")
    
    db_service = DatabaseService()
    
    async with WebhookService(db_service) as webhook_service:
        # 테스트 엔드포인트 생성
        test_endpoint = WebhookEndpoint(
            id="test_endpoint_1",
            url="https://webhook.site/your-unique-url",
            secret="test_secret_key",
            events=[WebhookEventType.PRODUCT_CREATED, WebhookEventType.PRICE_CHANGED],
            max_retries=2,
            timeout=10
        )
        
        # 엔드포인트 생성
        await webhook_service.create_endpoint(test_endpoint)
        
        # 테스트 웹훅 전송
        test_data = {
            "product_id": "test_product_123",
            "name": "테스트 상품",
            "price": 10000,
            "category": "electronics"
        }
        
        results = await webhook_service.trigger_webhook(
            WebhookEventType.PRODUCT_CREATED,
            test_data
        )
        
        logger.info(f"📊 웹훅 테스트 결과: {results}")
        
        # 통계 조회
        stats = await webhook_service.get_endpoint_stats()
        logger.info(f"📈 웹훅 통계: {stats}")


if __name__ == "__main__":
    asyncio.run(test_webhook_system())
