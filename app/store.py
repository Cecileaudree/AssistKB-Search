"""
R2 - QdrantStore
Adaptateur Qdrant : crée la collection si besoin, upsert idempotent, search top-k.

Choix techniques :
  - Distance  : COSINE  (vecteurs L2-normalisés → cosine == dot-product, plus rapide)
  - Dimension : 384     (all-MiniLM-L6-v2)
  - Idempotence : UUID v5 déterministe calculé à partir de (source, chunk_index)
                  ⟹ relancer embed ne duplique pas les points
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    PointStruct,
    VectorParams,
)

# ──────────────────────────────────────────────────────────────────────────── #
# Configuration (surchargeable via variables d'environnement)                 #
# ──────────────────────────────────────────────────────────────────────────── #

QDRANT_URL       = os.environ.get("QDRANT_URL",        "http://qdrant:6333")
COLLECTION_NAME  = os.environ.get("QDRANT_COLLECTION", "assistkb")
VECTOR_DIM       = 384          # all-MiniLM-L6-v2
DISTANCE         = Distance.COSINE   # cosinus pour vecteurs normalisés


# ──────────────────────────────────────────────────────────────────────────── #
# Résultat de recherche                                                        #
# ──────────────────────────────────────────────────────────────────────────── #

@dataclass
class SearchHit:
    """Un chunk retrouvé par Qdrant avec son score de similarité."""
    id:       str
    score:    float
    text:     str
    metadata: dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────── #
# QdrantStore                                                                  #
# ──────────────────────────────────────────────────────────────────────────── #

class QdrantStore:
    """
    Adaptateur haut niveau pour Qdrant.

    Utilisation :
        store = QdrantStore()
        store.upsert(chunks, vectors)   # indexation
        hits  = store.search(vec, k=5)  # retrieval
    """

    def __init__(self) -> None:
        self._client = QdrantClient(url=QDRANT_URL, timeout=30)
        self._ensure_collection()

    # ── Collection ────────────────────────────────────────────────────────── #

    def _ensure_collection(self) -> None:
        """
        Crée la collection Qdrant si elle n'existe pas encore.
        Idempotent : aucune action si la collection existe déjà.
        """
        existing = {c.name for c in self._client.get_collections().collections}
        if COLLECTION_NAME not in existing:
            self._client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_DIM,
                    distance=DISTANCE,
                ),
            )
            print(
                f"[store] Collection '{COLLECTION_NAME}' créée "
                f"(dim={VECTOR_DIM}, distance={DISTANCE.value})."
            )
        else:
            print(f"[store] Collection '{COLLECTION_NAME}' déjà existante — pas de recréation.")

    def delete_collection(self) -> None:
        """Supprime et recrée la collection (utile pour les tests)."""
        self._client.delete_collection(COLLECTION_NAME)
        print(f"[store] Collection '{COLLECTION_NAME}' supprimée.")
        self._ensure_collection()

    # ── Idempotence ───────────────────────────────────────────────────────── #

    @staticmethod
    def _get_meta(chunk: dict, field: str, default=None):
        """
        Lit un champ de métadonnée en supportant deux schémas :
          - Schéma plat  : {"text": ..., "source": ..., "chunk_index": ...}
          - Schéma R1    : {"text": ..., "metadata": {"source": ..., "chunk_index": ...}}
        """
        # Priorité au champ plat, fallback dans le dict 'metadata' imbriqué
        return chunk.get(field) if chunk.get(field) is not None \
            else chunk.get("metadata", {}).get(field, default)

    @staticmethod
    def _chunk_id(chunk: dict) -> str:
        """
        Génère un UUID v5 déterministe à partir de (source, chunk_index).

        La même clé produit toujours le même UUID :
          - Qdrant fait un UPSERT → le point existant est mis à jour, pas dupliqué.
          - Relancer embed_and_index plusieurs fois est donc sans danger.
        """
        source = QdrantStore._get_meta(chunk, "source", "unknown")
        idx    = QdrantStore._get_meta(chunk, "chunk_index", 0)
        key = f"{source}::{idx}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, key))

    # ── Upsert ────────────────────────────────────────────────────────────── #

    def upsert(
        self,
        chunks: list[dict],
        vectors: np.ndarray,
        batch_size: int = 128,
    ) -> None:
        """
        Insère ou met à jour les vecteurs dans Qdrant.

        Args:
            chunks    : liste de dicts avec au minimum 'text', 'source', 'chunk_index'.
            vectors   : tableau numpy float32 de shape (n, 384), L2-normalisé.
            batch_size: taille des batchs d'upsert (évite les timeouts sur grands corpus).
        """
        if len(chunks) != len(vectors):
            raise ValueError(
                f"Nombre de chunks ({len(chunks)}) ≠ nombre de vecteurs ({len(vectors)})."
            )

        points: list[PointStruct] = []
        for chunk, vector in zip(chunks, vectors):
            point_id = self._chunk_id(chunk)
            # Résoudre les champs selon le schéma (plat ou imbriqué R1)
            meta_dict = chunk.get("metadata", {})
            payload: dict[str, Any] = {
                "text":        chunk.get("text", ""),
                "source":      self._get_meta(chunk, "source", ""),
                "chunk_index": self._get_meta(chunk, "chunk_index", 0),
            }
            # Métadonnées additionnelles (type_doc, langue, position…)
            for k, v in meta_dict.items():
                if k not in payload:
                    payload[k] = v
            # Champs plats restants
            for k, v in chunk.items():
                if k not in payload and k != "metadata":
                    payload[k] = v

            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector.tolist(),
                    payload=payload,
                )
            )

        total = len(points)
        for i in range(0, total, batch_size):
            batch = points[i : i + batch_size]
            self._client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch,
                wait=True,  # attend la confirmation avant de continuer
            )
            end = min(i + batch_size, total)
            print(f"[store] Upsert {i + 1}–{end} / {total}")

        print(f"[store] ✓ {total} points upsertés dans '{COLLECTION_NAME}'.")

    # ── Search ────────────────────────────────────────────────────────────── #

    def search(self, vector: np.ndarray, top_k: int = 5) -> list[SearchHit]:
        """
        Cherche les top_k chunks les plus proches du vecteur requête.

        Args:
            vector: vecteur 1-D de shape (384,), L2-normalisé.
            top_k : nombre de résultats à retourner.

        Returns:
            Liste de SearchHit triée par score décroissant (meilleur en premier).
            Score compris entre 0 et 1 (similarité cosinus après normalisation).
        """
        raw = self._client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector.tolist(),
            limit=top_k,
            with_payload=True,
        )

        hits: list[SearchHit] = []
        for r in raw:
            metadata = {k: v for k, v in r.payload.items() if k != "text"}
            hits.append(
                SearchHit(
                    id=str(r.id),
                    score=float(r.score),
                    text=r.payload.get("text", ""),
                    metadata=metadata,
                )
            )
        return hits

    # ── Utilitaires ───────────────────────────────────────────────────────── #

    def count(self) -> int:
        """Retourne le nombre de vecteurs indexés dans la collection."""
        info = self._client.get_collection(COLLECTION_NAME)
        return info.points_count or 0
