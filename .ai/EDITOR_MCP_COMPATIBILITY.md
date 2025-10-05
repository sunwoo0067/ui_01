# 멀티 에디터 MCP 호환성 검토

## 개요
4개 AI 에디터(Claude Code, Cursor, Windsurf, Codex/Cline)의 MCP(Model Context Protocol) 지원 현황을 검토합니다.

## MCP 지원 현황 (2025)

### ✅ Claude Code
- **MCP 지원**: 완전 지원
- **개발사**: Anthropic (MCP 프로토콜 개발사)
- **설정 방식**:
  - CLI: `claude mcp add`
  - 파일: `.mcp.json` (프로젝트), User/Local scope
- **특징**:
  - MCP 프로토콜의 네이티브 지원
  - stdio, HTTP, SSE 전송 방식 모두 지원
  - Claude Desktop과 MCP 서버 공유 가능 (macOS/WSL)

### ✅ Cursor
- **MCP 지원**: 완전 지원
- **설정 방식**:
  - UI 설정 또는 `.cursor/mcp.json` 파일
- **특징**:
  - 여러 MCP 서버 동시 설정 가능
  - 외부 도구 체이닝 지원
  - HTTP/SSE 서버 지원

### ✅ Windsurf (Codeium)
- **MCP 지원**: 완전 지원
- **설정 방식**:
  - `mcp-remote` 모듈 사용
  - `.windsurfrules` + MCP 설정
- **특징**:
  - Flow/Cascade 모드에서 MCP 활용
  - 원격 MCP 서버 연결 가능

### ✅ Codex / Cline
- **MCP 지원**: 완전 지원
- **특징**:
  - 2025년 4월 기준 MCP 통합이 강점
  - 도구 사용 및 컨텍스트 인식에서 우수
  - `.clinerules` + MCP 설정

## 현재 프로젝트 MCP 서버

### 1. Filesystem (모든 에디터 호환)
```json
{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "${workspaceFolder}"],
    "description": "File system access for the project"
  }
}
```
- **호환성**: ✅ 모든 에디터
- **용도**: 프로젝트 파일 접근

### 2. Context7 (모든 에디터 호환)
```json
{
  "context7": {
    "command": "npx",
    "args": ["-y", "@upstash/context7-mcp", "--api-key", "${CONTEXT7_API_KEY}"],
    "env": { "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}" },
    "description": "Up-to-date documentation for libraries and frameworks"
  }
}
```
- **호환성**: ✅ 모든 에디터
- **용도**: 최신 라이브러리/프레임워크 문서
- **API 키**: 필요 (https://context7.com/dashboard)

### 3. Supabase (대부분 에디터 호환)
```json
{
  "supabase": {
    "type": "http",
    "url": "https://mcp.supabase.com/mcp",
    "description": "Supabase database management and queries"
  }
}
```
- **호환성**: ✅ Claude Code, Cursor, Windsurf (HTTP 지원 에디터)
- **용도**: Supabase 데이터베이스 관리 및 쿼리
- **인증**: OAuth (최초 설정 시 브라우저 로그인)
- **보안**:
  - 개발 프로젝트용 권장 (프로덕션 X)
  - read-only 모드 권장
  - 특정 프로젝트로 스코프 제한 가능

## 에디터별 설정 방법

### Claude Code
```bash
# 자동으로 .mcp.json 인식
# 또는 CLI 사용
claude mcp add context7 npx -y @upstash/context7-mcp --api-key YOUR_KEY
```

### Cursor
1. Settings → Features → MCP
2. 또는 `.cursor/mcp.json` 생성
```json
{
  "mcpServers": {
    "supabase": {
      "type": "http",
      "url": "https://mcp.supabase.com/mcp"
    }
  }
}
```

### Windsurf
```bash
# mcp-remote 모듈 사용
npm install -g mcp-remote
```
프로젝트 `.mcp.json` 파일 공유

### Codex/Cline
- 프로젝트 `.mcp.json` 자동 인식
- 환경 변수 `.env` 파일 사용

## MCP 서버 공유 전략

### 1. 프로젝트 공유 (`.mcp.json`)
- **목적**: 팀 전체가 사용하는 공통 MCP 서버
- **Git**: ✅ 버전 관리 포함
- **예시**: filesystem, context7, supabase

### 2. 개인 설정 (User scope)
- **목적**: 개인별 MCP 도구
- **Git**: ❌ 제외
- **예시**: 개인 API, 로컬 데이터베이스

### 3. 로컬 임시 (`.mcp.local.json`)
- **목적**: 실험적 MCP 서버
- **Git**: ❌ 제외

## 호환성 매트릭스

| MCP 서버 | Claude Code | Cursor | Windsurf | Codex/Cline |
|----------|-------------|--------|----------|-------------|
| Filesystem | ✅ | ✅ | ✅ | ✅ |
| Context7 | ✅ | ✅ | ✅ | ✅ |
| Supabase (HTTP) | ✅ | ✅ | ✅ | ⚠️* |
| GitHub | ✅ | ✅ | ✅ | ✅ |
| PostgreSQL | ✅ | ✅ | ✅ | ✅ |
| Notion | ✅ | ✅ | ✅ | ✅ |

*일부 에디터는 HTTP MCP 서버 지원 여부 확인 필요

## 권장사항

### 1. 표준 MCP 서버 사용
- stdio 방식 (npx): 모든 에디터 호환성 최고
- HTTP/SSE: 대부분의 에디터 지원

### 2. 환경 변수 관리
- `.env` 파일 사용 (Git 제외)
- `.env.example` 제공 (팀 공유)

### 3. 보안
- API 키는 환경 변수로만 관리
- Supabase는 개발 프로젝트로 제한
- read-only 모드 활성화

### 4. 문서화
- 각 MCP 서버의 용도 명시
- 설정 방법 문서화
- 팀원 온보딩 가이드 제공

## 결론

✅ **모든 4개 에디터가 MCP를 완전히 지원합니다**

- **Claude Code**: MCP 네이티브 지원 (개발사)
- **Cursor**: UI + 파일 설정 지원
- **Windsurf**: mcp-remote로 원격 서버 지원
- **Codex/Cline**: 강력한 MCP 통합

현재 프로젝트의 `.mcp.json` 설정은 모든 에디터에서 사용 가능하며,
환경 변수만 각 에디터에서 올바르게 설정하면 동일한 MCP 서버에 접근할 수 있습니다.

## 업데이트 이력
- 2025-10-06: 초기 문서 생성 [Claude Code]
