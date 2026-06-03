---
name: False positive
about: Suture reported an issue that you believe is incorrect for your project
labels: false-positive
---

## Issue code reported

<!-- e.g. IMP001, ENV003, PRJ002 -->

## Why you believe this is incorrect

<!-- Explain why the reported issue does not apply to your project.
     For example: "My package is installed with pip install -e . so pythonpath
     is not needed." -->

## Minimal project structure

<!-- Describe the relevant parts of your project layout. For example: -->

```text
myproject/
├── pyproject.toml
├── src/
│   └── mypackage/
│       └── __init__.py
└── tests/
    └── test_foo.py
```

## Relevant configuration

<!-- Paste any relevant sections of pyproject.toml, .env.example, or import
     statements. Remove any sensitive values before sharing. -->

```toml
# relevant pyproject.toml section
```

## JSON output

If safe to share, paste the output of:

```bash
suture doctor --json
```

> **Do not paste real secrets, API keys, passwords, or sensitive environment
> variable values.** Replace actual secret values with empty placeholders like
> `MY_VAR=` before sharing.

## Additional context

<!-- Anything else that helps explain why this is a false positive. -->
