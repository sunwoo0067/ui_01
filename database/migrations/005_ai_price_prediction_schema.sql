-- AI 가격 예측 시스템을 위한 데이터베이스 스키마
-- 파일: database/migrations/005_ai_price_prediction_schema.sql

-- 가격 예측 결과 테이블
CREATE TABLE IF NOT EXISTS price_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    predicted_price DECIMAL(10, 2) NOT NULL,
    strategy VARCHAR(50) NOT NULL, -- 'competitive', 'premium', 'aggressive', 'conservative'
    confidence_score DECIMAL(3, 2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    reasoning TEXT,
    market_trend JSONB,
    model_predictions JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 가격 예측 모델 성능 테이블
CREATE TABLE IF NOT EXISTS model_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    mae DECIMAL(10, 2), -- Mean Absolute Error
    mse DECIMAL(10, 2), -- Mean Squared Error
    r2_score DECIMAL(5, 4), -- R-squared score
    rmse DECIMAL(10, 2), -- Root Mean Squared Error
    training_samples INTEGER,
    test_samples INTEGER,
    feature_importance JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 가격 전략 히스토리 테이블
CREATE TABLE IF NOT EXISTS pricing_strategy_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    recommended_price DECIMAL(10, 2) NOT NULL,
    actual_price DECIMAL(10, 2),
    market_performance JSONB, -- 시장 성과 지표
    sales_volume INTEGER,
    revenue DECIMAL(12, 2),
    profit_margin DECIMAL(5, 2),
    competitor_response JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 시장 트렌드 분석 테이블
CREATE TABLE IF NOT EXISTS market_trend_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(100),
    trend_direction VARCHAR(20) NOT NULL, -- 'up', 'down', 'stable'
    trend_strength DECIMAL(3, 2) NOT NULL CHECK (trend_strength >= 0 AND trend_strength <= 1),
    volatility DECIMAL(5, 4) NOT NULL,
    seasonal_pattern VARCHAR(50),
    competitor_count INTEGER NOT NULL,
    price_range_min DECIMAL(10, 2),
    price_range_max DECIMAL(10, 2),
    analysis_period_start TIMESTAMP WITH TIME ZONE,
    analysis_period_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI 모델 훈련 로그 테이블
CREATE TABLE IF NOT EXISTS model_training_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    training_type VARCHAR(50) NOT NULL, -- 'initial', 'retrain', 'incremental'
    category VARCHAR(100),
    training_samples INTEGER NOT NULL,
    validation_samples INTEGER,
    training_duration_seconds INTEGER,
    hyperparameters JSONB,
    performance_metrics JSONB,
    status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'partial'
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 가격 예측 요청 로그 테이블
CREATE TABLE IF NOT EXISTS prediction_request_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    request_type VARCHAR(50) NOT NULL, -- 'single', 'batch', 'category'
    input_features JSONB NOT NULL,
    prediction_count INTEGER NOT NULL,
    processing_time_ms INTEGER,
    status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'partial'
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_price_predictions_product_id ON price_predictions(product_id);
CREATE INDEX IF NOT EXISTS idx_price_predictions_created_at ON price_predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_price_predictions_strategy ON price_predictions(strategy);

CREATE INDEX IF NOT EXISTS idx_model_performance_model_name ON model_performance(model_name);
CREATE INDEX IF NOT EXISTS idx_model_performance_category ON model_performance(category);
CREATE INDEX IF NOT EXISTS idx_model_performance_created_at ON model_performance(created_at);

CREATE INDEX IF NOT EXISTS idx_pricing_strategy_product_id ON pricing_strategy_history(product_id);
CREATE INDEX IF NOT EXISTS idx_pricing_strategy_created_at ON pricing_strategy_history(created_at);

CREATE INDEX IF NOT EXISTS idx_market_trend_category ON market_trend_analysis(category);
CREATE INDEX IF NOT EXISTS idx_market_trend_created_at ON market_trend_analysis(created_at);

CREATE INDEX IF NOT EXISTS idx_training_logs_model_name ON model_training_logs(model_name);
CREATE INDEX IF NOT EXISTS idx_training_logs_status ON model_training_logs(status);
CREATE INDEX IF NOT EXISTS idx_training_logs_created_at ON model_training_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_prediction_logs_product_id ON prediction_request_logs(product_id);
CREATE INDEX IF NOT EXISTS idx_prediction_logs_status ON prediction_request_logs(status);
CREATE INDEX IF NOT EXISTS idx_prediction_logs_created_at ON prediction_request_logs(created_at);

-- RLS (Row Level Security) 정책
ALTER TABLE price_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE pricing_strategy_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_trend_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_training_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE prediction_request_logs ENABLE ROW LEVEL SECURITY;

-- 기본 정책 (모든 사용자가 읽기/쓰기 가능)
CREATE POLICY "Enable all operations for all users" ON price_predictions FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON model_performance FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON pricing_strategy_history FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON market_trend_analysis FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON model_training_logs FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON prediction_request_logs FOR ALL USING (true);

-- 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 업데이트 트리거 생성
CREATE TRIGGER update_price_predictions_updated_at 
    BEFORE UPDATE ON price_predictions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pricing_strategy_history_updated_at 
    BEFORE UPDATE ON pricing_strategy_history 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 뷰 생성: 최신 가격 예측 결과
CREATE OR REPLACE VIEW latest_price_predictions AS
SELECT 
    pp.*,
    ROW_NUMBER() OVER (PARTITION BY pp.product_id ORDER BY pp.created_at DESC) as rn
FROM price_predictions pp;

-- 뷰 생성: 모델 성능 요약
CREATE OR REPLACE VIEW model_performance_summary AS
SELECT 
    model_name,
    category,
    AVG(r2_score) as avg_r2_score,
    AVG(mae) as avg_mae,
    AVG(rmse) as avg_rmse,
    COUNT(*) as training_count,
    MAX(created_at) as last_training
FROM model_performance
GROUP BY model_name, category;

-- 뷰 생성: 시장 트렌드 요약
CREATE OR REPLACE VIEW market_trend_summary AS
SELECT 
    category,
    trend_direction,
    AVG(trend_strength) as avg_trend_strength,
    AVG(volatility) as avg_volatility,
    AVG(competitor_count) as avg_competitor_count,
    COUNT(*) as analysis_count,
    MAX(created_at) as last_analysis
FROM market_trend_analysis
GROUP BY category, trend_direction;
