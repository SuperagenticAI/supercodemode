#!/usr/bin/env python3
"""Minimal Code Mode adapter example.

This demo uses an in-memory runner to illustrate the adapter contract without
requiring Cloudflare or UTCP setup.
"""

from __future__ import annotations

from typing import Any

from gepa.adapters.code_mode_adapter import CodeModeAdapter


class DemoRunner:
    """Tiny deterministic runner used for local demonstration only."""

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
        del additional_context, system_prompt, tool_alias_map, tool_description_overrides
        if "17 + 25" in user_query and "codemode" in codemode_description.lower():
            return {
                "final_answer": "42",
                "generated_code": "async () => { return 42; }",
                "selected_tool": "addNumbers",
                "tool_calls": [{"name": "addNumbers", "arguments": {"a": 17, "b": 25}}],
                "logs": ["calculated with addNumbers"],
                "error": None,
            }

        return {
            "final_answer": "I am not sure.",
            "generated_code": "async () => { return 'I am not sure.'; }",
            "selected_tool": None,
            "tool_calls": [],
            "logs": [],
            "error": None,
        }


def metric_fn(item: dict[str, Any], output: str) -> float:
    expected = item.get("reference_answer") or ""
    return 1.0 if expected and expected in output else 0.0


def main() -> None:
    dataset = [
        {
            "user_query": "What is 17 + 25?",
            "reference_answer": "42",
            "additional_context": {},
        }
    ]

    adapter = CodeModeAdapter(
        runner=DemoRunner(),
        metric_fn=metric_fn,
        default_system_prompt="You are a helpful assistant.",
        default_codemode_description="Execute code using codemode tools and return concise results.",
    )

    candidate = {
        "system_prompt": "You are a precise coding assistant.",
        "codemode_description": "Execute code using codemode tools and provide the final answer.",
    }

    eval_batch = adapter.evaluate(batch=dataset, candidate=candidate, capture_traces=True)
    print("Scores:", eval_batch.scores)
    print("Outputs:", eval_batch.outputs)


if __name__ == "__main__":
    main()
