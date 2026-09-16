from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.knowledge import router as kb_router
from app.api.documents import router as doc_router
from app.api.qa import router as qa_router
from app.api.history import router as history_router
from app.api.graph import router as graph_router
from app.api.users import router as users_router
from app.api.config import router as config_router
from app.api.dashboard import router as dashboard_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(kb_router, prefix="/knowledge-bases", tags=["知识库"])
api_router.include_router(doc_router, prefix="/documents", tags=["文档"])
api_router.include_router(qa_router, prefix="/qa", tags=["智能问答"])
api_router.include_router(history_router, prefix="/history", tags=["问答历史"])
api_router.include_router(graph_router, prefix="/graph", tags=["知识图谱"])
api_router.include_router(users_router, prefix="/users", tags=["用户管理"])
api_router.include_router(config_router, prefix="/config", tags=["系统配置"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["工作台"])
