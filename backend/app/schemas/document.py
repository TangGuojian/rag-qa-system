from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentResponse(BaseModel):
    id: int
    kb_id: int
    filename: str
    file_size: int
    file_type: str
    status: str
    tags: Optional[str] = None
    chunk_count: int = 0
    error_msg: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
