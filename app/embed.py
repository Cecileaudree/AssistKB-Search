"""
R2 - Embeddings
Charge all-MiniLM-L6-v2, vectorise les chunks en batchs,
normalise les vecteurs (L2) pour la similarité cosinus.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")
BATCH_SIZE = int(os.environ.get("EMBED_BATCH_SIZE", "64"))
CHUNKS_PATH = Path(os.environ.get("CHUNKS_PATH", "corpus/chunks.jsonl"))

# Singleton model — chargé une seule fois par processus
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Retourne le modèle d'embedding (singleton, chargé à la demande)."""
    global _model
    if _model is None:
        print(f"[embed] Chargement du modèle '{MODEL_NAME}'…")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Vectorise une liste de textes.

    Retourne un tableau float32 de shape (n, 384) avec vecteurs L2-normalisés.
    La normalisation L2 rend la similarité cosinus équivalente au produit scalaire,
    ce qui optimise les performances de recherche dans Qdrant.
    """
    if not texts:
        return np.empty((0, 384), dtype=np.float32)

    model = get_model()
    vectors: np.ndarray = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=len(texts) > BATCH_SIZE,
        convert_to_numpy=True,
        normalize_embeddings=True,  # normalisation L2 — obligatoire pour COSINE
    )
    return vectors.astype(np.float32)


def embed_single(text: str) -> np.ndarray:
    """
    Vectorise un texte unique (utilisé par retrieve.py pour les questions).
    Retourne un vecteur 1-D de shape (384,), L2-normalisé.
    """
    return embed_texts([text])[0]


# ──────────────────────────────────────────────────────────────────────────── #
# Pipeline complet : chunks.jsonl → Qdrant                                    #
# ──────────────────────────────────────────────────────────────────────────── #

def _iter_chunks(path: Path) -> Iterator[dict]:
    """Lit chunks.jsonl ligne par ligne (robuste aux fichiers volumineux)."""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def embed_and_index(chunks_path: Path = CHUNKS_PATH) -> None:
    """
    Lit corpus/chunks.jsonl, produit les embeddings en batchs,
    puis upsert dans Qdrant via QdrantStore.

    Idempotent : relancer cette fonction ne duplique pas les vecteurs
    (les IDs sont déterministes, voir store.py).
    """
    # Import local pour éviter la circularité au niveau module
    from app.store import QdrantStore

    if not chunks_path.exists():
        raise FileNotFoundError(
            f"[embed] Fichier introuvable : {chunks_path}\n"
            "Lancez d'abord app/ingest.py pour produire les chunks."
        )

    chunks = list(_iter_chunks(chunks_path))
    if not chunks:
        print("[embed] Aucun chunk dans", chunks_path)
        return

    print(f"[embed] {len(chunks)} chunks à vectoriser (modèle={MODEL_NAME}, batch={BATCH_SIZE})…")

    texts = [c["text"] for c in chunks]
    vectors = embed_texts(texts)

    print(f"[embed] Vecteurs produits — shape={vectors.shape}, dtype={vectors.dtype}")

    # Vérification de cohérence (dimension attendue : 384)
    assert vectors.shape[1] == 384, (
        f"Dimension inattendue : {vectors.shape[1]} (attendu 384). "
        "Vérifiez EMBED_MODEL."
    )

    store = QdrantStore()
    store.upsert(chunks, vectors)

    print(f"[embed] ✓ Indexation terminée — {len(chunks)} vecteurs dans Qdrant.")


if __name__ == "__main__":
    embed_and_index()
