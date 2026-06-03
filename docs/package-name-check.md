# Package Name Check

Before publishing, manually verify that the package name is available and
unambiguous.

## Where to check

- **PyPI**: search for `suture` at https://pypi.org
- **TestPyPI**: search for `suture` at https://test.pypi.org
- **GitHub**: search repositories named `suture`
- **Google**: search `suture python package`

Do not assume the name is available. Always confirm before attempting to
publish.

## Preferred naming

| Setting | Value |
|---|---|
| Package name (PyPI) | `suture` |
| CLI command | `suture` |
| Import name | `suture` |

## Fallback candidates (if `suture` is taken or confusing)

In order of preference:

| Package name | CLI command |
|---|---|
| `suture-cli` | `suture` |
| `suture-py` | `suture` |
| `suture-dev` | `suture` |

The CLI command (`suture`) should remain unchanged regardless of the package
name, because it is defined in `[project.scripts]` in `pyproject.toml` and
is separate from the install name.

## If the name needs to change

1. Update `name` in `pyproject.toml`.
2. Update the `check_release_ready.py` script (it checks for `suture-x.y.z`
   artifact names and the `suture` console script entry).
3. Update `CHANGELOG.md`, `README.md`, and all documentation references.
4. Re-run `uv run python scripts/preflight.py` to confirm everything is
   consistent.
