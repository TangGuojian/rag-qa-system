import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.mysql import get_db
from app.core.dependencies import get_current_user
from app.core.ai_config import for_user
from app.core.errors import EmbeddingMismatchError, MissingApiKeyError
from app.models.user import User
from app.models.history import QaHistory
from app.schemas.qa import AskRequest, FeedbackRequest, QAResult, SourceInfo
from app.rag.engine import answer_question, answer_question_stream

router = APIRouter()

NEED_KEY_MESSAGE = (
    "尚未配置 AI 服务 API Key。请先进入「个人设置」，"
    "选择服务商（如阿里云百炼 / 硅基流动）并填写你自己的 API Key，保存后再提问。"
)


@router.post("/ask", response_model=QAResult)
def ask_question(req: AskRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ai = for_user(user)
    if not ai.has_key:
        raise HTTPException(status_code=400, detail=NEED_KEY_MESSAGE)

    session_id = req.session_id or uuid.uuid4().hex

    try:
        answer, sources = answer_question(
            req.question, req.kb_ids,
            session_id=session_id, db_session=db, user_id=user.id, ai=ai,
        )
    except (MissingApiKeyError, EmbeddingMismatchError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答引擎错误: {str(e)}")

    record = QaHistory(
        user_id=user.id,
        question=req.question,
        answer=answer,
        kb_ids=req.kb_ids,
        session_id=session_id,
    )
    db.add(record)
    db.commit()

    return QAResult(
        answer=answer,
        sources=[
            SourceInfo(kb_name=s["kb_name"], filename=s["filename"], content=s["content"])
            for s in sources
        ],
        session_id=session_id,
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
    ai = for_user(user)

    async def event_stream():
        def sse(payload: dict) -> str:
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        # 缺少 Key 时不留白屏：直接把原因告诉前端
        if not ai.has_key:
            yield sse({"token": "", "done": True, "error": NEED_KEY_MESSAGE})
            db.close()
            return

        full_answer = ""
        sources = []
        try:
            generator = answer_question_stream(
                question, kb_ids, session_id=session_id,
                db_session=db, user_id=user_id, ai=ai,
            )
            for item in generator:
                if isinstance(item, dict):
                    # 引擎在回答结束后回传一次溯源信息
                    sources = item.get("sources", [])
                else:
                    full_answer += item
                    yield sse({"token": item, "done": False})
        except (MissingApiKeyError, EmbeddingMismatchError) as e:
            yield sse({"token": "", "done": True, "error": str(e)})
            db.close()
            return
        except Exception as e:
            yield sse({"token": "", "done": True, "error": str(e)})
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

        yield sse({"token": "", "done": True, "sources": sources, "qa_id": record.id})

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
