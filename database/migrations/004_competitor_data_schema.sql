-- 경쟁사 데이터 수집을 위한 데이터베이스 스키마
-- 쿠팡, 네이버 스마트스토어 등 경쟁사 상품 정보 저장

-- 경쟁사 상품 정보 테이블
CREATE TABLE IF NOT EXISTS competitor_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 플랫폼 정보
    platform TEXT NOT NULL, -- coupang, naver_smartstore, gmarket, 11st 등
    product_id TEXT NOT NULL, -- 플랫폼별 상품 ID
    
    -- 상품 기본 정보
    name TEXT NOT NULL,
    price INTEGER NOT NULL DEFAULT 0,
    original_price INTEGER DEFAULT 0,
    discount_rate INTEGER DEFAULT 0,
    
    -- 판매자 정보
    seller TEXT,
    
    -- 상품 평가
    rating DECIMAL(3,2) DEFAULT 0.0, -- 평점 (0.00 ~ 5.00)
    review_count INTEGER DEFAULT 0,
    
    -- 상품 이미지 및 URL
    image_url TEXT,
    product_url TEXT,
    
    -- 상품 분류
    category TEXT,
    brand TEXT,
    
    -- 검색 정보
    search_keyword TEXT, -- 검색에 사용된 키워드
    
    -- 수집 정보
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    
    -- 제약 조건
    CONSTRAINT competitor_products_platform_check 
        CHECK (platform IN ('coupang', 'naver_smartstore', 'gmarket', '11st', 'auction')),
    CONSTRAINT competitor_products_rating_check 
        CHECK (rating >= 0.0 AND rating <= 5.0),
    
    -- 유니크 제약
    UNIQUE(platform, product_id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_competitor_products_platform ON competitor_products(platform);
CREATE INDEX IF NOT EXISTS idx_competitor_products_product_id ON competitor_products(product_id);
CREATE INDEX IF NOT EXISTS idx_competitor_products_name ON competitor_products(name);
CREATE INDEX IF NOT EXISTS idx_competitor_products_price ON competitor_products(price);
CREATE INDEX IF NOT EXISTS idx_competitor_products_seller ON competitor_products(seller);
CREATE INDEX IF NOT EXISTS idx_competitor_products_category ON competitor_products(category);
CREATE INDEX IF NOT EXISTS idx_competitor_products_search_keyword ON competitor_products(search_keyword);
CREATE INDEX IF NOT EXISTS idx_competitor_products_collected_at ON competitor_products(collected_at);
CREATE INDEX IF NOT EXISTS idx_competitor_products_is_active ON competitor_products(is_active);

-- 가격 변동 이력 테이블
CREATE TABLE IF NOT EXISTS price_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 상품 정보
    product_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    
    -- 가격 정보
    old_price INTEGER NOT NULL,
    new_price INTEGER NOT NULL,
    price_change INTEGER NOT NULL, -- 가격 변동량
    price_change_rate DECIMAL(5,2) NOT NULL, -- 가격 변동률 (%)
    
    -- 변동 시점
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT price_history_platform_check 
        CHECK (platform IN ('coupang', 'naver_smartstore', 'gmarket', '11st', 'auction'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_price_history_product_id ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_platform ON price_history(platform);
CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_price_history_price_change ON price_history(price_change);

-- 경쟁사 분석 결과 테이블
CREATE TABLE IF NOT EXISTS competitor_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 분석 대상
    analysis_type TEXT NOT NULL, -- price_comparison, market_trend, competitor_monitoring
    target_keyword TEXT NOT NULL,
    platform TEXT NOT NULL,
    
    -- 분석 결과
    analysis_data JSONB NOT NULL, -- 분석 결과 데이터
    
    -- 분석 시점
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT competitor_analysis_type_check 
        CHECK (analysis_type IN ('price_comparison', 'market_trend', 'competitor_monitoring')),
    CONSTRAINT competitor_analysis_platform_check 
        CHECK (platform IN ('coupang', 'naver_smartstore', 'gmarket', '11st', 'auction', 'all'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_competitor_analysis_type ON competitor_analysis(analysis_type);
CREATE INDEX IF NOT EXISTS idx_competitor_analysis_keyword ON competitor_analysis(target_keyword);
CREATE INDEX IF NOT EXISTS idx_competitor_analysis_platform ON competitor_analysis(platform);
CREATE INDEX IF NOT EXISTS idx_competitor_analysis_analyzed_at ON competitor_analysis(analyzed_at);

-- 가격 알림 설정 테이블
CREATE TABLE IF NOT EXISTS price_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 알림 대상
    keyword TEXT NOT NULL,
    platform TEXT NOT NULL,
    
    -- 알림 조건
    alert_type TEXT NOT NULL, -- price_drop, price_increase, new_product
    threshold_value INTEGER, -- 임계값 (가격 또는 비율)
    threshold_type TEXT NOT NULL, -- absolute, percentage
    
    -- 알림 설정
    is_active BOOLEAN DEFAULT true,
    notification_method TEXT NOT NULL, -- email, webhook, database
    
    -- 알림 이력
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    
    -- 생성 정보
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT price_alerts_platform_check 
        CHECK (platform IN ('coupang', 'naver_smartstore', 'gmarket', '11st', 'auction', 'all')),
    CONSTRAINT price_alerts_type_check 
        CHECK (alert_type IN ('price_drop', 'price_increase', 'new_product')),
    CONSTRAINT price_alerts_threshold_type_check 
        CHECK (threshold_type IN ('absolute', 'percentage')),
    CONSTRAINT price_alerts_notification_method_check 
        CHECK (notification_method IN ('email', 'webhook', 'database'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_price_alerts_keyword ON price_alerts(keyword);
CREATE INDEX IF NOT EXISTS idx_price_alerts_platform ON price_alerts(platform);
CREATE INDEX IF NOT EXISTS idx_price_alerts_is_active ON price_alerts(is_active);
CREATE INDEX IF NOT EXISTS idx_price_alerts_alert_type ON price_alerts(alert_type);

-- 가격 알림 이력 테이블
CREATE TABLE IF NOT EXISTS price_alert_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 알림 정보
    alert_id UUID REFERENCES price_alerts(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    platform TEXT NOT NULL,
    
    -- 트리거된 상품 정보
    product_id TEXT,
    product_name TEXT,
    old_price INTEGER,
    new_price INTEGER,
    price_change INTEGER,
    
    -- 알림 내용
    alert_message TEXT NOT NULL,
    notification_sent BOOLEAN DEFAULT false,
    
    -- 알림 시점
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_price_alert_logs_alert_id ON price_alert_logs(alert_id);
CREATE INDEX IF NOT EXISTS idx_price_alert_logs_keyword ON price_alert_logs(keyword);
CREATE INDEX IF NOT EXISTS idx_price_alert_logs_platform ON price_alert_logs(platform);
CREATE INDEX IF NOT EXISTS idx_price_alert_logs_triggered_at ON price_alert_logs(triggered_at);

-- 데이터 수집 로그 테이블
CREATE TABLE IF NOT EXISTS data_collection_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 수집 정보
    platform TEXT NOT NULL,
    collection_type TEXT NOT NULL, -- search, product_details, price_monitoring
    keyword TEXT,
    
    -- 수집 결과
    success BOOLEAN NOT NULL DEFAULT true,
    items_collected INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- 수집 데이터
    collection_data JSONB,
    
    -- 수집 시점
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT data_collection_logs_platform_check 
        CHECK (platform IN ('coupang', 'naver_smartstore', 'gmarket', '11st', 'auction')),
    CONSTRAINT data_collection_logs_type_check 
        CHECK (collection_type IN ('search', 'product_details', 'price_monitoring'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_data_collection_logs_platform ON data_collection_logs(platform);
CREATE INDEX IF NOT EXISTS idx_data_collection_logs_type ON data_collection_logs(collection_type);
CREATE INDEX IF NOT EXISTS idx_data_collection_logs_keyword ON data_collection_logs(keyword);
CREATE INDEX IF NOT EXISTS idx_data_collection_logs_success ON data_collection_logs(success);
CREATE INDEX IF NOT EXISTS idx_data_collection_logs_collected_at ON data_collection_logs(collected_at);

-- 업데이트 트리거 함수들
CREATE OR REPLACE FUNCTION update_price_alerts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성
CREATE TRIGGER trigger_update_price_alerts_updated_at
    BEFORE UPDATE ON price_alerts
    FOR EACH ROW
    EXECUTE FUNCTION update_price_alerts_updated_at();
