# Observability

SuperCodeMode supports vendor neutral observability.

## Backends

- `none` default
- `jsonl`
- `otlp`

## JSONL Example

```bash
scm --obs-backend jsonl --obs-jsonl-path artifacts/obs.jsonl showcase --runner mcp-stdio
```

Example event fields include:

- timestamp
- run_id
- event name
- selected tool
- latency_ms
- error

## OTLP Example

```bash
scm --obs-backend otlp --obs-otlp-endpoint http://localhost:4318/v1/traces showcase --runner mcp-stdio
```

## Event Areas

Events are emitted from:

- runners (static, mcp, http)
- engine (showcase, optimize)
- doctor command

## Safety Rule

Telemetry failures do not fail the main run path.

This prevents observability outages from breaking optimization runs.
