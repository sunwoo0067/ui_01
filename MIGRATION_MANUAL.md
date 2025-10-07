# 마이그레이션 수동 적용 가이드

## Supabase Dashboard를 통한 마이그레이션 적용

### 1단계: Supabase Dashboard 열기
https://supabase.com/dashboard/project/vecvkvumzhldioifgbxb/sql

### 2단계: SQL Editor에서 마이그레이션 실행

1. 왼쪽 메뉴에서 **SQL Editor** 클릭
2. **New query** 버튼 클릭
3. `database/migrations/005_marketplace_seller_schema.sql` 파일 내용 전체 복사
4. SQL Editor에 붙여넣기
5. **Run** 버튼 클릭 (Ctrl+Enter 또는 Cmd+Enter)

### 3단계: 결과 확인

실행 후 다음 메시지가 표시되면 성공:
- "Success. No rows returned"
- 또는 "already exists" (이미 존재하는 경우 - 정상)

### 4단계: 테이블 확인

1. 왼쪽 메뉴에서 **Table Editor** 클릭
2. 다음 테이블이 생성되었는지 확인:
   - `marketplace_orders`
   - `marketplace_inventory_sync_log`
   - `marketplace_api_logs`

### 5단계: 뷰 확인

SQL Editor에서 실행:
```sql
SELECT * FROM marketplace_sales_summary LIMIT 1;
```

성공 메시지가 나오면 뷰도 정상 생성된 것입니다.

---

## 자동화 스크립트가 실패하는 이유

1. **exec_sql RPC 함수 없음**: Supabase Python 클라이언트는 DDL(CREATE, ALTER) 실행을 위한 RPC 함수를 제공하지 않음
2. **DATABASE_URL 미설정**: 직접 PostgreSQL 연결을 위한 DATABASE_URL이 .env에 없음

## 향후 자동화 방법

### 옵션 1: DATABASE_URL 설정
`.env` 파일에 추가:
```env
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres
SUPABASE_DB_PASSWORD=your_database_password
```

### 옵션 2: Supabase CLI 사용
```bash
# Supabase CLI 설치
npm install -g supabase

# 로그인
supabase login

# 프로젝트 연결
supabase link --project-ref vecvkvumzhldioifgbxb

# 마이그레이션 적용
supabase db push
```

---

## 마이그레이션 파일 위치
`database/migrations/005_marketplace_seller_schema.sql`

