from app.retrieve import retrieve

# commande pour lancer le script : docker compose exec api python -m analytics.evaluate_similarity

TOP_K = 5
SEUIL = 0.35

questions = [
    {
        "question": "Quelle est la météo demain ?",
        "type": "hors_corpus",
        "attendu": "refus",
    },
    {
        "question": "Qui a gagné la Coupe du monde 2018 ?",
        "type": "hors_corpus",
        "attendu": "refus",
    },
    {
        "question": "Quelle est la recette de la tarte aux pommes ?",
        "type": "hors_corpus",
        "attendu": "refus",
    },
    {
        "question": "Quelle est la capitale du Japon ?",
        "type": "hors_corpus",
        "attendu": "refus",
    },
    {
        "question": "Quels sont les critères d'inclusion d'un outil ? ",
        "type": "dans_corpus",
        "attendu": "réponse",
    },
    {
        "question": "Comment les données sont elles collectées ? ",
        "type": "dans_corpus",
        "attendu": "réponse",
    },
    {
        "question": "Quelle est la fréquence de mise à jour du jeu de données ?",
        "type": "dans_corpus",
        "attendu": "réponse",
    },
    {
        "question": "Combien d’outils IA sont recensés dans l’annuaire ?",
        "type": "dans_corpus",
        "attendu": "réponse",
    },
]

rows = []

for item in questions:
    result = retrieve(item["question"], top_k=TOP_K)

    hits = result["hits"]
    best_score = result["best_score"]
    threshold = result["threshold"]
    accepted = result["accepted"]

    if not hits:
      avg_score = 0
      source_top_1 = "-"
    else:
      avg_score = sum(hit.get("score", 0) for hit in hits) / len(hits)
      source_top_1 = hits[0].get("metadata", {}).get("source", "-")

    decision = "réponse" if accepted else "refus"

    rows.append({
        "question": item["question"],
        "type": item["type"],
        "meilleur_score": round(best_score, 3),
        "seuil": SEUIL,
        "attendu": item["attendu"],
        "obtenu": decision,
        "source_top_1": source_top_1,
    })

    print(item["question"])
    print("best_score brut =", best_score)
    print("threshold brut =", threshold)
    print("accepted =", accepted)
    print("---")

output_path = "analytics/resultats_similarity_threshold.md"

with open(output_path, "w", encoding="utf-8") as f:
    f.write("| Question | Type | Meilleur score | Seuil | Attendu | Obtenu | Source top 1 |\n")
    f.write("|---|---|---:|---:|---:|---|---|\n")

    for row in rows:
        f.write(
            f"| {row['question']} | {row['type']} | {row['meilleur_score']} | {row['seuil']} | {row['attendu']} | "
            f"{row['obtenu']} | {row['source_top_1']} |\n"
        )

print(f"Tableau généré : {output_path}")
