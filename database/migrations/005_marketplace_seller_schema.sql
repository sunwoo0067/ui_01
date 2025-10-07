-- 마켓플레이스 판매자 기능을 위한 스키마
-- 상품 등록, 주문 관리, 재고 동기화 기능 지원

-- 1. 마켓플레이스 주문 테이블
CREATE TABLE IF NOT EXISTS marketplace_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 마켓플레이스 정보
    marketplace_id UUID REFERENCES sales_marketplaces(id) ON DELETE CASCADE,
    sales_account_id UUID REFERENCES sales_accounts(id) ON DELETE SET NULL,
    
    -- 주문 기본 정보
    order_id TEXT NOT NULL, -- 마켓플레이스의 주문 ID
    order_number TEXT, -- 주문 번호 (고객용)
    
    -- 주문 상태
    order_status TEXT NOT NULL CHECK (order_status IN (
        'pending', 'confirmed', 'preparing', 'shipped', 'delivered', 
        'cancelled', 'returned', 'refunded'
    )),
    payment_status TEXT CHECK (payment_status IN (
        'pending', 'completed', 'failed', 'refunded'
    )),
    shipping_status TEXT CHECK (shipping_status IN (
        'pending', 'preparing', 'shipped', 'in_transit', 'delivered'
    )),
    
    -- 주문 상품 정보
    items JSONB NOT NULL, -- [{product_id, title, quantity, price, options}]
    
    -- 금액 정보
    total_amount DECIMAL(12, 2) NOT NULL,
    shipping_fee DECIMAL(12, 2) DEFAULT 0,
    discount_amount DECIMAL(12, 2) DEFAULT 0,
    final_amount DECIMAL(12, 2) NOT NULL,
    
    -- 고객 정보
    customer_info JSONB, -- {name, phone, email, address}
    
    -- 배송 정보
    shipping_info JSONB, -- {carrier, tracking_number, address}
    
    -- 메타데이터
    marketplace_data JSONB, -- 마켓플레이스 원본 주문 데이터
    
    -- 상태 변경 이력
    status_history JSONB DEFAULT '[]'::jsonb, -- [{status, changed_at, note}]
    
    -- 타임스탬프
    ordered_at TIMESTAMP WITH TIME ZONE,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    shipped_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 유니크 제약
    UNIQUE(marketplace_id, order_id)
);

-- 2. 재고 동기화 로그 테이블
CREATE TABLE IF NOT EXISTS marketplace_inventory_sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 동기화 대상
    marketplace_id UUID REFERENCES sales_marketplaces(id) ON DELETE CASCADE,
    sales_account_id UUID REFERENCES sales_accounts(id) ON DELETE SET NULL,
    listed_product_id UUID REFERENCES listed_products(id) ON DELETE CASCADE,
    
    -- 동기화 정보
    sync_type TEXT NOT NULL CHECK (sync_type IN ('manual', 'auto', 'scheduled')),
    sync_action TEXT NOT NULL CHECK (sync_action IN ('update', 'sync', 'check')),
    
    -- 재고 정보
    old_quantity INTEGER,
    new_quantity INTEGER,
    marketplace_quantity INTEGER, -- 마켓플레이스의 실제 재고
    
    -- 동기화 결과
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'pending')),
    error_message TEXT,
    
    -- 메타데이터
    sync_data JSONB, -- 동기화 세부 정보
    
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 마켓플레이스 API 호출 로그 테이블
CREATE TABLE IF NOT EXISTS marketplace_api_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 마켓플레이스 정보
    marketplace_id UUID REFERENCES sales_marketplaces(id) ON DELETE CASCADE,
    sales_account_id UUID REFERENCES sales_accounts(id) ON DELETE SET NULL,
    
    -- API 요청 정보
    api_method TEXT NOT NULL, -- GET, POST, PUT, DELETE
    api_endpoint TEXT NOT NULL,
    request_headers JSONB,
    request_body JSONB,
    
    -- API 응답 정보
    response_status INTEGER, -- HTTP status code
    response_headers JSONB,
    response_body JSONB,
    
    -- 실행 정보
    duration_ms INTEGER, -- 응답 시간 (밀리초)
    status TEXT CHECK (status IN ('success', 'failed', 'error')),
    error_message TEXT,
    
    -- 메타데이터
    context JSONB, -- {action, product_id, order_id 등}
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 마켓플레이스 상품 매핑 확장 (listed_products 보완)
-- listed_products 테이블에 추가 필드가 필요한 경우
ALTER TABLE listed_products 
ADD COLUMN IF NOT EXISTS marketplace_status TEXT 
    CHECK (marketplace_status IN ('draft', 'pending', 'active', 'paused', 'rejected', 'deleted'));

ALTER TABLE listed_products 
ADD COLUMN IF NOT EXISTS marketplace_response JSONB; -- 마켓플레이스 등록 응답

ALTER TABLE listed_products 
ADD COLUMN IF NOT EXISTS last_sync_error TEXT; -- 마지막 동기화 에러

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_marketplace_id 
    ON marketplace_orders(marketplace_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_sales_account_id 
    ON marketplace_orders(sales_account_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_order_id 
    ON marketplace_orders(order_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_order_status 
    ON marketplace_orders(order_status);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_ordered_at 
    ON marketplace_orders(ordered_at);

CREATE INDEX IF NOT EXISTS idx_marketplace_inventory_sync_log_marketplace_id 
    ON marketplace_inventory_sync_log(marketplace_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_inventory_sync_log_listed_product_id 
    ON marketplace_inventory_sync_log(listed_product_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_inventory_sync_log_synced_at 
    ON marketplace_inventory_sync_log(synced_at);

CREATE INDEX IF NOT EXISTS idx_marketplace_api_logs_marketplace_id 
    ON marketplace_api_logs(marketplace_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_api_logs_status 
    ON marketplace_api_logs(status);
CREATE INDEX IF NOT EXISTS idx_marketplace_api_logs_created_at 
    ON marketplace_api_logs(created_at);

-- 뷰 생성: 판매 대시보드용
CREATE OR REPLACE VIEW marketplace_sales_summary AS
SELECT 
    m.id AS marketplace_id,
    m.name AS marketplace_name,
    sa.id AS sales_account_id,
    sa.account_name,
    COUNT(DISTINCT lp.id) AS total_listed_products,
    COUNT(DISTINCT CASE WHEN lp.status = 'active' THEN lp.id END) AS active_products,
    COUNT(DISTINCT mo.id) AS total_orders,
    COUNT(DISTINCT CASE WHEN mo.order_status = 'delivered' THEN mo.id END) AS delivered_orders,
    COALESCE(SUM(CASE WHEN mo.order_status = 'delivered' THEN mo.final_amount END), 0) AS total_revenue,
    COALESCE(AVG(CASE WHEN mo.order_status = 'delivered' THEN mo.final_amount END), 0) AS avg_order_value
FROM sales_marketplaces m
LEFT JOIN sales_accounts sa ON m.id = sa.marketplace_id
LEFT JOIN listed_products lp ON sa.id = lp.sales_account_id
LEFT JOIN marketplace_orders mo ON sa.id = mo.sales_account_id
GROUP BY m.id, m.name, sa.id, sa.account_name;

-- 코멘트 추가
COMMENT ON TABLE marketplace_orders IS '마켓플레이스 주문 정보';
COMMENT ON TABLE marketplace_inventory_sync_log IS '재고 동기화 로그';
COMMENT ON TABLE marketplace_api_logs IS 'API 호출 로그 (디버깅용)';
COMMENT ON VIEW marketplace_sales_summary IS '마켓플레이스별 판매 요약 뷰';

