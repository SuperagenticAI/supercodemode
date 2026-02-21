from __future__ import annotations

import os

from supercodemode.env import bootstrap_reference_paths
from supercodemode.executors import build_executor

bootstrap_reference_paths()

try:
    from mcp.server.mcpserver import MCPServer
except Exception:  # pragma: no cover
    from mcp.server.fastmcp import FastMCP as MCPServer  # type: ignore

mcp = MCPServer("SuperCodeMode Demo MCP Server")
_EXECUTOR_BACKEND = os.environ.get("SCM_EXECUTOR_BACKEND", "local")
_DOCKER_IMAGE = os.environ.get("SCM_DOCKER_IMAGE", "python:3.12-alpine")
_EXECUTOR = build_executor(_EXECUTOR_BACKEND, docker_image=_DOCKER_IMAGE)


@mcp.tool()
def search_tools(task_description: str = "") -> str:
    _ = task_description
    return f"Available tools: search_tools, call_tool_chain (executor={_EXECUTOR.backend})"


@mcp.tool()
def findTools(task_description: str = "") -> str:
    _ = task_description
    return f"Available tools: findTools, runPlan (executor={_EXECUTOR.backend})"


@mcp.tool()
def call_tool_chain(code: str) -> str:
    result = _EXECUTOR.execute(code)
    if result.ok:
        return result.output
    return f"Execution error ({_EXECUTOR.backend}): {result.error}"


@mcp.tool()
def runPlan(code: str) -> str:
    result = _EXECUTOR.execute(code)
    if result.ok:
        return result.output
    return f"Execution error ({_EXECUTOR.backend}): {result.error}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
