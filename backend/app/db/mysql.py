import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# 测试环境下使用 SQLite，避免依赖外部 MySQL 服务。
# 大多数接口测试会通过 tests/conftest.py 的依赖覆盖注入测试会话；
# 但仍有代码路径（如 RAG 检索）直接使用 SessionLocal，因此这里让 app 自身的
# engine 也指向同一个测试库文件，保证表结构一致、不出现 "no such table"。
if settings.env == "test":
    _test_db = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_runtime.db")
    engine = create_engine(
        _test_db,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    if settings.mysql_url.startswith("sqlite"):
        engine = create_engine(settings.mysql_url, echo=False)
    else:
        engine = create_engine(
            settings.mysql_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False,
        )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
