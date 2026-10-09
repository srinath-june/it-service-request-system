from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.enums import Priority

class SLAConfigBase(BaseModel):
    priority: Priority
    resolution_sla_hours: float = Field(..., gt=0)
    response_sla_hours: float = Field(default=1.0, gt=0)
    is_active: bool = True

class SLAConfigUpdate(BaseModel):
    resolution_sla_hours: Optional[float] = Field(None, gt=0)
    response_sla_hours: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None

class SLAConfigResponse(SLAConfigBase):
    id: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
