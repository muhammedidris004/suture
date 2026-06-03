from __future__ import annotations

from pathlib import Path

from suture.models import CheckResult, Confidence, Issue, Severity

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


def _read_toml(path: Path) -> tuple[dict, str | None]:
    """Return (data, error_message). data is empty dict on error."""
    try:
        with open(path, "rb") as f:
            return tomllib.load(f), None
    except PermissionError:
        return {}, f"Permission denied reading {path}"
    except UnicodeDecodeError:
        return {}, f"Unicode decode error reading {path}"
    except Exception as e:  # tomllib.TOMLDecodeError and friends
        return {}, str(e)


def _resolve_script_entry(entry: str, root: Path) -> bool:
    """Return True if module:function entry point resolves on the filesystem."""
    if ":" not in entry:
        return False
    module_path, _func = entry.split(":", 1)
    parts = module_path.split(".")
    # Check both flat layout and src layout
    candidates = [
        root / Path(*parts).with_suffix(".py"),
        root / "src" / Path(*parts).with_suffix(".py"),
        root / Path(*parts) / "__init__.py",
        root / "src" / Path(*parts) / "__init__.py",
    ]
    return any(c.exists() for c in candidates)


def check_pyproject(root: Path) -> CheckResult:
    result = CheckResult(name="pyproject")
    pyproject_path = root / "pyproject.toml"
    requirements_path = root / "requirements.txt"

    if not pyproject_path.exists():
        result.issues.append(
            Issue(
                code="PRJ001",
                title="pyproject.toml missing",
                severity=Severity.CRITICAL,
                confidence=Confidence.HIGH,
                reason="No pyproject.toml file was found in the project root.",
                suggestion="Add pyproject.toml to define project metadata, dependencies, and tool configuration.",
            )
        )
        return result

    result.passed.append("pyproject.toml found")

    data, parse_error = _read_toml(pyproject_path)

    if parse_error is not None:
        result.issues.append(
            Issue(
                code="PRJ000",
                title="pyproject.toml is malformed",
                severity=Severity.CRITICAL,
                confidence=Confidence.HIGH,
                reason=f"pyproject.toml exists but could not be parsed as valid TOML. {parse_error}",
                suggestion="Fix the TOML syntax before running other pyproject checks.",
            )
        )
        return result

    project_section = data.get("project", {})

    # PRJ004: missing name or version
    missing_meta = []
    if not project_section.get("name"):
        missing_meta.append("name")
    if not project_section.get("version"):
        missing_meta.append("version")
    if missing_meta:
        result.issues.append(
            Issue(
                code="PRJ004",
                title="Missing project name or version",
                severity=Severity.MEDIUM,
                confidence=Confidence.HIGH,
                reason=f"[project] is missing {' and '.join(missing_meta)} metadata.",
                suggestion="Add name and version under [project].",
                fix_id=None,
            )
        )
    else:
        result.passed.append("[project] name and version present")

    # PRJ002: missing pytest config
    tool_section = data.get("tool", {})
    if "pytest" not in tool_section and "pytest.ini_options" not in tool_section:
        pytest_config = tool_section.get("pytest", {}).get("ini_options")
        if pytest_config is None and "ini_options" not in tool_section.get("pytest", {}):
            result.issues.append(
                Issue(
                    code="PRJ002",
                    title="[tool.pytest.ini_options] missing",
                    severity=Severity.HIGH,
                    confidence=Confidence.MEDIUM,
                    reason="No pytest configuration was found in pyproject.toml.",
                    suggestion="Add [tool.pytest.ini_options] if this project uses pytest.",
                    fix_id="add-pytest-config",
                )
            )
    else:
        result.passed.append("[tool.pytest.ini_options] present")

    # PRJ003: script entry points
    scripts = project_section.get("scripts", {})
    for cmd, entry in scripts.items():
        if not _resolve_script_entry(entry, root):
            result.issues.append(
                Issue(
                    code="PRJ003",
                    title="CLI script entry point points to a nonexistent module or function",
                    severity=Severity.HIGH,
                    confidence=Confidence.HIGH,
                    reason=f"[project.scripts] defines '{cmd} = {entry!r}', but Suture could not find the referenced module path or function.",
                    suggestion="Create the missing module/function or update the script entry point.",
                )
            )
        else:
            result.passed.append(f"Script entry point '{cmd}' resolves")

    # PRJ005: both requirements.txt and pyproject.toml
    if requirements_path.exists():
        result.issues.append(
            Issue(
                code="PRJ005",
                title="Both requirements.txt and pyproject.toml exist",
                severity=Severity.LOW,
                confidence=Confidence.MEDIUM,
                reason="Both dependency files exist. This can be valid, but it may confuse dependency ownership.",
                suggestion="Make sure one file is the source of truth, or clearly document why both exist.",
            )
        )

    return result
