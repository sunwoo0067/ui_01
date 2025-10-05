# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Multi-AI Editor Development Environment

This project is designed for collaborative development across **4 AI editors**: Claude Code, Cursor, Windsurf, and Codex/Cline. All editors share common configuration and documentation to ensure consistency.

### Central Documentation

**Always reference these files in `.ai/` before making changes:**

- **`.ai/DEVELOPMENT.md`** - Main development guide and single source of truth
- **`.ai/ARCHITECTURE.md`** - Project architecture and design patterns
- **`.ai/CODING_RULES.md`** - Coding standards and naming conventions
- **`.ai/MCP_GUIDE.md`** - MCP (Model Context Protocol) configuration
- **`.ai/EDITOR_MCP_COMPATIBILITY.md`** - MCP compatibility across all editors

### Core Principles

1. **Consistency**: All AI editors follow the same standards defined in `.ai/DEVELOPMENT.md`
2. **Transparency**: Tag all commits with the editor name (e.g., `[Claude Code]`)
3. **Collaboration**: Changes to core documentation require team consensus

## Architecture

### Layered Architecture

- **Presentation Layer**: `src/components/`, `src/pages/` - UI components
- **Business Logic Layer**: `src/services/` - Business logic and services
- **Data Layer**: `src/api/`, `src/store/` - Data management and API communication
- **Utility Layer**: `src/utils/` - Shared utilities and helpers

### Design Patterns

- **Components**: Atomic Design pattern, reusable and composable
- **State Management**: Context API or state management library
- **Props**: Always use explicit TypeScript type definitions

### Data Flow

```
User Interaction → Event Handler → Service/API → Data Processing → State Update → UI Re-render
```

## Coding Standards

### Naming Conventions

- **Components**: `PascalCase.tsx` (e.g., `UserProfile.tsx`)
- **Functions/Variables**: `camelCase` (e.g., `getUserData`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`)
- **Types/Interfaces**: `PascalCase` (e.g., `User`, `UserData`)
- **Test files**: `*.test.ts` or `*.spec.ts`

### Code Style

- **Indentation**: 2 spaces (no tabs)
- **Strings**: Single quotes `'` or backticks `` ` `` (JSX attributes use double quotes `"`)
- **Semicolons**: Required
- **Line length**: Max 100 characters
- **TypeScript**: Strict type safety, avoid `any`

### Function Guidelines

- One function = one responsibility
- Max 50 lines per function (split if longer)
- Max 3 parameters (use objects for more)
- Always include JSDoc for complex logic

### Import Order

1. External libraries (React, etc.)
2. Internal modules (@/services, @/components)
3. Type definitions
4. Styles

## MCP (Model Context Protocol) Integration

### Available MCP Servers

This project uses MCP to connect with external tools and data:

- **filesystem**: Project file access
- **context7**: Up-to-date library/framework documentation (requires `CONTEXT7_API_KEY`)
- **supabase**: Database management and queries (OAuth-based, HTTP server)

### MCP Configuration

- **Project-wide**: `.mcp.json` (versioned, team-shared)
- **Environment variables**: `.env` (not versioned - use `.env.example` as template)
- **Local overrides**: `.mcp.local.json` (not versioned)

### Database (Supabase)

- All database operations use Supabase MCP server
- **Security**: Development projects only (never production)
- **Access**: Read-only mode recommended
- **Auth**: OAuth login required on first use

See `.ai/MCP_GUIDE.md` for detailed MCP setup instructions.

## Git Workflow

### Commit Message Format

```
<type>: <subject> [Claude Code]

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Example**:
```
feat: Add user authentication [Claude Code]

- Implement login/logout functionality
- Add JWT token management
- Create auth context provider

Closes #123
```

### Commit Requirements

- Always tag commits with `[Claude Code]`
- Include Co-Authored-By: `Claude <noreply@anthropic.com>`
- Include 🤖 Generated with [Claude Code](https://claude.com/claude-code)
- Update `.ai/DEVELOPMENT.md` for significant architectural changes

### Before Committing

1. Review staged changes with `git status` and `git diff`
2. Ensure tests pass (when test infrastructure exists)
3. Check for conflicts
4. Update relevant documentation

## Project Structure

```
ui_01/
├── .ai/                    # AI editor shared documentation (ALWAYS REFERENCE)
├── src/                    # Source code (planned structure)
│   ├── components/         # UI components
│   ├── pages/             # Application pages
│   ├── services/          # Business logic
│   ├── utils/             # Utilities
│   └── types/             # TypeScript types
├── tests/                 # Test files
├── .mcp.json              # MCP server configuration
├── .env                   # Environment variables (not versioned)
├── .cursorrules           # Cursor-specific rules
├── .windsurfrules         # Windsurf-specific rules
├── .clinerules            # Codex/Cline-specific rules
├── .editorconfig          # Common editor config
└── .prettierrc            # Code formatting rules
```

## Multi-Editor Compatibility

### Editor-Specific Rules Files

Each editor has its own rules file that references the central `.ai/` documentation:
- `.cursorrules` - Cursor AI
- `.windsurfrules` - Windsurf
- `.clinerules` - Codex/Cline

**Important**: These files should NOT be modified unless updating all editors' rules in sync.

### MCP Across Editors

All 4 editors fully support MCP. Configuration in `.mcp.json` works across:
- Claude Code (native support, CLI management)
- Cursor (UI + `.cursor/mcp.json`)
- Windsurf (`mcp-remote` module)
- Codex/Cline (auto-detects `.mcp.json`)

## Development Workflow

1. **Pull latest changes**: `git pull`
2. **Read documentation**: Review `.ai/DEVELOPMENT.md` and related docs
3. **Make changes**: Follow coding standards in `.ai/CODING_RULES.md`
4. **Write tests**: Test coverage 80%+ (when infrastructure exists)
5. **Update docs**: Modify `.ai/` files for architectural changes
6. **Commit**: Use proper format with `[Claude Code]` tag
7. **Push**: `git push` (check for conflicts first)

## Security

- **Never commit**: API keys, tokens, passwords, credentials
- **Use environment variables**: Store secrets in `.env` (already in `.gitignore`)
- **Supabase**: Development projects only, read-only mode recommended
- **Input validation**: Always validate user input
- **XSS prevention**: Sanitize all user-generated content

## When Updating Central Documentation

If making changes to `.ai/DEVELOPMENT.md` or other central docs:

1. Discuss with team (cross-editor impact)
2. Update the document
3. Add entry to "변경 이력" (Change History) section with date and `[Claude Code]` tag
4. Consider updating editor-specific rules if needed
5. Commit with descriptive message explaining the documentation change

## Key Reminders

- This is a **multi-editor collaborative environment** - maintain consistency
- **`.ai/DEVELOPMENT.md` is the single source of truth** - reference it first
- All editors use the **same MCP servers** configured in `.mcp.json`
- **Tag all commits** with `[Claude Code]` for transparency
- **TypeScript strict mode** - no `any` types without justification
- **Test coverage matters** - write tests for all new functionality
