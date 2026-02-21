#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys

import gepa

from supercodemode.common import baseline_candidate, build_two_tool_dataset, contains_reference_metric
from supercodemode.io_utils import save_artifact
from supercodemode.runners import build_default_mcp_stdio_runner


def _build_adapter(runner):
    try:
        from gepa.adapters.code_mode_adapter import CodeModeAdapter
    except Exception:
        from supercodemode.gepa_compat import CodeModeAdapter
    return CodeModeAdapter(runner=runner, metric_fn=contains_reference_metric)


def main() -> None:
    parser = argparse.ArgumentParser(description="Small GEPA optimization demo using Gemini 2.5 Flash")
    parser.add_argument(
        "--task-lm",
        default="gemini/gemini-2.5-flash",
        help="Ignored when adapter is provided (kept only for compatibility/visibility).",
    )
    parser.add_argument("--reflection-lm", default="gemini/gemini-2.5-flash")
    parser.add_argument("--max-metric-calls", type=int, default=8, help="Keep small for low-cost demo")
    parser.add_argument("--seed", type=int, default=0)

    parser.add_argument("--mcp-command", default=sys.executable)
    parser.add_argument("--mcp-server", default="")
    parser.add_argument("--mcp-server-module", default="supercodemode.servers.demo_mcp_server")
    parser.add_argument("--executor-backend", choices=["local", "docker"], default="local")
    parser.add_argument("--docker-image", default="python:3.12-alpine")

    parser.add_argument("--artifact-dir", default="artifacts")
    parser.add_argument("--save-artifact", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not os.environ.get("GOOGLE_API_KEY"):
        raise SystemExit("GOOGLE_API_KEY is required for Gemini models")

    runner = build_default_mcp_stdio_runner(
        command=args.mcp_command,
        server_script=args.mcp_server or None,
        server_module=args.mcp_server_module,
        executor_backend=args.executor_backend,
        docker_image=args.docker_image,
    )
    adapter = _build_adapter(runner)

    dataset = build_two_tool_dataset()

    optimize_kwargs = {
        "seed_candidate": baseline_candidate(),
        "trainset": dataset,
        "valset": dataset,
        "adapter": adapter,
        "task_lm": None,
        "reflection_lm": args.reflection_lm,
        "max_metric_calls": args.max_metric_calls,
        "seed": args.seed,
        "display_progress_bar": True,
        "raise_on_exception": True,
        "reflection_minibatch_size": 2,
    }

    result = gepa.optimize(**optimize_kwargs)

    payload = {
        "best_idx": result.best_idx,
        "best_score": result.val_aggregate_scores[result.best_idx],
        "best_candidate": result.best_candidate,
    }

    if args.save_artifact:
        path = save_artifact(payload, artifact_dir=args.artifact_dir, prefix="optimize_gemini_flash")
        payload = {**payload, "artifact_path": path}

    if args.json:
        print(json.dumps(payload, indent=2))
        return

    print("best_idx:", payload["best_idx"])
    print("best_score:", payload["best_score"])
    print("best_candidate:")
    for k, v in payload["best_candidate"].items():
        print(f"- {k}: {v}")
    if "artifact_path" in payload:
        print("artifact_path:", payload["artifact_path"])


if __name__ == "__main__":
    main()
