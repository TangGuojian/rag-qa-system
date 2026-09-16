"""
批量导入知识库文档脚本
用法: python batch_import.py
"""
import os
import sys
import re
import time
import io
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pdfplumber
import openpyxl
from sqlalchemy.orm import Session

from app.db.mysql import SessionLocal, engine, Base
from app.db.chroma import chroma_client
from app.models.document import Document, DocStatus, DocType
from app.models.kb import KnowledgeBase
from app.rag.embedding import embed_texts as _embed_texts

BATCH_SIZE = 10


def embed_texts(texts: list[str]) -> list[list[float]]:
    results = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        results.extend(_embed_texts(batch))
    return results

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

DATA_DIRS = {
    1: os.getenv("KB1_DATA_DIR", r"data\公司相关制度"),
    2: os.getenv("KB2_DATA_DIR", r"data\财政数据集"),
}

# DocType override for kb 2 files: .md -> DocType.MD, .xlsx -> DocType.XLSX
EXT_TO_DOCTYPE = {
    ".pdf": DocType.PDF,
    ".md": DocType.MD,
    ".xlsx": DocType.XLSX,
    ".txt": DocType.TXT,
}


def get_doctype(ext: str) -> DocType:
    return EXT_TO_DOCTYPE.get(ext, DocType.TXT)


def parse_pdf(filepath: str) -> str:
    text_parts = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts)


def parse_md(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def parse_xlsx(filepath: str) -> str:
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    lines = []
    for sheet in wb.worksheets:
        for row in sheet.iter_rows(values_only=True):
            row_text = " | ".join(str(c) for c in row if c is not None)
            if row_text.strip():
                lines.append(row_text)
    wb.close()
    return "\n".join(lines)


def chunk_text(text: str, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> list[str]:
    if not text.strip():
        return []
    chunks = []
    paragraphs = re.split(r"\n\s*\n", text.strip())
    buffer = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(buffer) + len(para) < chunk_size:
            buffer += ("\n" if buffer else "") + para
            continue
        if buffer:
            chunks.append(buffer)
        while len(para) > chunk_size:
            chunks.append(para[:chunk_size])
            para = para[chunk_size - overlap:]
        buffer = para
    if buffer:
        chunks.append(buffer)
    return chunks


def process_file(kb_id: int, filepath: str, db: Session) -> Document:
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()
    file_size = os.path.getsize(filepath)
    doc_type = get_doctype(ext)

    existing = db.query(Document).filter(Document.filepath == filepath).first()
    if existing:
        safe_name = filename.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
        print(f"  SKIP (already exists): {safe_name}")
        return existing

    safe_name = filename.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    print(f"  PARSING: {safe_name} ({file_size} bytes) ...", end=" ", flush=True)

    if doc_type == DocType.PDF:
        text = parse_pdf(filepath)
    elif doc_type == DocType.XLSX:
        text = parse_xlsx(filepath)
    else:
        text = parse_md(filepath)

    if not text.strip():
        print("EMPTY - skipped")
        return None

    chunks = chunk_text(text)
    if not chunks:
        print("NO CHUNKS - skipped")
        return None

    doc = Document(
        kb_id=kb_id,
        filename=filename,
        filepath=filepath,
        file_size=file_size,
        file_type=doc_type,
        status=DocStatus.PARSING,
        uploaded_by=1,
    )
    db.add(doc)
    db.flush()
    doc_id = doc.id

    print(f"{len(chunks)} chunks, vectorizing...", end=" ", flush=True)

    try:
        embeddings = embed_texts(chunks)
        collection_name = f"collection_{kb_id}"
        collection = chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"kb_id": kb_id},
        )

        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "doc_id": doc_id,
                "kb_id": kb_id,
                "filename": filename,
                "chunk_idx": i,
            }
            for i in range(len(chunks))
        ]

        collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        doc.chunk_count = len(chunks)
        doc.status = DocStatus.COMPLETED
        db.commit()

        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if kb:
            kb.doc_count = db.query(Document).filter(
                Document.kb_id == kb_id,
                Document.status == DocStatus.COMPLETED,
            ).count()
            kb.chunk_count = (kb.chunk_count or 0) + len(chunks)
            db.commit()

        print("DONE")
    except Exception as e:
        doc.status = DocStatus.FAILED
        doc.error_msg = str(e)
        db.commit()
        print(f"FAILED: {e}")

    return doc


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for kb_id, data_dir in DATA_DIRS.items():
            kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
            if not kb:
                print(f"KnowledgeBase id={kb_id} not found, skipping")
                continue
            print(f"\n=== Knowledge Base: {kb.name} (id={kb_id}) ===")
            print(f"   Dir: {data_dir}")

            if not os.path.isdir(data_dir):
                print(f"   Directory not found: {data_dir}")
                continue

            all_files = []
            for root, dirs, files in os.walk(data_dir):
                for fname in files:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in EXT_TO_DOCTYPE:
                        all_files.append(os.path.join(root, fname))

            print(f"   Found {len(all_files)} files")
            for fpath in sorted(all_files):
                process_file(kb_id, fpath, db)
    finally:
        db.close()


if __name__ == "__main__":
    start = time.time()
    main()
    elapsed = time.time() - start
    print(f"\n=== Import completed in {elapsed:.1f}s ===")
