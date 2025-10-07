# Cursor Rules Documentation

This directory contains Cursor-specific rules (`.mdc` files) that help AI assistants understand and work with this codebase effectively.

## 📋 Available Rules

### Always Applied Rules
These rules are automatically shown to AI assistants on every request:

1. **quick-start.mdc** - Essential quick reference guide
2. **project-architecture.mdc** - Core architecture and data flow
3. **common-pitfalls.mdc** - Critical issues to avoid

### Context-Specific Rules
These rules are shown when working with specific file types or manually invoked:

4. **supplier-connectors.mdc** - Supplier API connector development
   - Applied to: `src/services/connectors/**`, `*_data_collector.py`

5. **database-operations.mdc** - Database operations and Supabase MCP
   - Applied to: `database_service.py`, `*_service.py`, `database/**`

6. **python-coding-standards.mdc** - Python code style and conventions
   - Applied to: `*.py`, `src/**/*.py`

7. **testing-pattern.mdc** - Testing conventions and patterns
   - Applied to: `test_*.py`, `tests/**`

8. **data-pipeline.mdc** - Data collection and processing pipeline
   - Applied to: `product_pipeline.py`, `*_data_collector.py`

9. **git-workflow.mdc** - Git workflow and commit conventions
   - Manually invoked when needed

## 🎯 How Rules Work

### Automatic Application
Rules with `alwaysApply: true` are shown on every request.

### Glob Pattern Matching
Rules with `globs:` are shown when working with matching files:
```yaml
---
globs: *.py,src/**/*.py
---
```

### Manual Invocation
Rules with `description:` can be manually invoked by the user or suggested by the AI when relevant.

## 📚 Rule Priority

1. **Start Here**: `quick-start.mdc`
2. **Architecture**: `project-architecture.mdc`
3. **Avoid Mistakes**: `common-pitfalls.mdc`
4. **Task-Specific**: Choose based on what you're working on

## ✏️ Editing Rules

### Rule Format
```markdown
---
alwaysApply: true|false
description: "Optional description"
globs: "*.ext,dir/**"
---
# Rule Title

Rule content in Markdown format...
```

### File References
Link to project files using:
```markdown
[filename.ext](mdc:path/to/filename.ext)
```

### Best Practices
- Keep rules focused and concise
- Include practical examples
- Reference actual project files
- Update rules when architecture changes
- Test rules by checking if AI assistants follow them

## 🔄 Maintenance

### When to Update Rules
- After major architectural changes
- When new patterns emerge
- After resolving repeated issues
- When adding new systems/modules

### How to Update
1. Edit the relevant `.mdc` file
2. Test with AI assistant
3. Commit with descriptive message
4. Update this README if adding new rules

## 📖 Additional Documentation

For comprehensive project documentation, always refer to:
- `.ai/DEVELOPMENT.md` - Main development guide
- `.ai/PLAN.md` - Project roadmap
- `.ai/ARCHITECTURE.md` - System architecture
- `.ai/CODING_RULES.md` - Detailed coding standards

## 🤝 Multi-Editor Support

These Cursor rules complement editor-specific rule files:
- `.cursorrules` - Cursor AI
- `.windsurfrules` - Windsurf
- `.clinerules` - Codex/Cline
- `CLAUDE.md` - Claude Code

All editors share the central `.ai/` documentation as the single source of truth.

