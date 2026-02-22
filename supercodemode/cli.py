from __future__ import annotations

import argparse
import json
import os
import sys

from .engine import run_benchmark, run_optimize, run_showcase
from .mcp_client_demo import run_demo_sync
from .doctor import format_human_report, run_doctor
from .io_utils import save_artifact, save_summary_artifacts
from .runners import MCPStreamableHTTPCodeModeRunner, HTTPCodeModeRunner, StaticCodeModeRunner, build_default_mcp_stdio_runner

DEFAULT_CLOUDFLARE_MCP_ENDPOINT = "https://mcp.cloudflare.com/mcp"


def _build_runner(args: argparse.Namespace):
    if args.runner == "http":
        if not args.endpoint:
            raise SystemExit("--endpoint is required for --runner http")
        return HTTPCodeModeRunner(endpoint_url=args.endpoint, timeout_seconds=args.timeout)
    if args.runner == "mcp-http":
        endpoint = args.endpoint or DEFAULT_CLOUDFLARE_MCP_ENDPOINT
        headers = {}
        if args.auth_bearer:
            headers["Authorization"] = f"Bearer {args.auth_bearer}"
        return MCPStreamableHTTPCodeModeRunner(
            endpoint_url=endpoint,
            timeout_seconds=args.timeout,
            headers=headers or None,
        )
    if args.runner == "mcp-stdio":
        return build_default_mcp_stdio_runner(
            command=args.mcp_command,
            server_script=args.mcp_server or None,
            server_module=args.mcp_server_module,
            executor_backend=args.executor_backend,
            docker_image=args.docker_image,
        )
    return StaticCodeModeRunner()


def _add_runner_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--runner", choices=["static", "mcp-stdio", "mcp-http", "http"], default="mcp-stdio")
    p.add_argument(
        "--endpoint",
        default="",
        help=(
            "Endpoint URL. For --runner mcp-http defaults to "
            "https://mcp.cloudflare.com/mcp when omitted."
        ),
    )
    p.add_argument("--auth-bearer", default="", help="Optional bearer token for MCP/HTTP endpoint")
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--mcp-command", default=sys.executable)
    p.add_argument("--mcp-server", default="")
    p.add_argument("--mcp-server-module", default="supercodemode.servers.demo_mcp_server")
    p.add_argument("--executor-backend", choices=["local", "docker", "monty"], default="local")
    p.add_argument("--docker-image", default="python:3.12-alpine")
    p.add_argument("--artifact-dir", default="artifacts")
    p.add_argument("--save-artifact", action="store_true")


def _set_obs_command_context(args: argparse.Namespace) -> None:
    os.environ["SCM_OBS_COMMAND"] = str(args.command)
    if hasattr(args, "runner"):
        os.environ["SCM_OBS_RUNNER"] = str(getattr(args, "runner"))
    elif args.command == "mcp-client":
        os.environ["SCM_OBS_RUNNER"] = "mcp-stdio"
    if hasattr(args, "executor_backend"):
        os.environ["SCM_OBS_EXECUTOR_BACKEND"] = str(getattr(args, "executor_backend"))

    # Default dataset label for built-in demos/benchmarks unless user already set one.
    if not os.environ.get("SCM_OBS_DATASET_NAME") and args.command in {"showcase", "optimize", "benchmark"}:
        os.environ["SCM_OBS_DATASET_NAME"] = "two_tool_dataset"


def main() -> None:
    parser = argparse.ArgumentParser(prog="scm", description="Super Code Mode CLI")
    parser.add_argument(
        "--obs-backend",
        choices=["none", "jsonl", "otlp", "logfire", "mlflow", "langsmith", "langfuse"],
        default=None,
    )
    parser.add_argument("--obs-jsonl-path", default=None)
    parser.add_argument("--obs-otlp-endpoint", default=None)
    parser.add_argument("--run-id", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    p_show = sub.add_parser("showcase", help="Run baseline vs tuned comparison")
    _add_runner_args(p_show)

    p_opt = sub.add_parser("optimize", help="Run GEPA optimization")
    _add_runner_args(p_opt)
    p_opt.add_argument("--max-metric-calls", type=int, default=20)
    p_opt.add_argument("--seed", type=int, default=0)

    p_bench = sub.add_parser("benchmark", help="Compare tool-call vs Code Mode strategy profiles")
    _add_runner_args(p_bench)

    p_mcp = sub.add_parser("mcp-client", help="Run direct MCP client demo")
    p_mcp.add_argument("--mcp-command", default=sys.executable)
    p_mcp.add_argument("--mcp-server", default="")
    p_mcp.add_argument("--mcp-server-module", default="supercodemode.servers.demo_mcp_server")
    p_mcp.add_argument("--executor-backend", choices=["local", "docker", "monty"], default="local")
    p_mcp.add_argument("--docker-image", default="python:3.12-alpine")
    p_mcp.add_argument("--artifact-dir", default="artifacts")
    p_mcp.add_argument("--save-artifact", action="store_true")

    p_doc = sub.add_parser("doctor", help="Run environment and runtime preflight checks")
    p_doc.add_argument("--mcp-command", default=sys.executable)
    p_doc.add_argument("--mcp-server", default="")
    p_doc.add_argument("--mcp-server-module", default="supercodemode.servers.demo_mcp_server")
    p_doc.add_argument("--executor-backend", choices=["local", "docker", "monty"], default="local")
    p_doc.add_argument("--docker-image", default="python:3.12-alpine")
    p_doc.add_argument("--no-docker-run", action="store_true")
    p_doc.add_argument("--no-mcp-roundtrip", action="store_true")
    p_doc.add_argument("--json", action="store_true")
    p_doc.add_argument("--strict", action="store_true")

    args = parser.parse_args()

    if args.obs_backend is not None:
        os.environ["SCM_OBS_BACKEND"] = args.obs_backend
    if args.obs_jsonl_path is not None:
        os.environ["SCM_OBS_JSONL_PATH"] = args.obs_jsonl_path
    if args.obs_otlp_endpoint is not None:
        os.environ["SCM_OBS_OTLP_ENDPOINT"] = args.obs_otlp_endpoint
    if args.run_id is not None:
        os.environ["SCM_RUN_ID"] = args.run_id
    _set_obs_command_context(args)

    if args.command == "showcase":
        runner = _build_runner(args)
        result = run_showcase(runner)
        if args.save_artifact:
            path = save_artifact(result, artifact_dir=args.artifact_dir, prefix="scm_showcase")
            summary_paths = save_summary_artifacts(result, artifact_dir=args.artifact_dir, prefix="scm_showcase")
            result = {**result, "artifact_path": path, **summary_paths}
        print(json.dumps(result, indent=2))
        return

    if args.command == "optimize":
        runner = _build_runner(args)
        result = run_optimize(runner, max_metric_calls=args.max_metric_calls, seed=args.seed)
        if args.save_artifact:
            path = save_artifact(result, artifact_dir=args.artifact_dir, prefix="scm_optimize")
            summary_paths = save_summary_artifacts(result, artifact_dir=args.artifact_dir, prefix="scm_optimize")
            result = {**result, "artifact_path": path, **summary_paths}
        print(json.dumps(result, indent=2))
        return

    if args.command == "benchmark":
        runner = _build_runner(args)
        result = run_benchmark(runner)
        if args.save_artifact:
            path = save_artifact(result, artifact_dir=args.artifact_dir, prefix="scm_benchmark")
            summary_paths = save_summary_artifacts(result, artifact_dir=args.artifact_dir, prefix="scm_benchmark")
            result = {**result, "artifact_path": path, **summary_paths}
        print(json.dumps(result, indent=2))
        return

    if args.command == "mcp-client":
        server_args = [args.mcp_server] if args.mcp_server else ["-m", args.mcp_server_module]
        server_env = {
            "SCM_EXECUTOR_BACKEND": args.executor_backend,
            "SCM_DOCKER_IMAGE": args.docker_image,
        }
        result = run_demo_sync(command=args.mcp_command, server_args=server_args, server_env=server_env)
        if args.save_artifact:
            path = save_artifact(result, artifact_dir=args.artifact_dir, prefix="scm_mcp_client")
            result = {**result, "artifact_path": path}
        print(json.dumps(result, indent=2))
        return

    if args.command == "doctor":
        report = run_doctor(
            mcp_command=args.mcp_command,
            mcp_server=args.mcp_server,
            mcp_server_module=args.mcp_server_module,
            executor_backend=args.executor_backend,
            docker_image=args.docker_image,
            check_docker_run=not args.no_docker_run,
            check_mcp_roundtrip=not args.no_mcp_roundtrip,
        )
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(format_human_report(report))

        fail = int(report.get("summary", {}).get("fail", 0))
        warn = int(report.get("summary", {}).get("warn", 0))
        if args.strict and (fail > 0 or warn > 0):
            raise SystemExit(1)
        return


if __name__ == "__main__":
    main()
