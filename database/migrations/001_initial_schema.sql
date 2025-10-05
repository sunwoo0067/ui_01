-- 드롭쉬핑 대량등록 자동화 프로그램 - 초기 스키마

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. 판매자 (Sellers) 테이블
CREATE TABLE IF NOT EXISTS sellers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 마켓플레이스 (Marketplaces) 테이블
CREATE TABLE IF NOT EXISTS marketplaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    api_endpoint TEXT,
    credentials JSONB, -- 암호화된 인증 정보
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 상품 (Products) 테이블
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seller_id UUID REFERENCES sellers(id) ON DELETE CASCADE,

    -- 기본 정보
    title TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2),
    currency TEXT DEFAULT 'KRW',

    -- 재고 및 옵션
    stock_quantity INTEGER DEFAULT 0,
    options JSONB, -- 색상, 사이즈 등

    -- 카테고리 및 태그
    category TEXT,
    tags TEXT[],

    -- 이미지 (Storage URLs)
    images JSONB, -- [{"url": "...", "is_primary": true}]

    -- AI 검색용 임베딩 (pgvector)
    embedding VECTOR(1536), -- OpenAI ada-002 dimension

    -- 상태 관리
    status TEXT CHECK (status IN ('draft', 'pending', 'uploaded', 'failed')) DEFAULT 'draft',
    error_message TEXT,

    -- 메타데이터
    metadata JSONB, -- 추가 정보 (브랜드, 원산지 등)

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 업로드 배치 (Upload Batches) 테이블
CREATE TABLE IF NOT EXISTS upload_batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seller_id UUID REFERENCES sellers(id) ON DELETE CASCADE,

    -- 배치 정보
    name TEXT NOT NULL,
    total_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,

    -- 상태
    status TEXT CHECK (status IN ('pending', 'processing', 'completed', 'failed')) DEFAULT 'pending',

    -- 에러 로그
    error_log JSONB, -- [{product_id, error, timestamp}]

    -- 진행 상황 (0-100)
    progress INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 5. 상품-마켓플레이스 매핑 (Product Mappings) 테이블
CREATE TABLE IF NOT EXISTS product_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    marketplace_id UUID REFERENCES marketplaces(id) ON DELETE CASCADE,

    -- 외부 플랫폼 정보
    external_id TEXT, -- 마켓플레이스의 상품 ID
    external_url TEXT,

    -- 동기화 상태
    sync_status TEXT CHECK (sync_status IN ('synced', 'pending', 'failed')) DEFAULT 'pending',
    last_synced_at TIMESTAMP WITH TIME ZONE,

    -- 플랫폼별 설정
    platform_config JSONB, -- 배송비, 할인율 등

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(product_id, marketplace_id)
);

-- 6. 이미지 메타데이터 (Image Metadata) 테이블
CREATE TABLE IF NOT EXISTS image_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,

    -- Storage 정보
    storage_path TEXT NOT NULL,
    public_url TEXT NOT NULL,

    -- 이미지 속성
    width INTEGER,
    height INTEGER,
    file_size INTEGER, -- bytes
    format TEXT, -- jpg, png, webp

    -- 최적화 여부
    is_optimized BOOLEAN DEFAULT false,
    original_path TEXT, -- 원본 경로

    -- 순서
    display_order INTEGER DEFAULT 0,
    is_primary BOOLEAN DEFAULT false,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_products_seller_id ON products(seller_id);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_embedding ON products USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_upload_batches_seller_id ON upload_batches(seller_id);
CREATE INDEX idx_upload_batches_status ON upload_batches(status);

CREATE INDEX idx_product_mappings_product_id ON product_mappings(product_id);
CREATE INDEX idx_product_mappings_marketplace_id ON product_mappings(marketplace_id);
CREATE INDEX idx_product_mappings_external_id ON product_mappings(external_id);

CREATE INDEX idx_image_metadata_product_id ON image_metadata(product_id);

-- Row Level Security (RLS) 활성화
ALTER TABLE sellers ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE image_metadata ENABLE ROW LEVEL SECURITY;

-- RLS 정책: 판매자는 자신의 데이터만 접근 가능
CREATE POLICY seller_isolation_sellers ON sellers
    FOR ALL
    USING (auth.uid()::text = id::text);

CREATE POLICY seller_isolation_products ON products
    FOR ALL
    USING (seller_id IN (SELECT id FROM sellers WHERE auth.uid()::text = id::text));

CREATE POLICY seller_isolation_upload_batches ON upload_batches
    FOR ALL
    USING (seller_id IN (SELECT id FROM sellers WHERE auth.uid()::text = id::text));

CREATE POLICY seller_isolation_product_mappings ON product_mappings
    FOR ALL
    USING (product_id IN (SELECT id FROM products WHERE seller_id IN (SELECT id FROM sellers WHERE auth.uid()::text = id::text)));

CREATE POLICY seller_isolation_image_metadata ON image_metadata
    FOR ALL
    USING (product_id IN (SELECT id FROM products WHERE seller_id IN (SELECT id FROM sellers WHERE auth.uid()::text = id::text)));

-- 트리거: updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_sellers_updated_at BEFORE UPDATE ON sellers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 트리거: 배치 진행 상황 자동 계산
CREATE OR REPLACE FUNCTION update_batch_progress()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE upload_batches
    SET
        progress = CASE
            WHEN total_count > 0 THEN ((success_count + failed_count) * 100 / total_count)
            ELSE 0
        END,
        status = CASE
            WHEN (success_count + failed_count) >= total_count THEN 'completed'
            ELSE status
        END,
        completed_at = CASE
            WHEN (success_count + failed_count) >= total_count THEN NOW()
            ELSE completed_at
        END
    WHERE id = NEW.id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_upload_batch_progress AFTER UPDATE OF success_count, failed_count ON upload_batches
    FOR EACH ROW EXECUTE FUNCTION update_batch_progress();

-- 함수: 시맨틱 검색 (유사 상품 찾기)
CREATE OR REPLACE FUNCTION find_similar_products(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.8,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    description TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.title,
        p.description,
        1 - (p.embedding <=> query_embedding) AS similarity
    FROM products p
    WHERE 1 - (p.embedding <=> query_embedding) > match_threshold
    ORDER BY p.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 함수: 대량 삽입 (PostgreSQL COPY)
CREATE OR REPLACE FUNCTION bulk_insert_products(csv_data TEXT)
RETURNS INTEGER AS $$
DECLARE
    inserted_count INTEGER;
BEGIN
    CREATE TEMP TABLE temp_products (
        seller_id UUID,
        title TEXT,
        description TEXT,
        price DECIMAL(10, 2),
        stock_quantity INTEGER
    ) ON COMMIT DROP;

    EXECUTE format('COPY temp_products FROM STDIN WITH CSV HEADER');

    INSERT INTO products (seller_id, title, description, price, stock_quantity)
    SELECT * FROM temp_products;

    GET DIAGNOSTICS inserted_count = ROW_COUNT;

    RETURN inserted_count;
END;
$$ LANGUAGE plpgsql;

-- Storage 버킷 생성 (Supabase Dashboard에서 실행 필요)
-- 또는 Supabase CLI로 실행:
-- supabase storage create product-images --public

-- Storage RLS 정책 (예시 - Dashboard에서 설정)
-- CREATE POLICY "Authenticated users can upload images" ON storage.objects
--     FOR INSERT TO authenticated
--     WITH CHECK (bucket_id = 'product-images');
