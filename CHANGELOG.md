# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - Unreleased

### Added
- Initial Suture CLI.
- `suture doctor` — runs all checks and produces a scored health report.
- `suture env` — checks `.env` safety, `.env.example` coverage, and static env var usage.
- `suture imports` — checks import layout, `src/` configuration, and `__init__.py` presence.
- `suture pyproject` — validates `pyproject.toml` structure and script entry points.
- `suture doctor --json` — outputs full report as parseable JSON.
- `suture apply --dry-run` — shows what fixes would be applied without touching files.
- `suture apply --safe` — applies only safe, additive auto-fixes.
- `suture apply --interactive` — asks before each fix.
- Optional project path argument for all commands.
- `suture env` accepts a single `.py` file as input.
- Broken project validation examples under `examples/broken-projects/`.
- Validation script at `scripts/validate_examples.py`.
- Severity and confidence levels on all issues.
- Score system (0–100) with deductions per severity.
