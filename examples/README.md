# Examples

All user-facing runnable examples live here.

## Setup

```bash
pip install -e .
```

## Dataset Templates

Use starter datasets from:

- `datasets/templates/two_tool_minimal.jsonl`
- `datasets/templates/cloudflare_search_execute.jsonl`
- `datasets/templates/routing_mix.jsonl`

## 1) Showcase (Static)

```bash
python examples/showcase_static.py
```

Save artifact JSON:

```bash
python examples/showcase_static.py --save-artifact
```

## 2) Showcase (Local MCP stdio)

```bash
python examples/showcase_mcp_stdio.py
```

Use Docker sandbox backend for tool execution:

```bash
python examples/showcase_mcp_stdio.py --executor-backend docker
```

Use a custom server script:

```bash
python examples/showcase_mcp_stdio.py --mcp-server /path/to/server.py
```

Save artifact JSON:

```bash
python examples/showcase_mcp_stdio.py --save-artifact
```

## 3) Showcase (HTTP runtime bridge)

```bash
python examples/showcase_http.py --endpoint http://localhost:8080/run-codemode
```

Save artifact JSON:

```bash
python examples/showcase_http.py --endpoint http://localhost:8080/run-codemode --save-artifact
```

## 4) Showcase (Cloudflare MCP direct)

```bash
python examples/showcase_mcp_cloudflare.py
```

## 5) Optimize (Local MCP stdio)

```bash
python examples/optimize_mcp_stdio.py
```

Docker backend:

```bash
python examples/optimize_mcp_stdio.py --executor-backend docker
```

Save artifact JSON:

```bash
python examples/optimize_mcp_stdio.py --save-artifact
```

## 6) Optimize (Cloudflare/HTTP bridge endpoint)

```bash
python examples/optimize_cloudflare_http.py --endpoint http://localhost:8080/run-codemode
```

Save artifact JSON:

```bash
python examples/optimize_cloudflare_http.py --endpoint http://localhost:8080/run-codemode --save-artifact
```

## 7) Optimize (Cloudflare MCP direct)

```bash
python examples/optimize_mcp_cloudflare.py
```

## 8) Real LLM optimization (Gemini 2.5 Flash)

Requires `GOOGLE_API_KEY`.
Note: in adapter mode, GEPA uses `reflection_lm` for optimization; `task_lm` is not used.

```bash
export GOOGLE_API_KEY=your_key_here
python examples/optimize_gemini_flash.py --max-metric-calls 8
```

Docker execution backend:

```bash
python examples/optimize_gemini_flash.py --executor-backend docker --max-metric-calls 8
```

Save artifact JSON:

```bash
python examples/optimize_gemini_flash.py --max-metric-calls 8 --save-artifact
```

## 9) Direct MCP client demo

```bash
python examples/mcp_client_demo.py
```

Docker backend:

```bash
python examples/mcp_client_demo.py --executor-backend docker
```

Save artifact JSON:

```bash
python examples/mcp_client_demo.py --save-artifact
```

Docker backend requirements:

- Docker daemon running and accessible by your user
- `docker run` permitted in your environment

## Equivalent CLI

```bash
scm doctor
scm showcase --runner static
scm showcase --runner mcp-stdio
scm showcase --runner mcp-http
scm showcase --runner mcp-stdio --executor-backend docker
scm showcase --runner http --endpoint http://localhost:8080/run-codemode
scm optimize --runner mcp-stdio
scm optimize --runner mcp-http
scm optimize --runner mcp-stdio --executor-backend docker
scm optimize --runner http --endpoint http://localhost:8080/run-codemode
scm mcp-client
scm mcp-client --executor-backend docker

# with artifacts
scm showcase --runner mcp-stdio --save-artifact
scm optimize --runner mcp-stdio --save-artifact
scm mcp-client --save-artifact

# with observability (jsonl)
scm --obs-backend jsonl --obs-jsonl-path artifacts/obs.jsonl showcase --runner mcp-stdio
```
