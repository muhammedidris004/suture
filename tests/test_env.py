from pathlib import Path

from suture.checks.env import check_env


def _make_py(root: Path, content: str) -> Path:
    pkg = root / "myapp"
    pkg.mkdir(exist_ok=True)
    (pkg / "__init__.py").write_text("")
    f = pkg / "config.py"
    f.write_text(content)
    return f


def test_env001_env_not_in_gitignore(project: Path) -> None:
    (project / ".env").write_text("SECRET=abc\n")
    (project / ".gitignore").write_text("*.pyc\n")
    _make_py(project, 'import os\nos.getenv("SECRET")\n')

    result = check_env(project)
    codes = [i.code for i in result.issues]
    assert "ENV001" in codes


def test_env001_not_raised_when_env_ignored(project: Path) -> None:
    (project / ".env").write_text("SECRET=abc\n")
    (project / ".gitignore").write_text(".env\n")
    (project / ".env.example").write_text("SECRET=\n")
    _make_py(project, 'import os\nos.getenv("SECRET")\n')

    result = check_env(project)
    codes = [i.code for i in result.issues]
    assert "ENV001" not in codes


def test_env002_var_missing_from_example(project: Path) -> None:
    (project / ".env.example").write_text("OTHER=\n")
    _make_py(project, 'import os\nos.getenv("DATABASE_URL")\n')

    result = check_env(project)
    codes = [i.code for i in result.issues]
    assert "ENV002" in codes
    issue = next(i for i in result.issues if i.code == "ENV002")
    assert "DATABASE_URL" in issue.reason


def test_env004_no_env_example(project: Path) -> None:
    _make_py(project, 'import os\nos.environ["API_KEY"]\n')

    result = check_env(project)
    codes = [i.code for i in result.issues]
    assert "ENV004" in codes


def test_env003_var_in_env_not_in_code(project: Path) -> None:
    (project / ".env").write_text("UNUSED_VAR=secret\n")
    (project / ".env.example").write_text("UNUSED_VAR=\n")
    # No Python code references UNUSED_VAR
    _make_py(project, "x = 1\n")

    result = check_env(project)
    codes = [i.code for i in result.issues]
    assert "ENV003" in codes
    issue = next(i for i in result.issues if i.code == "ENV003")
    assert "UNUSED_VAR" in issue.reason


def test_environ_get_pattern(project: Path) -> None:
    (project / ".env.example").write_text("TOKEN=\n")
    _make_py(project, 'import os\nos.environ.get("TOKEN")\n')

    result = check_env(project)
    codes = [i.code for i in result.issues]
    assert "ENV002" not in codes


def test_environ_subscript_pattern(project: Path) -> None:
    (project / ".env.example").write_text("")
    _make_py(project, 'import os\nx = os.environ["MY_VAR"]\n')

    result = check_env(project)
    codes = [i.code for i in result.issues]
    assert "ENV002" in codes
