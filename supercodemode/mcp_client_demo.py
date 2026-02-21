from __future__ import annotations

import asyncio
import sys

from .env import bootstrap_reference_paths


def _extract_text(result: object) -> str:
    content = getattr(result, "content", None) or []
    for block in content:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            return text
    if getattr(result, "structured_content", None):
        return str(getattr(result, "structured_content"))
    return ""


async def run_demo(command: str, server_args: list[str], server_env: dict[str, str] | None = None) -> dict[str, str]:
    bootstrap_reference_paths()
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    params = StdioServerParameters(command=command, args=server_args, env=server_env or None)

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]

            result1 = await session.call_tool("search_tools", {"task_description": "What tools do we have?"})
            result2 = await session.call_tool("call_tool_chain", {"code": "return 17 + 25;"})
            result3 = await session.call_tool("findTools", {"task_description": "Alias discovery"})
            result4 = await session.call_tool("runPlan", {"code": "return 17 + 25;"})

            return {
                "available_tools": str(names),
                "search_tools": _extract_text(result1),
                "call_tool_chain": _extract_text(result2),
                "findTools": _extract_text(result3),
                "runPlan": _extract_text(result4),
            }


def run_demo_sync(command: str, server_args: list[str], server_env: dict[str, str] | None = None) -> dict[str, str]:
    return asyncio.run(run_demo(command=command, server_args=server_args, server_env=server_env))


if __name__ == "__main__":
    data = run_demo_sync(
        command=sys.executable,
        server_args=["-m", "supercodemode.servers.demo_mcp_server"],
        server_env={"SCM_EXECUTOR_BACKEND": "local", "SCM_DOCKER_IMAGE": "python:3.12-alpine"},
    )
    for k, v in data.items():
        print(f"{k}: {v}")
