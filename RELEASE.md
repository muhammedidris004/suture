# Release Checklist

> For the first public release workflow (GitHub push → TestPyPI → PyPI decision),
> see [docs/first-release.md](docs/first-release.md).

---

## One-command preflight

Run:

```bash
uv run python scripts/preflight.py
```

This performs, in order:

- `uv run pytest`
- `uv run ruff check src/ tests/ scripts/`
- `uv run python scripts/validate_examples.py`
- clean rebuild of `dist/` via `uv build`
- installed-wheel verification via `scripts/verify_package.py`
- release metadata checks via `scripts/check_release_ready.py`
- `uv run twine check dist/*`

If this passes, the project is ready for TestPyPI upload.

> **Preflight does not upload anything. Publishing to TestPyPI/PyPI is always manual.**

---

## Pre-release

- [ ] Confirm package name availability on PyPI.
- [ ] Bump version in `pyproject.toml` and `src/suture/__init__.py`.
- [ ] Update `CHANGELOG.md` — replace `[Unreleased]` with the version and date.
- [ ] Run `uv run pytest`.
- [ ] Run `uv run ruff check src/ tests/ scripts/`.
- [ ] Run `uv run python scripts/validate_examples.py`.
- [ ] Build and verify the package locally (see below).
- [ ] Run `uvx twine check dist/*`.
- [ ] Upload to TestPyPI first:
      `uvx twine upload --repository testpypi dist/*`
- [ ] Install from TestPyPI in a clean environment:
      `pip install --index-url https://test.pypi.org/simple/ suture`
- [ ] Test `suture doctor` from the TestPyPI install.
- [ ] Publish to PyPI only after TestPyPI install works:
      `uvx twine upload dist/*`

---

## Local package verification and release readiness

Build the wheel and run all pre-publish verification steps in order:

```bash
rm -rf dist/
uv run pytest
uv run ruff check src/ tests/ scripts/
uv run python scripts/validate_examples.py
uv build
uv run python scripts/verify_package.py
uv run python scripts/check_release_ready.py
uv run python -m pip install --upgrade twine
uv run twine check dist/*
```

- `scripts/verify_package.py` installs the wheel into a clean venv under
  `.tmp/suture-install-test` and runs each CLI command against the example
  projects.
- `scripts/check_release_ready.py` checks that all required files exist,
  pyproject metadata is complete, the changelog contains the current version,
  and dist artifacts match.

**macOS/Linux** — the venv is created under `.tmp/` inside the project root.

**Windows** — the same `.tmp/` path is used; the script uses `Scripts/` instead
of `bin/` automatically. Alternatively, manually create a venv:

```
python -m venv .venv-install-test
.venv-install-test\Scripts\pip install dist\suture-0.1.0-py3-none-any.whl
.venv-install-test\Scripts\suture doctor --json
```

---

## TestPyPI publishing

After all local verification passes:

```bash
uv run twine upload --repository testpypi dist/*
```

Then verify the TestPyPI install in a clean environment:

```bash
python -m venv .tmp/testpypi-install
.tmp/testpypi-install/bin/python -m pip install --upgrade pip
.tmp/testpypi-install/bin/python -m pip install \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple \
    suture
.tmp/testpypi-install/bin/suture doctor --json
```

**Windows:**

```
python -m venv .tmp\testpypi-install
.tmp\testpypi-install\Scripts\python -m pip install --upgrade pip
.tmp\testpypi-install\Scripts\python -m pip install ^
    --index-url https://test.pypi.org/simple/ ^
    --extra-index-url https://pypi.org/simple ^
    suture
.tmp\testpypi-install\Scripts\suture doctor --json
```

> Do not upload to real PyPI until TestPyPI install verification succeeds.

## Post-release

- [ ] Create a GitHub release tag matching the version (e.g. `v0.1.0`).
- [ ] Add release notes to the GitHub release (copy from `CHANGELOG.md`).
- [ ] Share with early users.
