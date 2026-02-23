# SuperCodeMode

<p align="center">
  <img src="https://raw.githubusercontent.com/SuperagenticAI/supercodemode/main/assets/supercodemode.png" alt="SuperCodeMode logo" width="220">
</p>

SuperCodeMode helps you optimize Code Mode behavior with GEPA and run it on any backend.

Optimize Code Mode with GEPA. Run anywhere.

It helps MCP and HTTP tool users improve quality by tuning client side instruction text and routing policy without tying users to a specific runtime provider.

## What You Need to Bring (Real Usage)

SuperCodeMode is most useful when you already have:

- an MCP server or Code Mode runtime (Cloudflare, local, UTCP, internal)
- a small dataset of real tasks
- a scoring rule (metric) for success
- a client config where you can apply optimized prompt/Code Mode settings

Read `guides/from-demo-to-real-workflow.md` for the practical workflow.

## What This Project Solves

Many tool systems fail because the client logic is weak, even when tools are good.

Typical failures:

- execute tool used too early
- discovery step skipped
- weak execution instructions
- unstable or noisy final answers

SuperCodeMode gives you a repeatable loop to improve these behaviors.

## Who This Is For

- Cloudflare Code Mode MCP users
- MCP users running search and execute style tools
- platform engineers and evaluation teams

## What Is Included

- MCP stdio runner for local workflows
- MCP streamable HTTP runner for direct Cloudflare MCP
- HTTP runner for Cloudflare or bridge endpoints
- local, Docker, and Monty execution backend options in demo MCP server
- doctor checks for setup confidence
- artifacts for run outputs and best candidates
- observability output in JSONL and OTLP modes

## How GEPA Changes Work

This repo demonstrates the GEPA adapter approach where:

- GEPA optimizes client text policy
- runners execute tools on MCP or HTTP runtimes
- transport can switch without rewriting adapter logic

Read `guides/gepa-adapter.md` for the exact behavior and commands.

## What Is Not Included By Default

- automatic server code mutation
- automatic server deploy workflows

## Expected Benefits

- better tool routing quality
- better final answer consistency
- fewer unnecessary tool calls
- easier comparison of baseline vs tuned behavior
- easier debugging with traces and telemetry

## Left Menu Section Guide

Use the left menu in this order:

1. `Getting Started` for install and first run
2. `Examples` for runnable scenarios
3. `CLI and Config` for all flags and environment settings
4. `Operations` for checks, observability, and troubleshooting

## Quick Start

```bash
pip install -e .
scm doctor
scm showcase --runner mcp-http
scm showcase --runner mcp-stdio
```

Cloudflare MCP often requires auth:

```bash
scm showcase --runner mcp-http --auth-bearer "$CODEMODE_TOKEN"
```

## Recommended Next Commands

```bash
scm optimize --runner mcp-stdio --max-metric-calls 10 --save-artifact
scm --obs-backend jsonl --obs-jsonl-path artifacts/obs.jsonl showcase --runner mcp-stdio
```

## Useful Pages

- install: `getting-started/install.md`
- first run: `getting-started/first-run.md`
- examples: `guides/examples.md`
- from demo to real workflow: `guides/from-demo-to-real-workflow.md`
- gepa adapter: `guides/gepa-adapter.md`
- cloudflare http: `guides/cloudflare-http.md`
- cli reference: `reference/cli.md`
- observability: `operations/observability.md`
