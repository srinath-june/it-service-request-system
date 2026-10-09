from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.enums import Priority
from app.models.sla import SLAConfig
from app.schemas.sla import SLAConfigUpdate, SLAConfigResponse

router = APIRouter(prefix="/sla", tags=["SLA Configurations"])

@router.get("", response_model=List[SLAConfigResponse])
def list_sla_configurations(db: Session = Depends(get_db)):
    """Get all SLA target configurations by priority."""
    return db.query(SLAConfig).order_by(SLAConfig.resolution_sla_hours).all()

@router.put("/{priority}", response_model=SLAConfigResponse)
def update_sla_configuration(priority: Priority, sla_in: SLAConfigUpdate, db: Session = Depends(get_db)):
    """
    Dynamically update SLA resolution hours for a priority level.
    Allows changing SLA targets without modifying any backend application code!
    """
    config = db.query(SLAConfig).filter(SLAConfig.priority == priority).first()
    if not config:
        config = SLAConfig(
            priority=priority,
            resolution_sla_hours=sla_in.resolution_sla_hours or 24.0,
            response_sla_hours=sla_in.response_sla_hours or 1.0,
            is_active=True if sla_in.is_active is None else sla_in.is_active
        )
        db.add(config)
    else:
        if sla_in.resolution_sla_hours is not None:
            config.resolution_sla_hours = sla_in.resolution_sla_hours
        if sla_in.response_sla_hours is not None:
            config.response_sla_hours = sla_in.response_sla_hours
        if sla_in.is_active is not None:
            config.is_active = sla_in.is_active

    db.commit()
    db.refresh(config)
    return config
