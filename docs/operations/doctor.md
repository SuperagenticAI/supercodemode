# Doctor Command

`scm doctor` is the preflight command.

## What It Checks

- Python runtime
- `gepa` import
- `mcp` import
- optional `pydantic_monty` import check (warn when missing)
- Docker daemon reachability
- optional Docker run check
- MCP roundtrip check

## Commands

```bash
scm doctor
scm doctor --json
scm doctor --strict
scm doctor --executor-backend monty
scm doctor --no-docker-run
scm doctor --no-mcp-roundtrip
```

## Exit Behavior

- default: exits `0`, reports pass or fail in output
- `--strict`: exits non zero if any warn or fail exists

Use strict mode in CI pipelines.
