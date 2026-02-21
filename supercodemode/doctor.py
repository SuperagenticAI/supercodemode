from __future__ import annotations

import importlib
import json
import shutil
import subprocess
import sys
from typing import Any

from .mcp_client_demo import run_demo_sync
from .observability import emit_event


def run_doctor(
    *,
    mcp_command: str,
    mcp_server: str,
    mcp_server_module: str,
    docker_image: str,
    check_docker_run: bool,
    check_mcp_roundtrip: bool,
) -> dict[str, Any]:
    emit_event("doctor.start")
    checks: list[dict[str, str]] = []

    _add(checks, "python", "pass", f"python={sys.version.split()[0]}")

    _check_import(checks, "gepa")
    _check_import(checks, "mcp")

    docker_ok = _check_docker_info(checks)

    if docker_ok and check_docker_run:
        _check_docker_run(checks, docker_image)

    if check_mcp_roundtrip:
        server_args = [mcp_server] if mcp_server else ["-m", mcp_server_module]
        _check_mcp_roundtrip(checks, mcp_command=mcp_command, server_args=server_args)

    summary = _summarize(checks)
    report = {
        "summary": summary,
        "checks": checks,
    }
    emit_event("doctor.end", pass_count=summary["pass"], warn_count=summary["warn"], fail_count=summary["fail"])
    return report


def _add(checks: list[dict[str, str]], name: str, status: str, detail: str) -> None:
    checks.append({"name": name, "status": status, "detail": detail})


def _check_import(checks: list[dict[str, str]], module_name: str) -> None:
    try:
        mod = importlib.import_module(module_name)
        version = getattr(mod, "__version__", "unknown")
        _add(checks, f"import:{module_name}", "pass", f"version={version}")
    except Exception as exc:
        _add(checks, f"import:{module_name}", "fail", str(exc))


def _check_docker_info(checks: list[dict[str, str]]) -> bool:
    if shutil.which("docker") is None:
        _add(checks, "docker:cli", "fail", "docker not found in PATH")
        return False

    try:
        completed = subprocess.run(
            ["docker", "info"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as exc:
        _add(checks, "docker:info", "fail", str(exc))
        return False

    if completed.returncode == 0:
        _add(checks, "docker:info", "pass", "daemon reachable")
        return True

    detail = (completed.stderr or completed.stdout or "docker info failed").strip()
    _add(checks, "docker:info", "fail", detail)
    return False


def _check_docker_run(checks: list[dict[str, str]], image: str) -> None:
    try:
        completed = subprocess.run(
            ["docker", "run", "--rm", image, "python", "-c", "print(17+25)"],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except Exception as exc:
        _add(checks, "docker:run", "fail", str(exc))
        return

    if completed.returncode == 0 and (completed.stdout or "").strip().endswith("42"):
        _add(checks, "docker:run", "pass", f"image={image} output=42")
        return

    detail = (completed.stderr or completed.stdout or "docker run failed").strip()
    _add(checks, "docker:run", "fail", detail)


def _check_mcp_roundtrip(checks: list[dict[str, str]], *, mcp_command: str, server_args: list[str]) -> None:
    try:
        result = run_demo_sync(
            command=mcp_command,
            server_args=server_args,
            server_env={"SCM_EXECUTOR_BACKEND": "local", "SCM_DOCKER_IMAGE": "python:3.12-alpine"},
        )
    except Exception as exc:
        _add(checks, "mcp:roundtrip", "fail", str(exc))
        return

    out = result.get("call_tool_chain", "")
    if str(out).strip() == "42":
        _add(checks, "mcp:roundtrip", "pass", "call_tool_chain returned 42")
    else:
        _add(checks, "mcp:roundtrip", "warn", f"unexpected call_tool_chain={out}")


def _summarize(checks: list[dict[str, str]]) -> dict[str, int]:
    counts = {"pass": 0, "warn": 0, "fail": 0}
    for c in checks:
        status = c.get("status", "")
        if status in counts:
            counts[status] += 1
    return counts


def format_human_report(report: dict[str, Any]) -> str:
    lines = []
    summary = report.get("summary", {})
    lines.append(
        f"doctor summary: pass={summary.get('pass', 0)} warn={summary.get('warn', 0)} fail={summary.get('fail', 0)}"
    )
    for check in report.get("checks", []):
        lines.append(f"- [{check['status'].upper()}] {check['name']}: {check['detail']}")
    return "\n".join(lines)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run SuperCodeMode environment checks")
    parser.add_argument("--mcp-command", default=sys.executable)
    parser.add_argument("--mcp-server", default="")
    parser.add_argument("--mcp-server-module", default="supercodemode.servers.demo_mcp_server")
    parser.add_argument("--docker-image", default="python:3.12-alpine")
    parser.add_argument("--no-docker-run", action="store_true")
    parser.add_argument("--no-mcp-roundtrip", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="exit non-zero on any warn/fail")
    args = parser.parse_args()

    report = run_doctor(
        mcp_command=args.mcp_command,
        mcp_server=args.mcp_server,
        mcp_server_module=args.mcp_server_module,
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


if __name__ == "__main__":
    main()
