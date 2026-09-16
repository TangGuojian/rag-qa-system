from pydantic import BaseModel
from typing import Optional


class ConfigUpdate(BaseModel):
    llm_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    retrieval_mode: Optional[str] = None
    top_k: Optional[int] = None
    threshold: Optional[float] = None


class ConfigResponse(BaseModel):
    llm_model: str = "qwen3.7-plus"
    temperature: float = 0.7
    max_tokens: int = 4096
    chunk_size: int = 512
    chunk_overlap: int = 64
    retrieval_mode: str = "hybrid"
    top_k: int = 5
    threshold: float = 0.75
