#!/usr/bin/env python
"""Full local release preflight for Suture.

Runs every pre-publish check in the correct order and stops on the first
failure. Does not upload anything to TestPyPI or PyPI.

Usage:
    uv run python scripts/preflight.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DIST_DIR = ROOT / "dist"

_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"


def _header(text: str) -> None:
    print(f"\n{_BOLD}{text}{_RESET}")


def _step(label: str) -> None:
    print(f"\n{_DIM}▶  {label}{_RESET}")


def _ok(label: str) -> None:
    print(f"  {_GREEN}✓{_RESET}  {label}")


def _fail(label: str) -> None:
    print(f"  {_RED}✗{_RESET}  {label}")


def _warn(label: str) -> None:
    print(f"  {_YELLOW}~{_RESET}  {label}")


def _run(cmd: list[str], label: str) -> None:
    """Run cmd, print label. Exit with the command's status on failure."""
    _step(" ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        _fail(f"{label} failed (exit {result.returncode})")
        sys.exit(result.returncode)
    _ok(label)


def _clean_dist() -> None:
    _step("rm -rf dist/  (Python shutil.rmtree)")
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    _ok("dist/ removed")


def _check_twine_available() -> bool:
    result = subprocess.run(
        ["uv", "run", "twine", "--version"],
        capture_output=True,
        cwd=ROOT,
    )
    return result.returncode == 0


def _twine_check() -> None:
    _step("uv run twine check dist/*")
    if not _check_twine_available():
        _warn(
            "twine not found in project venv.\n"
            "       Install it: uv run python -m pip install --upgrade twine\n"
            "       Or add twine to [project.optional-dependencies] dev in pyproject.toml"
        )
        sys.exit(1)

    dist_files = [str(p) for p in DIST_DIR.glob("*") if not p.name.startswith(".")]
    if not dist_files:
        _fail("No dist artifacts found — uv build should have created them")
        sys.exit(1)

    result = subprocess.run(["uv", "run", "twine", "check"] + dist_files, cwd=ROOT)
    if result.returncode != 0:
        _fail("twine check failed")
        sys.exit(result.returncode)
    _ok("twine check passed")


def main() -> None:
    _header("Suture Preflight")
    print("Runs all local release checks. Does not upload anything.\n")

    _run(["uv", "run", "pytest"], "pytest")
    _run(["uv", "run", "ruff", "check", "src/", "tests/", "scripts/"], "ruff")
    _run(["uv", "run", "python", "scripts/validate_examples.py"], "validate examples")
    _clean_dist()
    _run(["uv", "build"], "uv build")
    _run(["uv", "run", "python", "scripts/verify_package.py"], "verify package")
    _run(["uv", "run", "python", "scripts/check_release_ready.py"], "check release ready")
    _twine_check()

    print(f"\n{_GREEN}{_BOLD}Suture preflight passed.{_RESET}")
    print(f"{_GREEN}Ready for TestPyPI upload.{_RESET}\n")


if __name__ == "__main__":
    main()
