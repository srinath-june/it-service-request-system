from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.enums import Priority, RequestStatus, SLAStatus
from app.models.request import ServiceRequest
from app.schemas.request import (
    RequestCreate,
    RequestUpdate,
    RequestAssign,
    RequestStatusUpdate,
    RequestResolve,
    RequestClose,
    RequestReopen,
    RequestResponse,
    RequestDetailResponse
)
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.history import HistoryResponse
from app.services.request_service import RequestService
from app.services.sla_service import SLAService

router = APIRouter(prefix="/requests", tags=["Service Requests"])

@router.post("", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
def create_service_request(request_in: RequestCreate, db: Session = Depends(get_db)):
    """Create a new IT service request."""
    db_request = RequestService.create_request(db, request_in)
    return RequestService.enrich_with_sla(db_request)

@router.get("", response_model=List[RequestResponse])
def list_service_requests(
    status_filter: Optional[RequestStatus] = Query(None, alias="status", description="Filter by status"),
    priority_filter: Optional[Priority] = Query(None, alias="priority", description="Filter by priority"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    assigned_to_id: Optional[int] = Query(None, description="Filter by assigned IT user ID"),
    unassigned_only: Optional[bool] = Query(False, description="Filter for unassigned requests"),
    requester_id: Optional[int] = Query(None, description="Filter by requester user ID"),
    sla_breached_only: Optional[bool] = Query(False, description="Filter for SLA breached requests only"),
    search: Optional[str] = Query(None, description="Search subject, description, or ticket number"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List service requests with rich filtering, search, and pagination."""
    query = db.query(ServiceRequest)

    if status_filter:
        query = query.filter(ServiceRequest.status == status_filter)

    if priority_filter:
        query = query.filter(ServiceRequest.priority == priority_filter)

    if category_id:
        query = query.filter(ServiceRequest.category_id == category_id)

    if unassigned_only:
        query = query.filter(ServiceRequest.assigned_to_id.is_(None))
    elif assigned_to_id is not None:
        query = query.filter(ServiceRequest.assigned_to_id == assigned_to_id)

    if requester_id:
        query = query.filter(ServiceRequest.requester_id == requester_id)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                ServiceRequest.request_number.ilike(term),
                ServiceRequest.subject.ilike(term),
                ServiceRequest.description.ilike(term)
            )
        )

    results = query.order_by(desc(ServiceRequest.created_at)).offset(skip).limit(limit).all()

    enriched_results = [RequestService.enrich_with_sla(req) for req in results]

    if sla_breached_only:
        enriched_results = [r for r in enriched_results if r["is_sla_breached"]]

    return enriched_results

@router.get("/{request_id}", response_model=RequestDetailResponse)
def get_service_request(request_id: int, db: Session = Depends(get_db)):
    """Get full details of a service request including comments and history."""
    db_request = RequestService.get_request(db, request_id)
    return RequestService.enrich_with_sla(db_request)

@router.put("/{request_id}", response_model=RequestResponse)
def update_service_request(request_id: int, update_in: RequestUpdate, db: Session = Depends(get_db)):
    """Update fields (subject, description, category, priority) of an active service request."""
    db_request = RequestService.update_request(db, request_id, update_in)
    return RequestService.enrich_with_sla(db_request)

@router.post("/{request_id}/assign", response_model=RequestResponse)
def assign_service_request(request_id: int, assign_in: RequestAssign, db: Session = Depends(get_db)):
    """Assign or reassign a request to an IT team member."""
    db_request = RequestService.assign_request(db, request_id, assign_in)
    return RequestService.enrich_with_sla(db_request)

@router.post("/{request_id}/status", response_model=RequestResponse)
def update_request_status(request_id: int, status_in: RequestStatusUpdate, db: Session = Depends(get_db)):
    """Update lifecycle status with transition validation."""
    db_request = RequestService.update_status(db, request_id, status_in)
    return RequestService.enrich_with_sla(db_request)

@router.post("/{request_id}/resolve", response_model=RequestResponse)
def resolve_service_request(request_id: int, resolve_in: RequestResolve, db: Session = Depends(get_db)):
    """Mark a service request as Resolved with mandatory resolution details."""
    db_request = RequestService.resolve_request(db, request_id, resolve_in)
    return RequestService.enrich_with_sla(db_request)

@router.post("/{request_id}/close", response_model=RequestResponse)
def close_service_request(request_id: int, close_in: RequestClose, db: Session = Depends(get_db)):
    """Close a resolved service request."""
    db_request = RequestService.close_request(db, request_id, close_in)
    return RequestService.enrich_with_sla(db_request)

@router.post("/{request_id}/reopen", response_model=RequestResponse)
def reopen_service_request(request_id: int, reopen_in: RequestReopen, db: Session = Depends(get_db)):
    """Reopen a resolved or closed service request with documented justification."""
    db_request = RequestService.reopen_request(db, request_id, reopen_in)
    return RequestService.enrich_with_sla(db_request)

@router.post("/{request_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_request_comment(request_id: int, comment_in: CommentCreate, db: Session = Depends(get_db)):
    """Add a public comment or internal IT work note."""
    comment = RequestService.add_comment(
        db,
        request_id=request_id,
        author_id=comment_in.author_id,
        comment_text=comment_in.comment,
        is_internal=comment_in.is_internal
    )
    return comment

@router.get("/{request_id}/history", response_model=List[HistoryResponse])
def get_request_history(request_id: int, db: Session = Depends(get_db)):
    """Get complete chronological audit history of a service request."""
    db_request = RequestService.get_request(db, request_id)
    return db_request.history
