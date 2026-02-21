# Install

## Requirements

- Python 3.10+
- `pip`
- optional Docker Desktop for Docker backend

## Install Package

```bash
pip install -e .
```

This installs CLI command `scm`.

## Verify Install

```bash
scm --help
```

## Check Environment

```bash
scm doctor
```

If you only want a quick check without Docker image run:

```bash
scm doctor --no-docker-run
```
