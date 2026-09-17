"""调用外部 AI 服务所需的凭据。

一个可用的调用需要三样东西同时正确，缺一不可：

    api_key    我是谁
    api_base   请求发往哪个服务商
    model      用哪个模型

项目支持两种来源，用户配置优先于系统配置：

    1. 用户在「个人设置」中填写的自有 Key（api_key / api_base / llm_model /
       embedding_model 四个字段，留空表示该项沿用系统默认）
    2. backend/.env 中的系统默认配置（LLM_API_KEY / LLM_API_BASE / LLM_MODEL ...）

这样既能让项目开箱即用（维护者配好一套默认值），
也允许任何拿到代码的人填自己的 Key 独立运行，不必依赖他人额度。
"""

from dataclasses import dataclass

from app.core.config import settings
from app.core.providers import provider_for_base


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


@dataclass(frozen=True)
class AIConfig:
    """一次 AI 调用的凭据组合。空字段表示回落到系统默认配置。"""

    api_key: str | None = None
    api_base: str | None = None
    llm_model: str | None = None
    embedding_model: str | None = None
    # 向量服务的独立出口：留空表示与对话服务共用同一套地址与 Key
    embedding_api_key: str | None = None
    embedding_api_base: str | None = None

    # ---------- 解析为最终生效值 ----------
    @property
    def resolved_api_base(self) -> str:
        return self.api_base or settings.llm_api_base

    @property
    def resolved_llm_model(self) -> str:
        return self.llm_model or settings.llm_model

    @property
    def resolved_embedding_model(self) -> str:
        return self.embedding_model or settings.embedding_model

    @property
    def resolved_embedding_api_base(self) -> str:
        """向量请求实际发往的地址。

        允许「对话用一个服务商、向量用另一个」，因为不少服务商只提供对话接口，
        此时必须给向量单独配一个出口，否则知识库功能完全不可用。
        """
        return self.embedding_api_base or self.resolved_api_base

    @property
    def resolved_llm_api_key(self) -> str:
        return self.api_key or settings.llm_api_key or settings.embedding_api_key or ""

    @property
    def resolved_embedding_api_key(self) -> str:
        return (
            self.embedding_api_key
            or self.api_key
            or settings.embedding_api_key
            or settings.llm_api_key
            or ""
        )

    @property
    def provider(self) -> dict | None:
        """当前生效地址对应的服务商预设（未知服务商返回 None）。"""
        return provider_for_base(self.resolved_api_base)

    @property
    def embedding_provider(self) -> dict | None:
        """向量请求实际访问的服务商预设。"""
        return provider_for_base(self.resolved_embedding_api_base)

    @property
    def has_dedicated_embedding(self) -> bool:
        """是否为向量服务单独指定了地址或 Key。"""
        return bool(self.embedding_api_base or self.embedding_api_key)

    @property
    def supports_embedding(self) -> bool:
        """当前服务商是否提供向量化接口。

        部分服务商（DeepSeek、Moonshot）只有对话接口。若不做这层判断，
        上传文档时会在向量化阶段报一个看不懂的 404，使用者无法自行定位。
        未知服务商（自建网关等）按「支持」处理，由实际调用结果来兜底。
        """
        p = self.embedding_provider
        if p is None:
            return True
        return bool(p.get("supports_embedding", True))

    # ---------- 状态查询 ----------
    @property
    def has_key(self) -> bool:
        """是否至少有一个可用的 Key（用户自有或系统默认）。"""
        return bool(self.resolved_llm_api_key)

    @property
    def uses_user_key(self) -> bool:
        """是否在使用用户自己的 Key（而非系统默认额度）。"""
        return bool(self.api_key)


def for_user(user) -> AIConfig:
    """从用户记录构造凭据；user 为 None 时返回纯系统默认配置。"""
    if user is None:
        return AIConfig()
    return AIConfig(
        api_key=_clean(getattr(user, "api_key", None)),
        api_base=_clean(getattr(user, "api_base", None)),
        llm_model=_clean(getattr(user, "llm_model", None)),
        embedding_model=_clean(getattr(user, "embedding_model", None)),
        embedding_api_key=_clean(getattr(user, "embedding_api_key", None)),
        embedding_api_base=_clean(getattr(user, "embedding_api_base", None)),
    )


def from_api_key(api_key: str | None) -> AIConfig:
    """仅有一个 Key 时的便捷构造（用于兼容既有调用方式与测试）。"""
    return AIConfig(api_key=_clean(api_key))
