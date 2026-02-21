from __future__ import annotations

import inspect
from statistics import mean
from typing import Any, Mapping, Sequence

from .common import baseline_candidate, build_two_tool_dataset, contains_reference_metric, tuned_candidate
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
    emit_event("engine.evaluate_candidate.end", avg=out["avg"], num_scores=len(out["scores"]))
    return out


def run_showcase(runner: Any) -> dict[str, Any]:
    emit_event("engine.showcase.start")
    adapter = _build_adapter(runner=runner, metric_fn=contains_reference_metric)
    base = evaluate_candidate(adapter, baseline_candidate())
    tuned = evaluate_candidate(adapter, tuned_candidate())
    out = {"baseline": base, "tuned": tuned}
    emit_event(
        "engine.showcase.end",
        baseline_avg=base["avg"],
        tuned_avg=tuned["avg"],
    )
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
        emit_event("engine.optimize.end", best_score=out["best_score"], mode="gepa_custom_proposer")
        return out

    # GEPA API variant without `custom_candidate_proposer`: run deterministic
    # compatibility optimization for reproducible local demos without LLM setup.
    base_eval = evaluate_candidate(adapter, baseline_candidate())
    tuned_eval = evaluate_candidate(adapter, tuned_candidate())
    if tuned_eval["avg"] >= base_eval["avg"]:
        out = {"best_score": tuned_eval["avg"], "best_candidate": tuned_candidate(), "mode": "deterministic_fallback"}
        emit_event("engine.optimize.end", best_score=out["best_score"], mode=out["mode"])
        return out
    out = {"best_score": base_eval["avg"], "best_candidate": baseline_candidate(), "mode": "deterministic_fallback"}
    emit_event("engine.optimize.end", best_score=out["best_score"], mode=out["mode"])
    return out
