from openai import OpenAI

from app.core.ai_config import AIConfig, from_api_key
from app.core.errors import MissingApiKeyError


# 批量向量化可能耗时较久（长文档一次提交很多分块），默认给足时间；
# 「测试连接」这类交互式探针会显式传入更短的超时，避免界面长时间无响应。
DEFAULT_TIMEOUT = 600.0


def _make_client(ai: AIConfig, timeout: float | None = None) -> OpenAI:
    api_key = ai.resolved_embedding_api_key
    if not api_key:
        raise MissingApiKeyError()
    return OpenAI(
        api_key=api_key,
        base_url=ai.resolved_api_base or None,
        timeout=timeout or DEFAULT_TIMEOUT,
    )


def embed_text(text: str, api_key: str | None = None, *, ai: AIConfig | None = None) -> list[float]:
    """把单条文本向量化。

    ai 提供完整的「Key + 地址 + 模型」组合（用户个人设置）；
    只传 api_key 时其余项回落系统默认配置。
    """
    cfg = ai or from_api_key(api_key)
    client = _make_client(cfg)
    resp = client.embeddings.create(
        model=cfg.resolved_embedding_model,
        input=text,
    )
    return resp.data[0].embedding


def embed_texts(texts: list[str], api_key: str | None = None, *, ai: AIConfig | None = None) -> list[list[float]]:
    """批量向量化。"""
    cfg = ai or from_api_key(api_key)
    client = _make_client(cfg)
    resp = client.embeddings.create(
        model=cfg.resolved_embedding_model,
        input=texts,
    )
    return [d.embedding for d in resp.data]


def probe_embedding(ai: AIConfig) -> int:
    """探针：调用一次向量接口，返回向量维度。用于「测试连接」。"""
    return len(embed_text("连接测试", ai=ai))
