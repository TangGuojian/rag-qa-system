from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MySQL
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "db_qa_core"

    @property
    def mysql_url(self) -> str:
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # ChromaDB
    chromadb_host: str = "localhost"
    chromadb_port: int = 8000

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    # JWT
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # LLM
    llm_model: str = "qwen3.7-plus"
    llm_api_key: str = ""
    llm_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Embedding
    embedding_model: str = "text-embedding-v3"
    embedding_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
