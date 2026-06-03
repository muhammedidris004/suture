"""Tests that verify the broken-project examples produce expected issue codes."""
from __future__ import annotations

from pathlib import Path

import pytest

from suture.doctor import run_all_checks

EXAMPLES_DIR = Path(__file__).parent.parent / "examples" / "broken-projects"

EXPECTED_ISSUES: dict[str, set[str]] = {
    "missing-env-gitignore": {"ENV001"},
    "src-layout-no-pytest-path": {"IMP001"},
    "broken-script-entrypoint": {"PRJ003"},
    "malformed-pyproject": {"PRJ000"},
    "missing-env-example": {"ENV004"},
    "mixed-requirements-pyproject": {"PRJ005"},
}


@pytest.mark.parametrize("project_name", list(EXPECTED_ISSUES))
def test_example_project_exists(project_name: str) -> None:
    assert (EXAMPLES_DIR / project_name).is_dir(), (
        f"Example project '{project_name}' not found at {EXAMPLES_DIR / project_name}"
    )


@pytest.mark.parametrize("project_name,expected_codes", list(EXPECTED_ISSUES.items()))
def test_example_produces_expected_codes(
    project_name: str, expected_codes: set[str]
) -> None:
    project_path = EXAMPLES_DIR / project_name
    report = run_all_checks(project_path)
    found_codes = {i.code for i in report.all_issues()}
    missing = expected_codes - found_codes
    assert not missing, (
        f"{project_name}: expected {sorted(expected_codes)}, "
        f"found {sorted(found_codes)}, missing {sorted(missing)}"
    )
