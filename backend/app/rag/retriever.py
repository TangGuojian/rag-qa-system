from app.core.ai_config import AIConfig, from_api_key
from app.core.errors import EmbeddingMismatchError
from app.db.chroma import get_collection
from app.rag.embedding import embed_text
from app.db.mysql import SessionLocal
from app.models.document import Document
from app.utils.text import extract_chinese_bigrams


TOP_K = 5
SCORE_THRESHOLD = 0.3
FALLBACK_THRESHOLD = 0.2


def _query(collection, query_vector: list[float], top_k: int):
    """向量检索。把「维度不一致」翻译成能看懂的中文提示。

    切换向量模型后旧索引仍然存在，此时维度往往对不上，
    ChromaDB 抛出的原始错误对使用者没有指导意义。
    """
    try:
        return collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:  # noqa: BLE001 - 需要区分是否为维度问题后再决定是否上抛
        message = str(exc).lower()
        if "dimension" in message or "dimensionality" in message:
            raise EmbeddingMismatchError() from exc
        raise


class ChunkResult:
    def __init__(self, content: str, kb_id: int, kb_name: str, filename: str, score: float):
        self.content = content
        self.kb_id = kb_id
        self.kb_name = kb_name
        self.filename = filename
        self.score = score


def _keyword_search(question: str, kb_ids: list[int]) -> list[dict]:
    keywords = extract_chinese_bigrams(question)

    db = SessionLocal()
    try:
        docs = db.query(Document).filter(
            Document.kb_id.in_(kb_ids),
            Document.status == "completed",
        ).all()
    finally:
        db.close()

    matched = []
    for doc in docs:
        fname = doc.filename.replace(".pdf", "").replace(".md", "").replace(".txt", "")
        score = 0
        for kw in keywords:
            if kw in fname:
                score += len(kw)
        if score > 0:
            matched.append({"doc_id": doc.id, "kb_id": doc.kb_id, "filename": doc.filename, "score": score})

    matched.sort(key=lambda x: x["score"], reverse=True)
    return matched[:3]


def _keyword_content_search(question: str, kb_ids: list[int]) -> list[dict]:
    keywords = extract_chinese_bigrams(question)
    if not keywords:
        return []

    for kb_id in kb_ids:
        try:
            collection = get_collection(kb_id)
        except Exception:
            continue

        all_docs = collection.get(include=["documents", "metadatas"])
        if not all_docs or not all_docs["documents"]:
            continue

        matched = []
        for i, doc_text in enumerate(all_docs["documents"]):
            score = 0
            for kw in keywords:
                if kw in doc_text:
                    score += len(kw) * 2
            if score > 0:
                meta = all_docs["metadatas"][i] if all_docs["metadatas"] else {}
                matched.append(ChunkResult(
                    content=doc_text,
                    kb_id=meta.get("kb_id", kb_id),
                    kb_name=meta.get("kb_name", ""),
                    filename=meta.get("filename", ""),
                    score=min(score / 10, 0.95),
                ))

        if matched:
            matched.sort(key=lambda r: r.score, reverse=True)
            return matched[:TOP_K]

    return []


def search_knowledge(
    question: str, kb_ids: list[int], api_key: str | None = None,
    top_k: int = TOP_K, threshold: float = SCORE_THRESHOLD,
    *, ai: AIConfig | None = None,
) -> list[ChunkResult]:
    cfg = ai or from_api_key(api_key)
    query_vector = embed_text(question, ai=cfg)
    results: list[ChunkResult] = []

    for kb_id in kb_ids:
        try:
            collection = get_collection(kb_id)
        except Exception:
            continue

        hits = _query(collection, query_vector, top_k)

        if not hits["documents"] or not hits["documents"][0]:
            continue

        for i, doc in enumerate(hits["documents"][0]):
            distance = hits["distances"][0][i]
            score = 1 - distance
            if score < threshold:
                continue
            meta = hits["metadatas"][0][i] if hits["metadatas"] else {}
            results.append(ChunkResult(
                content=doc,
                kb_id=meta.get("kb_id", kb_id),
                kb_name=meta.get("kb_name", ""),
                filename=meta.get("filename", ""),
                score=score,
            ))

    results.sort(key=lambda r: r.score, reverse=True)
    results = results[:top_k]

    if not results:
        keyword_hits = _keyword_content_search(question, kb_ids)
        if keyword_hits:
            return keyword_hits

        keyword_hits = _keyword_search(question, kb_ids)
        if keyword_hits:
            for kh in keyword_hits:
                try:
                    collection = get_collection(kh["kb_id"])
                    hits = _query(collection, query_vector, top_k)
                    if hits["documents"] and hits["documents"][0]:
                        for i, doc in enumerate(hits["documents"][0]):
                            meta = hits["metadatas"][0][i] if hits["metadatas"] else {}
                            distance = hits["distances"][0][i]
                            score = 1 - distance
                            if score >= FALLBACK_THRESHOLD and meta.get("doc_id") == kh["doc_id"]:
                                results.append(ChunkResult(
                                    content=doc,
                                    kb_id=kh["kb_id"],
                                    kb_name=meta.get("kb_name", ""),
                                    filename=kh["filename"],
                                    score=score,
                                ))
                    if len(results) >= top_k:
                        break
                except Exception:
                    continue

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k]
