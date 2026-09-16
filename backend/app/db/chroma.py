import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

_persist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_data")
os.makedirs(_persist_dir, exist_ok=True)

chroma_client = chromadb.PersistentClient(
    path=_persist_dir,
    settings=ChromaSettings(anonymized_telemetry=False),
)


def get_collection(kb_id: int):
    collection_name = f"collection_{kb_id}"
    try:
        return chroma_client.get_collection(collection_name)
    except (ValueError, chromadb.errors.NotFoundError):
        return chroma_client.create_collection(
            name=collection_name,
            metadata={"kb_id": kb_id},
        )


def delete_collection(kb_id: int):
    collection_name = f"collection_{kb_id}"
    try:
        chroma_client.delete_collection(collection_name)
    except (ValueError, chromadb.errors.NotFoundError):
        pass
