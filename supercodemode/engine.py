from __future__ import annotations

import inspect
from collections import Counter
from statistics import mean
from typing import Any, Mapping, Sequence

from .common import (
    baseline_candidate,
    build_two_tool_dataset,
    contains_reference_metric,
    tool_call_candidate,
    tuned_candidate,
)
from .env import bootstrap_reference_paths
from .observability import emit_event


def _build_adapter(runner: Any, metric_fn: Any) -> Any:
    bootstrap_reference_paths()
    try:
        from gepa.adapters.code_mode_adapter import CodeModeAdapter
    except Exception:
        # Fallback while adapter changes are being upstreamed to GEPA.
        from supercodemode.gepa_compat import CodeModeAdapter

    return CodeModeAdapter(runner=runner, metric_fn=metric_fn)


def evaluate_candidate(adapter: Any, candidate: dict[str, str]) -> dict[str, Any]:
    emit_event("engine.evaluate_candidate.start")
    dataset = build_two_tool_dataset()
    batch = adapter.evaluate(batch=dataset, candidate=candidate, capture_traces=True)
    out = {
        "scores": batch.scores,
        "avg": mean(batch.scores),
        "trajectories": batch.trajectories or [],
    }
    out["run_summary"] = _summarize_eval_result(out, candidate=candidate)
    _emit_run_summary_event("engine.evaluate_candidate.run_summary", out["run_summary"])
    for idx, traj in enumerate(out["trajectories"]):
        emit_event(
            "engine.evaluate_candidate.trajectory",
            item_index=idx,
            score=float(traj.get("score", 0.0)),
            selected_tool=traj.get("selected_tool"),
            tool_call_count=len(traj.get("tool_calls", []) or []),
            has_error=bool(traj.get("error")),
            error=str(traj.get("error") or ""),
        )
    emit_event("engine.evaluate_candidate.end", avg=out["avg"], num_scores=len(out["scores"]))
    return out


def run_showcase(runner: Any) -> dict[str, Any]:
    emit_event("engine.showcase.start")
    adapter = _build_adapter(runner=runner, metric_fn=contains_reference_metric)
    base = evaluate_candidate(adapter, baseline_candidate())
    tuned = evaluate_candidate(adapter, tuned_candidate())
    out = {
        "baseline": base,
        "tuned": tuned,
        "comparison_summary": _build_comparison_summary(base=base, tuned=tuned),
    }
    emit_event(
        "engine.showcase.end",
        baseline_avg=base["avg"],
        tuned_avg=tuned["avg"],
        delta_avg=out["comparison_summary"]["delta_avg"],
    )
    _emit_comparison_summary_event("engine.showcase.comparison_summary", out["comparison_summary"])
    return out


def run_benchmark(runner: Any) -> dict[str, Any]:
    """Compare multiple strategy profiles on the same runner/dataset."""
    emit_event("engine.benchmark.start")
    adapter = _build_adapter(runner=runner, metric_fn=contains_reference_metric)
    variants = {
        "tool_call": evaluate_candidate(adapter, tool_call_candidate()),
        "codemode_baseline": evaluate_candidate(adapter, baseline_candidate()),
        "codemode_optimized": evaluate_candidate(adapter, tuned_candidate()),
    }
    ranking = sorted(
        (
            {
                "name": name,
                "avg": float(result.get("avg", 0.0)),
                "summary": result.get("run_summary", {}),
            }
            for name, result in variants.items()
        ),
        key=lambda item: item["avg"],
        reverse=True,
    )
    leader = ranking[0]["name"] if ranking else ""
    out = {
        "variants": variants,
        "benchmark_summary": {
            "ranking": ranking,
            "leader": leader,
            "delta_vs_tool_call": {
                "codemode_baseline": float(variants["codemode_baseline"]["avg"]) - float(variants["tool_call"]["avg"]),
                "codemode_optimized": float(variants["codemode_optimized"]["avg"])
                - float(variants["tool_call"]["avg"]),
            },
            "delta_optimized_vs_baseline": float(variants["codemode_optimized"]["avg"])
            - float(variants["codemode_baseline"]["avg"]),
        },
    }
    emit_event(
        "engine.benchmark.end",
        leader=leader,
        tool_call_avg=float(variants["tool_call"]["avg"]),
        codemode_baseline_avg=float(variants["codemode_baseline"]["avg"]),
        codemode_optimized_avg=float(variants["codemode_optimized"]["avg"]),
    )
    _emit_benchmark_summary_event("engine.benchmark.summary", out["benchmark_summary"])
    return out


def _custom_proposer(
    candidate: dict[str, str],
    reflective_dataset: Mapping[str, Sequence[Mapping[str, Any]]],
    components_to_update: list[str],
) -> dict[str, str]:
    del candidate
    tuned = tuned_candidate()

    should_improve = False
    for records in reflective_dataset.values():
        for rec in records:
            feedback = str(rec.get("Feedback", "")).lower()
            if "low score" in feedback or "failed" in feedback or "error" in feedback:
                should_improve = True
                break
        if should_improve:
            break

    if not should_improve:
        return {}

    updates: dict[str, str] = {}
    for component in components_to_update:
        if component in tuned:
            updates[component] = tuned[component]
    return updates


def run_optimize(runner: Any, max_metric_calls: int = 20, seed: int = 0) -> dict[str, Any]:
    emit_event("engine.optimize.start", max_metric_calls=max_metric_calls, seed=seed)
    bootstrap_reference_paths()
    import gepa

    adapter = _build_adapter(runner=runner, metric_fn=contains_reference_metric)
    dataset = build_two_tool_dataset()

    sig = inspect.signature(gepa.optimize)
    if "custom_candidate_proposer" in sig.parameters:
        result = gepa.optimize(
            seed_candidate=baseline_candidate(),
            trainset=dataset,
            valset=dataset,
            adapter=adapter,
            custom_candidate_proposer=_custom_proposer,
            max_metric_calls=max_metric_calls,
            seed=seed,
        )
        out = {
            "best_score": result.val_aggregate_scores[result.best_idx],
            "best_candidate": result.best_candidate,
        }
        out["run_summary"] = _build_optimize_summary(
            best_score=float(out["best_score"]),
            best_candidate=out["best_candidate"],
            mode="gepa_custom_proposer",
            max_metric_calls=max_metric_calls,
            seed=seed,
        )
        _emit_optimize_summary_event("engine.optimize.run_summary", out["run_summary"])
        emit_event("engine.optimize.end", best_score=out["best_score"], mode="gepa_custom_proposer")
        return out

    # GEPA API variant without `custom_candidate_proposer`: run deterministic
    # compatibility optimization for reproducible local demos without LLM setup.
    base_eval = evaluate_candidate(adapter, baseline_candidate())
    tuned_eval = evaluate_candidate(adapter, tuned_candidate())
    if tuned_eval["avg"] >= base_eval["avg"]:
        out = {"best_score": tuned_eval["avg"], "best_candidate": tuned_candidate(), "mode": "deterministic_fallback"}
        out["run_summary"] = _build_optimize_summary(
            best_score=float(out["best_score"]),
            best_candidate=out["best_candidate"],
            mode=out["mode"],
            max_metric_calls=max_metric_calls,
            seed=seed,
            baseline_avg=float(base_eval["avg"]),
            tuned_avg=float(tuned_eval["avg"]),
        )
        _emit_optimize_summary_event("engine.optimize.run_summary", out["run_summary"])
        emit_event("engine.optimize.end", best_score=out["best_score"], mode=out["mode"])
        return out
    out = {"best_score": base_eval["avg"], "best_candidate": baseline_candidate(), "mode": "deterministic_fallback"}
    out["run_summary"] = _build_optimize_summary(
        best_score=float(out["best_score"]),
        best_candidate=out["best_candidate"],
        mode=out["mode"],
        max_metric_calls=max_metric_calls,
        seed=seed,
        baseline_avg=float(base_eval["avg"]),
        tuned_avg=float(tuned_eval["avg"]),
    )
    _emit_optimize_summary_event("engine.optimize.run_summary", out["run_summary"])
    emit_event("engine.optimize.end", best_score=out["best_score"], mode=out["mode"])
    return out


def _summarize_eval_result(eval_result: Mapping[str, Any], *, candidate: Mapping[str, str]) -> dict[str, Any]:
    trajectories = list(eval_result.get("trajectories", []) or [])
    scores = [float(x) for x in (eval_result.get("scores", []) or [])]
    selected_tool_counts = Counter()
    error_categories = Counter()
    tool_call_count_total = 0
    error_count = 0
    for traj in trajectories:
        tool = traj.get("selected_tool")
        if isinstance(tool, str) and tool:
            selected_tool_counts[tool] += 1
        tool_call_count_total += len(traj.get("tool_calls", []) or [])
        err = traj.get("error")
        if err:
            error_count += 1
            error_categories[_classify_error(str(err))] += 1

    avg_score = float(eval_result.get("avg", mean(scores) if scores else 0.0))
    num_examples = len(scores)
    return {
        "num_examples": num_examples,
        "avg_score": avg_score,
        "pass_count": sum(1 for s in scores if s > 0.0),
        "error_count": error_count,
        "tool_call_count_total": tool_call_count_total,
        "tool_call_count_avg": (tool_call_count_total / num_examples) if num_examples else 0.0,
        "selected_tools": dict(selected_tool_counts),
        "error_categories": dict(error_categories),
        "candidate_fields": sorted([k for k, v in candidate.items() if isinstance(v, str) and v]),
        "candidate_field_lengths": {
            k: len(v) for k, v in candidate.items() if isinstance(k, str) and isinstance(v, str)
        },
    }


def _build_comparison_summary(*, base: Mapping[str, Any], tuned: Mapping[str, Any]) -> dict[str, Any]:
    base_sum = dict(base.get("run_summary", {}))
    tuned_sum = dict(tuned.get("run_summary", {}))
    baseline_avg = float(base.get("avg", 0.0))
    tuned_avg = float(tuned.get("avg", 0.0))
    delta = tuned_avg - baseline_avg
    winner = "tie"
    if delta > 0:
        winner = "tuned"
    elif delta < 0:
        winner = "baseline"

    return {
        "baseline_avg": baseline_avg,
        "tuned_avg": tuned_avg,
        "delta_avg": delta,
        "winner": winner,
        "baseline": base_sum,
        "tuned": tuned_sum,
    }


def _build_optimize_summary(
    *,
    best_score: float,
    best_candidate: Mapping[str, Any],
    mode: str,
    max_metric_calls: int,
    seed: int,
    baseline_avg: float | None = None,
    tuned_avg: float | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "mode": mode,
        "best_score": best_score,
        "max_metric_calls": max_metric_calls,
        "seed": seed,
        "best_candidate_fields": sorted(best_candidate.keys()),
        "best_candidate_field_lengths": {
            k: len(v) for k, v in best_candidate.items() if isinstance(k, str) and isinstance(v, str)
        },
    }
    if baseline_avg is not None:
        out["baseline_avg"] = baseline_avg
    if tuned_avg is not None:
        out["tuned_avg"] = tuned_avg
        if baseline_avg is not None:
            out["delta_vs_baseline"] = tuned_avg - baseline_avg
    return out


def _emit_run_summary_event(event_name: str, summary: Mapping[str, Any]) -> None:
    emit_event(
        event_name,
        num_examples=int(summary.get("num_examples", 0)),
        avg_score=float(summary.get("avg_score", 0.0)),
        pass_count=int(summary.get("pass_count", 0)),
        error_count=int(summary.get("error_count", 0)),
        tool_call_count_total=int(summary.get("tool_call_count_total", 0)),
        tool_call_count_avg=float(summary.get("tool_call_count_avg", 0.0)),
        selected_tools=summary.get("selected_tools", {}),
        error_categories=summary.get("error_categories", {}),
    )


def _emit_comparison_summary_event(event_name: str, summary: Mapping[str, Any]) -> None:
    emit_event(
        event_name,
        baseline_avg=float(summary.get("baseline_avg", 0.0)),
        tuned_avg=float(summary.get("tuned_avg", 0.0)),
        delta_avg=float(summary.get("delta_avg", 0.0)),
        winner=str(summary.get("winner", "")),
    )


def _emit_benchmark_summary_event(event_name: str, summary: Mapping[str, Any]) -> None:
    ranking = summary.get("ranking", [])
    emit_event(
        event_name,
        leader=str(summary.get("leader", "")),
        ranking=[item.get("name", "") for item in ranking if isinstance(item, dict)],
        delta_vs_tool_call=summary.get("delta_vs_tool_call", {}),
        delta_optimized_vs_baseline=float(summary.get("delta_optimized_vs_baseline", 0.0)),
    )


def _emit_optimize_summary_event(event_name: str, summary: Mapping[str, Any]) -> None:
    emit_event(
        event_name,
        mode=str(summary.get("mode", "")),
        best_score=float(summary.get("best_score", 0.0)),
        max_metric_calls=int(summary.get("max_metric_calls", 0)),
        seed=int(summary.get("seed", 0)),
        baseline_avg=float(summary.get("baseline_avg", 0.0)) if "baseline_avg" in summary else None,
        tuned_avg=float(summary.get("tuned_avg", 0.0)) if "tuned_avg" in summary else None,
        delta_vs_baseline=float(summary.get("delta_vs_baseline", 0.0)) if "delta_vs_baseline" in summary else None,
    )


def _classify_error(error: str) -> str:
    msg = (error or "").lower()
    if not msg:
        return "none"
    if "401" in msg or "unauthorized" in msg or "forbidden" in msg:
        return "auth"
    if "timeout" in msg or "timed out" in msg:
        return "timeout"
    if "validation" in msg or "invalid arguments" in msg or "schema" in msg:
        return "schema_mismatch"
    if "mcp" in msg and ("connect" in msg or "transport" in msg or "stream" in msg):
        return "mcp_transport"
    if "docker" in msg:
        return "sandbox_docker"
    if "monty" in msg:
        return "sandbox_monty"
    if "execution error" in msg or "executor" in msg or "internal error" in msg:
        return "runtime_execution"
    return "other"
