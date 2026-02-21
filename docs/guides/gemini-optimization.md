# Gemini Optimization Guide

This guide runs real GEPA reflection optimization with Gemini Flash using small budget.

## Set API Key

```bash
export GOOGLE_API_KEY=your_key_here
```

## Run Low Cost Demo

```bash
python examples/optimize_gemini_flash.py --max-metric-calls 4
```

## Docker Backend (Optional)

```bash
python examples/optimize_gemini_flash.py --executor-backend docker --max-metric-calls 4
```

## Important Note

In adapter mode with current GEPA API:

- `task_lm` is not used
- `reflection_lm` drives optimization

This is expected behavior.

## Increase Quality If Needed

```bash
python examples/optimize_gemini_flash.py --max-metric-calls 12
```

Higher budgets can find better candidates but cost more.
