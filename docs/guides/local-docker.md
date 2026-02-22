# Local, Docker, and Monty Backends

SuperCodeMode demo MCP server supports multiple execution backends.

## Local Backend

```bash
scm showcase --runner mcp-stdio --executor-backend local
```

Best for speed and simple local demos.

## Docker Backend

```bash
scm showcase --runner mcp-stdio --executor-backend docker
```

Best for safer code execution isolation.

## Monty Backend

```bash
scm showcase --runner mcp-stdio --executor-backend monty
```

Best for a Python-native sandbox path without Docker.

Monty setup:

```bash
pip install "supercodemode[monty]"
```

If Monty is not installed, the demo server returns a clear executor error.

## Docker Requirements

- Docker daemon is running
- your user can run `docker run`

Validate with:

```bash
docker info
docker run --rm python:3.12-alpine python -c "print(17+25)"
```

## Select Docker Image

```bash
scm showcase --runner mcp-stdio --executor-backend docker --docker-image python:3.12-alpine
```

Use a custom image if your org has approved base images.
