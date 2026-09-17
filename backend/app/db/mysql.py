import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings, DATA_DIR


def _build_engine():
    """按配置选择数据库。

    - test：独立的 SQLite 库（由 tests/conftest.py 通过 TEST_DATABASE_URL 指定），
      保证测试不依赖外部服务，也不会污染开发数据。
    - 其他环境：未配置 mysql_host 时落到内置 SQLite（开箱即用），
      配置了则连 MySQL（与原行为一致）。
    """
    if settings.env == "test":
        url = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_runtime.db")
        return create_engine(
            url,
            connect_args={"check_same_thread": False, "timeout": 30},
            echo=False,
        )

    url = settings.effective_database_url
    if url.startswith("sqlite"):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return create_engine(
            url,
            connect_args={"check_same_thread": False, "timeout": 30},
            echo=False,
        )
    return create_engine(
        url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False,
    )


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
