from __future__ import annotations

from pathlib import Path
from typing import Callable

from rich.console import Console
from rich.prompt import Confirm

from suture.models import Issue, ProjectReport

console = Console()

FixFn = Callable[[Path], str]


def _fix_add_env_to_gitignore(root: Path) -> str:
    gitignore = root / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if ".env" not in content.splitlines():
            gitignore.write_text(content.rstrip() + "\n.env\n", encoding="utf-8")
            return "Added .env to .gitignore"
        return ".env already in .gitignore"
    else:
        gitignore.write_text(".env\n", encoding="utf-8")
        return "Created .gitignore with .env entry"


def _fix_create_env_example(root: Path) -> str:
    from suture.checks.env import _collect_python_files, _extract_env_vars_from_file

    py_files = _collect_python_files(root)
    code_vars: set[str] = set()
    for f in py_files:
        code_vars |= _extract_env_vars_from_file(f)

    env_example = root / ".env.example"
    existing: set[str] = set()

    if env_example.exists():
        for line in env_example.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                existing.add(line.split("=", 1)[0].strip())

    new_vars = code_vars - existing
    if not new_vars:
        return ".env.example already up to date"

    lines = []
    if env_example.exists():
        lines = env_example.read_text(encoding="utf-8").splitlines()

    for var in sorted(new_vars):
        lines.append(f"{var}=")

    env_example.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f"Added {len(new_vars)} variable(s) to .env.example"


def _fix_add_pytest_pythonpath(root: Path) -> str:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return "pyproject.toml not found, cannot apply fix"

    content = pyproject.read_text(encoding="utf-8")

    if "[tool.pytest.ini_options]" in content:
        # Add pythonpath under existing section
        lines = content.splitlines()
        new_lines = []
        inserted = False
        for line in lines:
            new_lines.append(line)
            if line.strip() == "[tool.pytest.ini_options]" and not inserted:
                new_lines.append('pythonpath = ["src"]')
                inserted = True
        if inserted:
            pyproject.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            return 'Added pythonpath = ["src"] under [tool.pytest.ini_options]'
        return "Could not locate [tool.pytest.ini_options] section to modify"
    else:
        content = content.rstrip() + "\n\n[tool.pytest.ini_options]\npythonpath = [\"src\"]\n"
        pyproject.write_text(content, encoding="utf-8")
        return 'Added [tool.pytest.ini_options] with pythonpath = ["src"]'


_SAFE_FIX_MAP: dict[str, FixFn] = {
    "add-env-to-gitignore": _fix_add_env_to_gitignore,
    "create-or-update-env-example": _fix_create_env_example,
    "add-pytest-pythonpath": _fix_add_pytest_pythonpath,
}

_INTERACTIVE_FIX_MAP: dict[str, FixFn] = {
    "add-pytest-config": _fix_add_pytest_pythonpath,
}


def get_fixable_issues(report: ProjectReport) -> list[tuple[Issue, FixFn, bool]]:
    """Return list of (issue, fix_fn, is_safe)."""
    seen_fix_ids: set[str] = set()
    fixable = []
    for issue in report.all_issues():
        if issue.fix_id is None:
            continue
        if issue.fix_id in seen_fix_ids:
            continue
        seen_fix_ids.add(issue.fix_id)
        if issue.fix_id in _SAFE_FIX_MAP:
            fixable.append((issue, _SAFE_FIX_MAP[issue.fix_id], True))
        elif issue.fix_id in _INTERACTIVE_FIX_MAP:
            fixable.append((issue, _INTERACTIVE_FIX_MAP[issue.fix_id], False))
    return fixable


def apply_dry_run(report: ProjectReport, root: Path) -> None:
    fixable = get_fixable_issues(report)
    if not fixable:
        console.print("[green]No fixable issues found.[/green]")
        return

    console.print("[bold]Dry run — no files will be changed:[/bold]")
    console.print()
    for issue, _fn, is_safe in fixable:
        safety = "[green]SAFE[/green]" if is_safe else "[yellow]INTERACTIVE[/yellow]"
        console.print(f"  {safety}  {issue.code}: {issue.title}")
        console.print(f"           Fix ID: {issue.fix_id}")
    console.print()


def apply_safe(report: ProjectReport, root: Path) -> None:
    fixable = [(i, fn) for i, fn, safe in get_fixable_issues(report) if safe]
    if not fixable:
        console.print("[green]No safe auto-fixes available.[/green]")
        return

    for issue, fix_fn in fixable:
        try:
            msg = fix_fn(root)
            console.print(f"  [green]✓[/green] {issue.code}: {msg}")
        except Exception as exc:
            console.print(f"  [red]✗[/red] {issue.code}: Fix failed — {exc}")


def apply_interactive(report: ProjectReport, root: Path) -> None:
    fixable = get_fixable_issues(report)
    if not fixable:
        console.print("[green]No fixable issues found.[/green]")
        return

    for issue, fix_fn, is_safe in fixable:
        safety = "safe" if is_safe else "requires review"
        console.print(f"\n[bold]{issue.code}[/bold]: {issue.title}  [{safety}]")
        console.print(f"  {issue.reason}")
        if Confirm.ask("  Apply this fix?"):
            try:
                msg = fix_fn(root)
                console.print(f"  [green]✓[/green] {msg}")
            except Exception as exc:
                console.print(f"  [red]✗[/red] Fix failed — {exc}")
        else:
            console.print("  Skipped.")
