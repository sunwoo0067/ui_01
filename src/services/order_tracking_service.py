"""
주문 상태 추적 및 동기화 서비스
도매꾹 주문의 상태를 추적하고 동기화하는 서비스
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
from loguru import logger

from src.services.database_service import DatabaseService
from src.services.supplier_account_manager import SupplierAccountManager
from src.utils.error_handler import ErrorHandler


class OrderStatus(Enum):
    """주문 상태 열거형"""
    PENDING = "pending"           # 주문 대기
    CONFIRMED = "confirmed"       # 주문 확인
    PREPARING = "preparing"       # 배송 준비중
    SHIPPED = "shipped"          # 배송중
    DELIVERED = "delivered"       # 배송 완료
    CANCELLED = "cancelled"       # 주문 취소
    RETURNED = "returned"        # 반품
    REFUNDED = "refunded"         # 환불


class OrderTrackingService:
    """주문 상태 추적 및 동기화 서비스"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
        self.account_manager = SupplierAccountManager()
        
        # 주문 상태 매핑 (도매꾹 상태 -> 시스템 상태)
        self.status_mapping = {
            "주문대기": OrderStatus.PENDING.value,
            "주문확인": OrderStatus.CONFIRMED.value,
            "배송준비중": OrderStatus.PREPARING.value,
            "배송중": OrderStatus.SHIPPED.value,
            "배송완료": OrderStatus.DELIVERED.value,
            "주문취소": OrderStatus.CANCELLED.value,
            "반품": OrderStatus.RETURNED.value,
            "환불": OrderStatus.REFUNDED.value
        }
    
    async def create_order_tracking(self, order_data: Dict[str, Any]) -> str:
        """
        새로운 주문 추적 생성
        
        Args:
            order_data: 주문 데이터
            
        Returns:
            str: 주문 추적 ID
        """
        try:
            logger.info(f"주문 추적 생성: {order_data.get('order_id', 'Unknown')}")
            
            # 주문 추적 데이터 구성
            tracking_data = {
                "order_id": order_data.get("order_id"),
                "supplier_id": order_data.get("supplier_id"),
                "supplier_account_id": order_data.get("supplier_account_id"),
                "supplier_order_id": order_data.get("supplier_order_id"),
                "current_status": OrderStatus.PENDING.value,
                "status_history": json.dumps([{
                    "status": OrderStatus.PENDING.value,
                    "timestamp": datetime.utcnow().isoformat(),
                    "note": "주문 추적 시작"
                }]),
                "order_details": json.dumps(order_data),
                "last_updated": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "is_active": True
            }
            
            # 데이터베이스에 저장
            result = await self.db_service.insert_data("order_tracking", tracking_data)
            
            if result:
                logger.info(f"주문 추적 생성 완료: {tracking_data['order_id']}")
                return tracking_data["order_id"]
            else:
                logger.error(f"주문 추적 생성 실패: {tracking_data['order_id']}")
                return None
                
        except Exception as e:
            self.error_handler.log_error(e, f"주문 추적 생성 실패: {order_data.get('order_id', 'Unknown')}")
            return None
    
    async def update_order_status(self, order_id: str, new_status: str, note: str = "") -> bool:
        """
        주문 상태 업데이트
        
        Args:
            order_id: 주문 ID
            new_status: 새로운 상태
            note: 상태 변경 메모
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            logger.info(f"주문 상태 업데이트: {order_id} -> {new_status}")
            
            # 기존 주문 추적 데이터 조회
            existing = await self.db_service.select_data(
                "order_tracking",
                {"order_id": order_id}
            )
            
            if not existing:
                logger.error(f"주문 추적 데이터를 찾을 수 없습니다: {order_id}")
                return False
            
            tracking_record = existing[0]
            
            # 상태 히스토리 업데이트
            status_history = json.loads(tracking_record.get("status_history", "[]"))
            status_history.append({
                "status": new_status,
                "timestamp": datetime.utcnow().isoformat(),
                "note": note
            })
            
            # 업데이트 데이터 구성
            update_data = {
                "current_status": new_status,
                "status_history": json.dumps(status_history),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # 데이터베이스 업데이트
            result = await self.db_service.update_data(
                "order_tracking",
                update_data,
                {"order_id": order_id}
            )
            
            if result:
                logger.info(f"주문 상태 업데이트 완료: {order_id} -> {new_status}")
                return True
            else:
                logger.error(f"주문 상태 업데이트 실패: {order_id}")
                return False
                
        except Exception as e:
            self.error_handler.log_error(e, f"주문 상태 업데이트 실패: {order_id}")
            return False
    
    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        주문 상태 조회
        
        Args:
            order_id: 주문 ID
            
        Returns:
            Dict: 주문 상태 정보
        """
        try:
            result = await self.db_service.select_data(
                "order_tracking",
                {"order_id": order_id}
            )
            
            if result:
                tracking_record = result[0]
                return {
                    "order_id": tracking_record["order_id"],
                    "current_status": tracking_record["current_status"],
                    "status_history": json.loads(tracking_record.get("status_history", "[]")),
                    "last_updated": tracking_record["last_updated"],
                    "is_active": tracking_record["is_active"]
                }
            else:
                logger.warning(f"주문 추적 데이터를 찾을 수 없습니다: {order_id}")
                return None
                
        except Exception as e:
            self.error_handler.log_error(e, f"주문 상태 조회 실패: {order_id}")
            return None
    
    async def get_active_orders(self, supplier_id: Optional[str] = None, 
                              status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        활성 주문 목록 조회
        
        Args:
            supplier_id: 공급사 ID (선택사항)
            status: 주문 상태 (선택사항)
            
        Returns:
            List[Dict]: 활성 주문 목록
        """
        try:
            filters = {"is_active": True}
            
            if supplier_id:
                filters["supplier_id"] = supplier_id
            if status:
                filters["current_status"] = status
            
            result = await self.db_service.select_data(
                "order_tracking",
                filters
            )
            
            orders = []
            for record in result:
                orders.append({
                    "order_id": record["order_id"],
                    "supplier_id": record["supplier_id"],
                    "supplier_order_id": record["supplier_order_id"],
                    "current_status": record["current_status"],
                    "status_history": json.loads(record.get("status_history", "[]")),
                    "last_updated": record["last_updated"],
                    "created_at": record["created_at"]
                })
            
            logger.info(f"활성 주문 조회 완료: {len(orders)}개")
            return orders
            
        except Exception as e:
            self.error_handler.log_error(e, "활성 주문 조회 실패")
            return []
    
    async def sync_order_status_from_supplier(self, supplier_id: str, 
                                            account_name: str) -> Dict[str, Any]:
        """
        공급사에서 주문 상태 동기화
        
        Args:
            supplier_id: 공급사 ID
            account_name: 계정 이름
            
        Returns:
            Dict: 동기화 결과
        """
        try:
            logger.info(f"공급사 주문 상태 동기화 시작: {supplier_id}/{account_name}")
            
            # 공급사별 동기화 로직
            if supplier_id == "domaemae_dome" or supplier_id == "domaemae_supply":
                return await self._sync_domaemae_orders(supplier_id, account_name)
            elif supplier_id == "ownerclan":
                return await self._sync_ownerclan_orders(supplier_id, account_name)
            elif supplier_id == "zentrade":
                return await self._sync_zentrade_orders(supplier_id, account_name)
            else:
                logger.warning(f"지원하지 않는 공급사: {supplier_id}")
                return {
                    "success": False,
                    "error": f"지원하지 않는 공급사: {supplier_id}",
                    "synced_count": 0
                }
                
        except Exception as e:
            self.error_handler.log_error(e, f"공급사 주문 상태 동기화 실패: {supplier_id}/{account_name}")
            return {
                "success": False,
                "error": str(e),
                "synced_count": 0
            }
    
    async def _sync_domaemae_orders(self, supplier_id: str, account_name: str) -> Dict[str, Any]:
        """도매꾹 주문 상태 동기화"""
        try:
            logger.info(f"도매꾹 주문 상태 동기화: {supplier_id}/{account_name}")
            
            # 도매꾹 API는 주문 조회를 직접 지원하지 않으므로
            # 로컬 주문 데이터를 기반으로 상태 추적
            synced_count = 0
            
            # 활성 주문 조회
            active_orders = await self.get_active_orders(supplier_id)
            
            for order in active_orders:
                # 주문 상태 업데이트 로직 (실제로는 공급사 API 호출)
                # 여기서는 시뮬레이션
                current_status = order["current_status"]
                
                # 상태 전환 로직 (예시)
                if current_status == OrderStatus.PENDING.value:
                    # 주문 확인으로 전환
                    await self.update_order_status(
                        order["order_id"], 
                        OrderStatus.CONFIRMED.value,
                        "주문 확인됨"
                    )
                    synced_count += 1
                elif current_status == OrderStatus.CONFIRMED.value:
                    # 배송 준비중으로 전환
                    await self.update_order_status(
                        order["order_id"],
                        OrderStatus.PREPARING.value,
                        "배송 준비중"
                    )
                    synced_count += 1
            
            logger.info(f"도매꾹 주문 상태 동기화 완료: {synced_count}개")
            return {
                "success": True,
                "synced_count": synced_count,
                "message": f"도매꾹 주문 상태 동기화 완료: {synced_count}개"
            }
            
        except Exception as e:
            self.error_handler.log_error(e, f"도매꾹 주문 상태 동기화 실패: {supplier_id}/{account_name}")
            return {
                "success": False,
                "error": str(e),
                "synced_count": 0
            }
    
    async def _sync_ownerclan_orders(self, supplier_id: str, account_name: str) -> Dict[str, Any]:
        """오너클랜 주문 상태 동기화"""
        try:
            logger.info(f"오너클랜 주문 상태 동기화: {supplier_id}/{account_name}")
            
            # 오너클랜 API를 통한 주문 상태 동기화
            # 실제 구현에서는 오너클랜 API 호출
            synced_count = 0
            
            # 활성 주문 조회
            active_orders = await self.get_active_orders(supplier_id)
            
            for order in active_orders:
                # 오너클랜 API 호출하여 실제 상태 확인
                # 여기서는 시뮬레이션
                await self.update_order_status(
                    order["order_id"],
                    OrderStatus.SHIPPED.value,
                    "오너클랜에서 배송중으로 상태 변경"
                )
                synced_count += 1
            
            logger.info(f"오너클랜 주문 상태 동기화 완료: {synced_count}개")
            return {
                "success": True,
                "synced_count": synced_count,
                "message": f"오너클랜 주문 상태 동기화 완료: {synced_count}개"
            }
            
        except Exception as e:
            self.error_handler.log_error(e, f"오너클랜 주문 상태 동기화 실패: {supplier_id}/{account_name}")
            return {
                "success": False,
                "error": str(e),
                "synced_count": 0
            }
    
    async def _sync_zentrade_orders(self, supplier_id: str, account_name: str) -> Dict[str, Any]:
        """젠트레이드 주문 상태 동기화"""
        try:
            logger.info(f"젠트레이드 주문 상태 동기화: {supplier_id}/{account_name}")
            
            # 젠트레이드 API를 통한 주문 상태 동기화
            # 실제 구현에서는 젠트레이드 API 호출
            synced_count = 0
            
            # 활성 주문 조회
            active_orders = await self.get_active_orders(supplier_id)
            
            for order in active_orders:
                # 젠트레이드 API 호출하여 실제 상태 확인
                # 여기서는 시뮬레이션
                await self.update_order_status(
                    order["order_id"],
                    OrderStatus.DELIVERED.value,
                    "젠트레이드에서 배송완료로 상태 변경"
                )
                synced_count += 1
            
            logger.info(f"젠트레이드 주문 상태 동기화 완료: {synced_count}개")
            return {
                "success": True,
                "synced_count": synced_count,
                "message": f"젠트레이드 주문 상태 동기화 완료: {synced_count}개"
            }
            
        except Exception as e:
            self.error_handler.log_error(e, f"젠트레이드 주문 상태 동기화 실패: {supplier_id}/{account_name}")
            return {
                "success": False,
                "error": str(e),
                "synced_count": 0
            }
    
    async def get_order_statistics(self, supplier_id: Optional[str] = None, 
                                 days: int = 30) -> Dict[str, Any]:
        """
        주문 통계 조회
        
        Args:
            supplier_id: 공급사 ID (선택사항)
            days: 조회 기간 (일)
            
        Returns:
            Dict: 주문 통계
        """
        try:
            logger.info(f"주문 통계 조회: {supplier_id}, {days}일")
            
            # 기간 필터
            start_date = datetime.utcnow() - timedelta(days=days)
            
            filters = {
                "created_at": f">={start_date.isoformat()}"
            }
            
            if supplier_id:
                filters["supplier_id"] = supplier_id
            
            result = await self.db_service.select_data(
                "order_tracking",
                filters
            )
            
            # 통계 계산
            total_orders = len(result)
            status_counts = {}
            
            for record in result:
                status = record["current_status"]
                status_counts[status] = status_counts.get(status, 0) + 1
            
            statistics = {
                "total_orders": total_orders,
                "status_distribution": status_counts,
                "period_days": days,
                "supplier_id": supplier_id,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"주문 통계 조회 완료: {total_orders}개 주문")
            return statistics
            
        except Exception as e:
            self.error_handler.log_error(e, f"주문 통계 조회 실패: {supplier_id}")
            return {
                "total_orders": 0,
                "status_distribution": {},
                "period_days": days,
                "supplier_id": supplier_id,
                "error": str(e)
            }
