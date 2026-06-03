from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


_SEVERITY_DEDUCTIONS: dict[Severity, int] = {
    Severity.CRITICAL: 25,
    Severity.HIGH: 15,
    Severity.MEDIUM: 8,
    Severity.LOW: 3,
    Severity.INFO: 0,
}


def calculate_score(issues: list[Issue]) -> int:
    score = 100
    for issue in issues:
        score -= _SEVERITY_DEDUCTIONS.get(issue.severity, 0)
    return max(0, score)


@dataclass
class Issue:
    code: str
    title: str
    severity: Severity
    confidence: Confidence
    reason: str
    suggestion: str
    fix_id: str | None = None


@dataclass
class CheckResult:
    name: str
    issues: list[Issue] = field(default_factory=list)
    passed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


@dataclass
class ProjectReport:
    project_root: str
    layout: str  # "src" | "flat" | "unknown"
    python_version: str
    package_manager: str  # "uv" | "poetry" | "pip" | "unknown"
    results: list[CheckResult] = field(default_factory=list)
    score: int = 100
    not_checked: list[str] = field(default_factory=list)

    def all_issues(self) -> list[Issue]:
        return [i for r in self.results for i in r.issues]

    def all_passed(self) -> list[str]:
        return [p for r in self.results for p in r.passed]

    def all_skipped(self) -> list[str]:
        return [s for r in self.results for s in r.skipped]
