# Contributing to BotCask

BotCask is intentionally a small, early-stage prototype. Contributions should
validate the core idea before adding framework complexity.

## GitHub Flow

1. Start from an up-to-date `main` branch.
2. Create a short, descriptive branch in English:
   - `feature/<description>` for new behavior
   - `fix/<description>` for bug fixes
   - `chore/<description>` for tooling or maintenance
3. Keep the change focused and open a Draft Pull Request early when the work
   is still in progress.
4. Use the pull request to describe the goal, behavior, validation steps, and
   known limitations.
5. Before merging, run the relevant tests locally. Automated checks are
   recommended when enabled, but they are optional while the project is
   establishing its foundation.
6. Mark the pull request ready when the change is complete.
7. Merge with **Squash and merge** to keep `main` linear and readable.
8. Use a concise conventional commit subject for the squash commit and add
   `Refs #<pull-request-number>` in its body.
9. Delete the feature branch after merging.

There may be no separate reviewer while the project is small. In that case,
the author should perform a self-review of the diff and confirm that the
relevant tests pass.

## Development workflow

Use `uv` for the Python environment and project commands:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

The test suite is the primary quality gate at this stage. Ruff checks and
future CI or branch-protection checks should be treated as required when the
repository enables them, but they are not a reason to add process before it
helps validate the product.

Prefer test-first development for behavior changes:

1. Add a focused test that describes the desired behavior.
2. Implement the smallest change that makes it pass.
3. Refactor only when the behavior is protected by tests.

Keep public APIs small and reuse existing runtime paths instead of duplicating
command loading, validation, or rendering logic. Avoid adding integrations,
plugins, caching, or automatic discovery of unrelated files until the core
convention has been validated.
