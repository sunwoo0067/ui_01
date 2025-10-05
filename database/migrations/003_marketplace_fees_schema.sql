-- 마켓플레이스 수수료 관련 테이블 추가
-- 기존 스키마에 마켓플레이스 수수료 정보를 저장할 테이블들을 추가

-- 마켓플레이스 수수료 테이블
CREATE TABLE IF NOT EXISTS marketplace_fees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    marketplace_id UUID NOT NULL REFERENCES marketplaces(id),
    category VARCHAR(50) NOT NULL,
    fee_type VARCHAR(20) NOT NULL, -- 'commission', 'payment', 'logistics', 'promotion', 'advertising'
    fee_rate DECIMAL(5,4) NOT NULL, -- 수수료율 (0.0000 ~ 1.0000)
    min_fee DECIMAL(10,2), -- 최소 수수료
    max_fee DECIMAL(10,2), -- 최대 수수료
    description TEXT,
    effective_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_date TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 가격 규칙 테이블 (기존 pricing_rules 테이블 확장)
CREATE TABLE IF NOT EXISTS pricing_rules_v2 (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID NOT NULL REFERENCES suppliers(id),
    marketplace_id UUID NOT NULL REFERENCES marketplaces(id),
    rule_name VARCHAR(100) NOT NULL,
    calculation_type VARCHAR(20) NOT NULL, -- 'percentage_margin', 'fixed_margin', 'cost_plus', 'competitive'
    calculation_value DECIMAL(8,4) NOT NULL, -- 계산 값 (마진율, 고정금액 등)
    min_price DECIMAL(10,2), -- 최소 판매가
    max_price DECIMAL(10,2), -- 최대 판매가
    round_to INTEGER DEFAULT 100, -- 반올림 단위
    conditions JSONB, -- 조건 (카테고리, 브랜드, 가격대 등)
    priority INTEGER DEFAULT 1, -- 우선순위
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 상품별 가격 계산 이력 테이블
CREATE TABLE IF NOT EXISTS product_price_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id),
    marketplace_id UUID NOT NULL REFERENCES marketplaces(id),
    original_price DECIMAL(10,2) NOT NULL, -- 원본 가격
    calculated_price DECIMAL(10,2) NOT NULL, -- 계산된 가격
    cost_price DECIMAL(10,2) NOT NULL, -- 원가
    margin_amount DECIMAL(10,2) NOT NULL, -- 마진 금액
    margin_rate DECIMAL(5,4) NOT NULL, -- 마진율
    fee_amount DECIMAL(10,2) NOT NULL, -- 수수료 금액
    fee_rate DECIMAL(5,4) NOT NULL, -- 수수료율
    net_profit DECIMAL(10,2) NOT NULL, -- 순이익
    pricing_rule_id UUID REFERENCES pricing_rules_v2(id),
    calculation_details JSONB, -- 계산 상세 정보
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 마켓플레이스별 상품 등록 상태 테이블
CREATE TABLE IF NOT EXISTS marketplace_product_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id),
    marketplace_id UUID NOT NULL REFERENCES marketplaces(id),
    marketplace_product_id VARCHAR(100), -- 마켓플레이스 상품 ID
    status VARCHAR(20) NOT NULL, -- 'draft', 'active', 'inactive', 'rejected', 'pending'
    listing_price DECIMAL(10,2), -- 등록 가격
    stock_quantity INTEGER DEFAULT 0, -- 재고 수량
    last_sync_at TIMESTAMP WITH TIME ZONE, -- 마지막 동기화 시간
    sync_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'success', 'failed'
    error_message TEXT, -- 에러 메시지
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(product_id, marketplace_id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_marketplace_fees_marketplace_category 
ON marketplace_fees(marketplace_id, category);

CREATE INDEX IF NOT EXISTS idx_marketplace_fees_fee_type 
ON marketplace_fees(fee_type);

CREATE INDEX IF NOT EXISTS idx_pricing_rules_v2_supplier_marketplace 
ON pricing_rules_v2(supplier_id, marketplace_id);

CREATE INDEX IF NOT EXISTS idx_product_price_history_product_marketplace 
ON product_price_history(product_id, marketplace_id);

CREATE INDEX IF NOT EXISTS idx_product_price_history_created_at 
ON product_price_history(created_at);

CREATE INDEX IF NOT EXISTS idx_marketplace_product_status_product_marketplace 
ON marketplace_product_status(product_id, marketplace_id);

CREATE INDEX IF NOT EXISTS idx_marketplace_product_status_status 
ON marketplace_product_status(status);

-- RLS 정책 추가
ALTER TABLE marketplace_fees ENABLE ROW LEVEL SECURITY;
ALTER TABLE pricing_rules_v2 ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_price_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketplace_product_status ENABLE ROW LEVEL SECURITY;

-- 마켓플레이스 수수료 테이블 RLS 정책
CREATE POLICY "marketplace_fees_policy" ON marketplace_fees
    FOR ALL USING (true); -- 모든 사용자가 읽기 가능

-- 가격 규칙 테이블 RLS 정책
CREATE POLICY "pricing_rules_v2_policy" ON pricing_rules_v2
    FOR ALL USING (true); -- 모든 사용자가 읽기 가능

-- 상품 가격 이력 테이블 RLS 정책
CREATE POLICY "product_price_history_policy" ON product_price_history
    FOR ALL USING (true); -- 모든 사용자가 읽기 가능

-- 마켓플레이스 상품 상태 테이블 RLS 정책
CREATE POLICY "marketplace_product_status_policy" ON marketplace_product_status
    FOR ALL USING (true); -- 모든 사용자가 읽기 가능

-- 트리거 함수 생성 (updated_at 자동 업데이트)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_marketplace_fees_updated_at 
    BEFORE UPDATE ON marketplace_fees 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pricing_rules_v2_updated_at 
    BEFORE UPDATE ON pricing_rules_v2 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_marketplace_product_status_updated_at 
    BEFORE UPDATE ON marketplace_product_status 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 마켓플레이스 수수료 데이터 삽입 함수
CREATE OR REPLACE FUNCTION insert_marketplace_fees()
RETURNS VOID AS $$
BEGIN
    -- 쿠팡 수수료 데이터 삽입
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'fashion',
        'commission',
        0.08,
        '패션의류 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Coupang'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'beauty',
        'commission',
        0.10,
        '뷰티 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Coupang'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'home_living',
        'commission',
        0.08,
        '홈리빙 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Coupang'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'digital',
        'commission',
        0.05,
        '디지털 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Coupang'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'food',
        'commission',
        0.12,
        '식품 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Coupang'
    ON CONFLICT DO NOTHING;
    
    -- 쿠팡 결제 수수료
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'etc',
        'payment',
        0.025,
        '결제 수수료'
    FROM marketplaces m WHERE m.name = 'Coupang'
    ON CONFLICT DO NOTHING;
    
    -- 네이버 스마트스토어 수수료 데이터 삽입
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'fashion',
        'commission',
        0.05,
        '패션의류 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Naver SmartStore'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'beauty',
        'commission',
        0.06,
        '뷰티 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Naver SmartStore'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'home_living',
        'commission',
        0.05,
        '홈리빙 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Naver SmartStore'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'digital',
        'commission',
        0.03,
        '디지털 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Naver SmartStore'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'food',
        'commission',
        0.08,
        '식품 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Naver SmartStore'
    ON CONFLICT DO NOTHING;
    
    -- 네이버 결제 수수료
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'etc',
        'payment',
        0.02,
        '결제 수수료'
    FROM marketplaces m WHERE m.name = 'Naver SmartStore'
    ON CONFLICT DO NOTHING;
    
    -- 11번가 수수료 데이터 삽입
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'fashion',
        'commission',
        0.07,
        '패션의류 판매 수수료'
    FROM marketplaces m WHERE m.name = '11st'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'beauty',
        'commission',
        0.08,
        '뷰티 판매 수수료'
    FROM marketplaces m WHERE m.name = '11st'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'home_living',
        'commission',
        0.07,
        '홈리빙 판매 수수료'
    FROM marketplaces m WHERE m.name = '11st'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'digital',
        'commission',
        0.04,
        '디지털 판매 수수료'
    FROM marketplaces m WHERE m.name = '11st'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'food',
        'commission',
        0.10,
        '식품 판매 수수료'
    FROM marketplaces m WHERE m.name = '11st'
    ON CONFLICT DO NOTHING;
    
    -- 11번가 결제 수수료
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'etc',
        'payment',
        0.022,
        '결제 수수료'
    FROM marketplaces m WHERE m.name = '11st'
    ON CONFLICT DO NOTHING;
    
    -- 지마켓 수수료 데이터 삽입
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'fashion',
        'commission',
        0.06,
        '패션의류 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Gmarket'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'beauty',
        'commission',
        0.07,
        '뷰티 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Gmarket'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'home_living',
        'commission',
        0.06,
        '홈리빙 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Gmarket'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'digital',
        'commission',
        0.03,
        '디지털 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Gmarket'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'food',
        'commission',
        0.09,
        '식품 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Gmarket'
    ON CONFLICT DO NOTHING;
    
    -- 지마켓 결제 수수료
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'etc',
        'payment',
        0.02,
        '결제 수수료'
    FROM marketplaces m WHERE m.name = 'Gmarket'
    ON CONFLICT DO NOTHING;
    
    -- 옥션 수수료 데이터 삽입
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'fashion',
        'commission',
        0.06,
        '패션의류 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Auction'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'beauty',
        'commission',
        0.07,
        '뷰티 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Auction'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'home_living',
        'commission',
        0.06,
        '홈리빙 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Auction'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'digital',
        'commission',
        0.03,
        '디지털 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Auction'
    ON CONFLICT DO NOTHING;
    
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'food',
        'commission',
        0.09,
        '식품 판매 수수료'
    FROM marketplaces m WHERE m.name = 'Auction'
    ON CONFLICT DO NOTHING;
    
    -- 옥션 결제 수수료
    INSERT INTO marketplace_fees (marketplace_id, category, fee_type, fee_rate, description)
    SELECT 
        m.id,
        'etc',
        'payment',
        0.02,
        '결제 수수료'
    FROM marketplaces m WHERE m.name = 'Auction'
    ON CONFLICT DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- 마켓플레이스 데이터 삽입 함수
CREATE OR REPLACE FUNCTION insert_marketplaces()
RETURNS VOID AS $$
BEGIN
    INSERT INTO marketplaces (name, api_endpoint, is_active) VALUES
    ('Coupang', 'https://api.coupang.com', true),
    ('Naver SmartStore', 'https://api.commerce.naver.com', true),
    ('11st', 'https://api.11st.co.kr', true),
    ('Gmarket', 'https://api.gmarket.co.kr', true),
    ('Auction', 'https://api.auction.co.kr', true)
    ON CONFLICT (name) DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- 함수 실행
SELECT insert_marketplaces();
SELECT insert_marketplace_fees();
