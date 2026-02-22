# Super Code Mode (`supercodemode`)

<p align="center">
  <img src="https://raw.githubusercontent.com/SuperagenticAI/supercodemode/main/assets/supercodemode.png" alt="SuperCodeMode" width="220">
</p>

[![PyPI version](https://img.shields.io/pypi/v/supercodemode.svg)](https://pypi.org/project/supercodemode/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/supercodemode/)
[![License](https://img.shields.io/pypi/l/supercodemode.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/SuperagenticAI/supercodemode/ci.yml?branch=main&label=ci)](https://github.com/SuperagenticAI/supercodemode/actions/workflows/ci.yml)
[![Docs Deploy](https://img.shields.io/github/actions/workflow/status/SuperagenticAI/supercodemode/deploy-docs.yml?branch=main&label=docs-deploy)](https://github.com/SuperagenticAI/supercodemode/actions/workflows/deploy-docs.yml)
[![Docs](https://img.shields.io/badge/docs-live-0EA5E9)](https://superagenticai.github.io/supercodemode/)
[![GEPA](https://img.shields.io/badge/GEPA-docs-111827)](https://gepa-ai.github.io/gepa/)

SuperCodeMode is a Python CLI and demo harness for optimizing Code Mode style
client behavior in MCP workflows with GEPA.

It focuses on improving the text and routing policy around a small tool surface
(typically discovery + execution), so agents make better tool choices and
produce more reliable results.

## 🔗 Quick Links

- 📚 Docs: https://superagenticai.github.io/supercodemode/
- 📦 PyPI: https://pypi.org/project/supercodemode/
- 🧠 GEPA docs: https://gepa-ai.github.io/gepa/
- ☁️ Cloudflare Code Mode MCP: https://blog.cloudflare.com/code-mode-mcp/
- 🧰 UTCP Code Mode: https://github.com/universal-tool-calling-protocol/code-mode

## ✨ What This Project Solves

Many tool systems fail because the client logic is weak even when the tools are
good.

Typical failures:

- execution tool is used too early
- discovery step is skipped
- execution instructions are vague
- final answers are noisy or inconsistent

SuperCodeMode gives you a repeatable GEPA-driven optimization loop to improve
those behaviors.

## 👥 Who This Is For

- Cloudflare Code Mode MCP users
- MCP users running discovery + execution style tool patterns
- platform engineers and evaluation teams
- teams experimenting with Code Mode style agent behavior before changing server code

## ✅ What Is Included

- MCP stdio runner for local workflows
- MCP streamable HTTP runner for direct Cloudflare MCP
- HTTP bridge runner for custom runtime bridges
- local, Docker, and Monty execution backends in the demo MCP server
- `scm doctor` preflight checks
- artifact saving for showcase/optimization runs
- observability output (JSONL and OTLP)

## 🧩 What "Code Mode" Means Here

Code Mode here means a code-first MCP orchestration pattern where the model uses
a small tool surface and generates code for multi-step work.

Background:

- Cloudflare Code Mode MCP blog: https://blog.cloudflare.com/code-mode-mcp/
- UTCP Code Mode implementation: https://github.com/universal-tool-calling-protocol/code-mode

## 📦 Install

From PyPI:

```bash
pip install supercodemode
```

With `uv` (tool install, recommended for CLI usage):

```bash
uv tool install supercodemode
```

With `uv` (current environment):

```bash
uv pip install supercodemode
```

Optional Monty executor backend:

```bash
pip install "supercodemode[monty]"
```

With `uv`:

```bash
uv pip install "supercodemode[monty]"
```

Optional observability integrations (LangSmith, Logfire, MLflow, Langfuse):

```bash
pip install "supercodemode[observability]"
```

With `uv`:

```bash
uv pip install "supercodemode[observability]"
```

Then verify install:

```bash
scm --help
```

For local development:

```bash
pip install -e .
```

With `uv`:

```bash
uv pip install -e .
```

## ⚡ Quick Start

Check your environment:

```bash
scm doctor
```

Run a Cloudflare MCP showcase (defaults to `https://mcp.cloudflare.com/mcp`):

```bash
scm showcase --runner mcp-http
```

Run a local MCP showcase (demo server over stdio):

```bash
scm showcase --runner mcp-stdio
```

If Cloudflare MCP requires auth in your environment:

```bash
scm showcase --runner mcp-http --auth-bearer "$CODEMODE_TOKEN"
```

## 🎯 What You Can Optimize

SuperCodeMode uses GEPA to optimize Code Mode client-side text such as:

- system prompt text
- Code Mode description / routing guidance
- tool alias mappings
- tool description overrides

This improves client behavior without requiring server/runtime code changes.

## 🧠 How It Works (High Level)

SuperCodeMode demonstrates a GEPA-centric adapter approach where:

1. GEPA optimizes client text policy
2. runners execute tools on MCP or HTTP runtimes
3. the same optimization logic can be reused across local and remote transports

This keeps GEPA optimization logic separate from runtime transport details.

## 🛠️ Common Commands

### Preflight

```bash
scm doctor
scm doctor --json
scm doctor --strict
```

### Showcase runs (baseline vs tuned)

```bash
scm showcase --runner mcp-http
scm showcase --runner mcp-stdio
scm showcase --runner mcp-stdio --executor-backend monty
scm showcase --runner mcp-stdio --executor-backend docker
scm showcase --runner http --endpoint http://localhost:8080/run-codemode
```

Note: `showcase` is an active CLI command. The removed `showcase/` directory was
an older repo layout, not the `scm showcase` command.

### Optimization runs

```bash
scm optimize --runner mcp-http --max-metric-calls 10
scm optimize --runner mcp-stdio --max-metric-calls 10
scm optimize --runner mcp-stdio --executor-backend monty --max-metric-calls 10
scm optimize --runner mcp-stdio --executor-backend docker --max-metric-calls 10
scm optimize --runner http --endpoint http://localhost:8080/run-codemode --max-metric-calls 10
```

Save artifacts:

```bash
scm showcase --runner mcp-stdio --save-artifact
scm optimize --runner mcp-http --max-metric-calls 10 --save-artifact
```

When `--save-artifact` is enabled, SuperCodeMode also writes compact summary files:

- showcase: `comparison_summary`, `baseline_run_summary`, `tuned_run_summary`
- optimize: `run_summary`
- benchmark: `benchmark_summary` + per-variant `run_summary`

### Direct MCP connectivity checks

```bash
scm mcp-client
scm mcp-client --executor-backend monty
scm mcp-client --executor-backend docker
```

### Strategy benchmark (tool-call vs Code Mode)

```bash
scm benchmark --runner mcp-stdio
scm benchmark --runner mcp-stdio --executor-backend monty
scm benchmark --runner mcp-http
```

This compares three policy profiles on the same runner/dataset:

- `tool_call` (naive execution-first policy)
- `codemode_baseline`
- `codemode_optimized`

## 🧪 Examples

All runnable examples are under `examples/`.

Recommended starting points:

```bash
python examples/showcase_mcp_cloudflare.py
python examples/showcase_mcp_stdio.py
python examples/optimize_mcp_cloudflare.py --max-metric-calls 10
python examples/optimize_mcp_stdio.py --max-metric-calls 10
```

Real LLM optimization demo (Gemini, low-cost settings):

```bash
export GOOGLE_API_KEY=your_key_here
python examples/optimize_gemini_flash.py --max-metric-calls 4
```

Full example list:

- Examples README (GitHub): https://github.com/SuperagenticAI/supercodemode/blob/main/examples/README.md
- Examples guide (Docs): https://superagenticai.github.io/supercodemode/guides/examples/

## ☁️ Cloudflare MCP Notes

- `mcp-http` runner defaults to `https://mcp.cloudflare.com/mcp`
- Cloudflare MCP may require auth for your usage:

```bash
scm showcase --runner mcp-http --auth-bearer "$CODEMODE_TOKEN"
```

- Demo scoring can show `0.5` even when integration works if Cloudflare returns
  structured JSON for `search` and the metric expects a literal keyword match

In that case, the primary success signal is:

- case 1 selects `search`
- case 2 selects `execute`
- case 2 returns `42`

## 🧱 Local, Docker, and Monty Execution

Use Monty for a Python-native sandboxed execution path in demo MCP flows:

```bash
scm showcase --runner mcp-stdio --executor-backend monty
```

Requirements:

- install `pydantic-monty` (or `pip install "supercodemode[monty]"`)

Use Docker for safer local code execution in demo MCP flows:

```bash
scm showcase --runner mcp-stdio --executor-backend docker
```

Requirements:

- Docker daemon running
- your user can run `docker run`

## 📈 Observability

JSONL:

```bash
scm --obs-backend jsonl --obs-jsonl-path artifacts/obs.jsonl showcase --runner mcp-stdio
```

OTLP:

```bash
scm --obs-backend otlp --obs-otlp-endpoint http://localhost:4318/v1/traces showcase --runner mcp-stdio
```

Optional SDK backends (same event schema, best-effort adapters):

```bash
scm --obs-backend logfire showcase --runner mcp-stdio
scm --obs-backend mlflow showcase --runner mcp-stdio
scm --obs-backend langsmith showcase --runner mcp-stdio
scm --obs-backend langfuse showcase --runner mcp-stdio
```

Install optional integrations:

```bash
pip install "supercodemode[observability]"
```

Environment variables (alternative to CLI flags):

- `SCM_OBS_BACKEND=none|jsonl|otlp|logfire|mlflow|langsmith|langfuse`
- `SCM_OBS_JSONL_PATH=artifacts/obs.jsonl`
- `SCM_OBS_OTLP_ENDPOINT=http://localhost:4318/v1/traces`
- `SCM_RUN_ID=demo-run-001`
- `SCM_OBS_DATASET_NAME=two_tool_dataset` (optional)
- `SCM_OBS_TAGS_JSON='{"env":"dev","team":"research"}'` (optional)

Event payloads include GEPA/Code Mode run fields such as selected tool, tool call
count, score, and error state, and the saved summary artifacts provide compact
rollups for comparisons and quick benchmarking.

CLI commands also stamp command context into events (for example `cli_command`,
`cli_runner`, and `cli_executor_backend`) to make JSONL/OTLP filtering easier.

Benchmark and run summaries also include:

- runtime capability hints (for example local vs docker vs monty constraints)
- error taxonomy rollups (`error_categories`) for quick failure analysis

## 🧠 Relationship to GEPA

This repo is the end-to-end GEPA optimization demo and experimentation harness
for the GEPA Code Mode adapter work (examples, CLI, docs, local/docker/monty
execution, observability).

GEPA docs (main site): [https://gepa-ai.github.io/gepa/](https://gepa-ai.github.io/gepa/)

GEPA PR (status may change):

- https://github.com/gepa-ai/gepa/pull/225

Whether the adapter lands in GEPA mainline now or later, SuperCodeMode can be
used directly for GEPA-based optimization of Code Mode behavior.

## 🚫 What Is Not Included by Default

- automatic server code mutation
- automatic deploy pipelines for MCP servers
- provider-specific server-side optimization logic

This project is focused on client-side behavior optimization and runnable demos.

## 📚 Documentation

- [Docs homepage](https://superagenticai.github.io/supercodemode/)
- [Getting started](https://superagenticai.github.io/supercodemode/getting-started/)
- [Examples and guides](https://superagenticai.github.io/supercodemode/guides/)
- [CLI reference](https://superagenticai.github.io/supercodemode/reference/cli/)
- [Operations](https://superagenticai.github.io/supercodemode/operations/)

Run docs locally:

```bash
mkdocs serve
```

Build docs:

```bash
mkdocs build
```

## 🧰 Development Notes

- `scm` uses installed `gepa` and `mcp` from your environment
- a vendored GEPA contribution snapshot exists in `vendor/gepa_new_files`
- refresh vendor snapshot with:
  - `GEPA_SOURCE_DIR=/path/to/gepa ./scripts/sync_gepa_vendor.sh`

## 🚀 Release (Maintainers)

Build and publish with `uv`:

```bash
uv build
uv publish
```

If publishing to PyPI, make sure your credentials/token are configured for `uv publish`.
