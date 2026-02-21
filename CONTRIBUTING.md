# Contributing

Thanks for contributing to SuperCodeMode.

## Setup

```bash
pip install -e .
```

## Before Opening a PR

Run checks from repo root:

```bash
ruff check .
python -m py_compile supercodemode/*.py
```

If you changed `Reference/gepa` adapter code, also run:

```bash
PYTHONPATH=Reference/gepa/src pytest -q Reference/gepa/tests/test_code_mode_adapter.py Reference/gepa/tests/test_code_mode_runners.py
```

## PR Scope

- Keep changes focused and small.
- Include docs updates for user-facing behavior changes.
- Prefer real runnable examples over mock-only behavior for integration paths.
