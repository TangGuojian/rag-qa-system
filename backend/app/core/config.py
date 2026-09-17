import secrets
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


def _ephemeral_jwt_key() -> str:
    """未显式配置 JWT_SECRET_KEY 时，进程启动即生成一个随机密钥。

    早先这里是一个写死的默认值，任何人拿到代码就能用该已知密钥伪造管理员令牌。
    随机化的代价是重启后已签发的令牌会失效（本地演示可接受，生产必须显式配置）。
    """
    return secrets.token_urlsafe(32)

# backend/ 目录（本文件位于 backend/app/core/config.py）
BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
    # 运行环境：development / production / test
    # 测试环境（test）使用独立的 SQLite 库并跳过启动建表，便于在无外部依赖的 CI 中运行
    env: str = "development"

    # ---------------- 数据库 ----------------
    # 开箱即用：不填 mysql_host 时自动使用内置 SQLite（无需安装任何数据库服务）。
    # 需要 MySQL 时在 .env 里填 MYSQL_HOST 等即可，行为与之前完全一致。
    database_url: str = ""  # 显式指定连接串，优先级最高，例如 sqlite:///./data/app.db
    mysql_host: str = ""
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "db_qa_core"

    @property
    def sqlite_path(self) -> Path:
        return DATA_DIR / "app.db"

    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if not self.mysql_host:
            return f"sqlite:///{self.sqlite_path.as_posix()}"
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @property
    def is_sqlite(self) -> bool:
        return self.effective_database_url.startswith("sqlite")

    # ---------------- Neo4j（可选）----------------
    # 知识图谱增强检索需要 Neo4j。未部署时整条链路会自动降级跳过，不影响问答主链路。
    # neo4j_enabled 留空表示「自动探测」：启动后首次用到时探一次连通性并缓存结果，
    # 没装 Neo4j 的机器不会被反复重试拖慢；也可以显式设为 true / false 强制开关。
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_enabled: bool | None = None

    # ---------------- ChromaDB ----------------
    # 项目使用的是 ChromaDB 嵌入式模式，数据落在 backend/chroma_data/，
    # 不需要单独启动服务，下面的配置仅为兼容保留。
    chromadb_host: str = "localhost"
    chromadb_port: int = 8000

    # ---------------- JWT ----------------
    # 未配置时自动随机生成（避免「已知默认密钥」导致令牌可被伪造）。
    # 部署到多进程 / 长期环境时，务必在 .env 里显式设置 JWT_SECRET_KEY，
    # 否则重启后所有登录态失效，且多 worker 之间令牌互不通用。
    jwt_secret_key: str = Field(default_factory=_ephemeral_jwt_key)
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # 是否开放 POST /auth/init（免登录创建管理员）。
    # 历史上该接口无需任何鉴权且明文返回默认密码，属于越权风险，故默认关闭。
    # 本地演示需要时，在 .env 中设置 ALLOW_INIT_ADMIN=true 显式开启。
    allow_init_admin: bool = False

    @property
    def jwt_using_ephemeral_key(self) -> bool:
        """当前使用的是随机密钥（即调用方没有显式配置 JWT_SECRET_KEY）。"""
        fields_set = getattr(self, "model_fields_set", None) or set()
        return "jwt_secret_key" not in fields_set

    # ---------------- AI 服务（系统默认值）----------------
    # 仅作为兜底：每个用户都可以在「个人设置」里填写自己的 Key、服务地址与模型，
    # 用户配置优先于这里的默认值。
    llm_model: str = "qwen3.7-plus"
    llm_api_key: str = ""
    llm_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    embedding_model: str = "text-embedding-v3"
    embedding_api_key: str = ""

    # ---------------- 已废弃：仅为兼容旧 .env 保留 ----------------
    # Redis / Celery 在本项目中没有任何代码引用（原先只在 README 里宣称过）。
    # 保留字段是为了让旧 .env 仍能正常加载，读取后不使用，可直接从 .env 删除。
    redis_host: str = ""
    redis_port: int = 6379

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
