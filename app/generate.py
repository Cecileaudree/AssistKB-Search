import os
from time import perf_counter

from app.retrieve import retrieve

SEUIL_SIMILARITE = float(os.getenv("SEUIL_SIMILARITE", "0.35"))
TOP_K = int(os.getenv("TOP_K", "5"))

REFUS_MESSAGE = "Je ne dispose pas de cette information dans le corpus."


def extract_sources(hits: list[dict]) -> list[str]:
    sources = []

    for hit in hits:
        source = hit.get("metadata", {}).get("source")
        if source:
            sources.append(source)

    return list(dict.fromkeys(sources))


def answer(question: str, top_k: int = TOP_K) -> dict:
    start = perf_counter()

    hits = retrieve(question, top_k=top_k)

    if not hits or hits[0].get("score", 0) < SEUIL_SIMILARITE:
        latency_ms = round((perf_counter() - start) * 1000)

        return {
            "answer": REFUS_MESSAGE,
            "sources": [],
            "latency_ms": latency_ms,
            "tokens": {
                "prompt": 0,
                "completion": 0,
            },
        }

    latency_ms = round((perf_counter() - start) * 1000)

    return {
        "answer": "Réponse temporaire : les sources sont trouvées, le LLM sera branché ensuite.",
        "sources": extract_sources(hits),
        "latency_ms": latency_ms,
        "tokens": {
            "prompt": 0,
            "completion": 0,
        },
    }