from __future__ import annotations

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.text import Text

from suture.models import CheckResult, Confidence, Issue, ProjectReport, Severity

console = Console()

_SEVERITY_STYLES: dict[Severity, str] = {
    Severity.CRITICAL: "bold red",
    Severity.HIGH: "red",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "blue",
    Severity.INFO: "dim",
}


def _score_style(score: int) -> str:
    if score >= 80:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


def _is_confirmed(issue: Issue) -> bool:
    return issue.confidence == Confidence.HIGH


def print_report(report: ProjectReport) -> None:
    console.print(
        Panel("[bold]Suture Project Health Report[/bold]", expand=False)
    )
    console.print()

    # Checked items
    all_passed = report.all_passed()
    all_skipped = report.all_skipped()

    checked_items = set()
    for r in report.results:
        checked_items.add(r.name)

    console.print("[bold]Checked:[/bold]")
    check_labels = {
        "pyproject": "pyproject.toml structure",
        "imports": "import layout and package structure",
        "env": ".env and environment variable handling",
        "check_pyproject": "pyproject.toml structure",
        "check_imports": "import layout and package structure",
        "check_env": ".env and environment variable handling",
    }
    for name in checked_items:
        label = check_labels.get(name, name)
        console.print(f"  {label}")
    console.print()

    # Score
    score = report.score
    style = _score_style(score)
    score_text = Text(f"Score: {score}/100", style=f"bold {style}")
    console.print(score_text)
    console.print()

    issues = report.all_issues()
    confirmed = [i for i in issues if _is_confirmed(i)]
    possible = [i for i in issues if not _is_confirmed(i)]

    if confirmed:
        console.print("[bold]Confirmed Issues:[/bold]")
        for issue in confirmed:
            style = _SEVERITY_STYLES.get(issue.severity, "")
            console.print(
                f"  [bold {style}]✗ {issue.code}[/bold {style}]  [{style}]{escape(issue.title)}[/{style}]"
            )
            console.print(f"       [dim]{escape(issue.reason)}[/dim]")
            console.print(f"       [italic]{escape(issue.suggestion)}[/italic]")
        console.print()

    if possible:
        console.print("[bold]Possible Issues:[/bold]")
        for issue in possible:
            style = _SEVERITY_STYLES.get(issue.severity, "")
            console.print(
                f"  [bold yellow]! {issue.code}[/bold yellow]  [{style}]{escape(issue.title)}[/{style}]"
            )
            console.print(f"       [dim]{escape(issue.reason)}[/dim]")
            console.print(f"       [italic]{escape(issue.suggestion)}[/italic]")
        console.print()

    if all_passed:
        console.print("[bold]Passed:[/bold]")
        for p in all_passed:
            console.print(f"  [green]✓[/green] {escape(p)}")
        console.print()

    if all_skipped:
        console.print("[bold]Skipped:[/bold]")
        for s in all_skipped:
            console.print(f"  [dim]~ {escape(s)}[/dim]")
        console.print()

    console.print("[bold]Not checked:[/bold]")
    for item in report.not_checked:
        console.print(f"  [dim]- {item}[/dim]")
    console.print()


def print_check_result(result: CheckResult, title: str) -> None:
    console.print(Panel(f"[bold]{title}[/bold]", expand=False))
    console.print()

    if result.issues:
        confirmed = [i for i in result.issues if _is_confirmed(i)]
        possible = [i for i in result.issues if not _is_confirmed(i)]

        if confirmed:
            console.print("[bold]Confirmed Issues:[/bold]")
            for issue in confirmed:
                style = _SEVERITY_STYLES.get(issue.severity, "")
                console.print(f"  [bold {style}]✗ {issue.code}[/bold {style}]  {escape(issue.title)}")
                console.print(f"       [dim]{escape(issue.reason)}[/dim]")
                console.print(f"       [italic]{escape(issue.suggestion)}[/italic]")
            console.print()

        if possible:
            console.print("[bold]Possible Issues:[/bold]")
            for issue in possible:
                style = _SEVERITY_STYLES.get(issue.severity, "")
                console.print(f"  [bold yellow]! {issue.code}[/bold yellow]  {escape(issue.title)}")
                console.print(f"       [dim]{escape(issue.reason)}[/dim]")
                console.print(f"       [italic]{escape(issue.suggestion)}[/italic]")
            console.print()
    else:
        console.print("[green]No issues found.[/green]")
        console.print()

    if result.passed:
        console.print("[bold]Passed:[/bold]")
        for p in result.passed:
            console.print(f"  [green]✓[/green] {escape(p)}")
        console.print()

    if result.skipped:
        console.print("[bold]Skipped:[/bold]")
        for s in result.skipped:
            console.print(f"  [dim]~ {escape(s)}[/dim]")
        console.print()


def report_to_dict(report: ProjectReport) -> dict:
    return {
        "project_root": report.project_root,
        "layout": report.layout,
        "python_version": report.python_version,
        "package_manager": report.package_manager,
        "score": report.score,
        "issues": [
            {
                "code": i.code,
                "title": i.title,
                "severity": i.severity.value,
                "confidence": i.confidence.value,
                "reason": i.reason,
                "suggestion": i.suggestion,
                "fix_id": i.fix_id,
            }
            for i in report.all_issues()
        ],
        "passed": report.all_passed(),
        "skipped": report.all_skipped(),
        "not_checked": report.not_checked,
    }
