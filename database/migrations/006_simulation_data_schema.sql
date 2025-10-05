-- 시뮬레이션 데이터 지원을 위한 스키마 업데이트
-- Migration: 006_simulation_data_schema.sql

-- normalized_products 테이블에 시뮬레이션 관련 컬럼 추가
ALTER TABLE normalized_products 
ADD COLUMN IF NOT EXISTS collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS is_simulation BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_competitor BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS simulation_source VARCHAR(50),
ADD COLUMN IF NOT EXISTS data_quality_score DECIMAL(3,2) DEFAULT 1.0;

-- 시뮬레이션 데이터 품질 테이블 생성
CREATE TABLE IF NOT EXISTS simulation_data_quality (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES normalized_products(id),
    quality_score DECIMAL(3,2) NOT NULL,
    completeness_score DECIMAL(3,2) NOT NULL,
    accuracy_score DECIMAL(3,2) NOT NULL,
    consistency_score DECIMAL(3,2) NOT NULL,
    evaluation_criteria JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 시뮬레이션 분석 결과 테이블 생성
CREATE TABLE IF NOT EXISTS simulation_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_type VARCHAR(50) NOT NULL, -- 'trend', 'prediction', 'recommendation'
    analysis_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    model_version VARCHAR(20),
    simulation_params JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 시뮬레이션 데이터 통계 테이블 생성
CREATE TABLE IF NOT EXISTS simulation_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stat_type VARCHAR(50) NOT NULL, -- 'product_count', 'price_range', 'category_distribution'
    stat_value DECIMAL(15,2) NOT NULL,
    stat_metadata JSONB,
    simulation_batch_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_normalized_products_simulation 
ON normalized_products(is_simulation, collected_at);

CREATE INDEX IF NOT EXISTS idx_normalized_products_competitor 
ON normalized_products(is_competitor, collected_at);

CREATE INDEX IF NOT EXISTS idx_simulation_quality_product 
ON simulation_data_quality(product_id);

CREATE INDEX IF NOT EXISTS idx_simulation_analysis_type 
ON simulation_analysis_results(analysis_type, created_at);

CREATE INDEX IF NOT EXISTS idx_simulation_statistics_type 
ON simulation_statistics(stat_type, created_at);

-- RLS 정책 설정
ALTER TABLE simulation_data_quality ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulation_analysis_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulation_statistics ENABLE ROW LEVEL SECURITY;

-- 기본 정책 설정 (모든 사용자 접근 허용)
CREATE POLICY "Enable all operations for simulation_data_quality" 
ON simulation_data_quality FOR ALL USING (true);

CREATE POLICY "Enable all operations for simulation_analysis_results" 
ON simulation_analysis_results FOR ALL USING (true);

CREATE POLICY "Enable all operations for simulation_statistics" 
ON simulation_statistics FOR ALL USING (true);

-- 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_simulation_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 업데이트 트리거 생성
CREATE TRIGGER update_simulation_data_quality_updated_at
    BEFORE UPDATE ON simulation_data_quality
    FOR EACH ROW
    EXECUTE FUNCTION update_simulation_updated_at();

-- 시뮬레이션 데이터 검증 함수
CREATE OR REPLACE FUNCTION validate_simulation_data()
RETURNS TRIGGER AS $$
BEGIN
    -- 시뮬레이션 데이터 품질 점수 검증
    IF NEW.is_simulation = TRUE THEN
        IF NEW.data_quality_score < 0 OR NEW.data_quality_score > 1 THEN
            RAISE EXCEPTION 'Data quality score must be between 0 and 1';
        END IF;
        
        -- 시뮬레이션 소스 필수 검증
        IF NEW.simulation_source IS NULL OR NEW.simulation_source = '' THEN
            RAISE EXCEPTION 'Simulation source is required for simulation data';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 시뮬레이션 데이터 검증 트리거
CREATE TRIGGER validate_simulation_data_trigger
    BEFORE INSERT OR UPDATE ON normalized_products
    FOR EACH ROW
    EXECUTE FUNCTION validate_simulation_data();

-- 시뮬레이션 데이터 통계 뷰 생성
CREATE OR REPLACE VIEW simulation_data_summary AS
SELECT 
    COUNT(*) as total_products,
    COUNT(*) FILTER (WHERE is_simulation = TRUE) as simulation_products,
    COUNT(*) FILTER (WHERE is_competitor = TRUE) as competitor_products,
    AVG(data_quality_score) FILTER (WHERE is_simulation = TRUE) as avg_quality_score,
    MIN(collected_at) as earliest_collection,
    MAX(collected_at) as latest_collection
FROM normalized_products;

-- 시뮬레이션 데이터 품질 뷰 생성
CREATE OR REPLACE VIEW simulation_quality_summary AS
SELECT 
    p.id as product_id,
    p.name,
    p.is_simulation,
    p.data_quality_score,
    q.quality_score,
    q.completeness_score,
    q.accuracy_score,
    q.consistency_score
FROM normalized_products p
LEFT JOIN simulation_data_quality q ON p.id = q.product_id
WHERE p.is_simulation = TRUE;

-- 마이그레이션 완료 로그
INSERT INTO migration_log (migration_name, applied_at, description)
VALUES (
    '006_simulation_data_schema',
    NOW(),
    'Added simulation data support with quality tracking and analysis capabilities'
) ON CONFLICT (migration_name) DO NOTHING;
