# Code Mode Adapter Examples

## 1) Minimal optimization example

```bash
python src/gepa/examples/code_mode_adapter/code_mode_optimization_example.py
```

Shows the smallest end-to-end adapter flow with a deterministic demo runner.

## 2) Two-tool showcase (Cloudflare/UTCP style)

```bash
python src/gepa/examples/code_mode_adapter/code_mode_two_tool_showcase.py
```

Demonstrates the `search_tools` + `call_tool_chain` pattern and optional
candidate fields:

- `tool_alias_map`
- `tool_description_overrides`

## Adapting to real runtimes

Replace the static runner with `HTTPCodeModeRunner` and point it to your
runtime bridge endpoint (Cloudflare worker, UTCP local service, Node executor,
etc.).
