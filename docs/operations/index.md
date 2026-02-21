# Operations

This section is for production readiness and debugging.

## Core Operations Workflow

1. run doctor checks
2. run showcase or optimization
3. inspect artifacts and telemetry
4. troubleshoot failures quickly

## Pages

- [Doctor](doctor.md)
- [Observability](observability.md)
- [Troubleshooting](troubleshooting.md)

## Recommended Routine

```bash
scm doctor
scm --obs-backend jsonl --obs-jsonl-path artifacts/obs.jsonl showcase --runner mcp-stdio --save-artifact
```
