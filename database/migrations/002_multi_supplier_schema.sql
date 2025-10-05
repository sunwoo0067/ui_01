-- 멀티공급사/멀티계정 드롭쉬핑 자동화 스키마
-- 개인용 (배포 없음)

-- 1. 공급사 (Suppliers) 테이블
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 공급사 기본 정보
    name TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL, -- 코드명 (예: 'naver_smartstore', 'taobao')
    type TEXT NOT NULL CHECK (type IN ('api', 'excel', 'web_crawling')),

    -- API 설정 (type='api'인 경우)
    api_endpoint TEXT,
    api_version TEXT,
    auth_type TEXT, -- 'api_key', 'oauth', 'basic_auth' 등

    -- 인증 정보 (암호화 저장)
    credentials JSONB, -- {api_key, secret, username, password 등}

    -- 웹 크롤링 설정 (type='web_crawling'인 경우)
    crawl_config JSONB, -- {base_url, selectors, pagination 등}

    -- 엑셀 설정 (type='excel'인 경우)
    excel_config JSONB, -- {column_mapping, sheet_name 등}

    -- 데이터 매핑 설정 (공급사별 필드 매핑)
    field_mapping JSONB, -- {supplier_field: our_field}

    -- 상태
    is_active BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP WITH TIME ZONE,

    -- 메타데이터
    metadata JSONB, -- 추가 정보

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 공급사 계정 (Supplier Accounts) 테이블 - 멀티계정
CREATE TABLE IF NOT EXISTS supplier_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,

    -- 계정 정보
    account_name TEXT NOT NULL, -- 계정 식별명
    account_credentials JSONB NOT NULL, -- 계정별 인증 정보

    -- 상태
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(supplier_id, account_name)
);

-- 3. 원본 데이터 (Raw Data) 테이블 - 수집된 원본 데이터 저장
CREATE TABLE IF NOT EXISTS raw_product_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 공급사 정보
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    supplier_account_id UUID REFERENCES supplier_accounts(id) ON DELETE SET NULL,

    -- 원본 데이터 (JSONB - 공급사별 형식 유지)
    raw_data JSONB NOT NULL,

    -- 수집 정보
    collection_method TEXT NOT NULL CHECK (collection_method IN ('api', 'excel', 'web_crawling')),
    collection_source TEXT, -- URL, 파일명 등

    -- 공급사의 고유 ID (중복 체크용)
    supplier_product_id TEXT, -- 공급사의 상품 ID

    -- 처리 상태
    is_processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMP WITH TIME ZONE,

    -- 해시값 (중복 감지)
    data_hash TEXT, -- raw_data의 해시

    -- 메타데이터
    metadata JSONB, -- 수집 시간, IP, 에러 등

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 중복 방지 인덱스
    UNIQUE(supplier_id, supplier_product_id)
);

-- 4. 정규화된 상품 (Normalized Products) 테이블
CREATE TABLE IF NOT EXISTS normalized_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 원본 데이터 참조
    raw_data_id UUID REFERENCES raw_product_data(id) ON DELETE SET NULL,

    -- 공급사 정보
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    supplier_product_id TEXT,

    -- 정규화된 상품 정보
    title TEXT NOT NULL,
    description TEXT,
    price DECIMAL(12, 2) NOT NULL,
    original_price DECIMAL(12, 2),
    cost_price DECIMAL(12, 2), -- 원가
    currency TEXT DEFAULT 'KRW',

    -- 재고 및 옵션
    stock_quantity INTEGER DEFAULT 0,
    options JSONB, -- 색상, 사이즈 등

    -- 카테고리 및 태그
    category TEXT,
    tags TEXT[],
    brand TEXT,

    -- 이미지 URL (공급사 이미지)
    images JSONB, -- [{url, order}]

    -- 상품 속성 (공급사별로 다양)
    attributes JSONB, -- {weight, dimensions, material 등}

    -- AI 검색용 임베딩
    embedding VECTOR(1536),

    -- 상태
    status TEXT CHECK (status IN ('active', 'inactive', 'out_of_stock')) DEFAULT 'active',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 판매 마켓플레이스 (Sales Marketplaces) 테이블
CREATE TABLE IF NOT EXISTS sales_marketplaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 마켓플레이스 정보
    name TEXT NOT NULL, -- 네이버 스마트스토어, 쿠팡, 11번가 등
    code TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL, -- 'korean_mall', 'global_mall' 등

    -- API 설정
    api_endpoint TEXT,
    api_version TEXT,
    auth_type TEXT,

    -- 상태
    is_active BOOLEAN DEFAULT true,

    -- 수수료 정보
    commission_rate DECIMAL(5, 2), -- 수수료율 (%)

    -- 메타데이터
    metadata JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. 판매 계정 (Sales Accounts) 테이블 - 멀티계정
CREATE TABLE IF NOT EXISTS sales_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    marketplace_id UUID REFERENCES sales_marketplaces(id) ON DELETE CASCADE,

    -- 계정 정보
    account_name TEXT NOT NULL,
    account_credentials JSONB NOT NULL,

    -- 스토어 정보
    store_id TEXT,
    store_name TEXT,

    -- 상태
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(marketplace_id, account_name)
);

-- 7. 등록 상품 (Listed Products) 테이블
CREATE TABLE IF NOT EXISTS listed_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 원본 상품 참조
    normalized_product_id UUID REFERENCES normalized_products(id) ON DELETE CASCADE,

    -- 판매 마켓플레이스 정보
    marketplace_id UUID REFERENCES sales_marketplaces(id) ON DELETE CASCADE,
    sales_account_id UUID REFERENCES sales_accounts(id) ON DELETE SET NULL,

    -- 마켓플레이스의 상품 ID
    marketplace_product_id TEXT,
    marketplace_product_url TEXT,

    -- 판매 가격 (마진 포함)
    selling_price DECIMAL(12, 2) NOT NULL,
    margin_rate DECIMAL(5, 2), -- 마진율 (%)

    -- 등록 정보
    title TEXT NOT NULL, -- 마켓플레이스용 제목 (수정 가능)
    description TEXT, -- 마켓플레이스용 설명

    -- 이미지 (Supabase Storage에 복사본)
    images JSONB,

    -- 상태
    status TEXT CHECK (status IN ('draft', 'pending', 'active', 'paused', 'failed')) DEFAULT 'draft',

    -- 동기화
    last_synced_at TIMESTAMP WITH TIME ZONE,
    sync_status TEXT CHECK (sync_status IN ('synced', 'pending', 'failed')),

    -- 메타데이터
    metadata JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(normalized_product_id, marketplace_id, sales_account_id)
);

-- 8. 수집 작업 (Collection Jobs) 테이블
CREATE TABLE IF NOT EXISTS collection_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 공급사 정보
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    supplier_account_id UUID REFERENCES supplier_accounts(id) ON DELETE SET NULL,

    -- 작업 정보
    job_type TEXT NOT NULL CHECK (job_type IN ('api', 'excel', 'web_crawling')),
    job_name TEXT NOT NULL,

    -- 설정
    config JSONB, -- API params, 엑셀 경로, 크롤링 URL 등

    -- 진행 상황
    status TEXT CHECK (status IN ('pending', 'running', 'completed', 'failed')) DEFAULT 'pending',
    total_items INTEGER DEFAULT 0,
    collected_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    progress INTEGER DEFAULT 0, -- 0-100

    -- 결과
    result JSONB, -- 성공/실패 상세
    error_log JSONB,

    -- 실행 시간
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. 가격 규칙 (Pricing Rules) 테이블
CREATE TABLE IF NOT EXISTS pricing_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 적용 범위
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    marketplace_id UUID REFERENCES sales_marketplaces(id) ON DELETE CASCADE,

    -- 규칙 이름
    rule_name TEXT NOT NULL,
    priority INTEGER DEFAULT 0, -- 우선순위 (높을수록 먼저 적용)

    -- 조건 (JSONB 쿼리)
    conditions JSONB, -- {price_range: [min, max], category: '의류'}

    -- 가격 계산 방식
    calculation_type TEXT CHECK (calculation_type IN ('fixed_margin', 'percentage_margin', 'fixed_price')),
    calculation_value DECIMAL(12, 2), -- 마진율 또는 고정가격

    -- 반올림 설정
    round_to INTEGER DEFAULT 10, -- 10원, 100원, 1000원 단위

    -- 상태
    is_active BOOLEAN DEFAULT true,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_raw_product_data_supplier ON raw_product_data(supplier_id);
CREATE INDEX idx_raw_product_data_processed ON raw_product_data(is_processed);
CREATE INDEX idx_raw_product_data_hash ON raw_product_data(data_hash);
CREATE INDEX idx_raw_product_data_supplier_product ON raw_product_data(supplier_product_id);

CREATE INDEX idx_normalized_products_supplier ON normalized_products(supplier_id);
CREATE INDEX idx_normalized_products_status ON normalized_products(status);
CREATE INDEX idx_normalized_products_embedding ON normalized_products USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_listed_products_normalized ON listed_products(normalized_product_id);
CREATE INDEX idx_listed_products_marketplace ON listed_products(marketplace_id);
CREATE INDEX idx_listed_products_status ON listed_products(status);

CREATE INDEX idx_collection_jobs_supplier ON collection_jobs(supplier_id);
CREATE INDEX idx_collection_jobs_status ON collection_jobs(status);

-- 트리거: updated_at 자동 업데이트
CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_raw_product_data_updated_at BEFORE UPDATE ON raw_product_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_normalized_products_updated_at BEFORE UPDATE ON normalized_products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_listed_products_updated_at BEFORE UPDATE ON listed_products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pricing_rules_updated_at BEFORE UPDATE ON pricing_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 함수: 수집 작업 진행률 자동 계산
CREATE OR REPLACE FUNCTION update_collection_job_progress()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE collection_jobs
    SET
        progress = CASE
            WHEN total_items > 0 THEN ((collected_items + failed_items) * 100 / total_items)
            ELSE 0
        END,
        status = CASE
            WHEN (collected_items + failed_items) >= total_items THEN 'completed'
            WHEN failed_items > 0 AND (collected_items + failed_items) < total_items THEN 'running'
            ELSE status
        END,
        completed_at = CASE
            WHEN (collected_items + failed_items) >= total_items THEN NOW()
            ELSE completed_at
        END
    WHERE id = NEW.id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_collection_job_progress_trigger
AFTER UPDATE OF collected_items, failed_items ON collection_jobs
    FOR EACH ROW EXECUTE FUNCTION update_collection_job_progress();

-- 함수: 원본 데이터 해시 생성
CREATE OR REPLACE FUNCTION generate_raw_data_hash()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_hash := MD5(NEW.raw_data::TEXT);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER generate_raw_data_hash_trigger
BEFORE INSERT OR UPDATE ON raw_product_data
    FOR EACH ROW EXECUTE FUNCTION generate_raw_data_hash();

-- 함수: 가격 규칙 적용
CREATE OR REPLACE FUNCTION apply_pricing_rule(
    p_supplier_id UUID,
    p_marketplace_id UUID,
    p_cost_price DECIMAL,
    p_category TEXT DEFAULT NULL
)
RETURNS DECIMAL AS $$
DECLARE
    v_rule pricing_rules;
    v_selling_price DECIMAL;
BEGIN
    -- 우선순위 높은 규칙부터 조회
    SELECT * INTO v_rule
    FROM pricing_rules
    WHERE supplier_id = p_supplier_id
      AND marketplace_id = p_marketplace_id
      AND is_active = true
      AND (
          conditions IS NULL OR
          (conditions->>'category' IS NULL OR conditions->>'category' = p_category)
      )
    ORDER BY priority DESC
    LIMIT 1;

    IF v_rule IS NULL THEN
        -- 기본 마진 30%
        RETURN ROUND(p_cost_price * 1.3, -1);
    END IF;

    -- 가격 계산
    v_selling_price := CASE v_rule.calculation_type
        WHEN 'percentage_margin' THEN p_cost_price * (1 + v_rule.calculation_value / 100)
        WHEN 'fixed_margin' THEN p_cost_price + v_rule.calculation_value
        WHEN 'fixed_price' THEN v_rule.calculation_value
        ELSE p_cost_price * 1.3
    END;

    -- 반올림
    RETURN ROUND(v_selling_price, -LOG(v_rule.round_to)::INTEGER);
END;
$$ LANGUAGE plpgsql;

-- 뷰: 전체 상품 현황
CREATE OR REPLACE VIEW product_overview AS
SELECT
    np.id,
    np.title,
    s.name AS supplier_name,
    np.price AS cost_price,
    COUNT(DISTINCT lp.id) AS listed_count,
    COUNT(DISTINCT lp.marketplace_id) AS marketplace_count,
    np.stock_quantity,
    np.status,
    np.created_at
FROM normalized_products np
JOIN suppliers s ON np.supplier_id = s.id
LEFT JOIN listed_products lp ON np.id = lp.normalized_product_id
GROUP BY np.id, np.title, s.name, np.price, np.stock_quantity, np.status, np.created_at;

-- 초기 데이터 (예시)
-- 공급사 예시
INSERT INTO suppliers (name, code, type, credentials) VALUES
('네이버 스마트스토어', 'naver_smartstore', 'api', '{"api_key": "YOUR_KEY"}'::jsonb),
('타오바오', 'taobao', 'web_crawling', '{"base_url": "https://taobao.com"}'::jsonb),
('엑셀 공급사', 'excel_supplier', 'excel', '{"column_mapping": {}}'::jsonb)
ON CONFLICT (code) DO NOTHING;

-- 판매 마켓플레이스 예시
INSERT INTO sales_marketplaces (name, code, type, commission_rate) VALUES
('네이버 스마트스토어', 'naver_smartstore', 'korean_mall', 5.0),
('쿠팡', 'coupang', 'korean_mall', 10.0),
('11번가', '11st', 'korean_mall', 8.0)
ON CONFLICT (code) DO NOTHING;
