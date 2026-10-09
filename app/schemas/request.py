from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.enums import Priority, RequestStatus, SLAStatus
from app.schemas.user import UserResponse
from app.schemas.category import CategoryResponse
from app.schemas.comment import CommentResponse
from app.schemas.history import HistoryResponse

class RequestCreate(BaseModel):
    subject: str = Field(..., min_length=3, max_length=200, description="Brief summary of the issue")
    description: str = Field(..., min_length=5, description="Detailed explanation of the request")
    category_id: int = Field(..., description="ID of the category (e.g. Hardware, Software, Network)")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level: LOW, MEDIUM, HIGH, CRITICAL")
    requester_id: int = Field(..., description="ID of employee raising the request")

class RequestUpdate(BaseModel):
    subject: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=5)
    category_id: Optional[int] = None
    priority: Optional[Priority] = None
    actor_id: Optional[int] = Field(None, description="User performing the update for audit logging")

class RequestAssign(BaseModel):
    assigned_to_id: int = Field(..., description="ID of the IT team member taking ownership")
    actor_id: int = Field(..., description="ID of the user performing assignment/reassignment")
    remarks: Optional[str] = None

class RequestStatusUpdate(BaseModel):
    new_status: RequestStatus = Field(..., description="Target status in lifecycle")
    actor_id: int = Field(..., description="ID of the user performing status change")
    remarks: Optional[str] = None

class RequestResolve(BaseModel):
    resolution_details: str = Field(..., min_length=5, description="Mandatory details of how the issue was resolved")
    resolved_by_id: int = Field(..., description="ID of IT team member who resolved the request")

class RequestClose(BaseModel):
    actor_id: int = Field(..., description="ID of requester or IT manager closing the request")
    remarks: Optional[str] = None

class RequestReopen(BaseModel):
    actor_id: int = Field(..., description="ID of user reopening the ticket")
    reason: str = Field(..., min_length=5, description="Reason why the request is being reopened")

class RequestResponse(BaseModel):
    id: int
    request_number: str
    subject: str
    description: str
    category_id: int
    priority: Priority
    status: RequestStatus
    requester_id: int
    assigned_to_id: Optional[int] = None

    resolution_details: Optional[str] = None
    resolved_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    reopened_at: Optional[datetime] = None

    sla_target_hours: float
    sla_due_at: datetime
    total_on_hold_seconds: int
    created_at: datetime
    updated_at: datetime

    # Nested related data
    category: Optional[CategoryResponse] = None
    requester: Optional[UserResponse] = None
    assigned_to: Optional[UserResponse] = None
    resolved_by: Optional[UserResponse] = None

    # Calculated SLA Computed Fields
    sla_status: SLAStatus
    is_sla_breached: bool
    sla_remaining_seconds: float
    sla_progress_percent: float

    model_config = ConfigDict(from_attributes=True)

class RequestDetailResponse(RequestResponse):
    comments: List[CommentResponse] = []
    history: List[HistoryResponse] = []
