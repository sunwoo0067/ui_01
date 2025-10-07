-- 공급사 적립금 관리 시스템 스키마
-- 파일: database/migrations/008_supplier_credit_schema.sql

-- 공급사 적립금 테이블
CREATE TABLE IF NOT EXISTS supplier_credits (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    account_name VARCHAR(100) NOT NULL,
    current_balance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    reserved_balance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 복합 유니크 제약조건
    UNIQUE(supplier_id, account_name)
);

-- 적립금 거래 내역 테이블
CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    transaction_id VARCHAR(100) NOT NULL UNIQUE,
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    account_name VARCHAR(100) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('deposit', 'withdrawal', 'refund', 'adjustment')),
    amount DECIMAL(15,2) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
    description TEXT,
    order_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    failure_reason TEXT,
    
    -- 인덱스
    INDEX idx_credit_transactions_supplier (supplier_id, account_name),
    INDEX idx_credit_transactions_order (order_id),
    INDEX idx_credit_transactions_created (created_at)
);

-- 적립금 알림 테이블
CREATE TABLE IF NOT EXISTS credit_alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    account_name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(20) NOT NULL CHECK (alert_type IN ('low_balance', 'insufficient_funds', 'deposit_received')),
    threshold_amount DECIMAL(15,2),
    current_balance DECIMAL(15,2) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 인덱스
    INDEX idx_credit_alerts_supplier (supplier_id, account_name),
    INDEX idx_credit_alerts_unread (is_read, created_at)
);

-- 적립금 설정 테이블
CREATE TABLE IF NOT EXISTS credit_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    account_name VARCHAR(100) NOT NULL,
    min_balance_threshold DECIMAL(15,2) DEFAULT 10000.00,
    auto_alert_enabled BOOLEAN DEFAULT TRUE,
    alert_email VARCHAR(255),
    alert_phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 복합 유니크 제약조건
    UNIQUE(supplier_id, account_name)
);

-- 적립금 사용 통계 테이블 (월별 집계)
CREATE TABLE IF NOT EXISTS credit_usage_stats (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    account_name VARCHAR(100) NOT NULL,
    year_month VARCHAR(7) NOT NULL, -- YYYY-MM 형식
    total_deposits DECIMAL(15,2) DEFAULT 0.00,
    total_withdrawals DECIMAL(15,2) DEFAULT 0.00,
    total_refunds DECIMAL(15,2) DEFAULT 0.00,
    transaction_count INTEGER DEFAULT 0,
    avg_transaction_amount DECIMAL(15,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 복합 유니크 제약조건
    UNIQUE(supplier_id, account_name, year_month)
);

-- 적립금 관련 뷰
CREATE OR REPLACE VIEW supplier_credit_summary AS
SELECT 
    sc.supplier_id,
    s.supplier_code,
    s.supplier_name,
    sc.account_name,
    sc.current_balance,
    sc.reserved_balance,
    (sc.current_balance - sc.reserved_balance) as available_balance,
    sc.last_updated,
    cs.min_balance_threshold,
    CASE 
        WHEN (sc.current_balance - sc.reserved_balance) < cs.min_balance_threshold THEN TRUE
        ELSE FALSE
    END as is_low_balance
FROM supplier_credits sc
JOIN suppliers s ON sc.supplier_id = s.id
LEFT JOIN credit_settings cs ON sc.supplier_id = cs.supplier_id AND sc.account_name = cs.account_name;

-- 적립금 거래 내역 뷰
CREATE OR REPLACE VIEW credit_transaction_history AS
SELECT 
    ct.transaction_id,
    ct.supplier_id,
    s.supplier_code,
    s.supplier_name,
    ct.account_name,
    ct.transaction_type,
    ct.amount,
    ct.status,
    ct.description,
    ct.order_id,
    ct.created_at,
    ct.completed_at,
    ct.failure_reason,
    CASE 
        WHEN ct.transaction_type = 'deposit' THEN '+'
        WHEN ct.transaction_type = 'withdrawal' THEN '-'
        WHEN ct.transaction_type = 'refund' THEN '+'
        WHEN ct.transaction_type = 'adjustment' THEN 
            CASE WHEN ct.amount > 0 THEN '+' ELSE '-' END
    END as amount_sign
FROM credit_transactions ct
JOIN suppliers s ON ct.supplier_id = s.id
ORDER BY ct.created_at DESC;

-- 적립금 관련 함수들

-- 적립금 잔액 업데이트 함수
CREATE OR REPLACE FUNCTION update_supplier_credit_balance(
    p_supplier_id UUID,
    p_account_name VARCHAR(100),
    p_amount_change DECIMAL(15,2),
    p_transaction_type VARCHAR(20)
) RETURNS BOOLEAN AS $$
DECLARE
    current_balance DECIMAL(15,2);
    new_balance DECIMAL(15,2);
BEGIN
    -- 현재 잔액 조회
    SELECT current_balance INTO current_balance
    FROM supplier_credits
    WHERE supplier_id = p_supplier_id AND account_name = p_account_name;
    
    -- 잔액이 없으면 새로 생성
    IF current_balance IS NULL THEN
        INSERT INTO supplier_credits (supplier_id, account_name, current_balance)
        VALUES (p_supplier_id, p_account_name, GREATEST(0, p_amount_change));
        RETURN TRUE;
    END IF;
    
    -- 새 잔액 계산
    IF p_transaction_type = 'deposit' OR p_transaction_type = 'refund' THEN
        new_balance := current_balance + ABS(p_amount_change);
    ELSIF p_transaction_type = 'withdrawal' THEN
        new_balance := current_balance - ABS(p_amount_change);
        -- 잔액 부족 체크
        IF new_balance < 0 THEN
            RETURN FALSE;
        END IF;
    ELSE
        new_balance := current_balance + p_amount_change;
        -- 잔액 부족 체크
        IF new_balance < 0 THEN
            RETURN FALSE;
        END IF;
    END IF;
    
    -- 잔액 업데이트
    UPDATE supplier_credits
    SET current_balance = new_balance,
        last_updated = NOW(),
        updated_at = NOW()
    WHERE supplier_id = p_supplier_id AND account_name = p_account_name;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- 적립금 부족 알림 생성 함수
CREATE OR REPLACE FUNCTION create_low_balance_alert(
    p_supplier_id UUID,
    p_account_name VARCHAR(100),
    p_current_balance DECIMAL(15,2),
    p_threshold DECIMAL(15,2)
) RETURNS VOID AS $$
BEGIN
    INSERT INTO credit_alerts (
        supplier_id, 
        account_name, 
        alert_type, 
        threshold_amount, 
        current_balance, 
        message
    ) VALUES (
        p_supplier_id,
        p_account_name,
        'low_balance',
        p_threshold,
        p_current_balance,
        '적립금 잔액이 임계값(' || p_threshold || '원) 이하로 떨어졌습니다. 현재 잔액: ' || p_current_balance || '원'
    );
END;
$$ LANGUAGE plpgsql;

-- 적립금 사용 통계 업데이트 함수
CREATE OR REPLACE FUNCTION update_credit_usage_stats(
    p_supplier_id UUID,
    p_account_name VARCHAR(100),
    p_transaction_type VARCHAR(20),
    p_amount DECIMAL(15,2)
) RETURNS VOID AS $$
DECLARE
    current_year_month VARCHAR(7);
BEGIN
    current_year_month := TO_CHAR(NOW(), 'YYYY-MM');
    
    INSERT INTO credit_usage_stats (
        supplier_id, 
        account_name, 
        year_month,
        total_deposits,
        total_withdrawals,
        total_refunds,
        transaction_count,
        avg_transaction_amount
    ) VALUES (
        p_supplier_id,
        p_account_name,
        current_year_month,
        CASE WHEN p_transaction_type = 'deposit' THEN p_amount ELSE 0 END,
        CASE WHEN p_transaction_type = 'withdrawal' THEN p_amount ELSE 0 END,
        CASE WHEN p_transaction_type = 'refund' THEN p_amount ELSE 0 END,
        1,
        p_amount
    )
    ON CONFLICT (supplier_id, account_name, year_month)
    DO UPDATE SET
        total_deposits = credit_usage_stats.total_deposits + 
            CASE WHEN p_transaction_type = 'deposit' THEN p_amount ELSE 0 END,
        total_withdrawals = credit_usage_stats.total_withdrawals + 
            CASE WHEN p_transaction_type = 'withdrawal' THEN p_amount ELSE 0 END,
        total_refunds = credit_usage_stats.total_refunds + 
            CASE WHEN p_transaction_type = 'refund' THEN p_amount ELSE 0 END,
        transaction_count = credit_usage_stats.transaction_count + 1,
        avg_transaction_amount = (
            credit_usage_stats.total_deposits + 
            credit_usage_stats.total_withdrawals + 
            credit_usage_stats.total_refunds
        ) / (credit_usage_stats.transaction_count + 1),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- 적립금 관련 트리거

-- 적립금 변경 시 알림 생성 트리거
CREATE OR REPLACE FUNCTION trigger_low_balance_alert()
RETURNS TRIGGER AS $$
DECLARE
    threshold_amount DECIMAL(15,2);
BEGIN
    -- 설정에서 임계값 조회
    SELECT min_balance_threshold INTO threshold_amount
    FROM credit_settings
    WHERE supplier_id = NEW.supplier_id AND account_name = NEW.account_name;
    
    -- 임계값이 설정되어 있고 현재 잔액이 임계값 이하인 경우 알림 생성
    IF threshold_amount IS NOT NULL AND 
       (NEW.current_balance - NEW.reserved_balance) < threshold_amount AND
       (OLD.current_balance - OLD.reserved_balance) >= threshold_amount THEN
        
        PERFORM create_low_balance_alert(
            NEW.supplier_id,
            NEW.account_name,
            NEW.current_balance - NEW.reserved_balance,
            threshold_amount
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_supplier_credit_low_balance
    AFTER UPDATE ON supplier_credits
    FOR EACH ROW
    EXECUTE FUNCTION trigger_low_balance_alert();

-- 적립금 거래 내역 생성 시 통계 업데이트 트리거
CREATE OR REPLACE FUNCTION trigger_update_credit_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- 통계 업데이트
    PERFORM update_credit_usage_stats(
        NEW.supplier_id,
        NEW.account_name,
        NEW.transaction_type,
        NEW.amount
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_credit_transaction_stats
    AFTER INSERT ON credit_transactions
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_credit_stats();

-- 초기 데이터 삽입 (테스트용)
INSERT INTO credit_settings (supplier_id, account_name, min_balance_threshold, auto_alert_enabled)
SELECT 
    s.id,
    'test_account',
    10000.00,
    TRUE
FROM suppliers s
WHERE s.supplier_code IN ('ownerclan', 'domaemae_dome', 'domaemae_supply', 'zentrade')
ON CONFLICT (supplier_id, account_name) DO NOTHING;

-- 적립금 관련 인덱스 최적화
CREATE INDEX IF NOT EXISTS idx_supplier_credits_balance ON supplier_credits(current_balance);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_type_status ON credit_transactions(transaction_type, status);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_date_range ON credit_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_credit_alerts_type_unread ON credit_alerts(alert_type, is_read);

-- 코멘트 추가
COMMENT ON TABLE supplier_credits IS '공급사별 적립금 잔액 관리';
COMMENT ON TABLE credit_transactions IS '적립금 거래 내역';
COMMENT ON TABLE credit_alerts IS '적립금 관련 알림';
COMMENT ON TABLE credit_settings IS '적립금 관리 설정';
COMMENT ON TABLE credit_usage_stats IS '적립금 사용 통계 (월별 집계)';

COMMENT ON COLUMN supplier_credits.current_balance IS '현재 적립금 잔액';
COMMENT ON COLUMN supplier_credits.reserved_balance IS '예약된 적립금 (주문 진행 중)';
COMMENT ON COLUMN credit_transactions.transaction_type IS '거래 유형: deposit(입금), withdrawal(출금), refund(환불), adjustment(조정)';
COMMENT ON COLUMN credit_transactions.status IS '거래 상태: pending(대기), completed(완료), failed(실패), cancelled(취소)';
