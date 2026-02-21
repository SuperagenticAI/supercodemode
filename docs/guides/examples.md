# Examples Overview

All runnable scripts are under `examples/`.

## Dataset Templates

Starter datasets:

- `datasets/templates/two_tool_minimal.jsonl`
- `datasets/templates/cloudflare_search_execute.jsonl`
- `datasets/templates/routing_mix.jsonl`

## Local MCP Showcase

```bash
python examples/showcase_mcp_stdio.py
```

With artifact:

```bash
python examples/showcase_mcp_stdio.py --save-artifact
```

## Static Showcase

```bash
python examples/showcase_static.py
```

## HTTP Showcase

```bash
python examples/showcase_http.py --endpoint http://localhost:8080/run-codemode
```

## Cloudflare MCP Showcase

```bash
python examples/showcase_mcp_cloudflare.py
# or
scm showcase --runner mcp-http
```

## Local Optimization

```bash
python examples/optimize_mcp_stdio.py --max-metric-calls 10
```

## HTTP Bridge Optimization

```bash
python examples/optimize_cloudflare_http.py --endpoint http://localhost:8080/run-codemode --max-metric-calls 10
```

## Cloudflare MCP Optimization

```bash
python examples/optimize_mcp_cloudflare.py --max-metric-calls 10
# or
scm optimize --runner mcp-http --max-metric-calls 10
```

Expected behavior:

- case 1 often selects `search` and returns structured metadata JSON
- case 2 selects `execute` and returns `{"result": 42}`
- average score may show `0.5` with current demo metric

## Gemini Low Cost Optimization

```bash
export GOOGLE_API_KEY=your_key_here
python examples/optimize_gemini_flash.py --max-metric-calls 4
```

## Direct MCP Client Demo

```bash
python examples/mcp_client_demo.py
```

## Add Observability to Any Command

```bash
scm --obs-backend jsonl --obs-jsonl-path artifacts/obs.jsonl showcase --runner mcp-stdio
```

## Understand What Is Being Optimized

Read `guides/gepa-adapter.md` for a plain explanation of GEPA candidate fields, runner behavior, and transport choices.
