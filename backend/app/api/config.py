from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.mysql import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.models.config import SystemConfig
from app.schemas.config import ConfigUpdate, ConfigResponse

router = APIRouter()

DEFAULT_CONFIG = {
    "llm_model": "qwen3.7-plus",
    "temperature": 0.7,
    "max_tokens": 4096,
    "chunk_size": 512,
    "chunk_overlap": 64,
    "retrieval_mode": "hybrid",
    "top_k": 5,
    "threshold": 0.75,
}


def _load_config(db: Session) -> dict:
    config = {}
    rows = db.query(SystemConfig).filter(SystemConfig.config_key == "app_config").all()
    for row in rows:
        if isinstance(row.config_value, dict):
            config.update(row.config_value)
    return {**DEFAULT_CONFIG, **config}


@router.get("", response_model=ConfigResponse)
def get_config(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return ConfigResponse(**_load_config(db))


@router.put("")
def update_config(req: ConfigUpdate, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    existing = db.query(SystemConfig).filter(SystemConfig.config_key == "app_config").first()
    current = _load_config(db)
    updated = {**current, **req.model_dump(exclude_none=True)}
    if existing:
        existing.config_value = updated
        existing.updated_by = user.id
    else:
        db.add(SystemConfig(
            config_key="app_config",
            config_value=updated,
            description="应用配置",
            updated_by=user.id,
        ))
    db.commit()
    return {"message": "配置已更新", "config": updated}
