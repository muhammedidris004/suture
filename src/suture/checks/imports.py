from __future__ import annotations

import ast
from pathlib import Path

from suture.checks import SKIP_DIRS
from suture.models import CheckResult, Confidence, Issue, Severity

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


def _is_package_dir(path: Path) -> bool:
    return path.is_dir() and (path / "__init__.py").exists()


def _is_likely_package_dir(path: Path) -> bool:
    """Dir looks like a package but has no __init__.py."""
    if not path.is_dir():
        return False
    if path.name.startswith(".") or path.name in SKIP_DIRS:
        return False
    py_files = list(path.glob("*.py"))
    subdirs = [d for d in path.iterdir() if d.is_dir() and d.name not in SKIP_DIRS]
    return len(py_files) > 0 or len(subdirs) > 0


def detect_layout(root: Path) -> tuple[str, list[Path]]:
    """Return (layout, package_paths). layout: 'src' | 'flat' | 'unknown'."""
    src_dir = root / "src"
    packages: list[Path] = []

    if src_dir.is_dir():
        for child in src_dir.iterdir():
            if _is_package_dir(child):
                packages.append(child)
        if packages:
            return "src", packages

    for child in root.iterdir():
        if child.name in SKIP_DIRS or child.name.startswith("."):
            continue
        if _is_package_dir(child):
            packages.append(child)

    if packages:
        return "flat", packages

    return "unknown", []


def _get_pytest_pythonpath(root: Path) -> list[str]:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return []
    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        return data.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("pythonpath", [])
    except Exception:
        return []


def _collect_python_files(root: Path) -> list[Path]:
    result = []
    for path in root.rglob("*.py"):
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        result.append(path)
    return result


def _has_relative_imports(path: Path) -> bool:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level and node.level > 0:
            return True
    return False


def check_imports(root: Path) -> CheckResult:
    result = CheckResult(name="imports")
    layout, packages = detect_layout(root)
    src_dir = root / "src"

    if layout == "unknown":
        # Check if there are likely-package dirs without __init__.py
        candidates = []
        for child in root.iterdir():
            if child.name in SKIP_DIRS or child.name.startswith("."):
                continue
            if _is_likely_package_dir(child) and not _is_package_dir(child):
                candidates.append(child)

        if src_dir.is_dir():
            for child in src_dir.iterdir():
                if _is_likely_package_dir(child) and not _is_package_dir(child):
                    candidates.append(child)

        if candidates:
            for candidate in candidates:
                result.issues.append(
                    Issue(
                        code="IMP003",
                        title="__init__.py missing from likely package root",
                        severity=Severity.HIGH,
                        confidence=Confidence.MEDIUM,
                        reason=f"A likely package folder '{candidate.name}' was found but it does not contain __init__.py.",
                        suggestion="Add __init__.py if this folder is intended to be a regular Python package.",
                    )
                )
        else:
            result.issues.append(
                Issue(
                    code="IMP002",
                    title="Package folder not found",
                    severity=Severity.CRITICAL,
                    confidence=Confidence.HIGH,
                    reason="Suture could not find a package folder in src/ or the project root.",
                    suggestion="Create a package folder such as src/your_package/__init__.py or verify your project structure.",
                )
            )
        return result

    result.passed.append(f"{layout} layout detected")

    if layout == "src":
        pythonpath = _get_pytest_pythonpath(root)
        if "src" not in pythonpath:
            result.issues.append(
                Issue(
                    code="IMP001",
                    title="src layout may not be configured for pytest",
                    severity=Severity.HIGH,
                    confidence=Confidence.MEDIUM,
                    reason='This project uses src/ layout, but [tool.pytest.ini_options] pythonpath does not include "src".',
                    suggestion='If tests fail with ModuleNotFoundError, add pythonpath = ["src"] under [tool.pytest.ini_options] in pyproject.toml, or install the package using pip install -e .',
                    fix_id="add-pytest-pythonpath",
                )
            )
        else:
            result.passed.append('pytest pythonpath includes "src"')

    # IMP004: relative imports outside detected package paths
    package_roots = set(packages)
    py_files = _collect_python_files(root)
    for py_file in py_files:
        # Skip files that are inside a detected package
        in_package = any(
            py_file.is_relative_to(pkg) for pkg in package_roots
        )
        if not in_package and _has_relative_imports(py_file):
            result.issues.append(
                Issue(
                    code="IMP004",
                    title="Relative imports may be used outside a package context",
                    severity=Severity.MEDIUM,
                    confidence=Confidence.MEDIUM,
                    reason=f"Relative imports were found in '{py_file.relative_to(root)}' which may not be inside a detected package.",
                    suggestion="Use package-based imports or ensure the file is inside a proper package.",
                )
            )

    return result
