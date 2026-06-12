from app.retrieve import retrieve

# docker compose exec api python -m analytics.evaluate_topk
TOP_K_VALUES = [3, 5, 8]

questions = [
    "Quels sont les critères d'inclusion d'un outil ? ",
    "Comment les données sont elles collectées ?",
    "Quelle est la fréquence de mise à jour du jeu de données ?",
]

rows = []

for top_k in TOP_K_VALUES:
    best_scores = []
    avg_scores = []
    sources_top_1 = []

    for question in questions:
        result = retrieve(question, top_k=top_k)

        hits = result["hits"]
        best_score = result["best_score"]

        if not hits:
            best_scores.append(0)
            avg_scores.append(0)
            sources_top_1.append("-")
            continue

        avg_score = sum(hit.get("score", 0) for hit in hits) / len(hits)

        best_scores.append(best_score)
        avg_scores.append(avg_score)
        sources_top_1.append(hits[0].get("metadata", {}).get("source", "-"))

    global_best_score = sum(best_scores) / len(best_scores)
    global_avg_score = sum(avg_scores) / len(avg_scores)

    rows.append({
        "top_k": top_k,
        "meilleur_score_moyen": round(global_best_score, 3),
        "score_moyen_des_chunks": round(global_avg_score, 3),
        "sources_top_1": ", ".join(sorted(set(sources_top_1))),
        "commentaire": "",
    })

output_path = "analytics/resultats_topk.md"

with open(output_path, "w", encoding="utf-8") as f:
    f.write("| top_k | Meilleur score moyen | Score moyen des chunks | Sources top 1 | Commentaire |\n")
    f.write("|---:|---:|---:|---|---|\n")

    for row in rows:
        f.write(
            f"| {row['top_k']} | {row['meilleur_score_moyen']} | "
            f"{row['score_moyen_des_chunks']} | {row['sources_top_1']} | {row['commentaire']} |\n"
        )

print(f"Tableau généré : {output_path}")