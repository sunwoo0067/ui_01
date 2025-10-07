#!/usr/bin/env python3
"""
공급사 적립금 시스템 테스트
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from loguru import logger
import uuid

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.services.supplier_credit_manager import SupplierCreditManager, CreditTransactionType, CreditTransactionStatus
from src.services.payment_shipping_automation import PaymentProcessor, PaymentRequest, PaymentMethod

async def test_supplier_credit_system():
    """공급사 적립금 시스템 통합 테스트"""
    logger.info("=== 공급사 적립금 시스템 테스트 시작 ===")
    
    db_service = DatabaseService()
    credit_manager = SupplierCreditManager(db_service)
    payment_processor = PaymentProcessor(db_service)
    
    # 테스트용 공급사 및 계정 정보
    test_suppliers = [
        {"supplier_id": "ownerclan", "account_name": "test_account"},
        {"supplier_id": "domaemae_dome", "account_name": "test_account"},
        {"supplier_id": "domaemae_supply", "account_name": "test_account"},
        {"supplier_id": "zentrade", "account_name": "test_account"}
    ]
    
    # --- 1. 적립금 입금 테스트 ---
    logger.info("\n--- 적립금 입금 테스트 ---")
    for supplier in test_suppliers:
        supplier_id = supplier["supplier_id"]
        account_name = supplier["account_name"]
        
        # 각 공급사에 100,000원 입금
        success = await credit_manager.deposit_credit(
            supplier_id=supplier_id,
            account_name=account_name,
            amount=100000.0,
            description=f"{supplier_id} 테스트 입금"
        )
        
        if success:
            logger.info(f"✅ {supplier_id} 적립금 입금 성공: 100,000원")
        else:
            logger.error(f"❌ {supplier_id} 적립금 입금 실패")
    
    # --- 2. 적립금 잔액 조회 테스트 ---
    logger.info("\n--- 적립금 잔액 조회 테스트 ---")
    for supplier in test_suppliers:
        supplier_id = supplier["supplier_id"]
        account_name = supplier["account_name"]
        
        credit_info = await credit_manager.get_supplier_credit(supplier_id, account_name)
        if credit_info:
            logger.info(f"📊 {supplier_id} 적립금 정보:")
            logger.info(f"   현재 잔액: {credit_info.current_balance:,.0f}원")
            logger.info(f"   예약 금액: {credit_info.reserved_balance:,.0f}원")
            logger.info(f"   사용 가능: {credit_info.available_balance:,.0f}원")
        else:
            logger.warning(f"⚠️ {supplier_id} 적립금 정보 없음")
    
    # --- 3. 적립금 충분 여부 확인 테스트 ---
    logger.info("\n--- 적립금 충분 여부 확인 테스트 ---")
    test_amounts = [50000, 150000, 200000]
    
    for supplier in test_suppliers:
        supplier_id = supplier["supplier_id"]
        account_name = supplier["account_name"]
        
        logger.info(f"🔍 {supplier_id} 적립금 충분 여부 확인:")
        for amount in test_amounts:
            sufficient = await credit_manager.check_sufficient_credit(supplier_id, account_name, amount)
            status = "✅ 충분" if sufficient else "❌ 부족"
            logger.info(f"   {amount:,}원: {status}")
    
    # --- 4. 주문 결제 시뮬레이션 테스트 ---
    logger.info("\n--- 주문 결제 시뮬레이션 테스트 ---")
    
    # 테스트 주문 생성
    test_order_id = f"TEST_ORDER_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_order_data = {
        "order_id": test_order_id,
        "supplier_id": "ownerclan",
        "account_name": "test_account",
        "payment_amount": 75000,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # 주문 정보를 DB에 저장
    await db_service.insert_data("local_orders", test_order_data)
    logger.info(f"📝 테스트 주문 생성: {test_order_id}")
    
    # 결제 요청 생성
    payment_request = PaymentRequest(
        payment_id=f"PAY_{test_order_id}",
        order_id=test_order_id,
        amount=75000.0,
        payment_method=PaymentMethod.CREDIT,
        transaction_id=None
    )
    
    # 결제 처리
    payment_result = await payment_processor.process_payment(payment_request)
    if payment_result.status.value == "completed":
        logger.info(f"✅ 결제 성공: {test_order_id}, 거래 ID: {payment_result.transaction_id}")
        
        # 적립금 차감 확정
        confirm_success = await payment_processor.confirm_credit_payment(test_order_id)
        if confirm_success:
            logger.info(f"✅ 적립금 차감 확정 성공: {test_order_id}")
        else:
            logger.error(f"❌ 적립금 차감 확정 실패: {test_order_id}")
    else:
        logger.error(f"❌ 결제 실패: {test_order_id}, 오류: {payment_result.failure_reason}")
    
    # --- 5. 적립금 거래 내역 조회 테스트 ---
    logger.info("\n--- 적립금 거래 내역 조회 테스트 ---")
    for supplier in test_suppliers:
        supplier_id = supplier["supplier_id"]
        account_name = supplier["account_name"]
        
        transactions = await credit_manager.get_credit_transactions(supplier_id, account_name, limit=10)
        logger.info(f"📋 {supplier_id} 거래 내역 ({len(transactions)}건):")
        
        for txn in transactions[:3]:  # 최근 3건만 표시
            logger.info(f"   {txn.created_at.strftime('%Y-%m-%d %H:%M')} | "
                       f"{txn.transaction_type.value} | "
                       f"{txn.amount:,.0f}원 | "
                       f"{txn.status.value} | "
                       f"{txn.description}")
    
    # --- 6. 주문 취소 시뮬레이션 테스트 ---
    logger.info("\n--- 주문 취소 시뮬레이션 테스트 ---")
    
    # 취소할 주문 생성
    cancel_order_id = f"CANCEL_ORDER_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    cancel_order_data = {
        "order_id": cancel_order_id,
        "supplier_id": "domaemae_dome",
        "account_name": "test_account",
        "payment_amount": 50000,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db_service.insert_data("local_orders", cancel_order_data)
    
    # 결제 요청 및 처리
    cancel_payment_request = PaymentRequest(
        payment_id=f"PAY_{cancel_order_id}",
        order_id=cancel_order_id,
        amount=50000.0,
        payment_method=PaymentMethod.CREDIT,
        transaction_id=None
    )
    
    cancel_payment_result = await payment_processor.process_payment(cancel_payment_request)
    if cancel_payment_result.status.value == "completed":
        logger.info(f"📝 취소 테스트 주문 결제 완료: {cancel_order_id}")
        
        # 주문 취소 (적립금 예약 해제)
        cancel_success = await payment_processor.cancel_credit_payment(cancel_order_id)
        if cancel_success:
            logger.info(f"✅ 주문 취소 및 적립금 예약 해제 성공: {cancel_order_id}")
        else:
            logger.error(f"❌ 주문 취소 실패: {cancel_order_id}")
    
    # --- 7. 최종 적립금 상태 확인 ---
    logger.info("\n--- 최종 적립금 상태 확인 ---")
    for supplier in test_suppliers:
        supplier_id = supplier["supplier_id"]
        account_name = supplier["account_name"]
        
        credit_info = await credit_manager.get_supplier_credit(supplier_id, account_name)
        if credit_info:
            logger.info(f"💰 {supplier_id} 최종 적립금 상태:")
            logger.info(f"   현재 잔액: {credit_info.current_balance:,.0f}원")
            logger.info(f"   예약 금액: {credit_info.reserved_balance:,.0f}원")
            logger.info(f"   사용 가능: {credit_info.available_balance:,.0f}원")
            logger.info(f"   마지막 업데이트: {credit_info.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
    
    logger.info("\n=== 공급사 적립금 시스템 테스트 완료 ===")

async def test_credit_insufficient_scenario():
    """적립금 부족 시나리오 테스트"""
    logger.info("\n=== 적립금 부족 시나리오 테스트 ===")
    
    db_service = DatabaseService()
    credit_manager = SupplierCreditManager(db_service)
    payment_processor = PaymentProcessor(db_service)
    
    # 적립금이 부족한 상황 시뮬레이션
    supplier_id = "zentrade"
    account_name = "test_account"
    
    # 현재 적립금 확인
    credit_info = await credit_manager.get_supplier_credit(supplier_id, account_name)
    if credit_info:
        logger.info(f"📊 {supplier_id} 현재 적립금: {credit_info.available_balance:,.0f}원")
        
        # 부족한 금액으로 주문 시도
        insufficient_amount = credit_info.available_balance + 50000
        logger.info(f"🔍 부족한 금액으로 주문 시도: {insufficient_amount:,.0f}원")
        
        # 충분 여부 확인
        sufficient = await credit_manager.check_sufficient_credit(supplier_id, account_name, insufficient_amount)
        if not sufficient:
            logger.info(f"✅ 적립금 부족 정상 감지: 필요 {insufficient_amount:,.0f}원, 사용가능 {credit_info.available_balance:,.0f}원")
        else:
            logger.warning(f"⚠️ 적립금 부족 감지 실패")
    
    logger.info("=== 적립금 부족 시나리오 테스트 완료 ===")

if __name__ == "__main__":
    asyncio.run(test_supplier_credit_system())
    asyncio.run(test_credit_insufficient_scenario())
