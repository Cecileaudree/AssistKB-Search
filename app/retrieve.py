import os
from typing import Any

TOP_K = int(os.getenv("TOP_K", "5"))


def retrieve(question: str, top_k: int = TOP_K) -> list[dict[str, Any]]:
    """
    Recherche les chunks les plus pertinents.

    Version temporaire : sera branchée ensuite sur Qdrant.
    """
    return []