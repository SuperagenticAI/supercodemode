#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from supercodemode.io_utils import save_artifact
from supercodemode.mcp_client_demo import run_demo_sync


def main() -> None:
    parser = argparse.ArgumentParser(description="Run direct MCP client demo")
    parser.add_argument("--mcp-command", default=sys.executable)
    parser.add_argument("--mcp-server", default="")
    parser.add_argument("--mcp-server-module", default="supercodemode.servers.demo_mcp_server")
    parser.add_argument("--executor-backend", choices=["local", "docker", "monty"], default="local")
    parser.add_argument("--docker-image", default="python:3.12-alpine")
    parser.add_argument("--artifact-dir", default="artifacts")
    parser.add_argument("--save-artifact", action="store_true")
    args = parser.parse_args()

    server_args = [args.mcp_server] if args.mcp_server else ["-m", args.mcp_server_module]
    server_env = {
        "SCM_EXECUTOR_BACKEND": args.executor_backend,
        "SCM_DOCKER_IMAGE": args.docker_image,
    }
    result = run_demo_sync(command=args.mcp_command, server_args=server_args, server_env=server_env)

    if args.save_artifact:
        path = save_artifact(result, artifact_dir=args.artifact_dir, prefix="mcp_client_demo")
        result = {**result, "artifact_path": path}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
