# Compte rendu - Projet A : AssistKB Search

> Template a copier dans `docs/COMPTE-RENDU.md` de votre repo et a
> remplir. Les 8 premieres sections sont **obligatoires** pour le rendu
> fin de journee. Les sections 9 a 11 sont pour le rendu complet
> (semaine +1, optionnel). Conformite verifiee via
> [STRUCTURE-RENDU.md](../STRUCTURE-RENDU.md).

-----

## 1\. Presentation

  - **Equipe** : ***\_**\_***\_
  - **Membres et roles** :
  - ***\_***\_\_\_\_\_\_ - R1 Data / Ingestion
  - ***\_***\_\_\_\_\_\_ - R2 Embeddings / Index
  - ***\_***\_\_\_\_\_\_ - R3 Retrieval / LLM
  - ***\_***\_\_\_\_\_\_ - R4 DevOps / Observabilite
  - **Projet** : A - AssistKB Search (vector store Qdrant)
  - **Depot GitHub** : https://github.com/***\_**\_***\_

## 2\. Objectif

> En 5 lignes : que fait votre RAG, sur quel corpus, pour quel besoin
> (lien fil rouge AssistKB-Neosoft).

## 3\. Architecture

> Inserez votre schema (Mermaid). Decrivez chaque composant et les flux.

``` mermaid
flowchart LR
    t_q["Question"] -->|"embedding"| t_search["Qdrant top-k"]
    t_search -->|"contexte + sources"| t_llm["LLM"]
    t_llm -->|"reponse citee"| t_api["API /ask"]
```

## 4\. Fonctionnement

> Le parcours d'une question, etape par etape : reception API -\>
> embedding -\> recherche Qdrant -\> seuil de refus -\> prompt -\> LLM
> -\> reponse + sources. Precisez votre **seuil de similarite**.

## 5\. Structure du projet

> Arborescence commentee (quel fichier fait quoi).

## 6\. Choix techniques (le pourquoi)

| Choix                 | Valeur retenue       | Justification        |
| --------------------- | -------------------- | -------------------- |
| Modele embeddings     | all-MiniLM-L6-v2     | ***\_***\_\_\_\_\_\_ |
| Vector store          | Qdrant               | ***\_***\_\_\_\_\_\_ |
| Distance              | ***\_***\_\_\_\_\_\_ | ***\_***\_\_\_\_\_\_ |
| chunk\_size / overlap | ***\_* /** \_\_\_    | ***\_***\_\_\_\_\_\_ |
| top\_k                | \_\_\_\_\_           | ***\_***\_\_\_\_\_\_ |
| seuil de refus        | \_\_\_\_\_           | ***\_***\_\_\_\_\_\_ |
| LLM                   | ***\_***\_\_\_\_\_\_ | ***\_***\_\_\_\_\_\_ |

## 7\. Resultats / metriques

| Metrique                                | Valeur               | Commentaire                            |
| --------------------------------------- | -------------------- | -------------------------------------- |
| Score similarite moyen (top-k)          | \_\_\_\_\_           | qualite retrieval                      |
| Taux de refus (questions hors corpus)   | \_\_\_\_\_ %         | doit etre eleve sur le lot hors-corpus |
| Latence p50 / p95                       | ***\_* /** \_\_\_ ms | exploitation                           |
| Tokens moyens (prompt + completion)     | \_\_\_\_\_           | FinOps                                 |
| Cout projete "si paye" / 1000 questions | \_\_\_\_\_ USD       | cf. app/metrics.py                     |

> Joignez une capture de 2-3 questions/reponses (une qui repond, une qui
> refuse).

## 8\. Difficultes et limites

> Ce qui n'a pas marche, ce que vous feriez avec plus de temps.

-----

## 9\. (Bonus) Evaluation - golden dataset

> 10 questions de reference avec la source attendue. recall@k mesure.

## 10\. (Bonus) Reranking

> Effet du cross-encoder sur la pertinence (avant/apres).

## 11\. (Bonus) Pistes d'amelioration

> Recherche hybride (BM25 + vectoriel), optimisation cout/latence, etc.
