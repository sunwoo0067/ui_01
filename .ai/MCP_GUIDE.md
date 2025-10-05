# MCP (Model Context Protocol) 설정 가이드

## 개요
MCP는 AI 어시스턴트를 외부 도구, 데이터베이스, API와 연결하는 오픈소스 표준 프로토콜입니다.

## MCP 설정 스코프

### 1. Project Scope (`.mcp.json`)
- **위치**: 프로젝트 루트 디렉토리
- **용도**: 팀 전체가 공유하는 MCP 서버
- **Git**: 버전 관리에 포함
- **예시**: 프로젝트 데이터베이스, 공통 API, 파일시스템

### 2. User Scope
- **위치**: 사용자 홈 디렉토리
- **용도**: 개인적으로 사용하는 MCP 서버
- **Git**: 버전 관리에서 제외
- **예시**: 개인 도구, 로컬 데이터베이스

### 3. Local Scope
- **위치**: 프로젝트 디렉토리 (`.mcp.local.json`)
- **용도**: 임시 또는 실험적 MCP 서버
- **Git**: 버전 관리에서 제외

## 현재 프로젝트 설정

### 프로젝트 공유 MCP (`.mcp.json`)

```json
{
  "$schema": "https://schema.claudeapis.com/mcp-schema.json",
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "${workspaceFolder}"
      ],
      "description": "File system access for the project"
    }
  }
}
```

## MCP 서버 추가 방법

### 1. Claude Desktop에서 가져오기 (macOS/WSL)
```bash
claude mcp add-from-claude-desktop
```

**참고**: Windows에서는 지원되지 않습니다. 수동으로 설정하세요.

### 2. Stdio 서버 추가
```bash
# Project scope
claude mcp add <server-name> <command> [args...]

# User scope
claude mcp add --scope user <server-name> <command> [args...]

# Local scope
claude mcp add --scope local <server-name> <command> [args...]
```

**예시**:
```bash
# GitHub 이슈 트래커
claude mcp add github npx -y @modelcontextprotocol/server-github

# PostgreSQL 데이터베이스
claude mcp add postgres npx -y @modelcontextprotocol/server-postgres postgresql://localhost/mydb

# SQLite 데이터베이스
claude mcp add sqlite npx -y @modelcontextprotocol/server-sqlite --db-path ./data.db
```

### 3. HTTP/SSE 서버 추가
```bash
# SSE (Server-Sent Events)
claude mcp add --transport sse <server-name> <url>

# HTTP
claude mcp add --transport http <server-name> <url>
```

### 4. `.mcp.json` 직접 편집

```json
{
  "$schema": "https://schema.claudeapis.com/mcp-schema.json",
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      },
      "description": "GitHub repository integration"
    },
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://localhost/mydb"
      ],
      "description": "PostgreSQL database access"
    },
    "notion": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-notion"],
      "env": {
        "NOTION_API_KEY": "${NOTION_API_KEY}"
      },
      "description": "Notion workspace integration"
    }
  }
}
```

## 환경 변수 설정

### `.env` 파일 생성
```bash
# .env (Git에 포함하지 말 것!)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
NOTION_API_KEY=secret_xxxxxxxxxxxx
DATABASE_URL=postgresql://user:pass@localhost/db
```

### `.mcp.json`에서 환경 변수 참조
```json
{
  "mcpServers": {
    "github": {
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

## MCP 서버 관리 명령어

### 서버 목록 확인
```bash
claude mcp list
```

### 서버 상세 정보
```bash
claude mcp get <server-name>
```

### 서버 제거
```bash
claude mcp remove <server-name>
```

### 서버 테스트
```bash
# MCP 서버가 제대로 작동하는지 확인
# Claude Code에서 AI에게 물어보세요:
# "Can you list the available MCP tools?"
```

## 인기 MCP 서버

### 개발 도구
- **GitHub**: 이슈, PR, 리포지토리 관리
- **GitLab**: GitLab 리포지토리 통합
- **Linear**: 이슈 트래킹
- **Jira/Confluence**: Atlassian 도구 연동

### 데이터베이스
- **PostgreSQL**: PostgreSQL 쿼리
- **SQLite**: SQLite 데이터베이스
- **MongoDB**: MongoDB 쿼리

### 생산성 도구
- **Notion**: Notion 워크스페이스
- **Slack**: Slack 메시지 및 채널
- **Google Drive**: 파일 접근
- **Sentry**: 에러 모니터링

### 파일 시스템
- **Filesystem**: 로컬 파일 접근
- **Box**: Box 클라우드 스토리지

## 멀티 에디터 환경에서의 MCP

### Claude Code
- `.mcp.json` 자동 인식
- CLI 명령어로 관리
- @ 멘션으로 MCP 리소스 참조

### Claude Desktop
- GUI 설정 인터페이스
- macOS/WSL에서 Claude Code로 서버 내보내기 가능

### Cursor, Windsurf
- 각 에디터의 MCP 지원 여부 확인 필요
- `.mcp.json` 파일 공유 가능 (호환성에 따라)

## 보안 주의사항

### 절대 Git에 포함하지 말 것
- API 키, 토큰
- 데이터베이스 비밀번호
- 개인 인증 정보

### `.gitignore`에 추가
```
.env
.env.local
.mcp.local.json
**/secrets.json
```

### 환경 변수 사용
- 민감한 정보는 항상 환경 변수로 관리
- `.env.example` 파일로 필요한 환경 변수 명시

## 트러블슈팅

### MCP 서버가 작동하지 않을 때
1. `claude mcp list`로 서버 목록 확인
2. `claude mcp get <server-name>`로 설정 확인
3. 환경 변수가 올바르게 설정되었는지 확인
4. 필요한 npm 패키지가 설치되었는지 확인
5. Claude Code 재시작

### 토큰 제한 경고
- MCP 도구 출력이 10,000 토큰을 초과하면 경고 표시
- `MAX_MCP_OUTPUT_TOKENS` 환경 변수로 조정 (최대 25,000)

## 추가 리소스
- [MCP 공식 문서](https://modelcontextprotocol.io/)
- [Claude Code MCP 가이드](https://docs.claude.com/en/docs/claude-code/mcp)
- [MCP 서버 목록](https://github.com/modelcontextprotocol/servers)

## 업데이트 이력
- 2025-10-06: 초기 MCP 가이드 생성 [Claude Code]
