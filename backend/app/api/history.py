from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from app.db.mysql import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.history import QaHistory

router = APIRouter()


@router.get("")
def list_history(
    keyword: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(QaHistory).filter(QaHistory.user_id == user.id)

    if keyword:
        query = query.filter(QaHistory.question.like(f"%{keyword}%"))
    if session_id:
        query = query.filter(QaHistory.session_id == session_id)
    if date_from:
        query = query.filter(QaHistory.created_at >= date_from)
    if date_to:
        query = query.filter(QaHistory.created_at <= f"{date_to} 23:59:59")

    total = query.count()
    items = query.order_by(desc(QaHistory.created_at)) \
                 .offset((page - 1) * size).limit(size).all()

    return {
        "data": [
            {
                "id": r.id,
                "question": r.question,
                "answer": r.answer,
                "kb_ids": r.kb_ids,
                "useful": r.useful,
                "feedback": r.feedback,
                "session_id": r.session_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in items
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@router.delete("/{qa_id}")
def delete_history(qa_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(QaHistory).filter(QaHistory.id == qa_id, QaHistory.user_id == user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "删除成功"}
