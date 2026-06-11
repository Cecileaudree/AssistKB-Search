from typing import Any

from google import genai

MODEL_NAME = "gemini-2.5-flash"


def call_llm(prompt: str) -> tuple[str, dict[str, Any]]:
    """
    La clé API est lue depuis la variable d'environnement GEMINI_API_KEY.
    """
    client = genai.Client()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    generated_answer = response.text or ""

    return generated_answer, {
        "prompt": len(prompt.split()),
        "completion": len(generated_answer.split()),
    }