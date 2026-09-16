from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.mysql import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)
    target_type = Column(String(32), nullable=True)
    target_id = Column(Integer, nullable=True)
    detail = Column(JSON, nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(256), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
