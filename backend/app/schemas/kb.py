from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class KBCreate(BaseModel):
    name: str
    description: Optional[str] = None


class KBUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class KBResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    doc_count: int = 0
    chunk_count: int = 0
    graph_node_count: int = 0
    graph_edge_count: int = 0
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
