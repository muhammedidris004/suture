# Suture

**Suture is a Python project setup doctor.**

It diagnoses the boring setup mistakes that stop Python projects from running:
broken imports, unsafe `.env` handling, bad `pyproject.toml` entries, missing
pytest path config, and broken CLI script entry points.

Suture is not a linter, formatter, type checker, or security scanner. It
focuses on setup failures — the problems that usually show up as
`ModuleNotFoundError`, broken test discovery, missing environment variables, or
confusing packaging errors.

---

## Why Suture exists

Python projects often fail for reasons that are not code-quality problems:

- pytest cannot find a `src/` package
- `.env` exists but is not ignored by git
- code uses env vars that are not documented in `.env.example`
- `pyproject.toml` defines a CLI command that points to missing code
- both `requirements.txt` and `pyproject.toml` exist with unclear ownership

Suture checks those setup-level problems and explains them with severity and
confidence levels.

---

## Project status

Suture is currently alpha software. Issue codes and output format may change
before 1.0.

**Current focus:**
- Python setup diagnostics
- Safe, explainable issue reports
- JSON output for AI assistants and CI tools
- Conservative auto-fixes only

**Not yet supported:**
- Full framework-specific checks
- Dependency vulnerability scanning
- Circular import graph analysis
- Docker / CI runtime debugging
- Source-code rewriting

---

## Quick demo

```bash
uv run suture doctor examples/broken-projects/src-layout-no-pytest-path
```

Actual output:

```text
╭──────────────────────────────╮
│ Suture Project Health Report │
╰──────────────────────────────╯

Score: 85/100

Possible Issues:
  ! IMP001  src layout may not be configured for pytest
       This project uses src/ layout, but [tool.pytest.ini_options] pythonpath
       does not include "src".
       If tests fail with ModuleNotFoundError, add pythonpath = ["src"] under
       [tool.pytest.ini_options] in pyproject.toml, or install the package
       using pip install -e .

Passed:
  ✓ pyproject.toml found
  ✓ [project] name and version present
  ✓ [tool.pytest.ini_options] present
  ✓ src layout detected

Not checked:
  - Docker config
  - CI environment
  - runtime errors
  - async test setup
  - circular imports
  - dynamic imports
  - framework-specific settings
```

---

## Try locally

```bash
git clone <your-repo-url>
cd suture
uv sync --extra dev
uv run suture doctor
uv run suture doctor examples/broken-projects/missing-env-gitignore
```

---

## Install

Once published:

```bash
pipx install suture
suture doctor
```

> Suture is not yet published to PyPI. Use the local setup above.

---

## Commands

All commands accept an optional `PATH` argument. When omitted, the current
working directory is used.

`doctor`, `imports`, and `pyproject` require a project directory. `env` also
accepts a single `.py` file.

### Full health report

```bash
suture doctor                       # scan current directory
suture doctor /path/to/project      # scan a specific project
```

### Environment variables

```bash
suture env                          # scan current directory
suture env /path/to/project         # scan a specific project
suture env path/to/file.py          # scan a single Python file
```

Scans Python files for `os.getenv`, `os.environ["X"]`, and
`os.environ.get("X")`. Compares against `.env`, `.env.example`, and
`.gitignore`.

### Import layout

```bash
suture imports                      # scan current directory
suture imports /path/to/project     # scan a specific project
```

Detects `src/` vs flat layout, checks pytest `pythonpath` config, looks for
missing `__init__.py` files.

### pyproject.toml

```bash
suture pyproject                    # scan current directory
suture pyproject /path/to/project   # scan a specific project
```

Parses and validates `pyproject.toml`: metadata, pytest config, script entry
points, dual-file conflicts.

### Apply fixes

```bash
suture apply --dry-run        # show what would change, touch nothing
suture apply --safe           # apply only safe auto-fixes
suture apply --interactive    # ask before each fix
```

---

## JSON output

Suture can output clean JSON for AI assistants, CI tools, and editor
integrations:

```bash
suture doctor --json
suture doctor /path/to/project --json
```

Example:

```json
{
  "project_root": "/path/to/project",
  "layout": "src",
  "python_version": "3.12.0",
  "package_manager": "uv",
  "score": 72,
  "issues": [
    {
      "code": "IMP001",
      "title": "src layout may not be configured for pytest",
      "severity": "high",
      "confidence": "medium",
      "reason": "This project uses src/ layout, but pythonpath does not include \"src\".",
      "suggestion": "Add pythonpath = [\"src\"] under [tool.pytest.ini_options].",
      "fix_id": "add-pytest-pythonpath"
    }
  ],
  "passed": ["pyproject.toml found"],
  "skipped": [],
  "not_checked": [
    "Docker config",
    "CI environment",
    "runtime errors"
  ]
}
```

Paste the output directly into an AI assistant conversation to get targeted
advice. The `not_checked` field tells the assistant what Suture cannot see.

```bash
suture doctor --json | pbcopy   # macOS
suture doctor --json | xclip    # Linux
```

---

## What Suture checks

| Area | Checks |
|---|---|
| **pyproject.toml** | File exists, valid TOML, `[project]` has name and version, pytest config present, script entry points resolve on disk, no dual `requirements.txt` conflict |
| **Import layout** | `src/` vs flat layout detected, pytest `pythonpath` configured, `__init__.py` present, relative imports inside package context |
| **Environment variables** | `.env` in `.gitignore`, `.env.example` exists, all statically-referenced env vars documented, `.env` vars not silently undocumented |

## What Suture does NOT check

- Docker config
- CI environment
- Runtime errors
- Async test setup
- Circular imports
- Dynamic imports (`importlib`, `__import__`)
- Framework-specific settings (Django `INSTALLED_APPS`, FastAPI lifespan, etc.)
- Type correctness
- Code style or formatting

Suture always shows a "Not checked" section so you know its limits.

---

## Safety model

Suture is intentionally conservative.

It separates:
- **Confirmed issues** — high-confidence findings
- **Possible issues** — lower-confidence findings worth reviewing
- **Passed checks** — things that look correct
- **Skipped / not checked** — things Suture cannot assess

Each issue includes severity, confidence, reason, and suggestion. Suture will
never automatically delete files, remove dependencies, rewrite imports, move
packages, or modify source code.

The only safe auto-fixes (`suture apply --safe`) are additive and reversible:

- Adding `.env` to `.gitignore`
- Creating or updating `.env.example`
- Adding `pythonpath = ["src"]` to `pyproject.toml`

Everything else requires `--interactive` mode, which asks before each change.

---

## Confidence levels

Every issue has a confidence level: `high`, `medium`, or `low`.

Suture uses these because static analysis cannot always be certain:

- A `src/` layout without `pythonpath = ["src"]` in pytest config **might**
  cause test failures — but the package could also be installed with
  `pip install -e .`. Suture flags it as `HIGH` severity, `MEDIUM` confidence.
- A variable in `.env` that Suture couldn't find in Python code **might** be
  unused — or used dynamically or by a framework. `LOW` severity, `MEDIUM`
  confidence.

Confirmed issues (high confidence) appear under **Confirmed Issues**. Lower-
confidence findings appear under **Possible Issues**. Suture never mixes them.

---

## Score

Suture computes a 0–100 score based on issues found:

| Severity | Deduction |
|---|---|
| CRITICAL | −25 |
| HIGH | −15 |
| MEDIUM | −8 |
| LOW | −3 |
| INFO | 0 |

Score is displayed in green (≥80), yellow (≥50), or red (<50). A score below
50 exits with code 1, which is useful in CI.

---

## Development validation examples

Suture includes intentionally broken sample projects under `examples/broken-projects/`.

| Project | Expected issue |
|---|---|
| `missing-env-gitignore` | ENV001 |
| `src-layout-no-pytest-path` | IMP001 |
| `broken-script-entrypoint` | PRJ003 |
| `malformed-pyproject` | PRJ000 |
| `missing-env-example` | ENV004 |
| `mixed-requirements-pyproject` | PRJ005 |

```bash
uv run python scripts/validate_examples.py
```

These act as regression fixtures — if a check stops firing, the script catches
it before a release does.

---

## Package verification

Before publishing, build the wheel and run all pre-publish verification:

```bash
uv build
uv run python scripts/verify_package.py
uv run python scripts/check_release_ready.py
```

- `scripts/verify_package.py` — installs the wheel into a clean venv and runs
  each CLI command against the broken-project examples. Catches packaging
  mistakes that only appear after installation.
- `scripts/check_release_ready.py` — checks required files, pyproject metadata
  completeness, changelog version match, and dist artifact names.

For maintainers, run the full preflight in one command:

```bash
uv run python scripts/preflight.py
```

This runs all of the above in sequence and stops on the first failure. It does
not upload anything.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

For the first public release workflow, see [docs/first-release.md](docs/first-release.md).

## License

MIT — see [LICENSE](LICENSE).
