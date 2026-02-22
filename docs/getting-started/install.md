# Install

## Requirements

- Python 3.10+
- `pip` or `uv`
- optional Docker Desktop for Docker backend

## Install Package (CLI)

With `pip`:

```bash
pip install supercodemode
```

With `uv` (tool install):

```bash
uv tool install supercodemode
```

With `uv` (current environment):

```bash
uv pip install supercodemode
```

## Optional Extras

Monty executor backend:

```bash
pip install "supercodemode[monty]"
uv pip install "supercodemode[monty]"
```

Observability integrations (Logfire, MLflow, LangSmith, Langfuse):

```bash
pip install "supercodemode[observability]"
uv pip install "supercodemode[observability]"
```

## Install Package (Local Development)

With `pip`:

```bash
pip install -e .
```

With `uv`:

```bash
uv pip install -e .
```

This installs the CLI command `scm`.

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
