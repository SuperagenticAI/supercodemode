from __future__ import annotations

from typing import Any


def build_two_tool_dataset() -> list[dict[str, Any]]:
    return [
        {
            "user_query": "What tools are available for this task?",
            "reference_answer": "search_tools",
            "additional_context": {},
        },
        {
            "user_query": "Please calculate 17 + 25 using the execution tool.",
            "reference_answer": "42",
            "additional_context": {},
        },
    ]


def contains_reference_metric(item: dict[str, Any], output: str) -> float:
    expected = item.get("reference_answer") or ""
    output_l = (output or "").lower()
    if "tools are available" in item.get("user_query", "").lower():
        return 1.0 if ("search_tools" in output_l or "findtools" in output_l) else 0.0
    return 1.0 if expected and expected.lower() in output_l else 0.0


def baseline_candidate() -> dict[str, str]:
    return {
        "system_prompt": "You are a helpful assistant.",
        "codemode_description": "Use codemode tools to answer the user request.",
        "tool_alias_map": "{}",
        "tool_description_overrides": "{}",
    }


def tuned_candidate() -> dict[str, str]:
    return {
        "system_prompt": (
            "You are an execution-focused coding agent. Discover tools first when needed, "
            "then execute concise plans."
        ),
        "codemode_description": (
            "Use search_tools for capability discovery and call_tool_chain for code-plan execution."
        ),
        "tool_alias_map": '{"search_tools":"findTools","call_tool_chain":"runPlan"}',
        "tool_description_overrides": (
            '{"call_tool_chain":"Execute one complete multi-step code plan and return final result."}'
        ),
    }
