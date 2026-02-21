#!/usr/bin/env python3
"""Two-tool Code Mode showcase (search + execute pattern).

This demonstrates Cloudflare/UTCP-style flows where the model decides between:
- ``search_tools`` (discover capabilities)
- ``call_tool_chain`` (execute a multi-step plan)

No external services are required; it uses StaticCodeModeRunner.
"""

from __future__ import annotations

from typing import Any

from gepa.adapters.code_mode_adapter import CodeModeAdapter
from gepa.adapters.code_mode_adapter.runners import StaticCodeModeRunner


def metric_fn(item: dict[str, Any], output: str) -> float:
    expected = item.get("reference_answer") or ""
    return 1.0 if expected and expected.lower() in output.lower() else 0.0


def build_runner() -> StaticCodeModeRunner:
    return StaticCodeModeRunner(
        rules=[
            {
                "contains": "what tools",
                "result": {
                    "final_answer": "You can use search_tools and call_tool_chain.",
                    "generated_code": "async () => await codemode.search_tools({ task_description: 'available tools' })",
                    "selected_tool": "search_tools",
                    "tool_calls": [{"name": "search_tools", "arguments": {"task_description": "available tools"}}],
                    "logs": ["discovered tool list"],
                    "error": None,
                },
            },
            {
                "contains": "calculate 17 + 25",
                "result": {
                    "final_answer": "42",
                    "generated_code": "async () => await codemode.call_tool_chain({ code: 'return 17 + 25;' })",
                    "selected_tool": "call_tool_chain",
                    "tool_calls": [{"name": "call_tool_chain", "arguments": {"code": "return 17 + 25;"}}],
                    "logs": ["executed chain"],
                    "error": None,
                },
            },
        ]
    )


def evaluate_candidate(name: str, candidate: dict[str, str]) -> None:
    dataset = [
        {
            "user_query": "What tools are available?",
            "reference_answer": "search_tools",
            "additional_context": {},
        },
        {
            "user_query": "Please calculate 17 + 25.",
            "reference_answer": "42",
            "additional_context": {},
        },
    ]

    adapter = CodeModeAdapter(runner=build_runner(), metric_fn=metric_fn)
    result = adapter.evaluate(batch=dataset, candidate=candidate, capture_traces=True)

    print(f"\n=== {name} ===")
    print("scores:", result.scores)
    print("avg:", sum(result.scores) / len(result.scores))
    if result.trajectories:
        for i, traj in enumerate(result.trajectories, start=1):
            print(
                f"[{i}] selected_tool={traj['selected_tool']} tool_calls={len(traj['tool_calls'])} "
                f"error={traj['error']} final={traj['final_answer']}"
            )


def main() -> None:
    baseline = {
        "system_prompt": "You are a helpful assistant.",
        "codemode_description": "Use codemode tools.",
    }

    tuned = {
        "system_prompt": "You are a coding agent. Prefer tool discovery before execution when unclear.",
        "codemode_description": "Use search_tools to discover capabilities and call_tool_chain to execute plans.",
        "tool_alias_map": '{"search_tools":"findTools","call_tool_chain":"runPlan"}',
        "tool_description_overrides": '{"call_tool_chain":"Execute a complete multi-step code plan."}',
    }

    evaluate_candidate("baseline", baseline)
    evaluate_candidate("tuned", tuned)


if __name__ == "__main__":
    main()
