from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.generate import answer

app = FastAPI(title="AssistKB Search API")


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        description="Question utilisateur à poser au corpus.",
        examples=["Quelles mesures de sécurité sont recommandées pour les données personnelles ?"],
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="Nombre de chunks à récupérer. Si absent, utilise TOP_K défini dans .env.",
        examples=[5],
    )


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    latency_ms: int
    tokens: dict
    debug: dict | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> dict:
    if payload.top_k is None:
        return answer(payload.question)

    return answer(payload.question, top_k=payload.top_k)