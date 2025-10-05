# 드롭쉬핑 대량등록 자동화 프로그램

Supabase 기반 드롭쉬핑 상품 대량등록 자동화 시스템

## 프로젝트 개요

- **개발 환경**: Python 3.12.10
- **데이터베이스**: Supabase (PostgreSQL + pgvector)
- **주요 기능**:
  - 대량 상품 배치 업로드
  - 이미지 자동 처리 및 최적화
  - 실시간 진행 상황 모니터링
  - 시맨틱 검색 기반 중복 상품 감지

## 설치 및 설정

### 1. Python 환경 설정

```bash
# Python 3.12.10 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일 수정:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
```

### 3. Supabase 데이터베이스 설정

```bash
# 마이그레이션 실행
python -m src.utils.migrate
```

## 프로젝트 구조

```
ui_01/
├── src/
│   ├── config/          # 설정 파일
│   ├── models/          # 데이터 모델 (Pydantic)
│   ├── services/        # 비즈니스 로직
│   │   ├── supabase_client.py
│   │   ├── batch_upload.py
│   │   └── image_processor.py
│   └── utils/           # 유틸리티 함수
├── tests/               # 테스트 코드
├── database/            # SQL 마이그레이션
│   └── migrations/
├── .ai/                 # AI 에디터 공유 문서
├── requirements.txt     # Python 의존성
└── .env                 # 환경 변수 (Git 제외)
```

## 사용 방법

### 대량 상품 업로드

```python
from src.services.batch_upload import BatchUploader

# 업로더 초기화
uploader = BatchUploader()

# CSV에서 상품 로드
products = uploader.load_from_csv('products.csv')

# 대량 업로드 (비동기)
await uploader.upload_batch(products)
```

### 이미지 처리

```python
from src.services.image_processor import ImageProcessor

processor = ImageProcessor()

# 이미지 최적화 및 업로드
image_urls = await processor.upload_images(
    product_id='uuid',
    images=['path/to/image1.jpg', 'path/to/image2.jpg']
)
```

## 주요 기능

### 1. 배치 업로드 최적화
- 500~1,000개씩 청크 처리
- 비동기 병렬 업로드
- PostgreSQL COPY 명령 지원 (초대량)

### 2. Realtime 모니터링
- WebSocket 기반 진행 상황 추적
- 에러 발생 시 즉시 알림
- 대시보드 실시간 업데이트

### 3. 시맨틱 검색 (pgvector)
- 상품 설명 임베딩 저장
- 유사 상품 자동 매칭
- 중복 상품 감지

### 4. 이미지 자동 처리
- Storage API 통합
- 자동 리사이징/최적화
- CDN을 통한 빠른 전송

## 개발 가이드

### AI 에디터 사용

이 프로젝트는 멀티 AI 에디터 환경을 지원합니다:
- **Claude Code**, **Cursor**, **Windsurf**, **Codex/Cline**

작업 전 반드시 읽어주세요:
- [.ai/DEVELOPMENT.md](.ai/DEVELOPMENT.md) - 개발 가이드
- [.ai/ARCHITECTURE.md](.ai/ARCHITECTURE.md) - 아키텍처
- [.ai/CODING_RULES.md](.ai/CODING_RULES.md) - 코딩 규칙
- [.ai/SUPABASE_GUIDE.md](.ai/SUPABASE_GUIDE.md) - Supabase 가이드

### 테스트 실행

```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=src tests/

# 특정 테스트
pytest tests/test_batch_upload.py
```

### 코드 품질

```bash
# 포맷팅
black src/ tests/

# Linting
flake8 src/ tests/

# 타입 체크
mypy src/
```

## Supabase 기능 활용

### 사용 중인 Supabase 기능
- ✅ PostgreSQL Database
- ✅ Storage API (이미지 저장)
- ✅ Realtime (WebSocket 구독)
- ✅ Row Level Security (RLS)
- ✅ pgvector (벡터 검색)
- ✅ Database Functions & Triggers

### 무료 플랜 제약
- 데이터베이스: 500MB
- 스토리지: 1GB
- 대역폭: 월 5GB
- 백업: 미지원 (수동 백업 필요)

## 라이선스

MIT License

## 기여

Pull Request를 환영합니다. 커밋 시 `[AI Editor Name]` 태그를 포함해주세요.

## 문의

프로젝트 관련 문의는 이슈를 등록해주세요.
