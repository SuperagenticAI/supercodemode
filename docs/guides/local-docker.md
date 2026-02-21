# Local and Docker Backends

SuperCodeMode demo MCP server supports two execution backends.

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
