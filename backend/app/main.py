from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.config import settings
from app.db.mysql import engine, Base
from app.models import *  # noqa: ensure models are imported

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
    # 测试环境由测试用例自行建表（见 tests/conftest.py 的 SQLite 内存库），
    # 此处跳过，避免在无外部依赖的 CI 环境中尝试连接 MySQL。
    if settings.env == "test":
        return
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}
