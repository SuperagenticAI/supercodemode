# Observability

SuperCodeMode supports a common event schema with multiple backends.

## Backends

- `none` default
- `jsonl`
- `otlp`
- `logfire` (optional SDK)
- `mlflow` (optional SDK)
- `langsmith` (optional SDK)
- `langfuse` (optional SDK)

## JSONL Example

```bash
scm --obs-backend jsonl --obs-jsonl-path artifacts/obs.jsonl showcase --runner mcp-stdio
```

Example event fields include:

- timestamp
- run_id
- event name
- `cli_command`
- `cli_runner`
- `cli_executor_backend`
- selected tool
- tool_call_count
- score
- latency_ms
- error

## OTLP Example

```bash
scm --obs-backend otlp --obs-otlp-endpoint http://localhost:4318/v1/traces showcase --runner mcp-stdio
```

## Provider SDK Backends (optional)

Install provider integrations:

```bash
pip install "supercodemode[observability]"
```

Examples:

```bash
scm --obs-backend logfire showcase --runner mcp-stdio
scm --obs-backend mlflow showcase --runner mcp-stdio
scm --obs-backend langsmith benchmark --runner mcp-stdio
scm --obs-backend langfuse optimize --runner mcp-stdio --max-metric-calls 4
```

These adapters use the same SuperCodeMode event schema and are best-effort:
SDK import/config errors will not fail the main run.

## Event Areas

Events are emitted from:

- runners (static, mcp, http)
- engine (showcase, optimize)
- doctor command

Summary events are also emitted for:

- run summaries (`evaluate_candidate`, `optimize`)
- showcase comparison summary
- benchmark summary

The benchmark and run summary payloads are designed for filtering/aggregation and
include compact fields such as:

- selected tool histograms
- error taxonomy rollups (`error_categories`)
- runner/executor context (`cli_runner`, `cli_executor_backend`)

See `reference/telemetry-schema.md` for the exact summary fields, runtime
capability hints, and current error taxonomy labels.

## Summary Artifacts (with `--save-artifact`)

When you save CLI artifacts, SuperCodeMode also writes compact summary files for
quick comparisons and CI-friendly diffs.

`showcase` writes:

- `*_comparison_summary_*.json`
- `*_baseline_run_summary_*.json`
- `*_tuned_run_summary_*.json`

`optimize` writes:

- `*_run_summary_*.json`

`benchmark` writes:

- `*_benchmark_summary_*.json`
- `*_<variant>_run_summary_*.json`

## Safety Rule

Telemetry failures do not fail the main run path.

This prevents observability outages from breaking optimization runs.
