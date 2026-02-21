#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from supercodemode.engine import run_showcase
from supercodemode.io_utils import save_artifact
from supercodemode.runners import MCPStreamableHTTPCodeModeRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run showcase against Cloudflare MCP streamable-http")
    parser.add_argument("--endpoint", default="https://mcp.cloudflare.com/mcp")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--auth-bearer", default="")
    parser.add_argument("--artifact-dir", default="artifacts")
    parser.add_argument("--save-artifact", action="store_true")
    args = parser.parse_args()

    headers = {}
    if args.auth_bearer:
        headers["Authorization"] = f"Bearer {args.auth_bearer}"

    runner = MCPStreamableHTTPCodeModeRunner(endpoint_url=args.endpoint, timeout_seconds=args.timeout, headers=headers)
    result = run_showcase(runner)

    if args.save_artifact:
        path = save_artifact(result, artifact_dir=args.artifact_dir, prefix="showcase_mcp_cloudflare")
        result = {**result, "artifact_path": path}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
