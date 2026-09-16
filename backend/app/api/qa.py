import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.mysql import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.history import QaHistory
from app.schemas.qa import AskRequest, FeedbackRequest, QAResult, SourceInfo
from app.rag.engine import answer_question, answer_question_stream

router = APIRouter()


@router.post("/ask", response_model=QAResult)
def ask_question(req: AskRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        answer, sources = answer_question(
            req.question, req.kb_ids, user.api_key,
            session_id=req.session_id, db_session=db, user_id=user.id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答引擎错误: {str(e)}")

    record = QaHistory(
        user_id=user.id,
        question=req.question,
        answer=answer,
        kb_ids=req.kb_ids,
        session_id=req.session_id,
    )
    db.add(record)
    db.commit()

    return QAResult(
        answer=answer,
        sources=[
            SourceInfo(kb_name=s["kb_name"], filename=s["filename"], content=s["content"])
            for s in sources
        ],
        session_id=req.session_id,
    )


@router.post("/ask/stream")
async def ask_question_stream(req: Request):
    body = await req.json()
    question = body.get("question", "")
    kb_ids = body.get("kb_ids", [])
    session_id = body.get("session_id", "")

    token = req.headers.get("Authorization", "").replace("Bearer ", "")
    from app.core.auth import decode_access_token
    from app.db.mysql import SessionLocal
    from app.models.user import User, UserStatus

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的Token")
    db = SessionLocal()
    user = db.query(User).filter(User.id == int(payload["sub"]), User.status == UserStatus.ACTIVE).first()
    if not user:
        db.close()
        raise HTTPException(status_code=401, detail="用户不存在")
    user_id = user.id
    api_key = user.api_key

    async def event_stream():
        full_answer = ""
        sources = []
        try:
            generator = answer_question_stream(question, kb_ids, api_key, session_id=session_id, db_session=db, user_id=user_id)
            for token_text in generator:
                if isinstance(token_text, dict):
                    sources = token_text.get("sources", [])
                else:
                    full_answer += token_text
                    yield f"data: {json.dumps({'token': token_text, 'done': False})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'token': '', 'done': True, 'error': str(e)})}\n\n"
            db.close()
            return

        record = QaHistory(
            user_id=user_id,
            question=question,
            answer=full_answer,
            kb_ids=kb_ids,
            session_id=session_id,
        )
        db.add(record)
        db.commit()
        db.close()

        yield f"data: {json.dumps({'token': '', 'done': True, 'sources': sources, 'qa_id': record.id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/feedback")
def submit_feedback(req: FeedbackRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(QaHistory).filter(QaHistory.id == req.qa_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="问答记录不存在")
    record.useful = req.useful
    record.feedback = req.feedback
    db.commit()
    return {"message": "反馈已记录"}
