# 코딩 규칙 (Coding Rules)

## 개요
이 문서는 모든 AI 에디터가 준수해야 할 Python 코딩 표준을 정의합니다.

## 일반 원칙

### 1. 가독성 우선
- 명확하고 이해하기 쉬운 코드 작성
- 복잡한 로직에는 주석 추가
- 의미 있는 변수명 사용
- PEP 8 스타일 가이드 준수

### 2. DRY (Don't Repeat Yourself)
- 중복 코드 최소화
- 재사용 가능한 함수/클래스 작성
- 공통 로직은 유틸리티 함수로 분리

### 3. KISS (Keep It Simple, Stupid)
- 과도한 추상화 지양
- 단순하고 직관적인 구조 선호
- 명시적이 암시적보다 낫다

### 4. YAGNI (You Aren't Gonna Need It)
- 필요하지 않은 기능 미리 구현하지 않기
- 현재 요구사항에 집중

## 네이밍 규칙

### 파일명
- 모듈: `snake_case.py` (예: `user_service.py`)
- 패키지: `snake_case/` (예: `services/`)
- 테스트: `test_*.py` 또는 `*_test.py`
- 설정: `snake_case.py` (예: `settings.py`)

### 변수/함수명
```python
# 변수: snake_case
user_name = "John"
is_active = True

# 상수: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
API_BASE_URL = "https://api.example.com"

# 함수: snake_case, 동사로 시작
def get_user_data():
    pass

def calculate_total():
    pass

def is_valid_email():
    pass

# Boolean: is/has/should로 시작
is_loading = False
has_permission = True
should_redirect = False

# Private: _underscore prefix
def _internal_helper():
    pass
```

### 클래스/타입명
```python
# 클래스: PascalCase
class UserService:
    pass

class ProductPipeline:
    pass

# 타입 힌트: PascalCase
from typing import List, Dict, Optional
from pydantic import BaseModel

class User(BaseModel):
    id: str
    name: str

# Enum: PascalCase
from enum import Enum

class UserRole(Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    GUEST = "GUEST"
```

## 코드 스타일

### 들여쓰기
- 스페이스 4칸 사용 (PEP 8 표준)
- 탭 문자 사용 금지

### 따옴표
- 문자열: 작은따옴표 (`'`) 또는 큰따옴표 (`"`) 일관성 있게 사용
- f-string 사용 권장: `f"Hello {name}"`

### 줄 길이
- 최대 88자 권장 (Black 포맷터 기준)
- 긴 줄은 적절히 분리

### 공백
```python
# 연산자 양쪽에 공백
sum = a + b

# 함수 인자 쉼표 뒤 공백
def example(a, b, c):
    pass

# 딕셔너리 리터럴
obj = {'key': 'value'}

# 리스트
arr = [1, 2, 3]

# 함수 호출 시 공백 없음
result = function(arg1, arg2)
```

## 함수 작성 규칙

### 함수 크기
- 한 함수는 하나의 역할만 수행
- 최대 50줄 이내 권장
- 복잡한 함수는 여러 작은 함수로 분리

### 매개변수
- 최대 5개 권장
- 많은 매개변수는 딕셔너리나 Pydantic 모델로 전달
```python
# Bad
def create_user(name, email, age, address, phone, role):
    pass

# Good
def create_user(user_data: UserCreate):
    pass

# 또는
def create_user(name: str, email: str, **kwargs):
    pass
```

### 반환 값
- 명시적 타입 힌트 정의
- 일관된 반환 타입 유지
- Optional 사용 시 None 처리 명확히

### 비동기 함수
- 비동기 작업 시 `async def` 명시적 사용
- `await` 키워드 올바른 사용
```python
async def fetch_data() -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

## 주석 규칙

### Docstring 사용
```python
def get_user_data(user_id: str) -> Optional[Dict[str, Any]]:
    """
    사용자 데이터를 가져옵니다.
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        사용자 정보 딕셔너리 또는 None
        
    Raises:
        ValueError: 잘못된 user_id인 경우
    """
    pass

class UserService:
    """사용자 관련 서비스 클래스"""
    
    def __init__(self, db_client):
        """
        UserService 초기화
        
        Args:
            db_client: 데이터베이스 클라이언트
        """
        self.db_client = db_client
```

### 인라인 주석
- 복잡한 로직 설명
- TODO, FIXME, NOTE 태그 활용
```python
# TODO: 에러 핸들링 추가 필요
# FIXME: 성능 최적화 필요
# NOTE: API 버전 2.0으로 업그레이드 예정

# 복잡한 알고리즘 설명
# 이진 탐색을 사용하여 O(log n) 시간 복잡도 달성
def binary_search(arr: List[int], target: int) -> int:
    pass
```

## 에러 처리

### Try-Except 사용
```python
async def fetch_data() -> Dict[str, Any]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as e:
        logger.error(f"HTTP 클라이언트 오류: {e}")
        raise
    except Exception as e:
        logger.error(f"데이터 가져오기 실패: {e}")
        raise ValueError("데이터를 가져올 수 없습니다")
```

### 커스텀 예외 클래스
```python
class APIError(Exception):
    """API 관련 오류"""
    pass

class ValidationError(Exception):
    """데이터 검증 오류"""
    pass

class DatabaseError(Exception):
    """데이터베이스 오류"""
    pass
```

### 에러 메시지
- 명확하고 구체적인 메시지
- 사용자 친화적 표현
- 로깅과 사용자 메시지 분리

## 테스트 코드

### 테스트 작성 필수
- 모든 public 메서드에 테스트 작성
- 테스트 커버리지 80% 이상 유지
- pytest 사용 권장

### 테스트 구조
```python
import pytest
from unittest.mock import Mock, patch
from src.services.user_service import UserService

class TestUserService:
    """UserService 테스트 클래스"""
    
    def setup_method(self):
        """각 테스트 전 실행"""
        self.mock_db = Mock()
        self.user_service = UserService(self.mock_db)
    
    def test_get_user_success(self):
        """사용자 조회 성공 테스트"""
        # Arrange
        user_id = "test-user-123"
        expected_user = {"id": user_id, "name": "Test User"}
        self.mock_db.get_user.return_value = expected_user
        
        # Act
        result = self.user_service.get_user(user_id)
        
        # Assert
        assert result == expected_user
        self.mock_db.get_user.assert_called_once_with(user_id)
    
    def test_get_user_not_found(self):
        """사용자 조회 실패 테스트"""
        # Arrange
        user_id = "non-existent-user"
        self.mock_db.get_user.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="사용자를 찾을 수 없습니다"):
            self.user_service.get_user(user_id)
    
    @pytest.mark.asyncio
    async def test_create_user_async(self):
        """비동기 사용자 생성 테스트"""
        # Arrange
        user_data = {"name": "New User", "email": "new@example.com"}
        expected_id = "new-user-123"
        self.mock_db.create_user.return_value = expected_id
        
        # Act
        result = await self.user_service.create_user_async(user_data)
        
        # Assert
        assert result == expected_id
```

## Import 규칙

### Import 순서
1. 표준 라이브러리
2. 서드파티 라이브러리
3. 로컬 애플리케이션 모듈
4. 타입 정의 (typing)

```python
# 표준 라이브러리
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

# 서드파티 라이브러리
import aiohttp
import pandas as pd
from loguru import logger
from pydantic import BaseModel

# 로컬 모듈
from src.config import settings
from src.services.supabase_client import supabase_client
from src.models.product import Product
```

### Import 스타일
- 절대 import 사용 권장
- 상대 import는 같은 패키지 내에서만 사용
- `from module import *` 사용 금지
- 필요한 것만 import

### 타입 힌트
```python
from typing import List, Dict, Optional, Union, Any
from uuid import UUID

def process_products(
    products: List[Dict[str, Any]], 
    user_id: Optional[UUID] = None
) -> Dict[str, Union[int, List[str]]]:
    pass
```

## Git 커밋 메시지

### 형식
```
<type>: <subject> [AI Editor]

<body>

<footer>
```

### Type
- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅
- `refactor`: 리팩토링
- `test`: 테스트 추가
- `chore`: 기타 변경사항

### 예시
```
feat: Add user authentication [Cursor]

- Implement login/logout functionality
- Add JWT token management
- Create auth context provider

Closes #123
```

## AI 에디터별 주의사항

### 모든 에디터 공통
- 이 문서의 규칙을 엄격히 준수
- 불확실한 경우 DEVELOPMENT.md 참조
- 변경 전 기존 코드 스타일 확인

### 코드 생성 시
- 타입 안정성 보장 (타입 힌트 필수)
- 에러 처리 포함
- 테스트 코드 함께 작성
- 비동기 함수는 `async def` 명시

### Python 특화 규칙
- PEP 8 스타일 가이드 준수
- Black 포맷터 사용 권장
- Pydantic 모델 활용
- Loguru 로깅 사용

## 업데이트 이력
- 2025-10-06: 초기 문서 생성 [Claude Code]
- 2025-10-06: Python 중심으로 전면 수정 [Cursor]
