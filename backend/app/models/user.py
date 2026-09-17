from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
from app.db.mysql import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    display_name = Column(String(64), nullable=True)
    email = Column(String(128), nullable=True)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.USER)
    status = Column(SAEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    # 用户自带的 AI 服务凭据。四项留空即沿用 backend/.env 中的系统默认配置，
    # 因此「使用系统统一配置」与「每个人填自己的 Key」两种模式可以共存。
    api_key = Column(String(256), nullable=True, comment="用户自定义API Key")
    api_base = Column(String(256), nullable=True, comment="用户自定义API地址（OpenAI兼容）")
    llm_model = Column(String(128), nullable=True, comment="用户自定义对话模型名")
    embedding_model = Column(String(128), nullable=True, comment="用户自定义向量模型名")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
