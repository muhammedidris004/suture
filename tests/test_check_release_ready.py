"""Unit tests for check_release_ready helper functions."""
from __future__ import annotations

from pathlib import Path

from scripts.check_release_ready import (
    check_changelog_version,
    check_console_scripts,
    check_dist_artifacts,
    check_metadata_fields,
    check_readme_safety,
    check_required_files,
)


# ---------------------------------------------------------------------------
# check_required_files
# ---------------------------------------------------------------------------


def test_required_files_all_present(tmp_path: Path) -> None:
    files = [
        "README.md", "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md", "SECURITY.md", "RELEASE.md", "pyproject.toml",
    ]
    for f in files:
        (tmp_path / f).write_text("x")
    assert check_required_files(tmp_path) == []


def test_required_files_reports_missing(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("x")
    missing = check_required_files(tmp_path)
    assert "LICENSE" in missing
    assert "CHANGELOG.md" in missing
    assert "README.md" not in missing


# ---------------------------------------------------------------------------
# check_metadata_fields
# ---------------------------------------------------------------------------


def test_metadata_fields_complete() -> None:
    data = {
        "project": {
            "name": "suture",
            "version": "0.1.0",
            "description": "desc",
            "readme": "README.md",
            "requires-python": ">=3.10",
            "license": {"file": "LICENSE"},
            "authors": [{"name": "Test"}],
            "keywords": ["test"],
            "classifiers": ["Development Status :: 3 - Alpha"],
            "dependencies": ["typer"],
        }
    }
    assert check_metadata_fields(data) == []


def test_metadata_fields_missing() -> None:
    data = {"project": {"name": "suture"}}
    missing = check_metadata_fields(data)
    assert "version" in missing
    assert "description" in missing
    assert "name" not in missing


# ---------------------------------------------------------------------------
# check_console_scripts
# ---------------------------------------------------------------------------


def test_console_scripts_valid() -> None:
    data = {"project": {"scripts": {"suture": "suture.cli:main"}}}
    assert check_console_scripts(data) == []


def test_console_scripts_missing_entry() -> None:
    data = {"project": {"scripts": {}}}
    errors = check_console_scripts(data)
    assert any("missing" in e for e in errors)


def test_console_scripts_wrong_target() -> None:
    data = {"project": {"scripts": {"suture": "suture.cli:app"}}}
    errors = check_console_scripts(data)
    assert any("suture.cli:main" in e for e in errors)


# ---------------------------------------------------------------------------
# check_changelog_version
# ---------------------------------------------------------------------------


def test_changelog_version_found_unreleased(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text("## [0.1.0] - Unreleased\n\n### Added\n")
    assert check_changelog_version("0.1.0", tmp_path) is True


def test_changelog_version_found_with_date(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text("## [0.1.0] - 2024-06-01\n\n### Added\n")
    assert check_changelog_version("0.1.0", tmp_path) is True


def test_changelog_version_found_bare(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text("## [0.1.0]\n\n### Added\n")
    assert check_changelog_version("0.1.0", tmp_path) is True


def test_changelog_version_not_found(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text("## [0.2.0] - Unreleased\n")
    assert check_changelog_version("0.1.0", tmp_path) is False


def test_changelog_missing_file(tmp_path: Path) -> None:
    assert check_changelog_version("0.1.0", tmp_path) is False


# ---------------------------------------------------------------------------
# check_dist_artifacts
# ---------------------------------------------------------------------------


def test_dist_missing_is_warning_not_failure(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    ok, msg = check_dist_artifacts("0.1.0", dist)
    assert ok is True
    assert "not found" in msg


def test_dist_empty_is_warning(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    ok, msg = check_dist_artifacts("0.1.0", dist)
    assert ok is True
    assert "empty" in msg


def test_dist_correct_artifacts(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "suture_py-0.1.0.tar.gz").write_text("")
    (dist / "suture_py-0.1.0-py3-none-any.whl").write_text("")
    ok, msg = check_dist_artifacts("0.1.0", dist)
    assert ok is True
    assert "0.1.0" in msg


def test_dist_stale_version(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "suture_py-0.0.9.tar.gz").write_text("")
    ok, msg = check_dist_artifacts("0.1.0", dist)
    assert ok is False
    assert "stale" in msg


def test_dist_dotfiles_ignored(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / ".gitignore").write_text("*\n!.gitignore\n")
    (dist / "suture_py-0.1.0.tar.gz").write_text("")
    (dist / "suture_py-0.1.0-py3-none-any.whl").write_text("")
    ok, _ = check_dist_artifacts("0.1.0", dist)
    assert ok is True


# ---------------------------------------------------------------------------
# check_readme_safety
# ---------------------------------------------------------------------------


def test_readme_safety_guarded_install(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "### Once published to PyPI\n\n```\npipx install suture\n```\n"
    )
    ok, _ = check_readme_safety(tmp_path)
    assert ok is True


def test_readme_safety_bare_install_fails(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "## Install\n\n```\npipx install suture\n```\n"
    )
    ok, msg = check_readme_safety(tmp_path)
    assert ok is False
    assert "guard" in msg


def test_readme_safety_after_publishing_guard(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "After publishing:\n\n```bash\npipx install suture\n```\n"
    )
    ok, _ = check_readme_safety(tmp_path)
    assert ok is True


def test_readme_safety_no_install_line(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Suture\n\nA tool.\n")
    ok, _ = check_readme_safety(tmp_path)
    assert ok is True
