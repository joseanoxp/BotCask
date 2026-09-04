# BotCask Copilot Instructions

## Project context

BotCask is an intentionally minimal, early-stage Python prototype for building
bots from declarative YAML command files. Optimize for validating the core idea
and preserving a small, understandable codebase. Do not introduce framework
complexity, integrations, plugins, caching, or broad automatic discovery
without a concrete requirement.

## Contribution workflow

- Follow the GitHub Flow contract in `CONTRIBUTING.md`.
- Work from a descriptive English branch based on `main`.
- Keep changes focused and use Draft Pull Requests for work in progress.
- Before creating or editing a pull request, read
  `.github/pull_request_template.md`, complete each section, and preserve its
  headings and order exactly, including when supplying the body through the
  CLI or API.
- Prefer squash merging so `main` stays linear.
- For squash commits, use a concise conventional subject and put
  `Refs #<pull-request-number>` in the commit body.
- When no reviewer is available, perform a careful self-review of the diff.
- Never rewrite shared history or use destructive git commands.
- Use Issues as the source of truth for planned work and keep them focused.
- Link related Issues and PRs, use simple labels, and group related work in a
  Milestone when it contributes to one concrete project goal.
- Break larger work into smaller Issues with explicit acceptance criteria and
  dependencies instead of creating broad, ambiguous tasks.

## Implementation expectations

- Use test-first development for behavior changes when practical.
- Preserve the existing public API unless the task explicitly changes it.
- Reuse `execute_command()` for command loading, validation, and rendering.
- Keep command names constrained to the configured commands directory; do not
  reintroduce path traversal through command resolution.
- Surface invalid input and runtime errors clearly. Do not silently swallow
  failures or add broad exception handlers.
- Make surgical changes and avoid unrelated refactors.
- Keep Python code typed and compatible with the version declared in
  `pyproject.toml`.

## Validation

The test suite is the primary quality gate while the project is still building
its foundation:

```bash
uv run pytest -q
```

When available or enabled for the repository, also run and honor these checks:

```bash
uv run ruff check .
uv run ruff format --check .
```

Ruff and future CI or branch-protection checks are intentionally documented as
optional for now. If they become enabled as required repository checks, treat
their results as merge requirements.
