from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median
from typing import Any


@dataclass
class ApiMetricsSummary:
    total_requests: int
    refusals: int
    refusal_rate: float
    latency_avg_ms: float
    latency_p50_ms: float
    latency_p95_ms: float
    tokens_avg: float
    cost_estimate_usd: float


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0

    sorted_values = sorted(values)
    index = round((len(sorted_values) - 1) * percent)
    return sorted_values[index]


def extract_token_count(tokens: dict[str, Any], *possible_keys: str) -> int:
    for key in possible_keys:
        value = tokens.get(key)
        if isinstance(value, int):
            return value
    return 0


def compute_refusal_rate(decision_flags: list[bool]) -> float:
    if not decision_flags:
        return 0.0
    return sum(1 for accepted in decision_flags if not accepted) / len(decision_flags)


def compute_latency_summary(latencies_ms: list[float]) -> dict[str, float]:
    if not latencies_ms:
        return {
            "latency_avg_ms": 0.0,
            "latency_p50_ms": 0.0,
            "latency_p95_ms": 0.0,
        }

    return {
        "latency_avg_ms": mean(latencies_ms),
        "latency_p50_ms": median(latencies_ms),
        "latency_p95_ms": percentile(latencies_ms, 0.95),
    }


def compute_token_summary(total_tokens: list[int]) -> dict[str, float]:
    if not total_tokens:
        return {"tokens_avg": 0.0}
    return {"tokens_avg": mean(total_tokens)}


def compute_cost_estimate(prompt_tokens: int, completion_tokens: int, prompt_price_per_1k: float = 0.03, completion_price_per_1k: float = 0.06) -> float:
    prompt_cost = prompt_tokens / 1000 * prompt_price_per_1k
    completion_cost = completion_tokens / 1000 * completion_price_per_1k
    return prompt_cost + completion_cost


def summarize_api_rows(rows: list[dict[str, Any]]) -> ApiMetricsSummary:
    total_requests = len(rows)
    refusals = sum(1 for row in rows if row.get("decision") == "refus")
    refusal_rate = compute_refusal_rate([row.get("decision") != "refus" for row in rows])

    latencies = [float(row.get("latency_ms", 0.0)) for row in rows]
    tokens = [int(row.get("total_tokens", 0)) for row in rows]

    latency_summary = compute_latency_summary(latencies)
    token_summary = compute_token_summary(tokens)

    total_prompt_tokens = sum(int(row.get("prompt_tokens", 0)) for row in rows)
    total_completion_tokens = sum(int(row.get("completion_tokens", 0)) for row in rows)
    cost_estimate = compute_cost_estimate(total_prompt_tokens, total_completion_tokens)

    return ApiMetricsSummary(
        total_requests=total_requests,
        refusals=refusals,
        refusal_rate=refusal_rate,
        latency_avg_ms=latency_summary["latency_avg_ms"],
        latency_p50_ms=latency_summary["latency_p50_ms"],
        latency_p95_ms=latency_summary["latency_p95_ms"],
        tokens_avg=token_summary["tokens_avg"],
        cost_estimate_usd=round(cost_estimate, 6),
    )
