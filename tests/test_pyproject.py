import json
from pathlib import Path

from suture.checks.pyproject import check_pyproject
from suture.doctor import run_all_checks
from suture.report import report_to_dict


def test_prj000_malformed_toml(project: Path) -> None:
    (project / "pyproject.toml").write_text("[ invalid toml !!!\n")

    result = check_pyproject(project)
    codes = [i.code for i in result.issues]
    assert "PRJ000" in codes


def test_prj001_missing_pyproject(project: Path) -> None:
    result = check_pyproject(project)
    codes = [i.code for i in result.issues]
    assert "PRJ001" in codes


def test_prj003_nonexistent_script_entry(project: Path) -> None:
    (project / "pyproject.toml").write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        '[project.scripts]\nmytool = "myapp.cli:main"\n'
    )

    result = check_pyproject(project)
    codes = [i.code for i in result.issues]
    assert "PRJ003" in codes


def test_prj003_valid_script_entry(project: Path) -> None:
    pkg = project / "src" / "myapp"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    cli = pkg / "cli.py"
    cli.write_text("def main(): pass\n")

    (project / "pyproject.toml").write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        '[project.scripts]\nmytool = "myapp.cli:main"\n'
    )

    result = check_pyproject(project)
    codes = [i.code for i in result.issues]
    assert "PRJ003" not in codes


def test_prj004_missing_name_and_version(project: Path) -> None:
    (project / "pyproject.toml").write_text("[project]\n")

    result = check_pyproject(project)
    codes = [i.code for i in result.issues]
    assert "PRJ004" in codes


def test_prj004_missing_version_only(project: Path) -> None:
    (project / "pyproject.toml").write_text('[project]\nname = "myapp"\n')

    result = check_pyproject(project)
    codes = [i.code for i in result.issues]
    assert "PRJ004" in codes


def test_prj005_both_requirements_and_pyproject(project: Path) -> None:
    (project / "pyproject.toml").write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n'
    )
    (project / "requirements.txt").write_text("requests\n")

    result = check_pyproject(project)
    codes = [i.code for i in result.issues]
    assert "PRJ005" in codes


def test_json_output_is_parseable(project: Path) -> None:
    # Set up a minimal valid project
    pkg = project / "src" / "myapp"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (project / "pyproject.toml").write_text(
        '[project]\nname = "myapp"\nversion = "0.1.0"\n\n'
        '[tool.pytest.ini_options]\npythonpath = ["src"]\n'
    )
    (project / ".gitignore").write_text(".env\n")

    report = run_all_checks(project)
    data = report_to_dict(report)
    serialized = json.dumps(data)
    parsed = json.loads(serialized)

    assert "project_root" in parsed
    assert "score" in parsed
    assert "issues" in parsed
    assert isinstance(parsed["issues"], list)
    assert "passed" in parsed
    assert "not_checked" in parsed
