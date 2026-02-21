from __future__ import annotations

import ast
import subprocess
import sys
from dataclasses import dataclass


_ALLOWED_AST_NODES: tuple[type[ast.AST], ...] = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.UAdd,
    ast.Load,
    ast.Tuple,
    ast.List,
)


_EVAL_WRAPPER = r"""
import ast
import json
import sys

expr = sys.argv[1]
node = ast.parse(expr, mode='eval')
allowed = {
    'Expression','BinOp','UnaryOp','Constant','Add','Sub','Mult','Div',
    'FloorDiv','Mod','Pow','USub','UAdd','Load','Tuple','List'
}
for n in ast.walk(node):
    if type(n).__name__ not in allowed:
        print(json.dumps({'ok': False, 'error': f'disallowed_node:{type(n).__name__}'}))
        raise SystemExit(0)
result = eval(compile(node, '<expr>', 'eval'), {'__builtins__': {}}, {})
print(json.dumps({'ok': True, 'result': result}))
""".strip()


@dataclass
class ExecutionResult:
    ok: bool
    output: str
    error: str | None = None


class CodeExecutor:
    backend: str

    def execute(self, code: str) -> ExecutionResult:
        raise NotImplementedError


class LocalCodeExecutor(CodeExecutor):
    backend = "local"

    def __init__(self, timeout_seconds: float = 3.0) -> None:
        self.timeout_seconds = timeout_seconds

    def execute(self, code: str) -> ExecutionResult:
        expr = _extract_expression(code)
        if expr is None:
            return ExecutionResult(ok=False, output="", error="No expression found")

        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-S", "-c", _EVAL_WRAPPER, expr],
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(ok=False, output="", error="Execution timeout")

        payload = (completed.stdout or "").strip()
        parsed = _parse_json_payload(payload)
        if not parsed:
            stderr = (completed.stderr or "").strip()
            return ExecutionResult(ok=False, output="", error=stderr or "Executor failed")

        if parsed.get("ok") is True:
            return ExecutionResult(ok=True, output=str(parsed.get("result", "")))
        return ExecutionResult(ok=False, output="", error=str(parsed.get("error", "Execution error")))


class DockerCodeExecutor(CodeExecutor):
    backend = "docker"

    def __init__(self, image: str = "python:3.12-alpine", timeout_seconds: float = 5.0) -> None:
        self.image = image
        self.timeout_seconds = timeout_seconds

    def execute(self, code: str) -> ExecutionResult:
        expr = _extract_expression(code)
        if expr is None:
            return ExecutionResult(ok=False, output="", error="No expression found")

        cmd = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--cpus",
            "0.5",
            "--memory",
            "128m",
            "--pids-limit",
            "64",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,nosuid,size=16m",
            self.image,
            "python",
            "-I",
            "-S",
            "-c",
            _EVAL_WRAPPER,
            expr,
        ]

        try:
            completed = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except FileNotFoundError:
            return ExecutionResult(ok=False, output="", error="Docker CLI not found")
        except subprocess.TimeoutExpired:
            return ExecutionResult(ok=False, output="", error="Docker execution timeout")

        payload = (completed.stdout or "").strip()
        parsed = _parse_json_payload(payload)
        if not parsed:
            stderr = (completed.stderr or "").strip()
            return ExecutionResult(ok=False, output="", error=stderr or "Docker executor failed")

        if parsed.get("ok") is True:
            return ExecutionResult(ok=True, output=str(parsed.get("result", "")))
        return ExecutionResult(ok=False, output="", error=str(parsed.get("error", "Execution error")))


def build_executor(backend: str = "local", docker_image: str = "python:3.12-alpine") -> CodeExecutor:
    key = (backend or "local").strip().lower()
    if key == "docker":
        return DockerCodeExecutor(image=docker_image)
    return LocalCodeExecutor()


def _extract_expression(code: str) -> str | None:
    src = (code or "").strip()
    if not src:
        return None

    if "return" in src:
        # supports snippets like `return 17 + 25;`
        rhs = src.split("return", 1)[1].strip()
        if rhs.endswith(";"):
            rhs = rhs[:-1].strip()
        src = rhs

    try:
        node = ast.parse(src, mode="eval")
    except SyntaxError:
        return None

    for n in ast.walk(node):
        if not isinstance(n, _ALLOWED_AST_NODES):
            return None

    return src


def _parse_json_payload(payload: str) -> dict[str, object] | None:
    if not payload:
        return None
    import json

    last_line = payload.splitlines()[-1]
    try:
        obj = json.loads(last_line)
    except Exception:
        return None
    if isinstance(obj, dict):
        return obj
    return None
