import json
from typing import Any

from gepa.adapters.code_mode_adapter.runners import HTTPCodeModeRunner, StaticCodeModeRunner


def test_static_runner_matches_rule() -> None:
    runner = StaticCodeModeRunner(
        rules=[
            {
                "contains": "tools",
                "result": {
                    "final_answer": "search_tools, call_tool_chain",
                    "generated_code": "async () => 1",
                    "selected_tool": "search_tools",
                    "tool_calls": [{"name": "search_tools", "arguments": {"task_description": "tools"}}],
                    "logs": ["ok"],
                    "error": None,
                },
            }
        ]
    )

    out = runner(
        user_query="what tools are available",
        system_prompt="sys",
        codemode_description="desc",
        tool_alias_map=None,
        tool_description_overrides=None,
        additional_context=None,
    )

    assert out["selected_tool"] == "search_tools"
    assert out["tool_calls"][0]["name"] == "search_tools"


def test_static_runner_no_match_returns_error() -> None:
    runner = StaticCodeModeRunner(rules=[])
    out = runner(
        user_query="no match",
        system_prompt="sys",
        codemode_description="desc",
        tool_alias_map=None,
        tool_description_overrides=None,
        additional_context=None,
    )
    assert out["error"] == "No matching static runner rule"


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_http_runner_parses_response(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResponse(
            {
                "final_answer": "42",
                "generated_code": "async () => 42",
                "selected_tool": "runPlan",
                "tool_calls": [{"name": "call_tool_chain", "arguments": {"code": "return 42;"}}],
                "logs": ["done"],
                "error": None,
            }
        )

    monkeypatch.setattr("gepa.adapters.code_mode_adapter.runners.request.urlopen", fake_urlopen)

    runner = HTTPCodeModeRunner(endpoint_url="http://localhost:8080/run", timeout_seconds=5)
    out = runner(
        user_query="calculate",
        system_prompt="sys",
        codemode_description="desc",
        tool_alias_map={"call_tool_chain": "runPlan"},
        tool_description_overrides={"call_tool_chain": "Execute plan"},
        additional_context={"tenant": "demo"},
    )

    assert captured["url"] == "http://localhost:8080/run"
    assert captured["timeout"] == 5
    assert captured["body"]["tool_alias_map"]["call_tool_chain"] == "runPlan"
    assert out["final_answer"] == "42"
    assert out["selected_tool"] == "runPlan"


def test_http_runner_normalizes_weird_payload(monkeypatch) -> None:
    def fake_urlopen(req, timeout):
        del req, timeout
        return _FakeResponse(
            {
                "final_answer": 42,
                "generated_code": None,
                "selected_tool": {"invalid": True},
                "tool_calls": ["bad", {"name": "ok", "arguments": {"x": 1}}],
                "logs": [1, "good"],
                "error": {"msg": "bad"},
            }
        )

    monkeypatch.setattr("gepa.adapters.code_mode_adapter.runners.request.urlopen", fake_urlopen)

    runner = HTTPCodeModeRunner(endpoint_url="http://localhost:8080/run")
    out = runner(
        user_query="q",
        system_prompt="s",
        codemode_description="d",
        tool_alias_map=None,
        tool_description_overrides=None,
        additional_context=None,
    )

    assert out["final_answer"] == "42"
    assert out["generated_code"] == ""
    assert out["selected_tool"] is None
    assert len(out["tool_calls"]) == 1
    assert out["logs"] == ["good"]
    assert out["error"] == "{'msg': 'bad'}"
