from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.db.mysql import Base


class UserKbAuthorization(Base):
    __tablename__ = "user_kb_authorization"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "kb_id", name="uk_user_kb"),
    )
