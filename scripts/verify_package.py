#!/usr/bin/env python
"""Verify the built wheel installs and works correctly in a clean environment.

Usage:
    uv build
    uv run python scripts/verify_package.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DIST_DIR = ROOT / "dist"
VENV_DIR = ROOT / ".tmp" / "suture-install-test"
EXAMPLES_DIR = ROOT / "examples" / "broken-projects"

_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _find_wheel() -> Path | None:
    wheels = sorted(DIST_DIR.glob("*.whl"))
    return wheels[-1] if wheels else None


def _venv_bin(name: str) -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / name
    return VENV_DIR / "bin" / name


def _run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
    )


def _step(label: str, ok: bool, detail: str = "") -> None:
    icon = f"{_GREEN}✓{_RESET}" if ok else f"{_RED}✗{_RESET}"
    suffix = f"  {detail}" if detail else ""
    print(f"  {icon}  {label}{suffix}")


def main() -> int:
    print(f"\n{_BOLD}Suture Package Verification{_RESET}\n")
    failures: list[str] = []

    # 1. Find wheel
    wheel = _find_wheel()
    if wheel is None:
        print(
            f"{_RED}No wheel found in dist/.{_RESET}\n"
            f"{_YELLOW}Run `uv build` first.{_RESET}\n"
        )
        return 1
    print(f"  Wheel: {wheel.name}")
    print(f"  Venv:  {VENV_DIR}\n")

    # 2. Remove old venv
    if VENV_DIR.exists():
        shutil.rmtree(VENV_DIR)

    # 3. Create fresh venv
    result = _run([sys.executable, "-m", "venv", str(VENV_DIR)])
    ok = result.returncode == 0
    _step("Create clean virtual environment", ok)
    if not ok:
        print(f"\n{_RED}Could not create virtual environment. Aborting.{_RESET}\n")
        return 1

    python = str(_venv_bin("python"))

    # 4. Install wheel (pip is already present in venv)
    result = _run([python, "-m", "pip", "install", "--quiet", str(wheel)])
    ok = result.returncode == 0
    _step(f"Install {wheel.name}", ok)
    if not ok:
        failures.append("wheel install")

    suture = str(_venv_bin("suture"))

    # 5. smoke: suture doctor --json
    label = "suture doctor --json"
    result = _run([suture, "doctor", str(ROOT), "--json"], capture=True)
    if result.returncode not in (0, 1):  # exit 1 is allowed for low score
        ok = False
        _step(label, False, "non-zero exit")
        failures.append(label)
    else:
        try:
            data = json.loads(result.stdout)
            assert "score" in data and "issues" in data
            _step(label, True, f"score={data['score']}")
        except (json.JSONDecodeError, AssertionError) as exc:
            _step(label, False, f"invalid JSON — {exc}")
            failures.append(label)

    # 6. suture env on a broken example
    label = "suture env missing-env-gitignore"
    result = _run(
        [suture, "env", str(EXAMPLES_DIR / "missing-env-gitignore")],
        capture=True,
    )
    ok = result.returncode == 0 and "ENV001" in result.stdout
    _step(label, ok, "ENV001 detected" if ok else f"stdout: {result.stdout[:80]!r}")
    if not ok:
        failures.append(label)

    # 7. suture imports on a broken example
    label = "suture imports src-layout-no-pytest-path"
    result = _run(
        [suture, "imports", str(EXAMPLES_DIR / "src-layout-no-pytest-path")],
        capture=True,
    )
    ok = result.returncode == 0 and "IMP001" in result.stdout
    _step(label, ok, "IMP001 detected" if ok else f"stdout: {result.stdout[:80]!r}")
    if not ok:
        failures.append(label)

    # 8. suture pyproject on a broken example
    label = "suture pyproject broken-script-entrypoint"
    result = _run(
        [suture, "pyproject", str(EXAMPLES_DIR / "broken-script-entrypoint")],
        capture=True,
    )
    ok = result.returncode == 0 and "PRJ003" in result.stdout
    _step(label, ok, "PRJ003 detected" if ok else f"stdout: {result.stdout[:80]!r}")
    if not ok:
        failures.append(label)

    print()
    if failures:
        print(f"{_RED}Verification failed: {', '.join(failures)}{_RESET}\n")
        return 1

    print(f"{_GREEN}All package verification checks passed.{_RESET}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
