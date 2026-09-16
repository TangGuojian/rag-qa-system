from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.mysql import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.kb import KnowledgeBase, KbStatus
from app.models.user import User
from app.schemas.kb import KBCreate, KBUpdate, KBResponse

router = APIRouter()


@router.get("", response_model=List[KBResponse])
def list_kbs(search: Optional[str] = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(KnowledgeBase).filter(KnowledgeBase.status == KbStatus.ACTIVE)
    if search:
        query = query.filter(KnowledgeBase.name.like(f"%{search}%"))
    return query.all()


@router.post("", response_model=KBResponse, status_code=status.HTTP_201_CREATED)
def create_kb(kb: KBCreate, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    existing = db.query(KnowledgeBase).filter(KnowledgeBase.name == kb.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="知识库名称已存在")
    new_kb = KnowledgeBase(name=kb.name, description=kb.description)
    db.add(new_kb)
    db.commit()
    db.refresh(new_kb)
    return new_kb


@router.put("/{kb_id}", response_model=KBResponse)
def update_kb(kb_id: int, kb: KBUpdate, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    db_kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not db_kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
    if kb.name is not None:
        db_kb.name = kb.name
    if kb.description is not None:
        db_kb.description = kb.description
    db.commit()
    db.refresh(db_kb)
    return db_kb


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kb(kb_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    db_kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not db_kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
    db_kb.status = KbStatus.ARCHIVED
    db.commit()
