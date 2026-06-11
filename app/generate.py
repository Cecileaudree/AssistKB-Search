import os
from time import perf_counter
from typing import Any

from app.retrieve import retrieve

SEUIL_SIMILARITE = float(os.getenv("SEUIL_SIMILARITE", "0.35"))
TOP_K = int(os.getenv("TOP_K", "5"))

REFUS_MESSAGE = "Je ne dispose pas de cette information dans le corpus."


def extract_sources(hits: list[dict[str, Any]]) -> list[str]:
    """
    Extrait la liste des sources depuis les résultats de recherche.

    On supprime les doublons avec dict.fromkeys().
    Exemple :
    ["doc1.pdf", "doc1.pdf", "doc2.txt"] -> ["doc1.pdf", "doc2.txt"]
    """
    sources = []

    for hit in hits:
        source = hit.get("metadata", {}).get("source")
        if source:
            sources.append(source)

    return list(dict.fromkeys(sources))


def build_context(hits: list[dict[str, Any]]) -> str:
    """
    Transforme les chunks trouvés en bloc de contexte pour le LLM.

    Exemple :
    [Source 1 - cnil.pdf]
    Texte du chunk...

    [Source 2 - rgpd.txt]
    Texte du chunk...
    """
    context_parts = []

    for index, hit in enumerate(hits, start=1):
        source = hit.get("metadata", {}).get("source", "source inconnue")
        text = hit.get("text", "")

        context_parts.append(f"[Source {index} - {source}]\n{text}")

    return "\n\n".join(context_parts)


def build_prompt(question: str, context: str) -> str:
    """
    Construit le prompt anti-hallucination.

    Le but est de forcer le LLM à répondre uniquement avec le contexte fourni.
    """
    return f"""
Tu es un assistant de recherche sur une base de connaissances.

Règles :
- Réponds uniquement avec les informations présentes dans le contexte.
- Cite les sources utilisées.
- Si le contexte ne permet pas de répondre, dis : "{REFUS_MESSAGE}"
- N'invente jamais d'information.

Contexte :
{context}

Question :
{question}

Réponse :
""".strip()


def answer(question: str, top_k: int = TOP_K) -> dict[str, Any]:
    """
    Fonction principale appelée par l'API.

    Elle :
    1. récupère les chunks pertinents ;
    2. refuse si aucun chunk n'est trouvé ou si le score est trop faible ;
    3. construit un prompt si les chunks sont pertinents ;
    4. retournera ensuite la réponse du LLM.
    """
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

    context = build_context(hits)
    prompt = build_prompt(question, context)

    # TODO: remplacer cette réponse temporaire par un vrai appel LLM.
    generated_answer = (
        "Réponse temporaire : les sources sont trouvées, "
        "le prompt est construit, le LLM sera branché ensuite."
    )

    latency_ms = round((perf_counter() - start) * 1000)

    return {
        "answer": generated_answer,
        "sources": extract_sources(hits),
        "latency_ms": latency_ms,
        "tokens": {
            # Estimation temporaire : on compte les mots du prompt.
            # Plus tard, on récupérera les vrais tokens depuis l'API du LLM.
            "prompt": len(prompt.split()),
            "completion": len(generated_answer.split()),
        },
        "debug": {
            "best_score": hits[0].get("score"),
            "threshold": SEUIL_SIMILARITE,
            "top_k": top_k,
        },
    }