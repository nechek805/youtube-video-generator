from datetime import datetime

from pydantic import BaseModel


class SessionReadFirstTime(BaseModel):
    session_token: str
    created_at: datetime
    expires_at: datetime


class SessionRead(BaseModel):
    id: int
    created_at: datetime
    expires_at: datetime
