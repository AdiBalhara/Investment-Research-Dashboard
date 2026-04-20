from uuid import UUID
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    query: str
    result: dict[str, Any]
    confidence: float = 0.75


class ReportResponse(BaseModel):
    id: UUID
    query: str
    result: dict[str, Any]
    confidence: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListItem(BaseModel):
    id: UUID
    query: str
    confidence: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
