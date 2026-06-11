from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.generate import answer

app = FastAPI(title="AssistKB Search API")


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        description="Question utilisateur à poser au corpus.",
        examples=["Comment les données sont collectées ?"],
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="Nombre de chunks à récupérer. Si absent, utilise TOP_K défini dans .env.",
        examples=[5],
    )


class TokenUsage(BaseModel):
    prompt: int = Field(..., examples=[439])
    completion: int = Field(..., examples=[42])


class DebugInfo(BaseModel):
    best_score: float | None = Field(default=None, examples=[0.3964938])
    threshold: float = Field(..., examples=[0.38])
    top_k: int = Field(..., examples=[5])
    retrieved_texts: list[str] | None = Field(
        default=None,
        examples=[["Extrait du chunk récupéré..."]],
    )


class AskResponse(BaseModel):
    answer: str = Field(
        ...,
        examples=["Les données sont collectées et vérifiées manuellement par l'équipe WebSentinel."],
    )
    sources: list[str] = Field(
        default_factory=list,
        examples=[["documentation.txt"]],
    )
    latency_ms: int = Field(..., examples=[2241])
    tokens: TokenUsage
    debug: DebugInfo | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> dict:
    if payload.top_k is None:
        return answer(payload.question)

    return answer(payload.question, top_k=payload.top_k)