# 코딩 규칙 (Coding Rules)

## 개요
이 문서는 모든 AI 에디터가 준수해야 할 코딩 표준을 정의합니다.

## 일반 원칙

### 1. 가독성 우선
- 명확하고 이해하기 쉬운 코드 작성
- 복잡한 로직에는 주석 추가
- 의미 있는 변수명 사용

### 2. DRY (Don't Repeat Yourself)
- 중복 코드 최소화
- 재사용 가능한 함수/컴포넌트 작성

### 3. KISS (Keep It Simple, Stupid)
- 과도한 추상화 지양
- 단순하고 직관적인 구조 선호

### 4. YAGNI (You Aren't Gonna Need It)
- 필요하지 않은 기능 미리 구현하지 않기
- 현재 요구사항에 집중

## 네이밍 규칙

### 파일명
- 컴포넌트: `PascalCase.tsx` (예: `UserProfile.tsx`)
- 유틸리티: `camelCase.ts` (예: `formatDate.ts`)
- 상수: `UPPER_SNAKE_CASE.ts` (예: `API_CONSTANTS.ts`)
- 테스트: `*.test.ts` 또는 `*.spec.ts`

### 변수/함수명
```typescript
// 변수: camelCase
const userName = "John";
const isActive = true;

// 상수: UPPER_SNAKE_CASE
const MAX_RETRY_COUNT = 3;
const API_BASE_URL = "https://api.example.com";

// 함수: camelCase, 동사로 시작
function getUserData() {}
function calculateTotal() {}
function isValidEmail() {}

// Boolean: is/has/should로 시작
const isLoading = false;
const hasPermission = true;
const shouldRedirect = false;
```

### 타입/인터페이스
```typescript
// Interface: PascalCase, I 접두사 없이
interface User {
  id: string;
  name: string;
}

// Type: PascalCase
type Status = "pending" | "active" | "inactive";

// Enum: PascalCase
enum UserRole {
  Admin = "ADMIN",
  User = "USER",
  Guest = "GUEST"
}
```

## 코드 스타일

### 들여쓰기
- 스페이스 2칸 사용
- 탭 문자 사용 금지

### 따옴표
- 문자열: 작은따옴표 (`'`) 또는 백틱 (`` ` ``) 사용
- JSX: 큰따옴표 (`"`) 사용

### 세미콜론
- 모든 구문 끝에 세미콜론 사용

### 줄 길이
- 최대 100자 권장
- 긴 줄은 적절히 분리

### 공백
```typescript
// 연산자 양쪽에 공백
const sum = a + b;

// 함수 인자 쉼표 뒤 공백
function example(a, b, c) {}

// 객체 리터럴
const obj = { key: 'value' };

// 배열
const arr = [1, 2, 3];
```

## 함수 작성 규칙

### 함수 크기
- 한 함수는 하나의 역할만 수행
- 최대 50줄 이내 권장
- 복잡한 함수는 여러 작은 함수로 분리

### 매개변수
- 최대 3개 권장
- 많은 매개변수는 객체로 전달
```typescript
// Bad
function createUser(name, email, age, address, phone) {}

// Good
function createUser(userData: UserData) {}
```

### 반환 값
- 명시적 타입 정의
- 일관된 반환 타입 유지

## 주석 규칙

### JSDoc 사용
```typescript
/**
 * 사용자 데이터를 가져옵니다
 * @param userId - 사용자 ID
 * @returns 사용자 정보 객체
 */
function getUserData(userId: string): User {}
```

### 인라인 주석
- 복잡한 로직 설명
- TODO, FIXME, NOTE 태그 활용
```typescript
// TODO: 에러 핸들링 추가 필요
// FIXME: 성능 최적화 필요
// NOTE: API 버전 2.0으로 업그레이드 예정
```

## 에러 처리

### Try-Catch
```typescript
async function fetchData() {
  try {
    const response = await api.get('/data');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch data:', error);
    throw new Error('Data fetch failed');
  }
}
```

### 에러 메시지
- 명확하고 구체적인 메시지
- 사용자 친화적 표현

## 테스트 코드

### 테스트 작성 필수
- 모든 함수/컴포넌트에 테스트 작성
- 테스트 커버리지 80% 이상 유지

### 테스트 구조
```typescript
describe('Component/Function Name', () => {
  it('should do something', () => {
    // Arrange
    // Act
    // Assert
  });
});
```

## Import/Export

### Import 순서
1. 외부 라이브러리
2. 내부 모듈
3. 타입 정의
4. 스타일

```typescript
// 외부 라이브러리
import React from 'react';
import { useState } from 'react';

// 내부 모듈
import { getUserData } from '@/services/user';
import { Button } from '@/components/Button';

// 타입
import type { User } from '@/types';

// 스타일
import './styles.css';
```

### Export
- Named export 선호
- Default export는 제한적으로 사용

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
- 타입 안정성 보장
- 에러 처리 포함
- 테스트 코드 함께 작성

## 업데이트 이력
- 2025-10-06: 초기 문서 생성 [Claude Code]
