# Contributing to Suture

Thank you for your interest in contributing. This document explains how to get
started, run the tests, and follow the project's conventions.

---

## Setup

Suture uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
git clone <repository-url>
cd suture
uv sync --extra dev
```

Verify the install:

```bash
uv run suture doctor
```

---

## Running tests

```bash
uv run pytest
```

Tests use `tmp_path` fixtures only — no real filesystem dependencies.

---

## Linting

```bash
uv run ruff check src/ tests/ scripts/
```

Fix auto-fixable issues:

```bash
uv run ruff check --fix src/ tests/ scripts/
```

---

## Running the validation examples

```bash
uv run python scripts/validate_examples.py
```

This runs Suture against each broken example project in `examples/broken-projects/`
and confirms the expected issue codes appear.

---

## Adding a new check

1. Decide which module owns the check: `checks/env.py`, `checks/imports.py`,
   `checks/pyproject.py`, or a new file if the check is unrelated.

2. Assign an issue code using the appropriate prefix:

   | Prefix | Area |
   |---|---|
   | `ENV` | Environment variables, `.env` files |
   | `IMP` | Import layout, package structure |
   | `PRJ` | `pyproject.toml` structure and metadata |

   New areas may introduce new prefixes. Keep them short (3 letters) and
   descriptive. Document the new prefix in this table.

3. Add the `Issue` to the `CheckResult` returned by the check function.
   Follow the existing pattern: code, title, severity, confidence, reason,
   suggestion, fix_id (or None).

4. Write a test in `tests/` using `tmp_path`. Do not test against the real
   filesystem.

5. If the check can be demonstrated with a minimal broken project, add an
   example under `examples/broken-projects/` and register it in
   `scripts/validate_examples.py`.

---

## Safety principle

Suture must never add an auto-fix that:

- deletes files
- removes dependencies
- moves or renames files
- modifies source code
- rewrites imports

Auto-fixes must be additive and reversible. When in doubt, leave it as a
suggestion only and set `fix_id = None`.

---

## Pull requests

- Keep PRs focused. One concern per PR.
- All tests must pass.
- Ruff must be clean.
- Update `CHANGELOG.md` under the `[Unreleased]` section.
