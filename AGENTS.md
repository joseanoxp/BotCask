# BotCask

BotCask is a small Python framework for building bots from declarative YAML command files rendered with Jinja2 and validated with Pydantic.

## Tooling & Feedback Loops

- **Package & environment manager**: `uv` (Python >= 3.14)
- **Run tests**: `uv run pytest`
- **Run linter / formatter check**: `uv run ruff check` and `uv run ruff format --check`

## Agent skills

### Issue tracker

Issues, specs, and wayfinder maps are tracked in GitHub Issues (`joseanoxp/BotCask`) via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Canonical five-label vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout (`GLOSSARY.md` at repo root and ADRs in `docs/adr/`). See `docs/agents/domain.md`.

### Antigravity harness mapping

When executing skills from `.agents/skills/`:
- **"Call the Skill tool with `<name>`"** or user invocation of `/<name>`: read `.agents/skills/<name>/SKILL.md` with `view_file` and follow its workflow.
- **Subagent dispatch** (`research`, `code-review`, `implement-spec`, `grilling` fact-finding): use `invoke_subagent` (`TypeName: "research"` for read-only exploration; `TypeName: "self"` with `Workspace: "share"` when worktree isolation is required).
