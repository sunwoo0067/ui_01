-- 외부 시스템 연동을 위한 스키마
-- Migration: 007_external_integration_schema.sql

-- 웹훅 엔드포인트 테이블
CREATE TABLE IF NOT EXISTS webhook_endpoints (
    id VARCHAR(50) PRIMARY KEY,
    url TEXT NOT NULL,
    secret TEXT NOT NULL,
    events JSONB NOT NULL, -- 구독할 이벤트 목록
    is_active BOOLEAN DEFAULT TRUE,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    timeout INTEGER DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 웹훅 전송 로그 테이블
CREATE TABLE IF NOT EXISTS webhook_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id VARCHAR(50) NOT NULL,
    endpoint_id VARCHAR(50) REFERENCES webhook_endpoints(id),
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    status_code INTEGER,
    response_data JSONB,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    response_time DECIMAL(10,3),
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API 연동 설정 테이블
CREATE TABLE IF NOT EXISTS api_integrations (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    base_url TEXT NOT NULL,
    api_type VARCHAR(20) NOT NULL, -- 'rest', 'graphql', 'soap', 'webhook'
    auth_type VARCHAR(20) NOT NULL, -- 'none', 'api_key', 'bearer_token', 'basic_auth', 'oauth2', 'jwt'
    auth_config JSONB NOT NULL, -- 인증 설정 정보
    headers JSONB DEFAULT '{}', -- 기본 헤더
    timeout INTEGER DEFAULT 30,
    retry_count INTEGER DEFAULT 3,
    rate_limit INTEGER, -- 분당 요청 수 제한
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API 호출 로그 테이블
CREATE TABLE IF NOT EXISTS api_call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id VARCHAR(50) REFERENCES api_integrations(id),
    method VARCHAR(10) NOT NULL,
    endpoint TEXT NOT NULL,
    request_data JSONB,
    response_data JSONB,
    status_code INTEGER,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    response_time DECIMAL(10,3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 외부 시스템 동기화 로그 테이블
CREATE TABLE IF NOT EXISTS sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_type VARCHAR(50) NOT NULL, -- 'marketplace', 'supplier', 'inventory', 'order'
    system_id VARCHAR(50) NOT NULL,
    operation VARCHAR(50) NOT NULL, -- 'sync', 'push', 'pull', 'update'
    data_type VARCHAR(50) NOT NULL, -- 'product', 'order', 'inventory', 'price'
    total_records INTEGER DEFAULT 0,
    successful_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    sync_details JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'running', -- 'running', 'completed', 'failed', 'cancelled'
    error_message TEXT
);

-- 외부 시스템 상태 모니터링 테이블
CREATE TABLE IF NOT EXISTS system_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_id VARCHAR(50) NOT NULL,
    system_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'online', 'offline', 'error', 'maintenance'
    last_check TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_time DECIMAL(10,3),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_webhook_endpoints_active 
ON webhook_endpoints(is_active);

CREATE INDEX IF NOT EXISTS idx_webhook_logs_endpoint 
ON webhook_logs(endpoint_id, created_at);

CREATE INDEX IF NOT EXISTS idx_webhook_logs_event_type 
ON webhook_logs(event_type, created_at);

CREATE INDEX IF NOT EXISTS idx_api_integrations_active 
ON api_integrations(is_active);

CREATE INDEX IF NOT EXISTS idx_api_call_logs_integration 
ON api_call_logs(integration_id, created_at);

CREATE INDEX IF NOT EXISTS idx_sync_logs_system 
ON sync_logs(system_type, system_id, created_at);

CREATE INDEX IF NOT EXISTS idx_sync_logs_status 
ON sync_logs(status, started_at);

CREATE INDEX IF NOT EXISTS idx_system_status_system 
ON system_status(system_id, system_type);

CREATE INDEX IF NOT EXISTS idx_system_status_last_check 
ON system_status(last_check);

-- RLS 정책 설정
ALTER TABLE webhook_endpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_call_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_status ENABLE ROW LEVEL SECURITY;

-- 기본 정책 설정 (모든 사용자 접근 허용)
CREATE POLICY "Enable all operations for webhook_endpoints" 
ON webhook_endpoints FOR ALL USING (true);

CREATE POLICY "Enable all operations for webhook_logs" 
ON webhook_logs FOR ALL USING (true);

CREATE POLICY "Enable all operations for api_integrations" 
ON api_integrations FOR ALL USING (true);

CREATE POLICY "Enable all operations for api_call_logs" 
ON api_call_logs FOR ALL USING (true);

CREATE POLICY "Enable all operations for sync_logs" 
ON sync_logs FOR ALL USING (true);

CREATE POLICY "Enable all operations for system_status" 
ON system_status FOR ALL USING (true);

-- 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_external_integration_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 업데이트 트리거 생성
CREATE TRIGGER update_webhook_endpoints_updated_at
    BEFORE UPDATE ON webhook_endpoints
    FOR EACH ROW
    EXECUTE FUNCTION update_external_integration_updated_at();

CREATE TRIGGER update_api_integrations_updated_at
    BEFORE UPDATE ON api_integrations
    FOR EACH ROW
    EXECUTE FUNCTION update_external_integration_updated_at();

-- 웹훅 통계 뷰 생성
CREATE OR REPLACE VIEW webhook_statistics AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    event_type,
    COUNT(*) as total_webhooks,
    COUNT(*) FILTER (WHERE success = true) as successful_webhooks,
    COUNT(*) FILTER (WHERE success = false) as failed_webhooks,
    AVG(response_time) as avg_response_time,
    MAX(response_time) as max_response_time
FROM webhook_logs
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at), event_type
ORDER BY hour DESC, event_type;

-- API 호출 통계 뷰 생성
CREATE OR REPLACE VIEW api_call_statistics AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    integration_id,
    method,
    COUNT(*) as total_calls,
    COUNT(*) FILTER (WHERE success = true) as successful_calls,
    COUNT(*) FILTER (WHERE success = false) as failed_calls,
    AVG(response_time) as avg_response_time,
    MAX(response_time) as max_response_time
FROM api_call_logs
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at), integration_id, method
ORDER BY hour DESC, integration_id, method;

-- 시스템 상태 요약 뷰 생성
CREATE OR REPLACE VIEW system_status_summary AS
SELECT 
    system_type,
    COUNT(*) as total_systems,
    COUNT(*) FILTER (WHERE status = 'online') as online_systems,
    COUNT(*) FILTER (WHERE status = 'offline') as offline_systems,
    COUNT(*) FILTER (WHERE status = 'error') as error_systems,
    AVG(response_time) FILTER (WHERE status = 'online') as avg_response_time,
    MAX(last_check) as last_check_time
FROM system_status
GROUP BY system_type;

-- 동기화 상태 요약 뷰 생성
CREATE OR REPLACE VIEW sync_status_summary AS
SELECT 
    system_type,
    system_id,
    COUNT(*) as total_syncs,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_syncs,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_syncs,
    COUNT(*) FILTER (WHERE status = 'running') as running_syncs,
    SUM(total_records) as total_records_processed,
    SUM(successful_records) as total_successful_records,
    SUM(failed_records) as total_failed_records,
    MAX(started_at) as last_sync_time
FROM sync_logs
WHERE started_at >= NOW() - INTERVAL '7 days'
GROUP BY system_type, system_id
ORDER BY system_type, system_id;

-- 웹훅 엔드포인트 검증 함수
CREATE OR REPLACE FUNCTION validate_webhook_endpoint()
RETURNS TRIGGER AS $$
BEGIN
    -- URL 형식 검증
    IF NEW.url !~ '^https?://' THEN
        RAISE EXCEPTION '웹훅 URL은 http:// 또는 https://로 시작해야 합니다';
    END IF;
    
    -- 시크릿 키 길이 검증
    IF LENGTH(NEW.secret) < 16 THEN
        RAISE EXCEPTION '웹훅 시크릿 키는 최소 16자 이상이어야 합니다';
    END IF;
    
    -- 이벤트 목록 검증
    IF jsonb_array_length(NEW.events) = 0 THEN
        RAISE EXCEPTION '최소 하나 이상의 이벤트를 구독해야 합니다';
    END IF;
    
    -- 타임아웃 범위 검증
    IF NEW.timeout < 5 OR NEW.timeout > 300 THEN
        RAISE EXCEPTION '타임아웃은 5초 이상 300초 이하여야 합니다';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 웹훅 엔드포인트 검증 트리거
CREATE TRIGGER validate_webhook_endpoint_trigger
    BEFORE INSERT OR UPDATE ON webhook_endpoints
    FOR EACH ROW
    EXECUTE FUNCTION validate_webhook_endpoint();

-- API 연동 설정 검증 함수
CREATE OR REPLACE FUNCTION validate_api_integration()
RETURNS TRIGGER AS $$
BEGIN
    -- URL 형식 검증
    IF NEW.base_url !~ '^https?://' THEN
        RAISE EXCEPTION 'API 기본 URL은 http:// 또는 https://로 시작해야 합니다';
    END IF;
    
    -- API 타입 검증
    IF NEW.api_type NOT IN ('rest', 'graphql', 'soap', 'webhook') THEN
        RAISE EXCEPTION '지원되지 않는 API 타입입니다';
    END IF;
    
    -- 인증 타입 검증
    IF NEW.auth_type NOT IN ('none', 'api_key', 'bearer_token', 'basic_auth', 'oauth2', 'jwt') THEN
        RAISE EXCEPTION '지원되지 않는 인증 타입입니다';
    END IF;
    
    -- 타임아웃 범위 검증
    IF NEW.timeout < 5 OR NEW.timeout > 300 THEN
        RAISE EXCEPTION '타임아웃은 5초 이상 300초 이하여야 합니다';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- API 연동 설정 검증 트리거
CREATE TRIGGER validate_api_integration_trigger
    BEFORE INSERT OR UPDATE ON api_integrations
    FOR EACH ROW
    EXECUTE FUNCTION validate_api_integration();

-- 마이그레이션 완료 로그
INSERT INTO migration_log (migration_name, applied_at, description)
VALUES (
    '007_external_integration_schema',
    NOW(),
    'Added external system integration support with webhooks, API connectors, and monitoring capabilities'
) ON CONFLICT (migration_name) DO NOTHING;
