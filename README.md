# AssistKB Search projet A 
# Membre de l'equipe
  Aurelie Demure(R3) Dina Chaouki(R2) Deumeni Cécile-Audrée (R1)
AssistKB Search est une application de recherche de documents basée sur des embeddings et Qdrant, avec une API FastAPI pour interroger un corpus.

## Architecture

- `app/` : logique principale du projet
  - `api.py` : serveur FastAPI exposant `/ask` et `/health`
  - `llm.py` : appel du LLM Google Gemini
  - `retrieve.py` : recherche de chunks dans Qdrant
  - `store.py` : gestion du store Qdrant
  - `embed.py` : génération d'embeddings et indexation
  - `generate.py` : construction du prompt et réponses basées sur le corpus
  - `ingest.py` : extraction et découpage du corpus en `corpus/chunks.jsonl`
- `fetch_corpus.ps1` : récupération de données publiques (`cert-fr`, `cnil`, `data.gouv`)
- `docker-compose.yml` : déploie Qdrant, l'indexeur et l'API
- `Dockerfile` : image Python pour l'application
- `requirements.txt` : dépendances Python
- `corpus/` : dossiers de données et chunks générés (ignoré par Git)

## Prérequis

- Python 3.10+
- Docker & Docker Compose
- Clé API Google Gemini dans `GEMINI_API_KEY`

## Installation

1. Copier le fichier d'environnement :

```powershell
copy .env.example .env
```

2. Remplir `.env`

- `GEMINI_API_KEY` : clé d'API Google Gemini
- `QDRANT_URL` : URL de Qdrant (`http://qdrant:6333` en Docker)
- `EMBED_MODEL` : modèle d'embedding (`all-MiniLM-L6-v2` par défaut)
- `CHUNKS_PATH` : chemin du fichier JSONL généré

3. Installer les dépendances (optionnel si vous utilisez Docker) :

```bash
pip install -r requirements.txt
```

## Flux de travail

### 1. Récupérer les données

Le script `fetch_corpus.ps1` télécharge des fichiers publics dans `corpus/raw/`.

```powershell
./fetch_corpus.ps1 -Profile open -DataQuery "intelligence artificielle"
```

### 2. Ingest et génération de chunks

Lancer le traitement du corpus pour produire `corpus/chunks.jsonl` :

```bash
python app/ingest.py
```

### 3. Démarrer en local avec Docker Compose

```bash
docker compose up -d
```

Cela démarre :

- `qdrant` : moteur vectoriel
- `indexer` : génération d'embeddings et insertion dans Qdrant
- `api` : API FastAPI exposée sur `http://localhost:8000`

### 4. Tester l'API

```bash
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "Quelle est la capitale de l’Australie ?"}'
```

### 5. Ou lancer l'API sans Docker

```bash
uvicorn app.api:app --reload --port 8000
```

## Structure du corpus

- `corpus/raw/` : fichiers sources téléchargés
- `corpus/chunks.jsonl` : corpus segmenté en chunks prêts à être indexés

`/corpus` est déjà ignoré dans `.gitignore`, donc les fichiers téléchargés ne sont pas suivis par Git.

## Notes

- `app/embed.py` produit des embeddings L2-normalisés pour une recherche cosine dans Qdrant.
- `app/generate.py` construit le prompt envoyé au LLM et formate la réponse avec les sources.
- `app/store.py` gère l'indexation et la recherche idempotente dans Qdrant.
- `app/llm.py` utilise `google-genai` pour appeler `gemini-2.5-flash`.

## Commandes utiles

- Recréer le corpus JSONL : `python app/ingest.py`
- Vérifier l'API : `http://localhost:8000/health`
- Relancer Docker Compose : `docker compose down && docker compose up -d`
- Recommencer l'indexation : supprimer `qdrant-data` ou la collection Qdrant puis relancer `docker compose up -d`

