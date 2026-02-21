# Cloudflare Guide

This guide shows Cloudflare MCP direct usage and HTTP bridge usage.

## Fit for Cloudflare Users

Cloudflare users often have a two tool pattern:

- search tool for capability discovery
- execute tool for running code

SuperCodeMode improves the client side text that decides when to use each tool.

## Option A: Cloudflare MCP Direct

Use the public MCP endpoint:

- `https://mcp.cloudflare.com/mcp`

Run showcase:

```bash
scm showcase --runner mcp-http
```

Run optimization:

```bash
scm optimize --runner mcp-http --max-metric-calls 10
```

Override endpoint if needed:

```bash
scm showcase --runner mcp-http --endpoint https://your-mcp-endpoint.example.com/mcp
```

## Expected Demo Output

For the current Cloudflare demo dataset, a run can show:

- first case uses `search` and returns JSON tool metadata
- second case uses `execute` and returns `{"result": 42}`
- average score can be `0.5`

This is expected with the current metric. The first example currently checks for
the literal word `search` in `final_answer`, but Cloudflare may return structured
JSON without that word. In that case integration is still working if:

- `selected_tool=search` for case 1
- `selected_tool=execute` for case 2
- case 2 returns `42`

## Option B: HTTP Bridge

Use this when you run your own bridge service.

Request fields expected by the bridge:

- `user_query`
- `system_prompt`
- `codemode_description`
- `tool_alias_map`
- `tool_description_overrides`
- `additional_context`

Response fields:

- `final_answer`
- `generated_code`
- `selected_tool`
- `tool_calls`
- `logs`
- `error`

Run showcase:

```bash
scm showcase --runner http --endpoint http://localhost:8080/run-codemode
```

Run optimization:

```bash
scm optimize --runner http --endpoint http://localhost:8080/run-codemode --max-metric-calls 10
```

Save artifact:

```bash
scm optimize --runner http --endpoint http://localhost:8080/run-codemode --save-artifact
```

## Why This Is Valuable Without Server Side Auto Optimization

You still get strong gains by improving:

- tool routing text
- planning instructions
- output consistency
- tool call quality

Server code can remain unchanged while client policy gets better.

For a detailed GEPA explanation, read `guides/gepa-adapter.md`.
