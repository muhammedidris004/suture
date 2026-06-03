"""Tests for project path argument support."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from suture.cli import app, resolve_project_path
from suture.checks.env import check_env

runner = CliRunner()


# ---------------------------------------------------------------------------
# resolve_project_path unit tests
# ---------------------------------------------------------------------------


def test_resolve_defaults_to_cwd() -> None:
    result = resolve_project_path(None)
    assert result == Path.cwd()


def test_resolve_explicit_directory(tmp_path: Path) -> None:
    result = resolve_project_path(str(tmp_path))
    assert result == tmp_path.resolve()


def test_resolve_nonexistent_path_raises(tmp_path: Path) -> None:
    with pytest.raises(typer.Exit):
        resolve_project_path(str(tmp_path / "does_not_exist"))


def test_resolve_file_without_allow_file_raises(tmp_path: Path) -> None:
    f = tmp_path / "script.py"
    f.write_text("x = 1\n")
    with pytest.raises(typer.Exit):
        resolve_project_path(str(f), allow_file=False)


def test_resolve_file_with_allow_file(tmp_path: Path) -> None:
    f = tmp_path / "script.py"
    f.write_text("x = 1\n")
    result = resolve_project_path(str(f), allow_file=True)
    assert result == f.resolve()


# ---------------------------------------------------------------------------
# CLI integration tests via CliRunner
# ---------------------------------------------------------------------------


def _make_minimal_project(root: Path) -> None:
    pkg = root / "src" / "myapp"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (root / "pyproject.toml").write_text(
        '[project]\nname = "myapp"\nversion = "0.1.0"\n\n'
        '[tool.pytest.ini_options]\npythonpath = ["src"]\n'
    )
    (root / ".gitignore").write_text(".env\n")


def test_doctor_default_path_works(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _make_minimal_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0


def test_doctor_explicit_path(tmp_path: Path) -> None:
    _make_minimal_project(tmp_path)
    result = runner.invoke(app, ["doctor", str(tmp_path)])
    assert result.exit_code == 0


def test_doctor_invalid_path_clean_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["doctor", str(tmp_path / "no_such_dir")])
    assert result.exit_code != 0
    assert "does not exist" in result.output or "Error" in result.output


def test_doctor_json_includes_absolute_project_root(tmp_path: Path) -> None:
    _make_minimal_project(tmp_path)
    result = runner.invoke(app, ["doctor", str(tmp_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert Path(data["project_root"]).is_absolute()
    assert Path(data["project_root"]) == tmp_path.resolve()


def test_env_explicit_directory(tmp_path: Path) -> None:
    (tmp_path / "myapp").mkdir()
    (tmp_path / "myapp" / "__init__.py").write_text("")
    (tmp_path / "myapp" / "config.py").write_text('import os\nos.getenv("KEY")\n')
    (tmp_path / ".env.example").write_text("KEY=\n")
    result = runner.invoke(app, ["env", str(tmp_path)])
    assert result.exit_code == 0


def test_env_single_py_file(tmp_path: Path) -> None:
    py_file = tmp_path / "script.py"
    py_file.write_text('import os\nos.getenv("SECRET")\n')
    (tmp_path / ".env.example").write_text("SECRET=\n")
    result = runner.invoke(app, ["env", str(py_file)])
    assert result.exit_code == 0
    # ENV002 should not fire because SECRET is in .env.example
    assert "ENV002" not in result.output


def test_env_single_py_file_detects_missing_example(tmp_path: Path) -> None:
    py_file = tmp_path / "script.py"
    py_file.write_text('import os\nos.getenv("MISSING_VAR")\n')
    # No .env.example created
    result = runner.invoke(app, ["env", str(py_file)])
    assert result.exit_code == 0
    assert "ENV004" in result.output


def test_imports_rejects_file_input(tmp_path: Path) -> None:
    py_file = tmp_path / "script.py"
    py_file.write_text("x = 1\n")
    result = runner.invoke(app, ["imports", str(py_file)])
    assert result.exit_code != 0
    assert "file" in result.output.lower() or "directory" in result.output.lower()


def test_pyproject_explicit_path(tmp_path: Path) -> None:
    _make_minimal_project(tmp_path)
    result = runner.invoke(app, ["pyproject", str(tmp_path)])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# check_env single-file mode unit test
# ---------------------------------------------------------------------------


def test_check_env_single_file_mode(tmp_path: Path) -> None:
    py_file = tmp_path / "app.py"
    py_file.write_text('import os\ndb = os.getenv("DB_URL")\n')
    (tmp_path / ".env.example").write_text("DB_URL=\n")

    result = check_env(tmp_path, py_files=[py_file])
    codes = [i.code for i in result.issues]
    assert "ENV002" not in codes
