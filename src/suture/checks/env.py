from __future__ import annotations

import ast
import warnings
from pathlib import Path

from suture.checks import SKIP_DIRS
from suture.models import CheckResult, Confidence, Issue, Severity


def _collect_python_files(root: Path) -> list[Path]:
    result = []
    for path in root.rglob("*.py"):
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        result.append(path)
    return result


def _extract_env_vars_from_file(path: Path) -> set[str]:
    """Extract statically referenced env var names from a Python file."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(source, filename=str(path))
    except (SyntaxError, PermissionError, UnicodeDecodeError):
        return set()

    vars_found: set[str] = set()

    for node in ast.walk(tree):
        # os.getenv("VAR") or os.environ.get("VAR")
        if isinstance(node, ast.Call):
            func = node.func
            # os.getenv("VAR")
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "getenv"
                and isinstance(func.value, ast.Name)
                and func.value.id == "os"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                vars_found.add(node.args[0].value)

            # os.environ.get("VAR")
            elif (
                isinstance(func, ast.Attribute)
                and func.attr == "get"
                and isinstance(func.value, ast.Attribute)
                and func.value.attr == "environ"
                and isinstance(func.value.value, ast.Name)
                and func.value.value.id == "os"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                vars_found.add(node.args[0].value)

        # os.environ["VAR"]
        elif isinstance(node, ast.Subscript):
            value = node.value
            if (
                isinstance(value, ast.Attribute)
                and value.attr == "environ"
                and isinstance(value.value, ast.Name)
                and value.value.id == "os"
            ):
                slice_node = node.slice
                # Python 3.9+ slice is the node directly
                if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
                    vars_found.add(slice_node.value)
                # Python 3.8 wraps in ast.Index
                elif isinstance(slice_node, ast.Index):  # type: ignore[attr-defined]
                    inner = slice_node.value  # type: ignore[attr-defined]
                    if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                        vars_found.add(inner.value)

    return vars_found


def _parse_env_file(path: Path) -> set[str]:
    """Parse KEY=VALUE lines from a .env style file."""
    if not path.exists():
        return set()
    keys: set[str] = set()
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key = line.split("=", 1)[0].strip()
                if key:
                    keys.add(key)
    except (PermissionError, UnicodeDecodeError):
        pass
    return keys


def _parse_gitignore(path: Path) -> set[str]:
    if not path.exists():
        return set()
    entries: set[str] = set()
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            entries.add(line)
    except (PermissionError, UnicodeDecodeError):
        pass
    return entries


# Well-known system/CI variables that are not application secrets.
# Findings for these are downgraded to LOW/MEDIUM so they don't dominate reports.
_SYSTEM_VARS = frozenset({
    "CI", "HOME", "PATH", "TERM", "SHELL", "USER", "LOGNAME", "LANG",
    "LC_ALL", "LC_CTYPE", "TMPDIR", "TMP", "TEMP", "PWD", "OLDPWD",
    "COLORFGBG", "COLORTERM", "TERM_PROGRAM", "TERM_PROGRAM_VERSION",
    "COLUMNS", "LINES",
})


def _is_env_ignored(gitignore_entries: set[str]) -> bool:
    return any(e in (".env", "*.env", ".env*") for e in gitignore_entries)


def check_env(root: Path, py_files: list[Path] | None = None) -> CheckResult:
    result = CheckResult(name="env")

    env_path = root / ".env"
    env_example_path = root / ".env.example"
    gitignore_path = root / ".gitignore"

    if py_files is None:
        py_files = _collect_python_files(root)
    code_vars: set[str] = set()
    for py_file in py_files:
        code_vars |= _extract_env_vars_from_file(py_file)

    env_vars = _parse_env_file(env_path)
    example_vars = _parse_env_file(env_example_path)
    gitignore_entries = _parse_gitignore(gitignore_path)

    # ENV001: .env exists but not in .gitignore
    if env_path.exists():
        if not _is_env_ignored(gitignore_entries):
            result.issues.append(
                Issue(
                    code="ENV001",
                    title=".env is not listed in .gitignore",
                    severity=Severity.CRITICAL,
                    confidence=Confidence.HIGH,
                    reason="A .env file exists but .env is not ignored by git. This can expose secrets.",
                    suggestion="Add .env to .gitignore.",
                    fix_id="add-env-to-gitignore",
                )
            )
        else:
            result.passed.append(".env is listed in .gitignore")
    else:
        result.skipped.append(".env not present, skipping gitignore check")

    if code_vars:
        # ENV004: vars used but no .env.example
        if not env_example_path.exists():
            result.issues.append(
                Issue(
                    code="ENV004",
                    title="No .env.example file found",
                    severity=Severity.MEDIUM,
                    confidence=Confidence.HIGH,
                    reason="Environment variables are used in code, but no .env.example file exists.",
                    suggestion="Create .env.example documenting required environment variables.",
                    fix_id="create-or-update-env-example",
                )
            )
        else:
            result.passed.append(".env.example found")
            # ENV002: vars in code but missing from .env.example
            missing_from_example = code_vars - example_vars
            for var in sorted(missing_from_example):
                is_system = var in _SYSTEM_VARS
                result.issues.append(
                    Issue(
                        code="ENV002",
                        title="Environment variable used in code but missing from .env.example",
                        severity=Severity.LOW if is_system else Severity.HIGH,
                        confidence=Confidence.LOW if is_system else Confidence.HIGH,
                        reason=f"Code references '{var}' but it is not documented in .env.example."
                               + (" This looks like a system variable — review before adding." if is_system else ""),
                        suggestion="Add the missing variable to .env.example with an empty placeholder.",
                        fix_id="create-or-update-env-example",
                    )
                )
            if not missing_from_example:
                result.passed.append("All code env vars documented in .env.example")
    else:
        result.skipped.append("No static env var references found in Python files")

    # ENV003: var in .env not found in static code refs
    if env_vars:
        undocumented = env_vars - code_vars
        for var in sorted(undocumented):
            result.issues.append(
                Issue(
                    code="ENV003",
                    title="Variable exists in .env but was not found in static code references",
                    severity=Severity.LOW,
                    confidence=Confidence.MEDIUM,
                    reason=f"'{var}' exists in .env, but Suture did not find it using os.getenv/os.environ static analysis.",
                    suggestion="Review before removing. It may be used dynamically, by a framework, or outside Python code.",
                )
            )

    return result
