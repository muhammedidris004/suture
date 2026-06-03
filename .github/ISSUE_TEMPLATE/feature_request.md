---
name: Feature request
about: Propose a new check or improvement to an existing check
labels: enhancement
---

## Problem

<!-- Describe the setup problem this check would catch. Be specific.
     Example: "Projects using src/ layout with a flat conftest.py often fail
     with ImportError because pytest does not add the package to sys.path." -->

## Proposed check

<!-- Describe what Suture should detect. -->

## Example project structure that should trigger the check

```text
myproject/
├── pyproject.toml
└── src/
    └── mypackage/
        └── __init__.py
```

## Expected issue code and title

<!-- If you have a suggestion for the issue code prefix and title, add it here.
     Existing prefixes: ENV (environment), IMP (imports), PRJ (pyproject).
     New areas may use a new prefix. -->

```
CODE: ???
Title: ???
```

## Should this be a confirmed or possible issue?

- [ ] Confirmed (high confidence — the problem is definitely present)
- [ ] Possible (medium/low confidence — worth flagging but may have valid exceptions)

## Safety concerns

<!-- Would detecting or fixing this issue ever risk data loss or unintended
     changes? Describe any cases where this check could produce a false
     positive. -->

## Additional context

<!-- Any other context, links, or examples. -->
