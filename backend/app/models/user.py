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
    api_key = Column(String(256), nullable=True, comment="用户自定义API Key")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
