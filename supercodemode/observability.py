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


_OBSERVER: Observer | None = None


def _load_config() -> ObservabilityConfig:
    backend = os.environ.get("SCM_OBS_BACKEND", "none").strip().lower()
    jsonl_path = os.environ.get("SCM_OBS_JSONL_PATH", "").strip()
    service_name = os.environ.get("SCM_OBS_SERVICE_NAME", "supercodemode").strip() or "supercodemode"
    otlp_endpoint = os.environ.get("SCM_OBS_OTLP_ENDPOINT", "").strip()
    run_id = os.environ.get("SCM_RUN_ID", "").strip() or uuid.uuid4().hex[:12]
    return ObservabilityConfig(
        backend=backend,
        jsonl_path=jsonl_path,
        service_name=service_name,
        otlp_endpoint=otlp_endpoint,
        run_id=run_id,
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
    else:
        _OBSERVER = NullObserver()
    return _OBSERVER


def emit_event(event: str, **fields: Any) -> None:
    try:
        get_observer().emit(event, **fields)
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
