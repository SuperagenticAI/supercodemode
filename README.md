# Super Code Mode (`supercodemode`)

Python implementation of Code Mode optimization with:

- MCP client support for local stdio MCP servers (including UTCP-style servers)
- HTTP runtime support for Cloudflare/UTCP bridge endpoints
- GEPA integration for optimizing Code Mode prompt/tool descriptions

## Install (editable)

```bash
pip install -e .
```

Dependencies are intentionally unpinned (`gepa`, `mcp`) to track latest releases.

## CLI

```bash
scm --help
```

Common commands:

```bash
scm doctor
scm showcase --runner mcp-stdio
scm showcase --runner mcp-stdio --executor-backend docker
scm showcase --runner http --endpoint http://localhost:8080/run-codemode
scm optimize --runner mcp-stdio
scm optimize --runner mcp-stdio --executor-backend docker
scm optimize --runner http --endpoint http://localhost:8080/run-codemode
scm mcp-client
scm mcp-client --executor-backend docker
```

Docker backend requirements:

- Docker daemon running and accessible by current user
- Ability to run `docker run` from your shell

Preflight checks:

```bash
scm doctor
scm doctor --json
scm doctor --strict
```

Observability (vendor-neutral):

```bash
scm --obs-backend jsonl --obs-jsonl-path artifacts/obs.jsonl showcase --runner mcp-stdio
scm --obs-backend otlp --obs-otlp-endpoint http://localhost:4318/v1/traces showcase --runner mcp-stdio
```

Environment variables (alternative to CLI flags):

- `SCM_OBS_BACKEND=none|jsonl|otlp`
- `SCM_OBS_JSONL_PATH=artifacts/obs.jsonl`
- `SCM_OBS_OTLP_ENDPOINT=http://localhost:4318/v1/traces`
- `SCM_RUN_ID=demo-run-001`

## Examples

User-facing runnable examples are in `examples/`.

Start here:

```bash
python examples/showcase_mcp_stdio.py
```

Cloudflare/HTTP optimization example:

```bash
python examples/optimize_cloudflare_http.py --endpoint http://localhost:8080/run-codemode
```

See full list:

```bash
cat examples/README.md
```

Real Gemini optimization demo (low-cost settings):

```bash
export GOOGLE_API_KEY=your_key_here
python examples/optimize_gemini_flash.py --max-metric-calls 8
```

## Notes

- By default, `scm` uses installed `gepa`/`mcp` from your environment.
- Vendored GEPA contribution snapshot is in `vendor/gepa_new_files` and can be refreshed with:
  - `GEPA_SOURCE_DIR=/path/to/gepa ./scripts/sync_gepa_vendor.sh`

## Docs

- homepage: `docs/index.md`
- getting started: `docs/getting-started/`
- examples and guides: `docs/guides/`
- cli reference: `docs/reference/`
- operations: `docs/operations/`

Run docs locally:

```bash
mkdocs serve
```
