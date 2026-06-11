import os
from typing import Any

from app.embed import embed_single
from app.store import QdrantStore

TOP_K = int(os.getenv("TOP_K", "5"))
SEUIL_SIMILARITE = float(os.getenv("SEUIL_SIMILARITE", "0.38"))

_store: QdrantStore | None = None


def get_store() -> QdrantStore:
    """
    Retourne une instance unique de QdrantStore.

    On évite de créer QdrantStore directement au chargement du fichier,
    car il essaie de se connecter à Qdrant dès son initialisation.
    """
    global _store

    if _store is None:
        _store = QdrantStore()

    return _store


def retrieve(question: str, top_k: int = TOP_K) -> dict[str, Any]:
    """
    Recherche les chunks les plus pertinents pour une question utilisateur.

    Cette fonction gère la partie retrieval :
    1. vectorisation de la question ;
    2. recherche top-k dans Qdrant ;
    3. conversion des résultats ;
    4. application du seuil de similarité ;
    5. retour de la décision d'acceptation ou de refus.
    """
    query_vector = embed_single(question)

    search_hits = get_store().search(query_vector, top_k=top_k)

    hits = [
        {
            "text": hit.text,
            "score": hit.score,
            "metadata": hit.metadata,
        }
        for hit in search_hits
    ]

    best_score = hits[0]["score"] if hits else None

    accepted = best_score is not None and best_score >= SEUIL_SIMILARITE

    return {
        "accepted": accepted,
        "hits": hits,
        "best_score": best_score,
        "threshold": SEUIL_SIMILARITE,
        "top_k": top_k,
    }