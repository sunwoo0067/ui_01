-- 트랜잭션 로그 테이블 생성
-- 오너클랜 주문 관련 트랜잭션을 로깅하기 위한 테이블

CREATE TABLE IF NOT EXISTS transaction_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 계정 정보
    account_name TEXT NOT NULL,
    
    -- 트랜잭션 정보
    transaction_type TEXT NOT NULL, -- create_order, update_order, cancel_order, request_cancellation, simulate_order
    order_key TEXT, -- 주문 키 (해당하는 경우)
    
    -- 결과 정보
    success BOOLEAN NOT NULL DEFAULT true,
    data JSONB, -- 트랜잭션 결과 데이터
    
    -- 타임스탬프
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 인덱스
    CONSTRAINT transaction_logs_transaction_type_check 
        CHECK (transaction_type IN ('create_order', 'update_order', 'cancel_order', 'request_cancellation', 'simulate_order'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_transaction_logs_account_name ON transaction_logs(account_name);
CREATE INDEX IF NOT EXISTS idx_transaction_logs_transaction_type ON transaction_logs(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transaction_logs_order_key ON transaction_logs(order_key);
CREATE INDEX IF NOT EXISTS idx_transaction_logs_timestamp ON transaction_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_transaction_logs_success ON transaction_logs(success);

-- 주문 관리 테이블 생성 (로컬 주문 추적용)
CREATE TABLE IF NOT EXISTS local_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 오너클랜 주문 정보
    ownerclan_order_key TEXT UNIQUE NOT NULL,
    ownerclan_order_id TEXT,
    
    -- 계정 정보
    account_name TEXT NOT NULL,
    
    -- 주문 상태
    status TEXT NOT NULL DEFAULT 'pending',
    
    -- 주문 정보
    products JSONB NOT NULL, -- 주문 상품 정보
    recipient JSONB NOT NULL, -- 수령자 정보
    
    -- 메모
    note TEXT,
    seller_note TEXT,
    orderer_note TEXT,
    
    -- 금액 정보
    total_amount INTEGER,
    shipping_amount INTEGER,
    
    -- 타임스탬프
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT local_orders_status_check 
        CHECK (status IN ('pending', 'paid', 'preparing', 'shipped', 'delivered', 'cancelled', 'refunded'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_local_orders_ownerclan_order_key ON local_orders(ownerclan_order_key);
CREATE INDEX IF NOT EXISTS idx_local_orders_account_name ON local_orders(account_name);
CREATE INDEX IF NOT EXISTS idx_local_orders_status ON local_orders(status);
CREATE INDEX IF NOT EXISTS idx_local_orders_created_at ON local_orders(created_at);

-- 주문 상태 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_local_orders_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성
CREATE TRIGGER trigger_update_local_orders_updated_at
    BEFORE UPDATE ON local_orders
    FOR EACH ROW
    EXECUTE FUNCTION update_local_orders_updated_at();

-- 주문 동기화 테이블 (오너클랜과 로컬 주문 동기화용)
CREATE TABLE IF NOT EXISTS order_sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 동기화 정보
    account_name TEXT NOT NULL,
    sync_type TEXT NOT NULL, -- pull_orders, push_order, sync_status
    
    -- 동기화 대상
    order_key TEXT,
    
    -- 동기화 결과
    success BOOLEAN NOT NULL DEFAULT true,
    synced_count INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- 동기화 데이터
    sync_data JSONB,
    
    -- 타임스탬프
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT order_sync_logs_sync_type_check 
        CHECK (sync_type IN ('pull_orders', 'push_order', 'sync_status'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_order_sync_logs_account_name ON order_sync_logs(account_name);
CREATE INDEX IF NOT EXISTS idx_order_sync_logs_sync_type ON order_sync_logs(sync_type);
CREATE INDEX IF NOT EXISTS idx_order_sync_logs_order_key ON order_sync_logs(order_key);
CREATE INDEX IF NOT EXISTS idx_order_sync_logs_timestamp ON order_sync_logs(timestamp);
