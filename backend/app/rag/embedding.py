from openai import OpenAI
from app.core.config import settings


def _make_client(api_key: str | None = None) -> OpenAI:
    return OpenAI(
        api_key=api_key or settings.embedding_api_key,
        base_url=settings.llm_api_base,
    )


def embed_text(text: str, api_key: str | None = None) -> list[float]:
    client = _make_client(api_key)
    resp = client.embeddings.create(
        model=settings.embedding_model,
        input=text,
    )
    return resp.data[0].embedding


def embed_texts(texts: list[str], api_key: str | None = None) -> list[list[float]]:
    client = _make_client(api_key)
    resp = client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    return [d.embedding for d in resp.data]
