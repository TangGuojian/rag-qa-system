"""AI 服务配置接口。

让使用者不必理解 OpenAI 兼容协议的细节：选一个服务商 → 填自己的 Key →
点「测试连接」，三件事同时正确才能跑通。这里把「错在哪」直接翻译成中文提示。
"""

from typing import Optional

from fastapi import APIRouter, Depends
from openai import OpenAI
from pydantic import BaseModel

from app.core.ai_config import AIConfig, for_user
from app.core.dependencies import get_current_user
from app.core.providers import PROVIDER_PRESETS
from app.models.user import User
from app.rag.embedding import probe_embedding
from app.rag.llm import probe_chat

router = APIRouter()


class AIProbeRequest(BaseModel):
    """测试连接。字段为空表示沿用已保存的配置，便于「先测再存」。"""

    api_key: Optional[str] = None
    api_base: Optional[str] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None


class ModelListRequest(BaseModel):
    api_key: Optional[str] = None
    api_base: Optional[str] = None


def _merge(user: User, req: AIProbeRequest) -> AIConfig:
    saved = for_user(user)
    return AIConfig(
        api_key=req.api_key if req.api_key is not None else saved.api_key,
        api_base=req.api_base if req.api_base is not None else saved.api_base,
        llm_model=req.llm_model if req.llm_model is not None else saved.llm_model,
        embedding_model=req.embedding_model if req.embedding_model is not None else saved.embedding_model,
    )


def _mask(key: str | None) -> str | None:
    if not key:
        return None
    if len(key) <= 10:
        return key[:2] + "***"
    return f"{key[:6]}***{key[-4:]}"


def _humanize(exc: Exception) -> str:
    """把 SDK 抛出的原始异常翻译成可执行的中文提示。

    先按异常类型判断，再匹配文本。顺序很重要：如果只做文本匹配，
    "unexpected keyword argument 'timeout'" 这类代码缺陷里的字样
    会被误判成网络问题，把真正的 bug 藏起来。
    """
    name = type(exc).__name__
    text = f"{name}: {exc}"
    low = text.lower()

    if name in ("TypeError", "AttributeError", "NameError", "ImportError", "KeyError"):
        return f"服务内部错误（{name}）：{str(exc)[:150]}。这是一处代码缺陷，不是配置问题。"
    if "APIConnectionError" in name or "ConnectTimeout" in name or "APITimeoutError" in name:
        return "无法连接到该服务地址。请检查 API 地址是否写错、本机网络是否可达（境外服务通常需要代理）。"
    if "401" in low or "invalid_api_key" in low or "incorrect api key" in low or "authentication" in low:
        return "API Key 无效或已失效，请检查是否复制完整、是否与该服务商匹配。"
    if "model_not_found" in low or "does not exist" in low or ("404" in low and "model" in low):
        return "模型名不存在。请点「获取可用模型」从服务商返回的列表里选一个。"
    if "429" in low or "rate limit" in low or "quota" in low:
        return "请求过于频繁或额度不足，请稍后重试，或检查账户余额。"
    if "insufficient" in low or "arrears" in low or "balance" in low:
        return "账户余额不足，请先充值或更换服务商。"
    if "timed out" in low or "ssl" in low:
        return "连接超时。请检查本机网络是否可达该服务地址（境外服务通常需要代理）。"
    if "not supported" in low or "unsupported" in low:
        return "该服务商不支持这个接口（例如不提供向量化接口），请更换服务商或模型。"
    return f"调用失败：{text[:180]}"


@router.get("/providers")
def list_providers(user: User = Depends(get_current_user)):
    """可选的服务商预设，供前端下拉框使用。"""
    return {"data": PROVIDER_PRESETS}


@router.get("/status")
def ai_status(user: User = Depends(get_current_user)):
    """当前账号实际生效的 AI 配置。"""
    ai = for_user(user)
    return {
        "has_key": ai.has_key,
        "uses_user_key": ai.uses_user_key,
        "api_key_masked": _mask(ai.api_key) or ("（系统默认）" if ai.has_key else None),
        "api_base": ai.resolved_api_base,
        "llm_model": ai.resolved_llm_model,
        "embedding_model": ai.resolved_embedding_model,
        "api_base_overridden": bool(ai.api_base),
        "llm_model_overridden": bool(ai.llm_model),
        "embedding_model_overridden": bool(ai.embedding_model),
    }


@router.post("/test")
def test_connection(req: AIProbeRequest, user: User = Depends(get_current_user)):
    """分别验证对话模型与向量模型，两者都通过才算配置成功。"""
    ai = _merge(user, req)
    result: dict = {"chat": None, "embedding": None}

    try:
        sample = (probe_chat(ai) or "").strip()
        result["chat"] = {
            "ok": True,
            "model": ai.resolved_llm_model,
            "message": f"对话模型可用（{ai.resolved_llm_model}）",
            "sample": sample[:60],
        }
    except Exception as exc:  # noqa: BLE001
        result["chat"] = {
            "ok": False,
            "model": ai.resolved_llm_model,
            "message": _humanize(exc),
        }

    try:
        dimension = probe_embedding(ai)
        result["embedding"] = {
            "ok": True,
            "model": ai.resolved_embedding_model,
            "message": f"向量模型可用（{ai.resolved_embedding_model}，{dimension} 维）",
            "dimension": dimension,
        }
    except Exception as exc:  # noqa: BLE001
        result["embedding"] = {
            "ok": False,
            "model": ai.resolved_embedding_model,
            "message": _humanize(exc),
        }

    result["ok"] = bool(result["chat"]["ok"] and result["embedding"]["ok"])
    result["api_base"] = ai.resolved_api_base
    return result


@router.post("/models")
def list_models(req: ModelListRequest, user: User = Depends(get_current_user)):
    """向服务商拉取真实可用的模型列表。

    模型名会随服务商迭代而变，与其在文档里写死，不如现场拉一次。
    """
    ai = _merge(user, AIProbeRequest(api_key=req.api_key, api_base=req.api_base))
    if not ai.has_key:
        return {"ok": False, "message": "请先填写 API Key", "models": []}
    try:
        client = OpenAI(api_key=ai.resolved_llm_api_key, base_url=ai.resolved_api_base or None, timeout=20.0)
        page = client.models.list()
        ids = sorted({m.id for m in page.data})
        return {"ok": True, "models": ids, "message": f"共获取到 {len(ids)} 个模型"}
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "models": [],
            "message": _humanize(exc) + "（也可以直接在输入框里手动填写模型名）",
        }
