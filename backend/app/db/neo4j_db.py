from app.core.config import settings

try:
    from neo4j import GraphDatabase
except ImportError:  # 未安装 neo4j 依赖时，图谱功能整体降级，不影响主链路
    GraphDatabase = None

# 注意：GraphDatabase.driver() 是惰性的，不会立刻建立连接，
# 因此这里在未部署 Neo4j 的机器上 import 也不会报错。
neo4j_driver = (
    GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    if GraphDatabase is not None
    else None
)

_probe_result: bool | None = None


def neo4j_available() -> bool:
    """Neo4j 是否可用。

    settings.neo4j_enabled 显式设置时以它为准；留空则自动探测一次并缓存，
    避免每次问答都去连一个不存在的服务。
    """
    global _probe_result
    if neo4j_driver is None:
        return False
    if settings.neo4j_enabled is not None:
        return settings.neo4j_enabled
    if _probe_result is None:
        try:
            with neo4j_driver.session() as session:
                session.run("RETURN 1")
            _probe_result = True
        except Exception:
            _probe_result = False
    return _probe_result


def get_neo4j_session():
    with neo4j_driver.session() as session:
        yield session


def close_neo4j():
    if neo4j_driver is not None:
        neo4j_driver.close()
