import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import settings
from app.db.migrations import ensure_schema
from app.db.mysql import engine, Base
from app.models import *  # noqa: ensure models are imported

logger = logging.getLogger("app")

# 前端构建产物。存在时由后端直接托管，使用者无需安装 Node.js。
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

app = FastAPI(title="智能问答系统 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    # 测试环境由测试用例自行建表（见 tests/conftest.py），
    # 此处跳过，避免在无外部依赖的 CI 环境中尝试连接数据库。
    if settings.env == "test":
        return
    Base.metadata.create_all(bind=engine)
    applied = ensure_schema(engine)
    if applied:
        logger.info("已补齐数据库缺失字段: %s", ", ".join(applied))
    logger.info("数据库: %s", engine.url.render_as_string(hide_password=True))


@app.get("/health")
def health_check():
    return {"status": "ok", "database": engine.dialect.name}


# ---------------- 前端静态资源（放在最后注册，避免遮挡上面的接口）----------------
if FRONTEND_DIST.is_dir():
    _assets = FRONTEND_DIST / "assets"
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        # 未匹配到的接口路径应返回 404，而不是把 index.html 当作 JSON 返回
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "接口不存在"}, status_code=404)

        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        # 其余路径交给前端路由（history 模式）
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/", include_in_schema=False)
    async def no_frontend():
        return {
            "message": "后端已启动，但未找到前端构建产物 frontend/dist。",
            "hint": "可执行 python run_demo.py 自动准备，或在 frontend/ 下运行 npm install && npm run build。",
            "docs": "/docs",
        }
