"""
Pydantic schemas for request/response validation.

NodeCreate: for POST body (name, host, port — all required)
NodeUpdate: for PUT body (host, port — optional)
NodeResponse: for API responses (includes id, status, timestamps)
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class NodeCreate(BaseModel):
    name: str
    host: str
    port: int = Field(..., ge=1, le=65535)

class NodeUpdate(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)

class NodeResponse(BaseModel):
    id: int
    name: str
    host: str
    port: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class HealthResponse(BaseModel):
    status: str
    db: str
    nodes_count: int