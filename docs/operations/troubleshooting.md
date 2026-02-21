# Troubleshooting

## Docker Permission Error

Symptom:

- permission denied for Docker socket

Fix:

```bash
docker info
docker run --rm python:3.12-alpine python -c "print(17+25)"
```

Ensure your shell user can access Docker daemon.

## HTTP Runner Connection Error

Symptom:

- `urlopen error` or connection refused

Fix:

- verify endpoint URL and port
- verify server accepts expected request and response contract
- test endpoint with a simple curl before optimization run

## No Improvement In Optimization

Symptom:

- best candidate remains baseline

Fix:

- increase `--max-metric-calls`
- use focused dataset templates
- inspect artifacts and traces to see failure pattern

## Gemini Demo Fails

Symptom:

- missing API key error

Fix:

```bash
export GOOGLE_API_KEY=your_key_here
```

## GEPA API Version Mismatch

Symptom:

- argument mismatch errors

Fix:

- run `scm doctor`
- reinstall latest `gepa`
- use provided fallback adapter flow already in this repo
