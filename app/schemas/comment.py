from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.user import UserResponse

class CommentCreate(BaseModel):
    author_id: int
    comment: str = Field(..., min_length=1)
    is_internal: bool = False

class CommentResponse(BaseModel):
    id: int
    request_id: int
    author_id: int
    author: Optional[UserResponse] = None
    comment: str
    is_internal: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
