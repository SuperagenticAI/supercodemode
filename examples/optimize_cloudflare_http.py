#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from supercodemode.engine import run_optimize
from supercodemode.io_utils import save_artifact
from supercodemode.runners import HTTPCodeModeRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run optimization against Cloudflare/HTTP Code Mode endpoint")
    parser.add_argument("--endpoint", required=True, help="Code Mode runtime endpoint URL")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--max-metric-calls", type=int, default=10, help="Small demo budget")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--artifact-dir", default="artifacts")
    parser.add_argument("--save-artifact", action="store_true")
    args = parser.parse_args()

    runner = HTTPCodeModeRunner(endpoint_url=args.endpoint, timeout_seconds=args.timeout)
    result = run_optimize(runner, max_metric_calls=args.max_metric_calls, seed=args.seed)

    if args.save_artifact:
        path = save_artifact(result, artifact_dir=args.artifact_dir, prefix="optimize_cloudflare_http")
        result = {**result, "artifact_path": path}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
