from __future__ import annotations

import sys
from pathlib import Path

from suture.checks.env import check_env
from suture.checks.imports import check_imports, detect_layout
from suture.checks.pyproject import check_pyproject
from suture.models import ProjectReport, calculate_score

NOT_CHECKED = [
    "Docker config",
    "CI environment",
    "runtime errors",
    "async test setup",
    "circular imports",
    "dynamic imports",
    "framework-specific settings",
]


def _detect_python_version() -> str:
    v = sys.version_info
    return f"{v.major}.{v.minor}.{v.micro}"


def _detect_package_manager(root: Path) -> str:
    if (root / "uv.lock").exists():
        return "uv"
    if (root / "poetry.lock").exists():
        return "poetry"
    if (root / "requirements.txt").exists():
        return "pip"
    return "unknown"


def run_all_checks(root: Path) -> ProjectReport:
    layout, _ = detect_layout(root)

    results = []

    for check_fn in (check_pyproject, check_imports, check_env):
        try:
            results.append(check_fn(root))
        except Exception as exc:
            from suture.models import CheckResult
            cr = CheckResult(name=check_fn.__name__)
            cr.skipped.append(f"Check failed unexpectedly: {exc}")
            results.append(cr)

    all_issues = [i for r in results for i in r.issues]
    score = calculate_score(all_issues)

    return ProjectReport(
        project_root=str(root.resolve()),
        layout=layout,
        python_version=_detect_python_version(),
        package_manager=_detect_package_manager(root),
        results=results,
        score=score,
        not_checked=NOT_CHECKED,
    )
