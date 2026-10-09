from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.enums import ActionType
from app.schemas.user import UserResponse

class HistoryResponse(BaseModel):
    id: int
    request_id: int
    actor_id: Optional[int] = None
    actor: Optional[UserResponse] = None
    action_type: ActionType
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    remarks: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
