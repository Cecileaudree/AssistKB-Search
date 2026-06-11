import os
from typing import Any

from app.embed import embed_single
from app.store import QdrantStore

TOP_K = int(os.getenv("TOP_K", "5"))

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


def retrieve(question: str, top_k: int = TOP_K) -> list[dict[str, Any]]:
    """
    Recherche les chunks les plus pertinents pour une question utilisateur.

    Étapes :
    1. transformer la question en vecteur avec embed_single ;
    2. chercher les top_k chunks dans Qdrant ;
    3. convertir les SearchHit en dictionnaires compatibles avec generate.py.
    """
    query_vector = embed_single(question)

    hits = get_store().search(query_vector, top_k=top_k)

    return [
        {
            "text": hit.text,
            "score": hit.score,
            "metadata": hit.metadata,
        }
        for hit in hits
    ]