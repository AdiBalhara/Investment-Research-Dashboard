from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class WatchlistAdd(BaseModel):
    ticker: str
    company_name: str


class WatchlistItemResponse(BaseModel):
    id: UUID
    ticker: str
    company_name: str
    added_at: datetime

    class Config:
        from_attributes = True
