import os
import json
import glob
import re
from pathlib import Path
from typing import List, Dict, Any

# Stratégie de Chunking (Variables globales faciles à modifier pour vos tests)
CHUNK_SIZE = 500       # Nombre de caractères par chunk (~100-150 mots)
CHUNK_OVERLAP = 100    # Recouvrement pour ne pas couper le contexte au milieu d'une phrase

def clean_text(text: str) -> str:
    """Nettoie le texte des sauts de ligne excessifs et des encodages brisés."""
    if not text:
        return ""
    # Remplacement des espaces/sauts de ligne multiples par un seul espace
    text = re.sub(r'\s+', ' ', text)
    # Nettoyage basique des caractères spéciaux bizarres d'encodage
    text = text.encode("utf-8", errors="ignore").decode("utf-8")
    return text.strip()

def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Découpe un texte en morceaux de taille fixe avec un recouvrement."""
    chunks = []
    if len(text) <= chunk_size:
        return [text] if text else []
        
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (chunk_size - overlap)
    return chunks

def extract_from_json(file_path: Path) -> List[Dict[str, Any]]:
    """Extrait les données si le fichier téléchargé est un JSON (ex: métadonnées data.gouv)."""
    documents = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Si c'est une liste d'articles ou de lignes
        if isinstance(data, list):
            for idx, item in enumerate(data):
                # On cherche des clés textuelles courantes
                content = item.get("text") or item.get("content") or item.get("description") or str(item)
                documents.append({
                    "content": clean_text(content),
                    "meta": {"position": f"item_{idx}"}
                })
        elif isinstance(data, dict):
            content = data.get("text") or data.get("content") or data.get("description") or json.dumps(data)
            documents.append({
                "content": clean_text(content),
                "meta": {"position": "root"}
            })
    except Exception as e:
        print(f"[-] Erreur lors de la lecture du JSON {file_path}: {e}")
    return documents

def extract_from_txt(file_path: Path) -> List[Dict[str, Any]]:
    """Extrait le texte d'un fichier TXT ou Markdown classique."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return [{"content": clean_text(content), "meta": {"position": "full_text"}}]
    except Exception as e:
        print(f"[-] Erreur lors de la lecture du TXT {file_path}: {e}")
        return []

def process_corpus(input_dir: str, output_file: str):
    """Parcourt le dossier du corpus, extrait, découpe et sauvegarde en JSONL."""
    input_path = Path(input_dir)
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    total_chunks = 0
    
    with open(output_path, 'w', encoding='utf-8') as f_out:
        # Recherche récursive de tous les fichiers (txt, md, json, etc.)
        # Note : Si vous avez des vrais PDF, ajoutez la bibliothèque 'pypdf' ici.
        file_patterns = ["**/*.txt", "**/*.md", "**/*.json"]
        files = []
        for pattern in file_patterns:
            files.extend(input_path.glob(pattern))
            
        print(f"[+] {len(files)} fichiers trouvés dans '{input_dir}' à traiter.")
        
        for file_path in files:
            # Détermination du type de fichier
            ext = file_path.suffix.lower()
            docs = []
            
            if ext == '.json':
                docs = extract_from_json(file_path)
            else: # .txt ou .md
                docs = extract_from_txt(file_path)
                
            for doc in docs:
                text_content = doc["content"]
                if not text_content or len(text_content) < 20: # On ignore les morceaux vides ou trop courts
                    continue
                    
                # Chunking
                text_chunks = chunk_text(text_content, CHUNK_SIZE, CHUNK_OVERLAP)
                
                for chunk_idx, chunk_text_data in enumerate(text_chunks):
                    # Construction de la ligne JSONL avec métadonnées enrichies
                    chunk_entry = {
                        "text": chunk_text_data,
                        "metadata": {
                            "source": file_path.name,
                            "type": "seed" if "seed" in str(file_path) else "data_gouv",
                            "chunk_index": chunk_idx,
                            "total_chunks_file": len(text_chunks),
                            "sub_position": doc["meta"].get("position", "unknown")
                        }
                    }
                    # Écriture immédiate dans le fichier d'échange JSONL
                    f_out.write(json.dumps(chunk_entry, ensure_ascii=False) + "\n")
                    total_chunks += 1

    print(f"[+] Ingestion terminée. {total_chunks} chunks générés dans '{output_file}'.")

if __name__ == "__main__":
    # Chemins par défaut selon l'architecture du projet
    CORPUS_DIR = "corpus"
    OUTPUT_JSONL = "corpus/chunks.jsonl"
    
    process_corpus(CORPUS_DIR, OUTPUT_JSONL)