# First Run

This page shows the shortest path to a successful run.

## Step 1: Run Local Showcase

```bash
scm showcase --runner mcp-stdio
```

What you should see:

- baseline score output
- tuned score output
- tool traces for each dataset item

## Step 2: Run Cloudflare MCP Showcase

```bash
scm showcase --runner mcp-http
```

This uses default endpoint `https://mcp.cloudflare.com/mcp`.
Use `--endpoint` only if you want another MCP server.

## Step 3: Save Artifact

```bash
scm showcase --runner mcp-stdio --save-artifact
```

You will get `artifact_path` in output.

## Step 4: Run Optimization

```bash
scm optimize --runner mcp-stdio --max-metric-calls 10
```

This returns best score and best candidate text.

## Step 5: Enable Observability

```bash
scm --obs-backend jsonl --obs-jsonl-path artifacts/obs.jsonl showcase --runner mcp-stdio
```

Now you can inspect run events in `artifacts/obs.jsonl`.
