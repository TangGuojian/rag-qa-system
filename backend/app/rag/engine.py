from app.rag.retriever import search_knowledge
from app.rag.graph_retriever import search_graph
from app.rag.llm import generate_answer, generate_answer_stream
from app.db.mysql import SessionLocal
from app.models.config import SystemConfig
from app.models.history import QaHistory
from sqlalchemy import desc


def _load_rag_config() -> dict:
    default = {
        "temperature": 0.3, "max_tokens": 2048,
        "chat_temperature": 0.7, "chat_max_tokens": 2048,
        "top_k": 5, "threshold": 0.5,
    }
    try:
        db = SessionLocal()
        row = db.query(SystemConfig).filter(SystemConfig.config_key == "app_config").first()
        db.close()
        if row and isinstance(row.config_value, dict):
            cv = row.config_value
            return {
                "temperature": cv.get("temperature", default["temperature"]),
                "max_tokens": cv.get("max_tokens", default["max_tokens"]),
                "chat_temperature": cv.get("temperature", default["chat_temperature"]),
                "chat_max_tokens": cv.get("max_tokens", default["chat_max_tokens"]),
                "top_k": cv.get("top_k", default["top_k"]),
                "threshold": cv.get("threshold", default["threshold"]),
            }
    except Exception:
        pass
    return default


def _load_history(db_session, user_id: int, session_id: str, max_turns: int = 6) -> list[dict]:
    try:
        records = db_session.query(QaHistory).filter(
            QaHistory.user_id == user_id,
            QaHistory.session_id == session_id,
        ).order_by(desc(QaHistory.created_at)).limit(max_turns).all()
        records.reverse()
        return [{"question": r.question, "answer": r.answer or ""} for r in records]
    except Exception:
        return []


def _search_contexts(question: str, kb_ids: list[int], api_key: str | None, cfg: dict) -> list[dict]:
    chunks = search_knowledge(question, kb_ids, api_key, top_k=cfg["top_k"], threshold=cfg["threshold"])
    contexts = [
        {"content": c.content, "kb_name": c.kb_name, "filename": c.filename, "score": c.score}
        for c in chunks
    ]
    try:
        graph_results = search_graph(question)
        for gr in graph_results:
            contexts.append({
                "content": gr.content, "kb_name": gr.source, "filename": "知识图谱", "score": gr.score,
            })
    except Exception:
        pass
    contexts.sort(key=lambda x: x["score"], reverse=True)
    return contexts


def answer_question(
    question: str, kb_ids: list[int], api_key: str | None = None,
    session_id: str | None = None, db_session=None, user_id: int | None = None,
) -> tuple[str, list[dict]]:
    cfg = _load_rag_config()
    history = _load_history(db_session, user_id, session_id) if db_session and session_id and user_id else None
    contexts = _search_contexts(question, kb_ids, api_key, cfg)

    if not contexts:
        return "未在知识库中找到相关信息，请尝试换个问法。", []

    answer = generate_answer(question, contexts, api_key, temperature=cfg["temperature"], max_tokens=cfg["max_tokens"], history=history)
    return answer, contexts


def answer_question_stream(
    question: str, kb_ids: list[int], api_key: str | None = None,
    session_id: str | None = None, db_session=None, user_id: int | None = None,
):
    cfg = _load_rag_config()
    history = _load_history(db_session, user_id, session_id) if db_session and session_id and user_id else None
    contexts = _search_contexts(question, kb_ids, api_key, cfg)

    if not contexts:
        yield "未在知识库中找到相关信息，请尝试换个问法。"
    else:
        yield from generate_answer_stream(question, contexts, api_key, temperature=cfg["temperature"], max_tokens=cfg["max_tokens"], history=history)
