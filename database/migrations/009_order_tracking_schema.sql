-- 주문 추적 테이블 생성
-- 주문 상태 추적 및 동기화를 위한 테이블

CREATE TABLE IF NOT EXISTS order_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 주문 정보
    order_id TEXT UNIQUE NOT NULL,
    supplier_id TEXT NOT NULL,
    supplier_account_id TEXT NOT NULL,
    supplier_order_id TEXT,
    
    -- 주문 상태
    current_status TEXT NOT NULL DEFAULT 'pending',
    status_history JSONB NOT NULL DEFAULT '[]',
    
    -- 주문 상세 정보
    order_details JSONB,
    
    -- 추적 정보
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    -- 제약 조건
    CONSTRAINT order_tracking_status_check 
        CHECK (current_status IN ('pending', 'confirmed', 'preparing', 'shipped', 'delivered', 'cancelled', 'returned', 'refunded'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_order_tracking_order_id ON order_tracking(order_id);
CREATE INDEX IF NOT EXISTS idx_order_tracking_supplier_id ON order_tracking(supplier_id);
CREATE INDEX IF NOT EXISTS idx_order_tracking_supplier_account_id ON order_tracking(supplier_account_id);
CREATE INDEX IF NOT EXISTS idx_order_tracking_supplier_order_id ON order_tracking(supplier_order_id);
CREATE INDEX IF NOT EXISTS idx_order_tracking_current_status ON order_tracking(current_status);
CREATE INDEX IF NOT EXISTS idx_order_tracking_is_active ON order_tracking(is_active);
CREATE INDEX IF NOT EXISTS idx_order_tracking_created_at ON order_tracking(created_at);
CREATE INDEX IF NOT EXISTS idx_order_tracking_last_updated ON order_tracking(last_updated);

-- 주문 추적 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_order_tracking_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성
CREATE TRIGGER trigger_update_order_tracking_updated_at
    BEFORE UPDATE ON order_tracking
    FOR EACH ROW
    EXECUTE FUNCTION update_order_tracking_updated_at();

-- 주문 상태 변경 로그 테이블
CREATE TABLE IF NOT EXISTS order_status_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 주문 정보
    order_id TEXT NOT NULL,
    supplier_id TEXT NOT NULL,
    
    -- 상태 변경 정보
    old_status TEXT,
    new_status TEXT NOT NULL,
    change_reason TEXT,
    change_note TEXT,
    
    -- 변경자 정보
    changed_by TEXT DEFAULT 'system',
    
    -- 타임스탬프
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT order_status_logs_status_check 
        CHECK (new_status IN ('pending', 'confirmed', 'preparing', 'shipped', 'delivered', 'cancelled', 'returned', 'refunded'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_order_status_logs_order_id ON order_status_logs(order_id);
CREATE INDEX IF NOT EXISTS idx_order_status_logs_supplier_id ON order_status_logs(supplier_id);
CREATE INDEX IF NOT EXISTS idx_order_status_logs_new_status ON order_status_logs(new_status);
CREATE INDEX IF NOT EXISTS idx_order_status_logs_changed_at ON order_status_logs(changed_at);

-- 주문 상태 변경 시 로그 자동 생성 트리거 함수
CREATE OR REPLACE FUNCTION log_order_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- 상태가 변경된 경우에만 로그 생성
    IF OLD.current_status != NEW.current_status THEN
        INSERT INTO order_status_logs (
            order_id,
            supplier_id,
            old_status,
            new_status,
            change_reason,
            change_note,
            changed_by
        ) VALUES (
            NEW.order_id,
            NEW.supplier_id,
            OLD.current_status,
            NEW.current_status,
            'Status updated via API',
            'Status changed from ' || OLD.current_status || ' to ' || NEW.current_status,
            'system'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성
CREATE TRIGGER trigger_log_order_status_change
    AFTER UPDATE ON order_tracking
    FOR EACH ROW
    EXECUTE FUNCTION log_order_status_change();

-- 주문 동기화 상태 테이블
CREATE TABLE IF NOT EXISTS order_sync_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 동기화 정보
    supplier_id TEXT NOT NULL,
    supplier_account_id TEXT NOT NULL,
    
    -- 동기화 상태
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_status TEXT NOT NULL DEFAULT 'pending', -- pending, success, failed
    sync_error TEXT,
    
    -- 동기화 통계
    total_orders INTEGER DEFAULT 0,
    synced_orders INTEGER DEFAULT 0,
    failed_orders INTEGER DEFAULT 0,
    
    -- 타임스탬프
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT order_sync_status_sync_status_check 
        CHECK (sync_status IN ('pending', 'success', 'failed'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_order_sync_status_supplier_id ON order_sync_status(supplier_id);
CREATE INDEX IF NOT EXISTS idx_order_sync_status_supplier_account_id ON order_sync_status(supplier_account_id);
CREATE INDEX IF NOT EXISTS idx_order_sync_status_sync_status ON order_sync_status(sync_status);
CREATE INDEX IF NOT EXISTS idx_order_sync_status_last_sync_at ON order_sync_status(last_sync_at);

-- 동기화 상태 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_order_sync_status_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성
CREATE TRIGGER trigger_update_order_sync_status_updated_at
    BEFORE UPDATE ON order_sync_status
    FOR EACH ROW
    EXECUTE FUNCTION update_order_sync_status_updated_at();
