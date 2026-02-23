# From Demo to Real Workflow

This guide explains how to use SuperCodeMode in your own workflow, not just run the built-in demos.

SuperCodeMode optimizes **client-side Code Mode behavior** with GEPA.

It does **not** replace your MCP server.
It helps you improve how your client uses that server.

## Mental Model

SuperCodeMode sits between:

- your evaluation loop (GEPA)
- your Code Mode client behavior (prompting, routing guidance, tool naming)
- your MCP runtime (Cloudflare, local MCP, UTCP, custom)

It optimizes the client-side behavior and keeps runtime transport/backend separate.

## What You Need to Bring

Before using SuperCodeMode for a real workflow, you need:

1. An MCP server or Code Mode runtime
- Cloudflare MCP
- local MCP stdio server
- UTCP Code Mode
- internal/custom MCP server

2. A small evaluation dataset (real tasks)
- 10 to 50 tasks is enough to start
- use tasks that reflect real production usage

3. A scoring rule (metric)
- exact match
- contains required fields
- JSON validation
- custom pass/fail checks

4. A place to apply the optimized result
- your agent client config
- your prompt template
- your Code Mode tool descriptions / aliases

## What SuperCodeMode Optimizes

SuperCodeMode is designed to optimize client-side Code Mode text and behavior such as:

- `system_prompt`
- `codemode_description`
- `tool_alias_map`
- `tool_description_overrides`

These fields affect:

- whether the model discovers tools first
- whether it chooses the right tool
- how it plans execution
- how stable the final output is

## What It Does Not Change

SuperCodeMode does not automatically:

- modify your MCP server implementation
- deploy server-side changes
- change provider-side tool schemas

This is why it is useful even when you do not control the server.

## Recommended Workflow (Real Usage)

### Step 1: Prove your runtime works (smoke test)

Use a built-in showcase first.

Local MCP:

```bash
scm showcase --runner mcp-stdio
```

Cloudflare MCP (requires auth in most environments):

```bash
scm showcase --runner mcp-http --auth-bearer "$CODEMODE_TOKEN"
```

Goal:

- confirm transport works
- confirm tool calls happen
- confirm outputs and traces are produced

### Step 2: Benchmark baseline behavior

Run a quick comparison on the built-in dataset:

```bash
scm benchmark --runner mcp-stdio --save-artifact
```

This compares:

- `tool_call`
- `codemode_baseline`
- `codemode_optimized`

Goal:

- understand current behavior shape
- inspect scores, tool calls, and failures
- get familiar with summary artifacts

### Step 3: Replace the toy dataset with your tasks

For a real workflow, use your own tasks.

Good examples:

- "Find the right API endpoint for X and return the path"
- "Run a read-only audit and summarize results"
- "Compute/report using the execution tool and return structured JSON"

Tips:

- include easy, medium, and failure-prone tasks
- include tasks where routing matters
- include tasks where output format matters

### Step 4: Define a metric that reflects real success

Do not rely only on string contains checks for production workflows.

Use metrics like:

- exact expected value match
- JSON schema validation
- required keys present
- domain-specific pass/fail rules
- custom evaluator script

The metric determines what GEPA optimizes toward.

### Step 5: Run optimization

After your dataset and metric are ready:

```bash
scm optimize --runner mcp-stdio --max-metric-calls 10 --save-artifact
```

For Cloudflare MCP:

```bash
scm optimize --runner mcp-http --auth-bearer "$CODEMODE_TOKEN" --max-metric-calls 10 --save-artifact
```

Goal:

- generate improved client-side candidates
- compare scores
- inspect best candidate text

### Step 6: Apply the best candidate to your client

Take the optimized values (for example `system_prompt`, `codemode_description`, aliases, descriptions) and apply them to your real Code Mode client configuration.

This is the production handoff step.

### Step 7: Observe and iterate

Use observability and summary artifacts to track behavior changes over time.

Examples:

```bash
scm --obs-backend jsonl --obs-jsonl-path artifacts/obs.jsonl benchmark --runner mcp-stdio
scm --obs-backend langsmith benchmark --runner mcp-stdio
```

## How to Interpret Results

Focus on more than just average score.

Also inspect:

- `selected_tool`
- tool call count
- error count
- `error_categories`
- run summaries and benchmark summaries

A run can be useful even if scores are low, if it reveals routing mistakes, auth failures, or schema mismatches you can fix.

## Common Mistakes

### Mistake 1: Expecting SuperCodeMode to change the server

It optimizes the client-side behavior layer.
Your MCP server remains the same unless you change it separately.

### Mistake 2: Using a toy metric for real tasks

A weak metric teaches GEPA the wrong thing.
Use metrics that reflect real success in your workflow.

### Mistake 3: Skipping runtime smoke tests

If auth or MCP transport is broken, optimization results will be meaningless.
Run `showcase` or `doctor` first.

### Mistake 4: Treating demo dataset scores as product benchmarks

Built-in demos are smoke tests.
Use your own tasks for meaningful optimization.

## Good Next Steps

1. Run `scm showcase --runner mcp-stdio` to verify local flow
2. Run `scm benchmark --runner mcp-stdio --save-artifact`
3. Build a small dataset from your real MCP tasks
4. Define a metric that reflects real success
5. Run `scm optimize ...` and apply the best candidate to your client
