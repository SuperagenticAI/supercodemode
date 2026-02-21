#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from supercodemode.engine import run_showcase
from supercodemode.io_utils import save_artifact
from supercodemode.runners import build_default_mcp_stdio_runner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run showcase with local MCP stdio runner")
    parser.add_argument("--mcp-command", default=sys.executable)
    parser.add_argument("--mcp-server", default="")
    parser.add_argument("--mcp-server-module", default="supercodemode.servers.demo_mcp_server")
    parser.add_argument("--executor-backend", choices=["local", "docker"], default="local")
    parser.add_argument("--docker-image", default="python:3.12-alpine")
    parser.add_argument("--artifact-dir", default="artifacts")
    parser.add_argument("--save-artifact", action="store_true")
    args = parser.parse_args()

    runner = build_default_mcp_stdio_runner(
        command=args.mcp_command,
        server_script=args.mcp_server or None,
        server_module=args.mcp_server_module,
        executor_backend=args.executor_backend,
        docker_image=args.docker_image,
    )
    result = run_showcase(runner)
    if args.save_artifact:
        path = save_artifact(result, artifact_dir=args.artifact_dir, prefix="showcase_mcp_stdio")
        result = {**result, "artifact_path": path}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
