
from time import perf_counter
from typing import Any
from app.llm import call_llm
from app.retrieve import retrieve

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
    Construit le prompt envoyé au LLM.
    Le seuil de similarité a déjà filtré les résultats non pertinents.
    """
    return f"""
Tu es un assistant de recherche basé sur un corpus documentaire.

Tu dois répondre uniquement avec les informations présentes dans le contexte fourni.

Règles :
- Si le contexte contient des éléments utiles, réponds avec ces éléments.
- Si l'information est partielle, donne une réponse partielle sans inventer.
- Ne complète jamais avec des connaissances externes.
- Cite les sources utilisées à la fin de la réponse.
- Refuse uniquement si aucun élément du contexte ne permet de répondre.
- Dans ce cas seulement, réponds exactement : "{REFUS_MESSAGE}"

Contexte :
{context}

Question :
{question}

Réponse :
""".strip()


def answer(question: str, top_k: int | None = None) -> dict[str, Any]:
    """
    Fonction principale appelée par l'API.

    Elle :
    1. appelle retrieve.py pour récupérer les chunks et appliquer le seuil ;
    2. refuse si le retrieval indique que le score est trop faible ;
    3. construit le contexte et le prompt ;
    4. appelle le LLM ;
    5. retourne réponse + sources + latence + tokens.
    """
    start = perf_counter()

    if top_k is None:
        retrieval_result = retrieve(question)
    else:
        retrieval_result = retrieve(question, top_k=top_k)

    hits = retrieval_result["hits"]

    debug = {
        "best_score": retrieval_result["best_score"],
        "threshold": retrieval_result["threshold"],
        "top_k": retrieval_result["top_k"],
        "retrieved_texts": [
            hit.get("text", "")[:300]
            for hit in hits
        ],
    }

    if not retrieval_result["accepted"]:
        latency_ms = round((perf_counter() - start) * 1000)

        return {
            "answer": REFUS_MESSAGE,
            "sources": [],
            "latency_ms": latency_ms,
            "tokens": {
                "prompt": 0,
                "completion": 0,
            },
            "debug": debug,
        }

    context = build_context(hits)
    prompt = build_prompt(question, context)

    generated_answer, tokens = call_llm(prompt)

    sources = extract_sources(hits)

    if generated_answer.strip() == REFUS_MESSAGE:
        sources = []

    latency_ms = round((perf_counter() - start) * 1000)

    return {
        "answer": generated_answer,
        "sources": sources,
        "latency_ms": latency_ms,
        "tokens": tokens,
        "debug": debug,
    }