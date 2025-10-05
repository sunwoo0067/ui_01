# 개발 문서 (Development Guide)

## 프로젝트 개요
이 문서는 Claude Code, Codex, Cursor, Windsurf 등 여러 AI 에디터를 사용한 멀티 에디터 개발 환경의 중앙 참조 문서입니다.

## 프로젝트 정보
- **프로젝트명**: ui_01
- **시작일**: 2025-10-06
- **개발 환경**: Multi-AI Editor (Claude Code, Codex, Cursor, Windsurf)

## 핵심 원칙

### 1. 일관성 (Consistency)
- 모든 AI 에디터는 이 문서를 참조하여 동일한 컨텍스트로 작업합니다
- 코드 스타일, 네이밍 규칙, 아키텍처 패턴을 엄격히 준수합니다
- 변경사항은 반드시 이 문서에 반영합니다

### 2. 투명성 (Transparency)
- 각 AI 에디터가 수행한 작업은 커밋 메시지에 명시합니다
- 중요한 의사결정은 문서화합니다

### 3. 협업 (Collaboration)
- 에디터 간 충돌을 최소화하기 위해 명확한 역할 분담을 권장합니다
- Git을 통한 버전 관리로 모든 변경사항을 추적합니다

## 기술 스택
- 상세한 기술 스택은 [TECH_STACK.md](.ai/TECH_STACK.md) 참조

## 아키텍처
- 상세한 아키텍처는 [ARCHITECTURE.md](.ai/ARCHITECTURE.md) 참조

## 코딩 규칙
- 상세한 코딩 규칙은 [CODING_RULES.md](.ai/CODING_RULES.md) 참조

## MCP (Model Context Protocol) 통합
- MCP를 통해 외부 도구, 데이터베이스, API와 연동 가능
- 상세한 MCP 설정 가이드는 [MCP_GUIDE.md](.ai/MCP_GUIDE.md) 참조
- 프로젝트 공유 MCP 설정: `.mcp.json`
- Claude Desktop과 MCP 서버 공유 가능

### MCP 주요 기능
- 파일 시스템 접근
- 데이터베이스 쿼리 (PostgreSQL, SQLite 등)
- 이슈 트래커 연동 (GitHub, Jira, Linear 등)
- 외부 API 통합 (Notion, Slack 등)

## AI 에디터 사용 가이드

### 작업 시작 전
1. 최신 코드를 pull 받습니다
2. 이 문서와 관련 참조 문서를 확인합니다
3. 작업 범위를 명확히 정의합니다

### 작업 중
1. 코딩 규칙을 준수합니다
2. 테스트를 작성합니다
3. 문서를 업데이트합니다

### 작업 완료 후
1. 코드 리뷰를 수행합니다
2. 커밋 메시지에 사용한 AI 에디터를 명시합니다
   - 예: `feat: Add user authentication [Cursor]`
   - 예: `fix: Resolve login bug [Claude Code]`
3. 푸시 전 충돌을 확인합니다

## 문서 업데이트 규칙
- 이 문서는 프로젝트의 단일 진실 공급원(Single Source of Truth)입니다
- 중요한 결정사항은 반드시 이 문서에 기록합니다
- 문서 수정 시 날짜와 수정자(에디터)를 명시합니다

## 변경 이력
- 2025-10-06: 초기 문서 생성 [Claude Code]
- 2025-10-06: MCP (Model Context Protocol) 통합 가이드 추가 [Claude Code]
