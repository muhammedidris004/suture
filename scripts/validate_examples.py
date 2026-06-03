#!/usr/bin/env python
"""Validate that each broken-project example triggers its expected issue codes."""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running directly with `python scripts/validate_examples.py` from the
# project root even without the package installed, as long as src/ is present.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from suture.doctor import run_all_checks  # noqa: E402

EXAMPLES_DIR = Path(__file__).parent.parent / "examples" / "broken-projects"

EXPECTED_ISSUES: dict[str, set[str]] = {
    "missing-env-gitignore": {"ENV001"},
    "src-layout-no-pytest-path": {"IMP001"},
    "broken-script-entrypoint": {"PRJ003"},
    "malformed-pyproject": {"PRJ000"},
    "missing-env-example": {"ENV004"},
    "mixed-requirements-pyproject": {"PRJ005"},
}

_GREEN = "\033[32m"
_RED = "\033[31m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def main() -> int:
    print(f"\n{_BOLD}Suture Example Validation{_RESET}\n")

    failures: list[str] = []

    for project_name, expected_codes in EXPECTED_ISSUES.items():
        project_path = EXAMPLES_DIR / project_name

        if not project_path.is_dir():
            msg = f"project directory not found: {project_path}"
            print(f"  {_RED}✗{_RESET} {project_name:<35} {_RED}MISSING — {msg}{_RESET}")
            failures.append(project_name)
            continue

        report = run_all_checks(project_path)
        found_codes = {i.code for i in report.all_issues()}
        missing_codes = expected_codes - found_codes

        if missing_codes:
            missing_str = ", ".join(sorted(missing_codes))
            found_str = ", ".join(sorted(found_codes)) or "(none)"
            print(
                f"  {_RED}✗{_RESET} {project_name:<35} "
                f"{_RED}MISSING {missing_str} (found: {found_str}){_RESET}"
            )
            failures.append(project_name)
        else:
            found_str = ", ".join(sorted(expected_codes))
            print(f"  {_GREEN}✓{_RESET} {project_name:<35} {found_str} found")

    print()
    if failures:
        print(f"{_RED}Validation failed for: {', '.join(failures)}{_RESET}\n")
        return 1

    print(f"{_GREEN}All example validations passed.{_RESET}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
