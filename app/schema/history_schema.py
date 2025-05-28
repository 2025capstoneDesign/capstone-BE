from pydantic import BaseModel
from typing import Any
from datetime import datetime

class HistoryResponse(BaseModel):
    id: int
    user_email: str
    filename: str
    notes_json: Any
    created_at: datetime  

    class Config:
        from_attributes = True


class HistoryDeleteResponse(BaseModel):
    message: str
    filename: str