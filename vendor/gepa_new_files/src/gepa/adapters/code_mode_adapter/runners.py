# Copyright (c) 2025 Lakshya A Agrawal and the GEPA contributors
# https://github.com/gepa-ai/gepa

"""Runner utilities for the Code Mode adapter.

These runners keep the adapter runtime-agnostic:
- ``StaticCodeModeRunner`` for local demos and tests.
- ``HTTPCodeModeRunner`` for external runtimes (Cloudflare Worker, UTCP bridge,
  local Node service, etc.) exposed through a simple JSON API.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any
from urllib import request

from .code_mode_adapter import CodeModeRunnerResult, CodeModeToolCall


class StaticCodeModeRunner:
    """Deterministic in-memory runner for demos/tests.

    Parameters:
        rules: Ordered list of rules. The first rule whose ``contains`` text is
            present in the incoming query is used.

    Rule schema:
        {
            "contains": "substring to match",
            "result": {CodeModeRunnerResult payload}
        }
    """

    def __init__(self, rules: list[dict[str, Any]]):
        self.rules = rules

    def __call__(
        self,
        *,
        user_query: str,
        system_prompt: str,
        codemode_description: str,
        tool_alias_map: dict[str, str] | None = None,
        tool_description_overrides: dict[str, str] | None = None,
        additional_context: dict[str, str] | None = None,
    ) -> CodeModeRunnerResult:
        del (
            system_prompt,
            codemode_description,
            tool_alias_map,
            tool_description_overrides,
            additional_context,
        )
        for rule in self.rules:
            if rule.get("contains") and rule["contains"] in user_query:
                return _normalize_runner_result(rule.get("result", {}))

        return _normalize_runner_result(
            {
                "final_answer": "",
                "generated_code": "",
                "selected_tool": None,
                "tool_calls": [],
                "logs": [],
                "error": "No matching static runner rule",
            }
        )


class HTTPCodeModeRunner:
    """HTTP-backed runner for external Code Mode runtimes.

    The endpoint should accept JSON with adapter inputs and return JSON
    compatible with :class:`CodeModeRunnerResult`.
    """

    def __init__(
        self,
        endpoint_url: str,
        timeout_seconds: float = 30.0,
        headers: Mapping[str, str] | None = None,
    ):
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
    ) -> CodeModeRunnerResult:
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
            response_body = response.read().decode("utf-8")
            data = json.loads(response_body)

        return _normalize_runner_result(data)


def _normalize_runner_result(raw: Mapping[str, Any]) -> CodeModeRunnerResult:
    """Normalize untrusted runner payloads to the expected typed structure."""
    tool_calls: list[CodeModeToolCall] = []
    for item in raw.get("tool_calls", []) or []:
        if not isinstance(item, Mapping):
            continue
        name = item.get("name")
        arguments = item.get("arguments")
        if isinstance(name, str) and isinstance(arguments, Mapping):
            tool_calls.append({"name": name, "arguments": dict(arguments)})

    logs: list[str] = []
    for line in raw.get("logs", []) or []:
        if isinstance(line, str):
            logs.append(line)

    selected_tool = raw.get("selected_tool")
    if selected_tool is not None and not isinstance(selected_tool, str):
        selected_tool = None

    error = raw.get("error")
    if error is not None and not isinstance(error, str):
        error = str(error)

    final_answer = raw.get("final_answer")
    if not isinstance(final_answer, str):
        final_answer = str(final_answer or "")

    generated_code = raw.get("generated_code")
    if not isinstance(generated_code, str):
        generated_code = str(generated_code or "")

    return {
        "final_answer": final_answer,
        "generated_code": generated_code,
        "selected_tool": selected_tool,
        "tool_calls": tool_calls,
        "logs": logs,
        "error": error,
    }
