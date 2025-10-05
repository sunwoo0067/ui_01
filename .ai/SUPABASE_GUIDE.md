# Supabase 사용 가이드

## 개요
이 문서는 드롭쉬핑 대량등록 자동화 프로그램에서 Supabase를 사용하는 방법을 설명합니다.

## Supabase 프로젝트 설정

### 1. 프로젝트 생성
1. [Supabase Dashboard](https://supabase.com/dashboard)에서 새 프로젝트 생성
2. **Organization** 선택
3. **Project Name** 입력 (예: `dropshipping-automation`)
4. **Database Password** 설정 (안전하게 보관)
5. **Region** 선택 (Korea 또는 가장 가까운 리전)
6. **Free Plan** 선택 (또는 Pro)

### 2. API 키 확보
**Settings** → **API**에서 다음 키 복사:
- `Project URL`: https://your-project.supabase.co
- `anon public`: 클라이언트용 (RLS 적용)
- `service_role`: 서버용 (RLS 우회, 절대 노출 금지)

### 3. 환경 변수 설정
`.env` 파일 생성:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key
```

## 데이터베이스 스키마 설정

### 1. SQL 마이그레이션 실행
Supabase Dashboard → **SQL Editor**에서 실행:

```sql
-- database/migrations/001_initial_schema.sql 파일 내용 복사/붙여넣기
```

또는 Supabase CLI 사용:
```bash
supabase db push
```

### 2. pgvector 확장 활성화
**Database** → **Extensions** → `vector` 검색 → **Enable**

### 3. Storage 버킷 생성
**Storage** → **New Bucket**:
- **Name**: `product-images`
- **Public**: Yes (또는 RLS 정책으로 제어)

### 4. Storage RLS 정책 설정
SQL Editor에서 실행:

```sql
-- 인증된 사용자만 이미지 업로드 가능
CREATE POLICY "Authenticated users can upload images"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'product-images');

-- 모든 사용자가 이미지 조회 가능 (Public bucket)
CREATE POLICY "Public images are viewable"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'product-images');

-- 판매자는 자신의 이미지만 삭제 가능
CREATE POLICY "Sellers can delete own images"
ON storage.objects FOR DELETE
TO authenticated
USING (
  bucket_id = 'product-images' AND
  (storage.foldername(name))[1] IN (
    SELECT id::text FROM sellers WHERE auth.uid()::text = id::text
  )
);
```

## Python SDK 사용법

### 1. 클라이언트 초기화

#### 동기 클라이언트
```python
from src.services import supabase_client

# 테이블 조회
products = supabase_client.get_table('products').select('*').execute()

# Storage 접근
storage = supabase_client.get_storage()
```

#### 비동기 클라이언트
```python
from src.services import AsyncSupabaseClient

async def main():
    async with AsyncSupabaseClient() as client:
        # 배치 삽입
        result = await client.batch_insert(
            table_name='products',
            data=product_list,
            chunk_size=500
        )
```

### 2. 배치 업로드

```python
from uuid import uuid4
from src.services import BatchUploadService
from src.models import ProductCreate

# 판매자 ID
seller_id = uuid4()

# 업로더 초기화
uploader = BatchUploadService(seller_id)

# CSV에서 상품 로드
products = uploader.load_from_csv('products.csv')

# 배치 업로드 (비동기)
result = await uploader.upload_batch(products, batch_name='2025-10-06 배치')

# 결과
print(f"성공: {result['success']}/{result['total']}")
```

### 3. 이미지 업로드

```python
from uuid import uuid4
from src.services import ImageProcessor

processor = ImageProcessor()

# 상품 이미지 업로드
images = await processor.upload_product_images(
    product_id=uuid4(),
    image_paths=[
        '/path/to/image1.jpg',
        '/path/to/image2.jpg'
    ]
)

# 업로드된 URL
for img in images:
    print(f"Public URL: {img['public_url']}")
```

### 4. Realtime 구독

```python
from uuid import uuid4
from src.services import RealtimeProgressMonitor

batch_id = uuid4()

def on_progress(payload):
    """진행 상황 콜백"""
    data = payload['new']
    print(f"진행률: {data['progress']}%")
    print(f"성공: {data['success_count']}")
    print(f"실패: {data['failed_count']}")

# 구독 시작
monitor = RealtimeProgressMonitor(batch_id)
monitor.subscribe(on_progress)

# 작업 수행...

# 구독 해제
monitor.unsubscribe()
```

## Supabase 기능 활용

### 1. Row Level Security (RLS)

#### RLS 정책 확인
```sql
-- 현재 정책 조회
SELECT * FROM pg_policies WHERE tablename = 'products';
```

#### Service Key로 RLS 우회
```python
# Service Key 사용 (RLS 우회)
products = supabase_client.get_table('products', use_service_key=True).select('*').execute()

# 주의: Service Key는 서버에서만 사용!
```

### 2. pgvector 시맨틱 검색

#### 임베딩 생성 (OpenAI)
```python
import openai
from src.config import settings

openai.api_key = settings.OPENAI_API_KEY

def generate_embedding(text: str) -> list[float]:
    """텍스트 임베딩 생성"""
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

# 상품 설명 임베딩
description = "고급 가죽 백팩, 노트북 수납 가능"
embedding = generate_embedding(description)
```

#### 유사 상품 검색
```python
# 임베딩 기반 유사 상품 찾기
response = supabase_client.client.rpc(
    'find_similar_products',
    {
        'query_embedding': embedding,
        'match_threshold': 0.8,
        'match_count': 10
    }
).execute()

similar_products = response.data
for product in similar_products:
    print(f"{product['title']} (유사도: {product['similarity']:.2%})")
```

### 3. Database Functions

#### 대량 삽입 (PostgreSQL COPY)
```python
# CSV 기반 대량 삽입 (초고속)
csv_data = """
seller_id,title,description,price,stock_quantity
uuid1,상품1,설명1,10000,100
uuid2,상품2,설명2,20000,200
"""

response = supabase_client.client.rpc(
    'bulk_insert_products',
    {'csv_data': csv_data}
).execute()

print(f"삽입된 레코드 수: {response.data}")
```

### 4. Storage API

#### 이미지 업로드
```python
storage = supabase_client.get_storage()

# 파일 업로드
with open('image.jpg', 'rb') as f:
    response = storage.from_('product-images').upload(
        path='products/uuid/image.jpg',
        file=f,
        file_options={'content-type': 'image/jpeg'}
    )

# Public URL 생성
url = storage.from_('product-images').get_public_url('products/uuid/image.jpg')
```

#### Signed URL (임시 접근)
```python
# 1시간 동안 유효한 임시 URL
signed_url = storage.from_('product-images').create_signed_url(
    path='products/uuid/image.jpg',
    expires_in=3600  # seconds
)
```

### 5. Realtime Subscriptions

#### PostgreSQL Changes 구독
```python
# 테이블 변경사항 실시간 구독
channel = supabase_client.get_realtime().channel('products-changes')

channel.on(
    'postgres_changes',
    event='INSERT',
    schema='public',
    table='products',
    callback=lambda payload: print(f"새 상품: {payload['new']['title']}")
).subscribe()
```

## 무료 플랜 제약 및 최적화

### 무료 플랜 제한 (2025)
- **데이터베이스**: 500MB
- **Storage**: 1GB
- **대역폭**: 월 5GB
- **Realtime**: 동시 연결 200개
- **Edge Functions**: 500,000 호출/월
- **백업**: 없음 (수동 백업 필요)

### 최적화 전략

#### 1. 데이터베이스 용량 절감
```python
# 이미지는 Storage에, URL만 DB에
# ❌ Bad: 이미지 바이너리를 DB에 저장
# ✅ Good: Storage URL을 JSONB로 저장

product = {
    'images': [
        {'url': 'https://...', 'is_primary': True},
        {'url': 'https://...', 'is_primary': False}
    ]
}
```

#### 2. 대역폭 절감
```python
# 이미지 최적화로 전송량 감소
processor = ImageProcessor()

# 원본: 5MB → 최적화: 500KB (90% 절감)
optimized = processor.optimize_image(
    'image.jpg',
    max_width=1200,
    quality=85
)
```

#### 3. Realtime 연결 관리
```python
# 필요한 경우에만 구독
with RealtimeProgressMonitor(batch_id) as monitor:
    monitor.subscribe(callback)
    # 작업 수행
    # 컨텍스트 종료 시 자동 unsubscribe
```

#### 4. 수동 백업
```bash
# pg_dump로 백업 (Supabase CLI)
supabase db dump -f backup.sql

# 복원
supabase db reset
psql -h db.your-project.supabase.co -U postgres -d postgres -f backup.sql
```

## 트러블슈팅

### 1. RLS 정책 위반
**증상**: "new row violates row-level security policy"

**해결**:
- Service Key 사용 (`use_service_key=True`)
- RLS 정책 확인 (`SELECT * FROM pg_policies`)
- `auth.uid()`가 올바른지 확인

### 2. Storage 업로드 실패
**증상**: "Permission denied"

**해결**:
- Storage RLS 정책 확인
- 버킷이 존재하는지 확인
- Public/Private 설정 확인

### 3. Realtime 구독 안됨
**증상**: 이벤트가 수신되지 않음

**해결**:
- 테이블에 Realtime 활성화 확인
- Channel 이름 중복 확인
- 네트워크 방화벽 확인 (WebSocket 포트)

### 4. pgvector 인덱스 느림
**증상**: 유사도 검색이 느림

**해결**:
```sql
-- IVFFlat 인덱스 튜닝
CREATE INDEX idx_products_embedding
ON products USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- lists 값 조정 (데이터 크기에 따라)

-- 인덱스 통계 업데이트
ANALYZE products;
```

### 5. Connection Timeout
**증상**: "Connection timeout"

**해결**:
- Supabase 프로젝트 상태 확인
- Connection Pooling 설정 (Supavisor)
- 동시 연결 수 제한 확인

## 모니터링

### Supabase Dashboard
- **Database** → **Table Editor**: 데이터 확인
- **Database** → **Query Performance**: 느린 쿼리 분석
- **Logs** → **Postgres Logs**: DB 에러 로그
- **Storage** → **Usage**: Storage 용량 확인
- **Reports** → **API**: API 호출 통계

### Python 로깅
```python
from loguru import logger

# Supabase 응답 로깅
logger.info(f"Uploaded {len(products)} products")
logger.error(f"Failed to upload: {error}")
```

## 보안 체크리스트

- [ ] Service Key는 환경 변수로만 관리
- [ ] RLS 정책이 모든 테이블에 활성화
- [ ] Storage는 Private 또는 RLS 정책 설정
- [ ] API 키가 Git에 커밋되지 않음
- [ ] 프로덕션과 개발 프로젝트 분리
- [ ] 주기적 백업 (pg_dump)
- [ ] 이미지 업로드 시 파일 타입 검증
- [ ] SQL Injection 방지 (Parameterized queries)

## 업그레이드 가이드 (Free → Pro)

### Pro 플랜 이점
- **데이터베이스**: 8GB (확장 가능)
- **Storage**: 100GB
- **대역폭**: 월 250GB
- **Realtime**: 동시 연결 500개
- **백업**: 7일 PITR (Point-in-Time Recovery)
- **성능**: 더 빠른 CPU/메모리

### 마이그레이션 체크리스트
1. 무료 플랜 프로젝트 백업 (`pg_dump`)
2. Pro 플랜 프로젝트 생성
3. 백업 복원
4. 환경 변수 업데이트 (새 API 키)
5. RLS 정책 재설정
6. Storage 버킷 재생성
7. 애플리케이션 테스트
8. DNS/도메인 변경 (필요 시)

## 참고 자료
- [Supabase 공식 문서](https://supabase.com/docs)
- [Python SDK 문서](https://supabase.com/docs/reference/python/introduction)
- [pgvector 가이드](https://supabase.com/docs/guides/database/extensions/pgvector)
- [Storage API](https://supabase.com/docs/guides/storage)
- [Realtime](https://supabase.com/docs/guides/realtime)

## 업데이트 이력
- 2025-10-06: 초기 Supabase 가이드 생성 [Claude Code]
