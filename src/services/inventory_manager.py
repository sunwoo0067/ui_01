#!/usr/bin/env python3
"""
재고 관리 및 실시간 추적 시스템
"""

import asyncio
import sys
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.settings import settings
from src.utils.error_handler import ErrorHandler, BaseAPIError, DatabaseError
from src.services.database_service import DatabaseService
from src.services.supplier_account_manager import SupplierAccountManager


class InventoryStatus(Enum):
    """재고 상태"""
    IN_STOCK = "in_stock"           # 재고 있음
    LOW_STOCK = "low_stock"         # 재고 부족
    OUT_OF_STOCK = "out_of_stock"   # 재고 없음
    DISCONTINUED = "discontinued"   # 단종
    COMING_SOON = "coming_soon"     # 입고 예정


class InventoryAction(Enum):
    """재고 변동 액션"""
    PURCHASE = "purchase"           # 구매
    SALE = "sale"                   # 판매
    RETURN = "return"               # 반품
    ADJUSTMENT = "adjustment"       # 조정
    DAMAGE = "damage"               # 손상
    EXPIRED = "expired"             # 만료


@dataclass
class InventoryItem:
    """재고 아이템"""
    product_id: str
    supplier_code: str
    supplier_product_id: str
    product_name: str
    current_stock: int
    reserved_stock: int
    available_stock: int
    min_stock_level: int
    max_stock_level: int
    unit_cost: float
    last_updated: datetime
    status: InventoryStatus


@dataclass
class InventoryTransaction:
    """재고 트랜잭션"""
    transaction_id: str
    product_id: str
    supplier_code: str
    action: InventoryAction
    quantity: int
    unit_cost: Optional[float]
    total_cost: Optional[float]
    reference_id: Optional[str]  # 주문 ID, 구매 ID 등
    notes: Optional[str]
    created_at: datetime


@dataclass
class StockAlert:
    """재고 알림"""
    alert_id: str
    product_id: str
    product_name: str
    alert_type: str  # low_stock, out_of_stock, overstock
    current_stock: int
    threshold: int
    severity: str  # low, medium, high
    created_at: datetime


class InventoryManager:
    """재고 관리 시스템"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.error_handler = ErrorHandler()
        self.supplier_manager = SupplierAccountManager()
        
        # 재고 동기화 서비스
        self.sync_services = {
            "ownerclan": self._sync_ownerclan_inventory,
            "domaemae_dome": self._sync_domaemae_inventory,
            "domaemae_supply": self._sync_domaemae_inventory,
            "zentrade": self._sync_zentrade_inventory
        }
    
    async def get_inventory_status(self, product_id: Optional[str] = None, 
                                 supplier_code: Optional[str] = None) -> List[InventoryItem]:
        """재고 상태 조회"""
        try:
            logger.info(f"재고 상태 조회: product_id={product_id}, supplier={supplier_code}")
            
            filters = {}
            if product_id:
                filters["product_id"] = product_id
            if supplier_code:
                filters["supplier_code"] = supplier_code
            
            inventory_data = await self.db_service.select_data(
                table_name="product_inventory",
                conditions=filters
            )
            
            inventory_items = []
            for item in inventory_data:
                available_stock = item.get("current_stock", 0) - item.get("reserved_stock", 0)
                
                # 재고 상태 결정
                if available_stock <= 0:
                    status = InventoryStatus.OUT_OF_STOCK
                elif available_stock <= item.get("min_stock_level", 10):
                    status = InventoryStatus.LOW_STOCK
                else:
                    status = InventoryStatus.IN_STOCK
                
                inventory_item = InventoryItem(
                    product_id=item.get("product_id", ""),
                    supplier_code=item.get("supplier_code", ""),
                    supplier_product_id=item.get("supplier_product_id", ""),
                    product_name=item.get("product_name", ""),
                    current_stock=item.get("current_stock", 0),
                    reserved_stock=item.get("reserved_stock", 0),
                    available_stock=available_stock,
                    min_stock_level=item.get("min_stock_level", 10),
                    max_stock_level=item.get("max_stock_level", 100),
                    unit_cost=item.get("unit_cost", 0.0),
                    last_updated=datetime.fromisoformat(item.get("last_updated", datetime.now().isoformat())),
                    status=status
                )
                
                inventory_items.append(inventory_item)
            
            logger.info(f"재고 상태 조회 완료: {len(inventory_items)}개 아이템")
            return inventory_items
            
        except Exception as e:
            self.error_handler.log_error(e, "재고 상태 조회 실패")
            return []
    
    async def update_inventory(self, product_id: str, supplier_code: str, 
                             action: InventoryAction, quantity: int,
                             unit_cost: Optional[float] = None,
                             reference_id: Optional[str] = None,
                             notes: Optional[str] = None) -> bool:
        """재고 업데이트"""
        try:
            logger.info(f"재고 업데이트: {product_id}, {action.value}, {quantity}")
            
            # 현재 재고 조회
            current_inventory = await self.db_service.select_data(
                table="product_inventory",
                filters={
                    "product_id": product_id,
                    "supplier_code": supplier_code
                }
            )
            
            if not current_inventory:
                logger.error(f"재고 정보를 찾을 수 없음: {product_id}")
                return False
            
            current_item = current_inventory[0]
            current_stock = current_item.get("current_stock", 0)
            
            # 재고 변동 계산
            if action in [InventoryAction.PURCHASE, InventoryAction.RETURN]:
                new_stock = current_stock + quantity
            elif action in [InventoryAction.SALE, InventoryAction.DAMAGE, InventoryAction.EXPIRED]:
                new_stock = current_stock - quantity
            elif action == InventoryAction.ADJUSTMENT:
                new_stock = quantity  # 직접 설정
            else:
                logger.error(f"지원하지 않는 재고 액션: {action}")
                return False
            
            # 재고가 음수가 되지 않도록 확인
            if new_stock < 0:
                logger.warning(f"재고 부족으로 인한 업데이트 실패: {product_id}")
                return False
            
            # 재고 업데이트
            update_data = {
                "current_stock": new_stock,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            if unit_cost:
                update_data["unit_cost"] = unit_cost
            
            await self.db_service.update_data(
                table="product_inventory",
                filters={
                    "product_id": product_id,
                    "supplier_code": supplier_code
                },
                data=update_data
            )
            
            # 재고 트랜잭션 기록
            transaction = InventoryTransaction(
                transaction_id=f"TXN_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{product_id}",
                product_id=product_id,
                supplier_code=supplier_code,
                action=action,
                quantity=quantity,
                unit_cost=unit_cost,
                total_cost=unit_cost * quantity if unit_cost else None,
                reference_id=reference_id,
                notes=notes,
                created_at=datetime.now(timezone.utc)
            )
            
            await self._record_inventory_transaction(transaction)
            
            # 재고 알림 확인
            await self._check_stock_alerts(product_id, supplier_code, new_stock)
            
            logger.info(f"재고 업데이트 완료: {product_id}, {current_stock} -> {new_stock}")
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, "재고 업데이트 실패")
            return False
    
    async def reserve_inventory(self, product_id: str, supplier_code: str, 
                              quantity: int, order_id: str) -> bool:
        """재고 예약"""
        try:
            logger.info(f"재고 예약: {product_id}, {quantity}개, 주문: {order_id}")
            
            # 현재 재고 확인
            inventory = await self.get_inventory_status(product_id, supplier_code)
            if not inventory:
                logger.error(f"재고 정보 없음: {product_id}")
                return False
            
            item = inventory[0]
            if item.available_stock < quantity:
                logger.warning(f"재고 부족: 요청 {quantity}, 가용 {item.available_stock}")
                return False
            
            # 예약 재고 업데이트
            new_reserved = item.reserved_stock + quantity
            
            await self.db_service.update_data(
                table="product_inventory",
                filters={
                    "product_id": product_id,
                    "supplier_code": supplier_code
                },
                data={
                    "reserved_stock": new_reserved,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
            )
            
            # 예약 트랜잭션 기록
            await self.update_inventory(
                product_id, supplier_code, InventoryAction.SALE,
                quantity, reference_id=order_id,
                notes=f"주문 예약: {order_id}"
            )
            
            logger.info(f"재고 예약 완료: {product_id}, {quantity}개")
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, "재고 예약 실패")
            return False
    
    async def release_reservation(self, product_id: str, supplier_code: str, 
                                quantity: int, order_id: str) -> bool:
        """재고 예약 해제"""
        try:
            logger.info(f"재고 예약 해제: {product_id}, {quantity}개, 주문: {order_id}")
            
            # 현재 재고 확인
            inventory = await self.get_inventory_status(product_id, supplier_code)
            if not inventory:
                logger.error(f"재고 정보 없음: {product_id}")
                return False
            
            item = inventory[0]
            if item.reserved_stock < quantity:
                logger.warning(f"예약 재고 부족: 요청 {quantity}, 예약 {item.reserved_stock}")
                return False
            
            # 예약 재고 감소
            new_reserved = item.reserved_stock - quantity
            
            await self.db_service.update_data(
                table="product_inventory",
                filters={
                    "product_id": product_id,
                    "supplier_code": supplier_code
                },
                data={
                    "reserved_stock": new_reserved,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
            )
            
            logger.info(f"재고 예약 해제 완료: {product_id}, {quantity}개")
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, "재고 예약 해제 실패")
            return False
    
    async def sync_supplier_inventory(self, supplier_code: str) -> Dict[str, Any]:
        """공급사 재고 동기화"""
        try:
            logger.info(f"{supplier_code} 재고 동기화 시작")
            
            if supplier_code not in self.sync_services:
                raise ValueError(f"지원하지 않는 공급사: {supplier_code}")
            
            sync_service = self.sync_services[supplier_code]
            result = await sync_service()
            
            logger.info(f"{supplier_code} 재고 동기화 완료")
            return result
            
        except Exception as e:
            self.error_handler.log_error(e, f"{supplier_code} 재고 동기화 실패")
            return {"success": False, "error": str(e)}
    
    async def _sync_ownerclan_inventory(self) -> Dict[str, Any]:
        """오너클랜 재고 동기화"""
        try:
            # 오너클랜 재고 동기화 로직 (시뮬레이션)
            logger.info("오너클랜 재고 동기화 (시뮬레이션)")
            
            # 실제로는 오너클랜 API를 호출하여 재고 정보를 가져옴
            return {
                "success": True,
                "synced_items": 50,
                "updated_items": 12,
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"오너클랜 재고 동기화 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _sync_domaemae_inventory(self) -> Dict[str, Any]:
        """도매매 재고 동기화"""
        try:
            # 도매매 재고 동기화 로직 (시뮬레이션)
            logger.info("도매매 재고 동기화 (시뮬레이션)")
            
            return {
                "success": True,
                "synced_items": 200,
                "updated_items": 25,
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"도매매 재고 동기화 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _sync_zentrade_inventory(self) -> Dict[str, Any]:
        """젠트레이드 재고 동기화"""
        try:
            # 젠트레이드 재고 동기화 로직 (시뮬레이션)
            logger.info("젠트레이드 재고 동기화 (시뮬레이션)")
            
            return {
                "success": True,
                "synced_items": 100,
                "updated_items": 8,
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"젠트레이드 재고 동기화 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _record_inventory_transaction(self, transaction: InventoryTransaction) -> None:
        """재고 트랜잭션 기록"""
        try:
            transaction_data = asdict(transaction)
            transaction_data["created_at"] = transaction.created_at.isoformat()
            
            await self.db_service.insert_data("inventory_transactions", transaction_data)
            
        except Exception as e:
            self.error_handler.log_error(e, "재고 트랜잭션 기록 실패")
    
    async def _check_stock_alerts(self, product_id: str, supplier_code: str, 
                                current_stock: int) -> None:
        """재고 알림 확인"""
        try:
            # 재고 정보 조회
            inventory = await self.get_inventory_status(product_id, supplier_code)
            if not inventory:
                return
            
            item = inventory[0]
            
            # 재고 부족 알림
            if current_stock <= item.min_stock_level:
                alert = StockAlert(
                    alert_id=f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{product_id}",
                    product_id=product_id,
                    product_name=item.product_name,
                    alert_type="low_stock",
                    current_stock=current_stock,
                    threshold=item.min_stock_level,
                    severity="high" if current_stock == 0 else "medium",
                    created_at=datetime.now(timezone.utc)
                )
                
                await self._create_stock_alert(alert)
            
            # 재고 과다 알림
            elif current_stock >= item.max_stock_level:
                alert = StockAlert(
                    alert_id=f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{product_id}",
                    product_id=product_id,
                    product_name=item.product_name,
                    alert_type="overstock",
                    current_stock=current_stock,
                    threshold=item.max_stock_level,
                    severity="low",
                    created_at=datetime.now(timezone.utc)
                )
                
                await self._create_stock_alert(alert)
            
        except Exception as e:
            self.error_handler.log_error(e, "재고 알림 확인 실패")
    
    async def _create_stock_alert(self, alert: StockAlert) -> None:
        """재고 알림 생성"""
        try:
            alert_data = asdict(alert)
            alert_data["created_at"] = alert.created_at.isoformat()
            
            await self.db_service.insert_data("stock_alerts", alert_data)
            
            logger.warning(f"재고 알림 생성: {alert.product_name} - {alert.alert_type}")
            
        except Exception as e:
            self.error_handler.log_error(e, "재고 알림 생성 실패")
    
    async def get_stock_alerts(self, severity: Optional[str] = None) -> List[StockAlert]:
        """재고 알림 조회"""
        try:
            filters = {}
            if severity:
                filters["severity"] = severity
            
            alerts_data = await self.db_service.select_data(
                table_name="stock_alerts",
                conditions=filters
            )
            
            alerts = []
            for alert_data in alerts_data:
                alert = StockAlert(
                    alert_id=alert_data.get("alert_id", ""),
                    product_id=alert_data.get("product_id", ""),
                    product_name=alert_data.get("product_name", ""),
                    alert_type=alert_data.get("alert_type", ""),
                    current_stock=alert_data.get("current_stock", 0),
                    threshold=alert_data.get("threshold", 0),
                    severity=alert_data.get("severity", "low"),
                    created_at=datetime.fromisoformat(alert_data.get("created_at", datetime.now().isoformat()))
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            self.error_handler.log_error(e, "재고 알림 조회 실패")
            return []


async def test_inventory_manager():
    """재고 관리 시스템 테스트"""
    logger.info("재고 관리 시스템 테스트 시작")
    
    try:
        # 서비스 초기화
        db_service = DatabaseService()
        inventory_manager = InventoryManager(db_service)
        
        # 1. 재고 상태 조회 테스트
        logger.info("=== 재고 상태 조회 테스트 ===")
        inventory_items = await inventory_manager.get_inventory_status()
        logger.info(f"총 재고 아이템 수: {len(inventory_items)}")
        
        for item in inventory_items[:3]:  # 처음 3개만 출력
            logger.info(f"- {item.product_name}: {item.available_stock}개 ({item.status.value})")
        
        # 2. 재고 업데이트 테스트
        if inventory_items:
            test_item = inventory_items[0]
            logger.info(f"=== 재고 업데이트 테스트: {test_item.product_name} ===")
            
            success = await inventory_manager.update_inventory(
                test_item.product_id,
                test_item.supplier_code,
                InventoryAction.PURCHASE,
                10,
                unit_cost=1000.0,
                notes="테스트 구매"
            )
            
            logger.info(f"재고 업데이트 결과: {'성공' if success else '실패'}")
        
        # 3. 재고 동기화 테스트
        logger.info("=== 재고 동기화 테스트 ===")
        sync_result = await inventory_manager.sync_supplier_inventory("ownerclan")
        logger.info(f"오너클랜 동기화 결과: {sync_result}")
        
        # 4. 재고 알림 조회 테스트
        logger.info("=== 재고 알림 조회 테스트 ===")
        alerts = await inventory_manager.get_stock_alerts()
        logger.info(f"재고 알림 수: {len(alerts)}")
        
        for alert in alerts[:3]:  # 처음 3개만 출력
            logger.info(f"- {alert.product_name}: {alert.alert_type} ({alert.severity})")
        
        logger.info("재고 관리 시스템 테스트 완료")
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_inventory_manager())
