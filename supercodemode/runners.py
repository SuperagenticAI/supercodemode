from __future__ import annotations

import asyncio
import json
import sys
import time
from collections.abc import Mapping
from typing import Any
from urllib import request

from .env import bootstrap_reference_paths
from .observability import emit_event


class StaticCodeModeRunner:
    def __call__(
        self,
        *,
        user_query: str,
        system_prompt: str,
        codemode_description: str,
        tool_alias_map: dict[str, str] | None = None,
        tool_description_overrides: dict[str, str] | None = None,
        additional_context: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        del system_prompt, tool_description_overrides, additional_context
        alias_map = tool_alias_map or {}
        search_tool = alias_map.get("search_tools", "search_tools")
        exec_tool = alias_map.get("call_tool_chain", "call_tool_chain")
        emit_event(
            "runner.static.start",
            query=user_query,
            search_tool=search_tool,
            exec_tool=exec_tool,
        )

        if "tools are available" in user_query.lower():
            if "search_tools" in codemode_description.lower():
                out = {
                    "final_answer": f"Available tools: {search_tool}, {exec_tool}",
                    "generated_code": f"async () => await codemode.{search_tool}({{ task_description: 'available tools' }})",
                    "selected_tool": search_tool,
                    "tool_calls": [{"name": "search_tools", "arguments": {"task_description": "available tools"}}],
                    "logs": ["discovered tools"],
                    "error": None,
                }
                emit_event(
                    "runner.static.end",
                    latency_ms=int((time.perf_counter() - t0) * 1000),
                    selected_tool=out["selected_tool"],
                    error=out["error"],
                )
                return out
            out = {
                "final_answer": f"Use {exec_tool} for everything",
                "generated_code": "async () => await codemode.call_tool_chain({ code: 'tool discovery omitted' })",
                "selected_tool": exec_tool,
                "tool_calls": [{"name": "call_tool_chain", "arguments": {"code": "tool discovery omitted"}}],
                "logs": ["degraded discovery"],
                "error": None,
            }
            emit_event(
                "runner.static.end",
                latency_ms=int((time.perf_counter() - t0) * 1000),
                selected_tool=out["selected_tool"],
                error=out["error"],
            )
            return out

        if "calculate 17 + 25" in user_query.lower():
            out = {
                "final_answer": "42",
                "generated_code": f"async () => await codemode.{exec_tool}({{ code: 'return 17 + 25;' }})",
                "selected_tool": exec_tool,
                "tool_calls": [{"name": "call_tool_chain", "arguments": {"code": "return 17 + 25;"}}],
                "logs": ["executed code plan"],
                "error": None,
            }
            emit_event(
                "runner.static.end",
                latency_ms=int((time.perf_counter() - t0) * 1000),
                selected_tool=out["selected_tool"],
                error=out["error"],
            )
            return out

        out = {
            "final_answer": "",
            "generated_code": "",
            "selected_tool": None,
            "tool_calls": [],
            "logs": [],
            "error": "No matching rule",
        }
        emit_event(
            "runner.static.end",
            latency_ms=int((time.perf_counter() - t0) * 1000),
            selected_tool=out["selected_tool"],
            error=out["error"],
        )
        return out


class HTTPCodeModeRunner:
    def __init__(self, endpoint_url: str, timeout_seconds: float = 30.0, headers: Mapping[str, str] | None = None):
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds
        self.headers = dict(headers or {})

    def __call__(
        self,
        *,
        user_query: str,
        system_prompt: str,
        codemode_description: str,
        tool_alias_map: dict[str, str] | None = None,
        tool_description_overrides: dict[str, str] | None = None,
        additional_context: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        emit_event("runner.http.start", endpoint=self.endpoint_url, query=user_query)
        payload = {
            "user_query": user_query,
            "system_prompt": system_prompt,
            "codemode_description": codemode_description,
            "tool_alias_map": tool_alias_map or {},
            "tool_description_overrides": tool_description_overrides or {},
            "additional_context": additional_context or {},
        }
        body = json.dumps(payload).encode("utf-8")
        req_headers = {"Content-Type": "application/json", **self.headers}
        req = request.Request(self.endpoint_url, data=body, headers=req_headers, method="POST")
        with request.urlopen(req, timeout=self.timeout_seconds) as response:
            out = json.loads(response.read().decode("utf-8"))
        emit_event(
            "runner.http.end",
            endpoint=self.endpoint_url,
            latency_ms=int((time.perf_counter() - t0) * 1000),
            selected_tool=out.get("selected_tool"),
            error=out.get("error"),
        )
        return out


class MCPStreamableHTTPCodeModeRunner:
    def __init__(self, endpoint_url: str, timeout_seconds: float = 30.0, headers: Mapping[str, str] | None = None):
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds
        self.headers = dict(headers or {})

    def __call__(
        self,
        *,
        user_query: str,
        system_prompt: str,
        codemode_description: str,
        tool_alias_map: dict[str, str] | None = None,
        tool_description_overrides: dict[str, str] | None = None,
        additional_context: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return asyncio.run(
            self._run(
                user_query=user_query,
                system_prompt=system_prompt,
                codemode_description=codemode_description,
                tool_alias_map=tool_alias_map,
                tool_description_overrides=tool_description_overrides,
                additional_context=additional_context,
            )
        )

    async def _run(
        self,
        *,
        user_query: str,
        system_prompt: str,
        codemode_description: str,
        tool_alias_map: dict[str, str] | None,
        tool_description_overrides: dict[str, str] | None,
        additional_context: dict[str, str] | None,
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        del system_prompt, tool_description_overrides, additional_context
        bootstrap_reference_paths()

        import httpx
        from mcp.client.session import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        alias_map = tool_alias_map or {}
        search_tool_hint = alias_map.get("search_tools", "")
        exec_tool_hint = alias_map.get("call_tool_chain", "")
        emit_event(
            "runner.mcp_http.start",
            endpoint=self.endpoint_url,
            query=user_query,
            search_hint=search_tool_hint,
            exec_hint=exec_tool_hint,
        )

        timeout = httpx.Timeout(self.timeout_seconds)
        async with httpx.AsyncClient(headers=self.headers or None, timeout=timeout) as http_client:
            async with streamable_http_client(self.endpoint_url, http_client=http_client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    available = [tool.name for tool in tools.tools]
                    logs = [f"available_tools={available}"]

                    search_tool = _pick_tool_name(
                        available=available,
                        preferred=search_tool_hint or None,
                        fallback_priority=["search_tools", "searchTools", "search", "find_tools", "findTools"],
                    )
                    exec_tool = _pick_tool_name(
                        available=available,
                        preferred=exec_tool_hint or None,
                        fallback_priority=["call_tool_chain", "runPlan", "execute", "tool_execute", "run_chain"],
                    )

                    if "tools are available" in user_query.lower():
                        if "search_tools" in codemode_description.lower() and search_tool:
                            args = {"task_description": "available tools"}
                            emit_event("runner.mcp_http.tool_call.start", tool=search_tool, arguments=args)
                            result = await session.call_tool(search_tool, args)
                            emit_event("runner.mcp_http.tool_call.end", tool=search_tool)
                            answer = _extract_text_result(result) or f"Available tools: {', '.join(available)}"
                            out = {
                                "final_answer": answer,
                                "generated_code": (
                                    f"async () => await codemode.{search_tool}({{ task_description: 'available tools' }})"
                                ),
                                "selected_tool": search_tool,
                                "tool_calls": [{"name": search_tool, "arguments": args}],
                                "logs": logs + ["discovered tools via MCP streamable-http"],
                                "error": None,
                            }
                            emit_event(
                                "runner.mcp_http.end",
                                latency_ms=int((time.perf_counter() - t0) * 1000),
                                selected_tool=out["selected_tool"],
                                error=out["error"],
                            )
                            return out
                        out = {
                            "final_answer": f"Available tools: {', '.join(available)}",
                            "generated_code": "",
                            "selected_tool": None,
                            "tool_calls": [],
                            "logs": logs,
                            "error": "No search-like tool available",
                        }
                        emit_event(
                            "runner.mcp_http.end",
                            latency_ms=int((time.perf_counter() - t0) * 1000),
                            selected_tool=out["selected_tool"],
                            error=out["error"],
                        )
                        return out

                    if "calculate 17 + 25" in user_query.lower():
                        if not exec_tool:
                            out = {
                                "final_answer": "",
                                "generated_code": "",
                                "selected_tool": None,
                                "tool_calls": [],
                                "logs": logs,
                                "error": "No execute-like tool available",
                            }
                            emit_event(
                                "runner.mcp_http.end",
                                latency_ms=int((time.perf_counter() - t0) * 1000),
                                selected_tool=out["selected_tool"],
                                error=out["error"],
                            )
                            return out

                        args = {"code": "return 17 + 25;"}
                        emit_event("runner.mcp_http.tool_call.start", tool=exec_tool, arguments=args)
                        result = await session.call_tool(exec_tool, args)
                        emit_event("runner.mcp_http.tool_call.end", tool=exec_tool)
                        out = {
                            "final_answer": _extract_text_result(result) or "42",
                            "generated_code": f"async () => await codemode.{exec_tool}({{ code: 'return 17 + 25;' }})",
                            "selected_tool": exec_tool,
                            "tool_calls": [{"name": exec_tool, "arguments": args}],
                            "logs": logs + ["executed code plan via MCP streamable-http"],
                            "error": None,
                        }
                        emit_event(
                            "runner.mcp_http.end",
                            latency_ms=int((time.perf_counter() - t0) * 1000),
                            selected_tool=out["selected_tool"],
                            error=out["error"],
                        )
                        return out

                    out = {
                        "final_answer": "",
                        "generated_code": "",
                        "selected_tool": None,
                        "tool_calls": [],
                        "logs": logs,
                        "error": "No matching rule",
                    }
                    emit_event(
                        "runner.mcp_http.end",
                        latency_ms=int((time.perf_counter() - t0) * 1000),
                        selected_tool=out["selected_tool"],
                        error=out["error"],
                    )
                    return out


def _pick_tool_name(available: list[str], preferred: str | None, fallback_priority: list[str]) -> str | None:
    if preferred and preferred in available:
        return preferred
    for name in fallback_priority:
        if name in available:
            return name
    return None


def _extract_text_result(result: Any) -> str:
    content = getattr(result, "content", None) or []
    for block in content:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            return text
    if getattr(result, "structured_content", None):
        return str(result.structured_content)
    return ""


class MCPStdioCodeModeRunner:
    def __init__(
        self,
        *,
        command: str,
        args: list[str],
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self.command = command
        self.args = args
        self.cwd = cwd
        self.env = env or {}

    def __call__(
        self,
        *,
        user_query: str,
        system_prompt: str,
        codemode_description: str,
        tool_alias_map: dict[str, str] | None = None,
        tool_description_overrides: dict[str, str] | None = None,
        additional_context: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return asyncio.run(
            self._run(
                user_query=user_query,
                system_prompt=system_prompt,
                codemode_description=codemode_description,
                tool_alias_map=tool_alias_map,
                tool_description_overrides=tool_description_overrides,
                additional_context=additional_context,
            )
        )

    async def _run(
        self,
        *,
        user_query: str,
        system_prompt: str,
        codemode_description: str,
        tool_alias_map: dict[str, str] | None,
        tool_description_overrides: dict[str, str] | None,
        additional_context: dict[str, str] | None,
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        del system_prompt, tool_description_overrides, additional_context
        bootstrap_reference_paths()

        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        alias_map = tool_alias_map or {}
        search_tool = alias_map.get("search_tools", "search_tools")
        exec_tool = alias_map.get("call_tool_chain", "call_tool_chain")
        emit_event(
            "runner.mcp.start",
            query=user_query,
            search_tool=search_tool,
            exec_tool=exec_tool,
            command=self.command,
        )

        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
            cwd=self.cwd,
            env=self.env or None,
        )

        logs: list[str] = []
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                available = [tool.name for tool in tools.tools]
                logs.append(f"available_tools={available}")
                emit_event("runner.mcp.tools_listed", count=len(available), tools=available)

                if "tools are available" in user_query.lower():
                    if "search_tools" in codemode_description.lower() and search_tool in available:
                        args = {"task_description": "available tools"}
                        emit_event("runner.mcp.tool_call.start", tool=search_tool, arguments=args)
                        result = await session.call_tool(search_tool, args)
                        emit_event("runner.mcp.tool_call.end", tool=search_tool)
                        answer = _extract_text_result(result) or f"Available tools: {', '.join(available)}"
                        out = {
                            "final_answer": answer,
                            "generated_code": f"async () => await codemode.{search_tool}({{ task_description: 'available tools' }})",
                            "selected_tool": search_tool,
                            "tool_calls": [{"name": search_tool, "arguments": args}],
                            "logs": logs + ["discovered tools via MCP"],
                            "error": None,
                        }
                        emit_event(
                            "runner.mcp.end",
                            latency_ms=int((time.perf_counter() - t0) * 1000),
                            selected_tool=out["selected_tool"],
                            error=out["error"],
                        )
                        return out

                    args = {"code": "tool discovery omitted"}
                    emit_event("runner.mcp.tool_call.start", tool=exec_tool, arguments=args)
                    await session.call_tool(exec_tool, args)
                    emit_event("runner.mcp.tool_call.end", tool=exec_tool)
                    out = {
                        "final_answer": f"Use {exec_tool} for everything",
                        "generated_code": f"async () => await codemode.{exec_tool}({{ code: 'tool discovery omitted' }})",
                        "selected_tool": exec_tool,
                        "tool_calls": [{"name": exec_tool, "arguments": args}],
                        "logs": logs + ["degraded discovery"],
                        "error": None,
                    }
                    emit_event(
                        "runner.mcp.end",
                        latency_ms=int((time.perf_counter() - t0) * 1000),
                        selected_tool=out["selected_tool"],
                        error=out["error"],
                    )
                    return out

                if "calculate 17 + 25" in user_query.lower():
                    args = {"code": "return 17 + 25;"}
                    emit_event("runner.mcp.tool_call.start", tool=exec_tool, arguments=args)
                    result = await session.call_tool(exec_tool, args)
                    emit_event("runner.mcp.tool_call.end", tool=exec_tool)
                    out = {
                        "final_answer": _extract_text_result(result),
                        "generated_code": f"async () => await codemode.{exec_tool}({{ code: 'return 17 + 25;' }})",
                        "selected_tool": exec_tool,
                        "tool_calls": [{"name": exec_tool, "arguments": args}],
                        "logs": logs + ["executed code plan via MCP"],
                        "error": None,
                    }
                    emit_event(
                        "runner.mcp.end",
                        latency_ms=int((time.perf_counter() - t0) * 1000),
                        selected_tool=out["selected_tool"],
                        error=out["error"],
                    )
                    return out

                out = {
                    "final_answer": "",
                    "generated_code": "",
                    "selected_tool": None,
                    "tool_calls": [],
                    "logs": logs,
                    "error": "No matching rule",
                }
                emit_event(
                    "runner.mcp.end",
                    latency_ms=int((time.perf_counter() - t0) * 1000),
                    selected_tool=out["selected_tool"],
                    error=out["error"],
                )
                return out


def build_default_mcp_stdio_runner(
    command: str | None = None,
    server_script: str | None = None,
    server_module: str = "supercodemode.servers.demo_mcp_server",
    executor_backend: str = "local",
    docker_image: str = "python:3.12-alpine",
) -> MCPStdioCodeModeRunner:
    server_command = command or sys.executable
    if server_script is None:
        server_args = ["-m", server_module]
    else:
        server_args = [server_script]
    env = {
        "SCM_EXECUTOR_BACKEND": executor_backend,
        "SCM_DOCKER_IMAGE": docker_image,
    }
    return MCPStdioCodeModeRunner(command=server_command, args=server_args, env=env)
