from pathlib import Path

from suture.checks.imports import check_imports


def _make_src_package(root: Path, name: str = "myapp") -> Path:
    pkg = root / "src" / name
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("")
    return pkg


def _make_flat_package(root: Path, name: str = "myapp") -> Path:
    pkg = root / name
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("")
    return pkg


def _write_pyproject(root: Path, content: str) -> None:
    (root / "pyproject.toml").write_text(content)


def test_imp001_src_layout_missing_pythonpath(project: Path) -> None:
    _make_src_package(project)
    _write_pyproject(project, "[tool.pytest.ini_options]\ntestpaths = [\"tests\"]\n")

    result = check_imports(project)
    codes = [i.code for i in result.issues]
    assert "IMP001" in codes


def test_imp001_not_raised_with_pythonpath(project: Path) -> None:
    _make_src_package(project)
    _write_pyproject(project, '[tool.pytest.ini_options]\npythonpath = ["src"]\n')

    result = check_imports(project)
    codes = [i.code for i in result.issues]
    assert "IMP001" not in codes


def test_imp002_no_package_found(project: Path) -> None:
    # No package directories at all
    result = check_imports(project)
    codes = [i.code for i in result.issues]
    assert "IMP002" in codes


def test_imp003_likely_package_missing_init(project: Path) -> None:
    pkg = project / "myapp"
    pkg.mkdir()
    (pkg / "main.py").write_text("x = 1\n")
    # No __init__.py

    result = check_imports(project)
    codes = [i.code for i in result.issues]
    assert "IMP003" in codes


def test_flat_layout_detected(project: Path) -> None:
    _make_flat_package(project)
    _write_pyproject(project, "[project]\nname = \"test\"\n")

    result = check_imports(project)
    assert any("flat" in p for p in result.passed)
    codes = [i.code for i in result.issues]
    assert "IMP002" not in codes


def test_src_layout_no_issues_when_configured(project: Path) -> None:
    _make_src_package(project)
    _write_pyproject(project, '[tool.pytest.ini_options]\npythonpath = ["src"]\ntestpaths = ["tests"]\n')

    result = check_imports(project)
    codes = [i.code for i in result.issues]
    assert "IMP001" not in codes
    assert "IMP002" not in codes
