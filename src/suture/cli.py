from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from suture.checks.env import check_env
from suture.checks.imports import check_imports
from suture.checks.pyproject import check_pyproject
from suture.doctor import run_all_checks
from suture.fixer import apply_dry_run, apply_interactive, apply_safe
from suture.report import print_check_result, print_report, report_to_dict

app = typer.Typer(
    name="suture",
    help="Suture stitches broken Python project setups back together with safe, explainable diagnostics.",
    no_args_is_help=True,
)


def resolve_project_path(path: Optional[str], *, allow_file: bool = False) -> Path:
    """Resolve a user-supplied path to an absolute Path.

    Defaults to cwd when path is None. Raises typer.Exit on invalid input.
    Set allow_file=True to accept a single .py file in addition to directories.
    """
    resolved = Path(path).resolve() if path is not None else Path.cwd()

    if resolved.is_dir():
        return resolved

    if allow_file and resolved.is_file():
        return resolved

    if not resolved.exists():
        typer.echo(f"Error: path does not exist: '{resolved}'", err=True)
        raise typer.Exit(code=1)

    # exists but is a file where a directory was required
    typer.echo(
        f"Error: '{resolved}' is a file. This command requires a project directory.",
        err=True,
    )
    raise typer.Exit(code=1)


@app.command()
def doctor(
    path: Optional[str] = typer.Argument(None, help="Project root directory (default: current directory)."),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON."),
) -> None:
    """Run all checks and produce a combined health report."""
    root = resolve_project_path(path)
    report = run_all_checks(root)

    if json_output:
        print(json.dumps(report_to_dict(report), indent=2))
    else:
        print_report(report)

    if report.score < 50:
        raise typer.Exit(code=1)


@app.command(name="env")
def env_cmd(
    path: Optional[str] = typer.Argument(
        None,
        help="Project root directory or a single .py file (default: current directory).",
    ),
) -> None:
    """Check .env files, .gitignore safety, and environment variable usage."""
    resolved = resolve_project_path(path, allow_file=True)

    if resolved.is_file():
        root = resolved.parent
        result = check_env(root, py_files=[resolved])
    else:
        root = resolved
        result = check_env(root)

    print_check_result(result, "Suture — Environment Check")


@app.command(name="imports")
def imports_cmd(
    path: Optional[str] = typer.Argument(None, help="Project root directory (default: current directory)."),
) -> None:
    """Check import layout, package structure, and pytest path configuration."""
    root = resolve_project_path(path)
    result = check_imports(root)
    print_check_result(result, "Suture — Imports Check")


@app.command(name="pyproject")
def pyproject_cmd(
    path: Optional[str] = typer.Argument(None, help="Project root directory (default: current directory)."),
) -> None:
    """Validate pyproject.toml structure and content."""
    root = resolve_project_path(path)
    result = check_pyproject(root)
    print_check_result(result, "Suture — pyproject.toml Check")


@app.command(name="apply")
def apply_cmd(
    path: Optional[str] = typer.Argument(None, help="Project root directory (default: current directory)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would change without touching files."),
    safe: bool = typer.Option(False, "--safe", help="Apply only safe auto-fixes."),
    interactive: bool = typer.Option(False, "--interactive", help="Ask before each fix."),
) -> None:
    """Apply available fixes to diagnosed issues."""
    root = resolve_project_path(path)
    report = run_all_checks(root)

    if dry_run:
        apply_dry_run(report, root)
    elif safe:
        apply_safe(report, root)
    elif interactive:
        apply_interactive(report, root)
    else:
        typer.echo("Specify one of --dry-run, --safe, or --interactive.", err=True)
        raise typer.Exit(code=1)


def main() -> None:
    app()
