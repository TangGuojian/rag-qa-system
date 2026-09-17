from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from app.db.mysql import get_db
from app.db.chroma import get_collection
from app.core.dependencies import get_current_user, require_admin
from app.core.ai_config import AIConfig, for_user
from app.core.errors import EmbeddingMismatchError, MissingApiKeyError, humanize_error
from app.core.config import settings
from app.models.document import Document, DocStatus, DocType
from app.models.user import User
from app.models.kb import KnowledgeBase
from app.schemas.document import DocumentResponse
from app.rag.parser import parse_file, chunk_text
from app.rag.embedding import embed_texts

router = APIRouter()
UPLOAD_DIR = "uploads"


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    kb_id: int = Form(...),
    tags: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1].lower()
    allowed = {"pdf", "docx", "md", "xlsx", "txt", "csv"}
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"仅支持 {', '.join(sorted(allowed))} 格式")
    type_map = {"pdf": DocType.PDF, "docx": DocType.DOCX, "md": DocType.MD, "xlsx": DocType.XLSX, "txt": DocType.TXT, "csv": DocType.TXT}
    file_type = type_map[ext]
    save_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(UPLOAD_DIR, save_name)
    content = file.file.read()
    if len(content) > 1024 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 1024MB")
    with open(save_path, "wb") as f:
        f.write(content)
    doc = Document(
        kb_id=kb_id,
        filename=file.filename,
        filepath=save_path,
        file_size=len(content),
        file_type=file_type,
        tags=tags,
        uploaded_by=user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    ai = for_user(user)
    if not ai.has_key:
        return _fail(doc, db, (
            "尚未配置 AI 服务 API Key，无法向量化文档。请先进入「个人设置」，"
            "选择服务商并填写你自己的 API Key，保存后重新上传。"
        ))

    # 部分服务商只有对话接口（DeepSeek / Moonshot）。不提前拦住的话，
    # 会一直走到向量化阶段才报一个看不懂的 404，使用者无法自行定位。
    if not ai.supports_embedding:
        label = (ai.embedding_provider or {}).get("label", "当前配置的服务商")
        return _fail(doc, db, (
            f"「{label}」不提供向量化接口，无法为文档建立索引。"
            "RAG 的检索依赖向量，因此必须有一个向量模型。"
            "请到「个人设置」中：换用提供向量模型的服务商"
            "（阿里云百炼 / 硅基流动 / 智谱 / OpenAI），"
            "或保留当前对话服务商、在「向量服务（可选）」里单独填一个向量服务商的 Key 与地址。"
        ))

    try:
        _parse_and_index(doc, db, ai)
    except (MissingApiKeyError, EmbeddingMismatchError) as e:
        return _fail(doc, db, str(e))
    except Exception as e:
        return _fail(doc, db, humanize_error(e))

    return {"doc_id": doc.id, "status": doc.status.value, "chunk_count": doc.chunk_count}


def _fail(doc: Document, db: Session, message: str) -> dict:
    """把失败原因同时写进记录与响应，前端可以直接提示给使用者。"""
    doc.status = DocStatus.FAILED
    doc.error_msg = message
    db.commit()
    _refresh_kb_stats(doc.kb_id, db)
    return {"doc_id": doc.id, "status": doc.status.value, "error_msg": message}


def _refresh_kb_stats(kb_id: int, db: Session) -> None:
    """按文档表重算知识库的文档数与向量数。

    这里不用「自增」是因为失败/重试/删除都会让自增漂移，
    重算能保证列表里的数字永远和文档表一致（顺带自愈历史数据）。
    """
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        return
    kb.doc_count = (
        db.query(func.count(Document.id))
        .filter(Document.kb_id == kb_id, Document.status == DocStatus.COMPLETED)
        .scalar() or 0
    )
    kb.chunk_count = (
        db.query(func.coalesce(func.sum(Document.chunk_count), 0))
        .filter(Document.kb_id == kb_id, Document.status == DocStatus.COMPLETED)
        .scalar() or 0
    )
    db.commit()


def _parse_and_index(doc: Document, db: Session, ai: AIConfig | None = None):
    doc.status = DocStatus.PARSING
    db.commit()

    raw_text = parse_file(doc.filepath)
    chunk_size = 512
    chunk_overlap = 64
    chunks = chunk_text(raw_text, chunk_size=chunk_size, overlap=chunk_overlap)

    if not chunks:
        doc.status = DocStatus.COMPLETED
        doc.chunk_count = 0
        db.commit()
        _refresh_kb_stats(doc.kb_id, db)
        return

    doc.status = DocStatus.VECTORIZING
    db.commit()

    embeddings = embed_texts(chunks, ai=ai)

    collection = get_collection(doc.kb_id)
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == doc.kb_id).first()
    kb_name = kb.name if kb else ""

    ids = [f"doc_{doc.id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {"doc_id": doc.id, "kb_id": doc.kb_id, "kb_name": kb_name,
         "filename": doc.filename, "chunk_index": i}
        for i in range(len(chunks))
    ]
    collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)

    doc.status = DocStatus.COMPLETED
    doc.chunk_count = len(chunks)
    db.commit()
    _refresh_kb_stats(doc.kb_id, db)


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    kb_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Document)
    if kb_id:
        query = query.filter(Document.kb_id == kb_id)
    if status:
        query = query.filter(Document.status == status)
    return query.order_by(Document.created_at.desc()).all()


@router.get("/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if not os.path.exists(doc.filepath):
        raise HTTPException(status_code=404, detail="文件已丢失")
    return FileResponse(
        path=doc.filepath,
        filename=doc.filename,
        media_type="application/octet-stream",
    )


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if os.path.exists(doc.filepath):
        os.remove(doc.filepath)
    try:
        collection = get_collection(doc.kb_id)
        collection.delete(where={"doc_id": doc_id})
    except Exception:
        pass
    db.delete(doc)
    db.commit()
    _refresh_kb_stats(doc.kb_id, db)
