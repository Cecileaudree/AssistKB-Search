import statistics
import time
from typing import Any

import requests
from app.metrics import summarize_api_rows

# docker compose exec api python -m analytics.evaluate_api_metrics

API_URL = "http://localhost:8000/ask"

questions = [
    "Quels sont les critères d'inclusion d'un outil ?",
    "Comment les données sont-elles collectées ?",
    "Quelle est la fréquence de mise à jour du jeu de données ?",
    "Combien d’outils IA sont recensés dans l’annuaire ?",
    "Quelle est la météo demain ?",
    "Quelle est la recette de la tarte aux pommes ?",
]


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0

    values = sorted(values)
    index = round((len(values) - 1) * percent)
    return values[index]


def get_token_value(tokens: dict[str, Any], *possible_keys: str) -> int:
    for key in possible_keys:
        value = tokens.get(key)
        if isinstance(value, int):
            return value
    return 0


def evaluate_api_metrics() -> None:
    rows = []

    for question in questions:
        start = time.perf_counter()

        response = requests.post(
            API_URL,
            json={"question": question},
            timeout=180,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        response.raise_for_status()
        data = response.json()

        tokens = data.get("tokens", {})

        prompt_tokens = get_token_value(tokens, "prompt", "prompt_tokens", "input_tokens")
        completion_tokens = get_token_value(tokens, "completion", "completion_tokens", "output_tokens")
        total_tokens = prompt_tokens + completion_tokens

        latency_ms = data.get("latency_ms", elapsed_ms)

        answer = data.get("answer", "")
        is_refusal = "Je ne dispose pas de cette information" in answer

        rows.append(
            {
                "question": question,
                "latency_ms": round(float(latency_ms), 2),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "decision": "refus" if is_refusal else "réponse",
            }
        )

    latencies = [row["latency_ms"] for row in rows]
    total_tokens_values = [row["total_tokens"] for row in rows]

    summary = summarize_api_rows(rows)

    output_path = "analytics/resultats_api_metrics.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("## Mesures par question\n\n")
        f.write("| Question | Décision | Latence ms | Tokens prompt | Tokens completion | Tokens total |\n")
        f.write("|---|---|---:|---:|---:|---:|\n")

        for row in rows:
            f.write(
                f"| {row['question']} | {row['decision']} | {row['latency_ms']} | "
                f"{row['prompt_tokens']} | {row['completion_tokens']} | {row['total_tokens']} |\n"
            )

        f.write("\n## Synthèse\n\n")
        f.write("| Métrique | Valeur |\n")
        f.write("|---|---:|\n")
        f.write(f"| Total de requêtes | {summary.total_requests} |\n")
        f.write(f"| Taux de refus | {summary.refusal_rate:.2%} |\n")
        f.write(f"| Latence moyenne | {summary.latency_avg_ms:.2f} ms |\n")
        f.write(f"| Latence p50 | {summary.latency_p50_ms:.2f} ms |\n")
        f.write(f"| Latence p95 | {summary.latency_p95_ms:.2f} ms |\n")
        f.write(f"| Tokens moyens | {summary.tokens_avg:.2f} |\n")
        f.write(f"| Coût estimé | ${summary.cost_estimate_usd:.6f} |\n")

    print(f"Tableau généré : {output_path}")


if __name__ == "__main__":
    evaluate_api_metrics()