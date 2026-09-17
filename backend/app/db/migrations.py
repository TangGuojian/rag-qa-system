"""极简的幂等结构迁移。

`Base.metadata.create_all()` 只会创建缺失的**表**，不会给已存在的表补**列**。
为了让早期拉过代码的人（以及本地已有 MySQL 库的人）升级后不用手工改表，
这里在启动时补齐缺失的列。

只做「加列」这一件事，不做删改，可以安全地重复执行。
"""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

# 表名 -> [(列名, 列定义), ...]
_ADDITIVE_MIGRATIONS: dict[str, list[tuple[str, str]]] = {
    "users": [
        ("api_base", "VARCHAR(256) NULL"),
        ("llm_model", "VARCHAR(128) NULL"),
        ("embedding_model", "VARCHAR(128) NULL"),
        ("embedding_api_key", "VARCHAR(256) NULL"),
        ("embedding_api_base", "VARCHAR(256) NULL"),
    ],
}


def ensure_schema(engine: Engine) -> list[str]:
    """补齐缺失的列，返回本次实际执行的变更描述（便于日志与排查）。"""
    applied: list[str] = []
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for table, columns in _ADDITIVE_MIGRATIONS.items():
        if table not in existing_tables:
            continue  # 表还没建，create_all 会带上完整结构
        present = {col["name"] for col in inspector.get_columns(table)}
        missing = [(name, ddl) for name, ddl in columns if name not in present]
        if not missing:
            continue
        with engine.begin() as conn:
            for name, ddl in missing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                applied.append(f"{table}.{name}")
    return applied
