from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def save_artifact(payload: dict[str, Any], *, artifact_dir: str, prefix: str) -> str:
    root = Path(artifact_dir)
    root.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{prefix}_{ts}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)


def save_summary_artifacts(payload: dict[str, Any], *, artifact_dir: str, prefix: str) -> dict[str, str]:
    root = Path(artifact_dir)
    root.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    paths: dict[str, str] = {}

    # Common single-run summary (optimize output and per-eval outputs can expose this key).
    run_summary = payload.get("run_summary")
    if isinstance(run_summary, dict):
        p = root / f"{prefix}_run_summary_{ts}.json"
        p.write_text(json.dumps(run_summary, indent=2), encoding="utf-8")
        paths["run_summary_path"] = str(p)

    # Showcase comparison summary.
    comparison_summary = payload.get("comparison_summary")
    if isinstance(comparison_summary, dict):
        p = root / f"{prefix}_comparison_summary_{ts}.json"
        p.write_text(json.dumps(comparison_summary, indent=2), encoding="utf-8")
        paths["comparison_summary_path"] = str(p)

    # Also expose nested summaries when the root payload is a showcase result.
    baseline = payload.get("baseline")
    if isinstance(baseline, dict) and isinstance(baseline.get("run_summary"), dict):
        p = root / f"{prefix}_baseline_run_summary_{ts}.json"
        p.write_text(json.dumps(baseline["run_summary"], indent=2), encoding="utf-8")
        paths["baseline_run_summary_path"] = str(p)

    tuned = payload.get("tuned")
    if isinstance(tuned, dict) and isinstance(tuned.get("run_summary"), dict):
        p = root / f"{prefix}_tuned_run_summary_{ts}.json"
        p.write_text(json.dumps(tuned["run_summary"], indent=2), encoding="utf-8")
        paths["tuned_run_summary_path"] = str(p)

    benchmark_summary = payload.get("benchmark_summary")
    if isinstance(benchmark_summary, dict):
        p = root / f"{prefix}_benchmark_summary_{ts}.json"
        p.write_text(json.dumps(benchmark_summary, indent=2), encoding="utf-8")
        paths["benchmark_summary_path"] = str(p)

    variants = payload.get("variants")
    if isinstance(variants, dict):
        for name, variant in variants.items():
            if not isinstance(name, str) or not isinstance(variant, dict):
                continue
            run_summary = variant.get("run_summary")
            if not isinstance(run_summary, dict):
                continue
            p = root / f"{prefix}_{name}_run_summary_{ts}.json"
            p.write_text(json.dumps(run_summary, indent=2), encoding="utf-8")
            paths[f"{name}_run_summary_path"] = str(p)

    return paths
