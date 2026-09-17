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
from app.core.errors import humanize_error
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
    embedding_api_key: Optional[str] = None
    embedding_api_base: Optional[str] = None


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
        embedding_api_key=(
            req.embedding_api_key if req.embedding_api_key is not None else saved.embedding_api_key
        ),
        embedding_api_base=(
            req.embedding_api_base if req.embedding_api_base is not None else saved.embedding_api_base
        ),
    )


def _mask(key: str | None) -> str | None:
    if not key:
        return None
    if len(key) <= 10:
        return key[:2] + "***"
    return f"{key[:6]}***{key[-4:]}"


# 错误翻译统一放在 core/errors.py，上传等其它链路复用同一套话术
_humanize = humanize_error


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
        "embedding_api_base": ai.resolved_embedding_api_base,
        "embedding_api_base_masked": _mask(ai.embedding_api_key),
        "has_dedicated_embedding": ai.has_dedicated_embedding,
        "supports_embedding": ai.supports_embedding,
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
