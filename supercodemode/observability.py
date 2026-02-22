from __future__ import annotations

import json
import os
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ObservabilityConfig:
    backend: str
    jsonl_path: str
    service_name: str
    otlp_endpoint: str
    run_id: str
    tags: dict[str, str]
    dataset_name: str


class Observer:
    def emit(self, event: str, **fields: Any) -> None:
        raise NotImplementedError


class NullObserver(Observer):
    def emit(self, event: str, **fields: Any) -> None:
        del event, fields
        return


class JsonlObserver(Observer):
    def __init__(self, path: str, service_name: str, run_id: str) -> None:
        self._path = path
        self._service_name = service_name
        self._run_id = run_id
        self._lock = threading.Lock()

    def emit(self, event: str, **fields: Any) -> None:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "service": self._service_name,
            "run_id": self._run_id,
            "event": event,
            **fields,
        }
        line = json.dumps(payload, default=str)
        with self._lock:
            if self._path:
                with open(self._path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            else:
                sys.stdout.write(line + "\n")


class OTelObserver(Observer):
    def __init__(self, service_name: str, endpoint: str, run_id: str) -> None:
        self._service_name = service_name
        self._run_id = run_id
        self._enabled = False
        self._tracer = None

        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            resource = Resource.create({"service.name": service_name})
            provider = TracerProvider(resource=resource)
            exporter = OTLPSpanExporter(endpoint=endpoint) if endpoint else OTLPSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer("supercodemode")
            self._enabled = True
        except Exception as exc:
            sys.stderr.write(f"[supercodemode] otlp disabled: {exc}\n")

    def emit(self, event: str, **fields: Any) -> None:
        if not self._enabled or self._tracer is None:
            return

        with self._tracer.start_as_current_span(event) as span:
            span.set_attribute("scm.run_id", self._run_id)
            span.set_attribute("scm.service", self._service_name)
            for key, value in fields.items():
                attr = f"scm.{key}"
                if isinstance(value, (bool, int, float, str)):
                    span.set_attribute(attr, value)
                else:
                    span.set_attribute(attr, str(value))


class LogfireObserver(Observer):
    def __init__(self, service_name: str, run_id: str) -> None:
        self._service_name = service_name
        self._run_id = run_id
        self._enabled = False
        self._logfire = None
        try:
            import logfire

            self._logfire = logfire
            self._enabled = True
        except Exception as exc:
            sys.stderr.write(f"[supercodemode] logfire disabled: {exc}\n")

    def emit(self, event: str, **fields: Any) -> None:
        if not self._enabled or self._logfire is None:
            return
        payload = {
            "service": self._service_name,
            "run_id": self._run_id,
            "event": event,
            **fields,
        }
        try:
            logger = getattr(self._logfire, "info", None)
            if callable(logger):
                logger("scm_event", **payload)
                return
            # Fallback for SDK variants exposing a namespaced logger object.
            if hasattr(self._logfire, "default") and hasattr(self._logfire.default, "info"):
                self._logfire.default.info("scm_event", **payload)
        except Exception:
            return


class MLflowObserver(Observer):
    def __init__(self, service_name: str, run_id: str) -> None:
        self._service_name = service_name
        self._run_id = run_id
        self._enabled = False
        self._mlflow = None
        self._event_idx = 0
        try:
            import mlflow

            self._mlflow = mlflow
            if mlflow.active_run() is None:
                mlflow.start_run(run_name=f"{service_name}-{run_id}")
                self._owns_run = True
            else:
                self._owns_run = False
            try:
                mlflow.set_tags({"scm.service": service_name, "scm.run_id": run_id})
            except Exception:
                pass
            self._enabled = True
        except Exception as exc:
            self._owns_run = False
            sys.stderr.write(f"[supercodemode] mlflow disabled: {exc}\n")

    def emit(self, event: str, **fields: Any) -> None:
        if not self._enabled or self._mlflow is None:
            return
        self._event_idx += 1
        payload = {
            "event": event,
            "service": self._service_name,
            "run_id": self._run_id,
            **fields,
        }
        try:
            # Compact metrics for dashboarding
            metrics = {k: float(v) for k, v in fields.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
            if metrics:
                self._mlflow.log_metrics(metrics, step=self._event_idx)
            self._mlflow.log_dict(payload, artifact_file=f"scm_events/{self._event_idx:05d}_{event}.json")
        except Exception:
            return


class LangSmithObserver(Observer):
    def __init__(self, service_name: str, run_id: str) -> None:
        self._service_name = service_name
        self._run_id = run_id
        self._enabled = False
        self._client = None
        self._project = os.environ.get("LANGSMITH_PROJECT", "supercodemode").strip() or "supercodemode"
        self._seq = 0
        try:
            from langsmith import Client

            self._client = Client()
            self._enabled = True
        except Exception as exc:
            sys.stderr.write(f"[supercodemode] langsmith disabled: {exc}\n")

    def emit(self, event: str, **fields: Any) -> None:
        if not self._enabled or self._client is None:
            return
        self._seq += 1
        try:
            payload = {"service": self._service_name, "run_id": self._run_id, **fields}
            # Best-effort event logging as a lightweight run entry.
            self._client.create_run(
                name=event,
                run_type="tool",
                inputs={"event": event, "seq": self._seq},
                outputs=payload,
                extra={"metadata": {"scm_event": True, "service": self._service_name, "run_id": self._run_id}},
                project_name=self._project,
            )
        except Exception:
            return


class LangfuseObserver(Observer):
    def __init__(self, service_name: str, run_id: str) -> None:
        self._service_name = service_name
        self._run_id = run_id
        self._enabled = False
        self._client = None
        self._trace = None
        try:
            from langfuse import Langfuse

            self._client = Langfuse()
            self._trace = self._client.trace(
                id=run_id,
                name=service_name,
                metadata={"scm": True, "service": service_name, "run_id": run_id},
            )
            self._enabled = True
        except Exception as exc:
            sys.stderr.write(f"[supercodemode] langfuse disabled: {exc}\n")

    def emit(self, event: str, **fields: Any) -> None:
        if not self._enabled or self._trace is None:
            return
        try:
            # Best-effort event span/generation representation.
            if hasattr(self._trace, "event"):
                self._trace.event(name=event, metadata=fields)
                return
            if hasattr(self._trace, "span"):
                span = self._trace.span(name=event, metadata=fields)
                if hasattr(span, "end"):
                    span.end()
        except Exception:
            return


_OBSERVER: Observer | None = None


def _load_config() -> ObservabilityConfig:
    backend = os.environ.get("SCM_OBS_BACKEND", "none").strip().lower()
    jsonl_path = os.environ.get("SCM_OBS_JSONL_PATH", "").strip()
    service_name = os.environ.get("SCM_OBS_SERVICE_NAME", "supercodemode").strip() or "supercodemode"
    otlp_endpoint = os.environ.get("SCM_OBS_OTLP_ENDPOINT", "").strip()
    run_id = os.environ.get("SCM_RUN_ID", "").strip() or uuid.uuid4().hex[:12]
    dataset_name = os.environ.get("SCM_OBS_DATASET_NAME", "").strip()
    tags = _parse_tags_json(os.environ.get("SCM_OBS_TAGS_JSON", "").strip())
    return ObservabilityConfig(
        backend=backend,
        jsonl_path=jsonl_path,
        service_name=service_name,
        otlp_endpoint=otlp_endpoint,
        run_id=run_id,
        tags=tags,
        dataset_name=dataset_name,
    )


def get_observer() -> Observer:
    global _OBSERVER
    if _OBSERVER is not None:
        return _OBSERVER

    cfg = _load_config()
    if cfg.backend == "jsonl":
        _OBSERVER = JsonlObserver(path=cfg.jsonl_path, service_name=cfg.service_name, run_id=cfg.run_id)
    elif cfg.backend == "otlp":
        _OBSERVER = OTelObserver(service_name=cfg.service_name, endpoint=cfg.otlp_endpoint, run_id=cfg.run_id)
    elif cfg.backend == "logfire":
        _OBSERVER = LogfireObserver(service_name=cfg.service_name, run_id=cfg.run_id)
    elif cfg.backend == "mlflow":
        _OBSERVER = MLflowObserver(service_name=cfg.service_name, run_id=cfg.run_id)
    elif cfg.backend == "langsmith":
        _OBSERVER = LangSmithObserver(service_name=cfg.service_name, run_id=cfg.run_id)
    elif cfg.backend == "langfuse":
        _OBSERVER = LangfuseObserver(service_name=cfg.service_name, run_id=cfg.run_id)
    else:
        _OBSERVER = NullObserver()
    return _OBSERVER


def emit_event(event: str, **fields: Any) -> None:
    try:
        cfg = _load_config()
        ctx = _event_context_fields(cfg)
        get_observer().emit(event, **{**ctx, **fields})
    except Exception:
        # Observability should never break main flows.
        return


def timed_event(event_start: str, event_end: str, **start_fields: Any):
    class _Timer:
        def __enter__(self):
            self._t0 = time.perf_counter()
            emit_event(event_start, **start_fields)
            return self

        def __exit__(self, exc_type, exc, tb):
            latency_ms = int((time.perf_counter() - self._t0) * 1000)
            emit_event(
                event_end,
                latency_ms=latency_ms,
                error=str(exc) if exc else None,
                **start_fields,
            )
            return False

    return _Timer()


def _parse_tags_json(raw: str) -> dict[str, str]:
    if not raw:
        return {}
    try:
        obj = json.loads(raw)
    except Exception:
        return {}
    if not isinstance(obj, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in obj.items():
        if isinstance(k, str):
            out[k] = str(v)
    return out


def _event_context_fields(cfg: ObservabilityConfig) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    command = os.environ.get("SCM_OBS_COMMAND", "").strip()
    runner = os.environ.get("SCM_OBS_RUNNER", "").strip()
    executor_backend = os.environ.get("SCM_OBS_EXECUTOR_BACKEND", "").strip()
    if command:
        fields["cli_command"] = command
    if runner:
        fields["cli_runner"] = runner
    if executor_backend:
        fields["cli_executor_backend"] = executor_backend
    if cfg.dataset_name:
        fields["dataset_name"] = cfg.dataset_name
    if cfg.tags:
        fields["tags"] = cfg.tags
    return fields
