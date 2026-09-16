from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import datetime, timedelta
from app.db.mysql import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.models.kb import KnowledgeBase
from app.models.document import Document
from app.models.history import QaHistory
from app.utils.text import CHINESE_STOP_CHARS

router = APIRouter()


@router.get("/kb-overview")
def get_kb_overview(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    kbs = db.query(KnowledgeBase).filter(KnowledgeBase.status == "active").all()
    result = []
    for kb in kbs:
        doc_count = db.query(func.count(Document.id)).filter(Document.kb_id == kb.id).scalar() or 0
        parsed = db.query(func.count(Document.id)).filter(Document.kb_id == kb.id, Document.status == "completed").scalar() or 0
        result.append({
            "id": kb.id,
            "name": kb.name,
            "doc_count": doc_count,
            "parsed": parsed,
            "vectorized": kb.chunk_count,
            "nodes": kb.graph_node_count,
            "edges": kb.graph_edge_count,
        })
    return result


@router.get("/qa-stats")
def get_qa_stats(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    total_qa = db.query(func.count(QaHistory.id)).scalar() or 0
    active_users = db.query(func.count(distinct(QaHistory.user_id))).scalar() or 0

    today = datetime.utcnow().date()
    trend = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = db.query(func.count(QaHistory.id)).filter(
            func.date(QaHistory.created_at) == day
        ).scalar() or 0
        trend.append({"date": day.isoformat(), "count": count})

    return {"total_qa": total_qa, "active_users": active_users, "trend": trend}


@router.get("/system-status")
def get_system_status(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    total_size = db.query(func.coalesce(func.sum(Document.file_size), 0)).scalar() or 0
    today = datetime.utcnow().date()
    api_calls_today = db.query(func.count(QaHistory.id)).filter(
        func.date(QaHistory.created_at) == today
    ).scalar() or 0
    return {"storage_used": total_size, "api_calls_today": api_calls_today}


@router.get("/hot-topics")
def get_hot_topics(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    recent = db.query(QaHistory.question).order_by(QaHistory.created_at.desc()).limit(100).all()
    words = {}
    for row in recent:
        chars = [ch for ch in row.question if "\u4e00" <= ch <= "\u9fff"]
        for i in range(len(chars) - 1):
            bigram = chars[i] + chars[i + 1]
            if chars[i] in CHINESE_STOP_CHARS or chars[i + 1] in CHINESE_STOP_CHARS:
                continue
            words[bigram] = words.get(bigram, 0) + 1
    sorted_pairs = sorted(words.items(), key=lambda x: x[1], reverse=True)
    top = [pair for pair in sorted_pairs if pair[1] >= 2][:15]
    if not top:
        top = sorted_pairs[:15]
    return [{"name": w, "size": min(20, 12 + c // 2)} for w, c in top]
