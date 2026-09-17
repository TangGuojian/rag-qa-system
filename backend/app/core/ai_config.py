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
    def resolved_llm_api_key(self) -> str:
        return self.api_key or settings.llm_api_key or settings.embedding_api_key or ""

    @property
    def resolved_embedding_api_key(self) -> str:
        return self.api_key or settings.embedding_api_key or settings.llm_api_key or ""

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
    )


def from_api_key(api_key: str | None) -> AIConfig:
    """仅有一个 Key 时的便捷构造（用于兼容既有调用方式与测试）。"""
    return AIConfig(api_key=_clean(api_key))
