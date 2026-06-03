#!/usr/bin/env python
"""Check whether the project is ready to publish to TestPyPI/PyPI.

Usage:
    uv run python scripts/check_release_ready.py

Runs local checks only. Makes no network requests and touches no tokens.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).parent.parent
DIST_DIR = ROOT / "dist"

_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"
_BOLD = "\033[1m"

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "RELEASE.md",
    "pyproject.toml",
]

REQUIRED_METADATA_FIELDS = [
    "name",
    "version",
    "description",
    "readme",
    "requires-python",
    "authors",
    "keywords",
    "classifiers",
    "dependencies",
]


# ---------------------------------------------------------------------------
# Helpers (importable for testing)
# ---------------------------------------------------------------------------


def load_pyproject(root: Path = ROOT) -> dict:
    with open(root / "pyproject.toml", "rb") as f:
        return tomllib.load(f)


def get_version(data: dict) -> str:
    return data.get("project", {}).get("version", "")


def check_required_files(root: Path = ROOT) -> list[str]:
    """Return list of missing required files."""
    return [f for f in REQUIRED_FILES if not (root / f).exists()]


def check_metadata_fields(data: dict) -> list[str]:
    """Return list of missing [project] metadata fields."""
    project = data.get("project", {})
    return [f for f in REQUIRED_METADATA_FIELDS if not project.get(f)]


def check_console_scripts(data: dict) -> list[str]:
    """Return list of error messages for [project.scripts]."""
    scripts = data.get("project", {}).get("scripts", {})
    errors = []
    if "suture" not in scripts:
        errors.append("[project.scripts] is missing 'suture' entry")
    elif scripts["suture"] != "suture.cli:main":
        errors.append(
            f"[project.scripts] suture = {scripts['suture']!r}, expected 'suture.cli:main'"
        )
    return errors


def check_changelog_version(version: str, root: Path = ROOT) -> bool:
    """Return True if CHANGELOG.md contains a section header for version."""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return False
    text = changelog.read_text(encoding="utf-8")
    # Matches: ## [0.1.0] or ## [0.1.0] - Unreleased or ## [0.1.0] - 2024-01-01
    pattern = re.compile(r"^##\s+\[" + re.escape(version) + r"\]", re.MULTILINE)
    return bool(pattern.search(text))


def check_dist_artifacts(version: str, dist_dir: Path = DIST_DIR) -> tuple[bool, str]:
    """Return (ok, message) for dist artifact check.

    Returns (True, warning) if dist/ doesn't exist.
    Returns (True, info) if artifacts match version.
    Returns (False, error) if stale artifacts are found.
    """
    if not dist_dir.exists():
        return True, "dist/ not found — run `uv build` before uploading"

    artifacts = list(dist_dir.iterdir())
    if not artifacts:
        return True, "dist/ is empty — run `uv build` before uploading"

    stale = []
    for f in artifacts:
        name = f.name
        if name.startswith("."):  # skip .gitignore and other dotfiles created by build tools
            continue
        # Accept suture-py-<version>.tar.gz and suture_py-<version>-py3-none-any.whl
        # pip normalises hyphens to underscores in wheel filenames
        if not ((name.startswith(f"suture_py-{version}") or name.startswith(f"suture-py-{version}")) and (name.endswith(".whl") or name.endswith(".tar.gz"))):
            stale.append(name)

    if stale:
        return False, f"dist/ contains stale or unexpected files: {', '.join(stale)}"

    return True, f"dist/ contains artifacts for version {version}"


def check_readme_safety(root: Path = ROOT) -> tuple[bool, str]:
    """Return (ok, message).

    Fails if README contains a bare 'pipx install suture' not preceded by
    a 'once published' / 'after publishing' guard within the same section.
    """
    readme = root / "README.md"
    if not readme.exists():
        return True, "README.md not found (caught by required files check)"

    text = readme.read_text(encoding="utf-8")
    lines = text.splitlines()

    guard_pattern = re.compile(r"once published|after publishing", re.IGNORECASE)
    install_pattern = re.compile(r"^\s*pipx install suture\s*$", re.IGNORECASE)

    # Scan lines: for each pipx install line, check that within the preceding
    # 10 lines there is a guard phrase.
    for i, line in enumerate(lines):
        if install_pattern.match(line):
            context = "\n".join(lines[max(0, i - 10) : i + 1])
            if not guard_pattern.search(context):
                return (
                    False,
                    "README contains 'pipx install suture' without a nearby "
                    "'Once published' or 'After publishing' guard",
                )

    return True, "README does not claim published availability"


# ---------------------------------------------------------------------------
# Report helpers
# ---------------------------------------------------------------------------


def _pass(label: str) -> None:
    print(f"  {_GREEN}✓{_RESET}  {label}")


def _fail(label: str) -> None:
    print(f"  {_RED}✗{_RESET}  {label}")


def _warn(label: str) -> None:
    print(f"  {_YELLOW}~{_RESET}  {label}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"\n{_BOLD}Suture Release Readiness{_RESET}\n")
    failures = 0

    # 1. Required files
    missing = check_required_files()
    if missing:
        for f in missing:
            _fail(f"Missing required file: {f}")
        failures += len(missing)
    else:
        _pass("Required files found")

    # 2. Load pyproject
    try:
        data = load_pyproject()
    except Exception as exc:
        _fail(f"Could not parse pyproject.toml: {exc}")
        print(f"\n{_RED}Cannot continue without valid pyproject.toml.{_RESET}\n")
        return 1

    version = get_version(data)
    if not version:
        _fail("Could not read version from pyproject.toml")
        failures += 1

    # 3. Metadata fields
    missing_fields = check_metadata_fields(data)
    if missing_fields:
        _fail(f"pyproject.toml [project] missing fields: {', '.join(missing_fields)}")
        failures += 1
    else:
        _pass("pyproject.toml metadata complete")

    # 4. Console scripts
    script_errors = check_console_scripts(data)
    if script_errors:
        for e in script_errors:
            _fail(e)
        failures += len(script_errors)
    else:
        _pass("Console script entry point valid")

    # 5. Changelog version
    if version:
        if check_changelog_version(version):
            _pass(f"CHANGELOG.md contains version {version}")
        else:
            _fail(
                f"CHANGELOG.md does not contain a section header for version {version} "
                f"(expected '## [{version}]' or '## [{version}] - ...')"
            )
            failures += 1

    # 6. Dist artifacts
    if version:
        ok, msg = check_dist_artifacts(version)
        if ok:
            if "not found" in msg or "empty" in msg:
                _warn(msg)
            else:
                _pass(msg)
        else:
            _fail(msg)
            failures += 1

    # 7. README safety
    ok, msg = check_readme_safety()
    if ok:
        _pass(msg)
    else:
        _fail(msg)
        failures += 1

    # 8. Token guidance (informational only)
    print(f"\n  {_YELLOW}Note:{_RESET} Use API tokens from TestPyPI/PyPI. Never commit tokens.")

    print()
    if failures:
        print(f"{_RED}Release readiness check failed ({failures} issue(s)).{_RESET}\n")
        return 1

    print(f"{_GREEN}Release readiness checks passed.{_RESET}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
