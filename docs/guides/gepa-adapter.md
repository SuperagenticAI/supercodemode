# GEPA Adapter Changes

This page explains the GEPA Code Mode adapter changes used by this project.

## What Changed

The adapter keeps optimization logic in GEPA and keeps runtime execution in runner classes.

The runtime side now supports three patterns:

1. `MCPStdioCodeModeRunner`
- local MCP servers over stdio
- good for UTCP and local development

2. `MCPStreamableHTTPCodeModeRunner`
- direct MCP over streamable HTTP
- works with Cloudflare MCP endpoint `https://mcp.cloudflare.com/mcp`

3. `HTTPCodeModeRunner`
- JSON bridge endpoint
- useful if your platform exposes non MCP HTTP contract

## Why This Matters

Teams can optimize prompt and tool policy text once, while changing runtime transport without rewriting GEPA logic.

This makes contributions back to GEPA small:

- adapter core stays simple
- transport logic stays in runners
- examples show local and Cloudflare paths

## What GEPA Optimizes

GEPA optimizes candidate text fields:

- `system_prompt`
- `codemode_description`
- `tool_alias_map` (optional JSON string)
- `tool_description_overrides` (optional JSON string)

GEPA does not mutate your server code.

## How Execution Works

For each dataset row:

1. GEPA sends candidate text to the runner.
2. Runner calls MCP or HTTP runtime tools.
3. Runner returns:
   - `final_answer`
   - `generated_code`
   - `selected_tool`
   - `tool_calls`
   - `logs`
   - `error`
4. Metric scores result.
5. GEPA updates candidate text in optimization mode.

## Cloudflare MCP Flow

Use direct MCP transport:

```bash
scm showcase --runner mcp-http
scm optimize --runner mcp-http --max-metric-calls 10
```

`mcp-http` defaults to `https://mcp.cloudflare.com/mcp`.
You can still override with `--endpoint`.

Cloudflare response note for this demo:

- case 1 may return structured JSON from `search` (tool paths, counts)
- case 2 should return `{"result": 42}` from `execute`
- average score may be `0.5` with current string-match metric

Treat tool selection and response structure as the primary integration signal
for this demo.

## Local MCP Flow

Use stdio transport:

```bash
scm showcase --runner mcp-stdio
scm optimize --runner mcp-stdio --max-metric-calls 10
```

## GEPA Example Scripts

If you are validating GEPA adapter behavior directly, use:

- `code_mode_mcp_cloudflare_example.py` for Cloudflare MCP
- `code_mode_mcp_local_stdio_example.py` for local stdio MCP

These are real transport examples, not static mocks.
