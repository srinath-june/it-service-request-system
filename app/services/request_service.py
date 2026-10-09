from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from fastapi import HTTPException, status

from app.models.enums import Priority, RequestStatus, ActionType, UserRole
from app.models.user import User
from app.models.category import Category
from app.models.request import ServiceRequest
from app.models.comment import RequestComment
from app.models.history import RequestHistory
from app.schemas.request import (
    RequestCreate,
    RequestUpdate,
    RequestAssign,
    RequestStatusUpdate,
    RequestResolve,
    RequestClose,
    RequestReopen
)
from app.services.sla_service import SLAService

class RequestService:
    # Strict Valid Lifecycle Transitions Map
    # Current Status -> Set of allowed Target Statuses
    VALID_TRANSITIONS = {
        RequestStatus.NEW: {RequestStatus.ASSIGNED, RequestStatus.IN_PROGRESS, RequestStatus.ON_HOLD},
        RequestStatus.ASSIGNED: {RequestStatus.IN_PROGRESS, RequestStatus.ON_HOLD, RequestStatus.ASSIGNED},
        RequestStatus.IN_PROGRESS: {RequestStatus.ON_HOLD, RequestStatus.RESOLVED, RequestStatus.ASSIGNED},
        RequestStatus.ON_HOLD: {RequestStatus.IN_PROGRESS, RequestStatus.ASSIGNED, RequestStatus.RESOLVED},
        RequestStatus.RESOLVED: {RequestStatus.CLOSED, RequestStatus.IN_PROGRESS, RequestStatus.ASSIGNED},
        RequestStatus.CLOSED: set(),  # CLOSED tickets cannot change status directly; must use explicit reopen endpoint
    }

    @staticmethod
    def generate_request_number(db: Session) -> str:
        """Generates unique human-readable ticket number (e.g. SR-2026-0001)."""
        year = datetime.utcnow().year
        last_request = db.query(ServiceRequest).filter(
            ServiceRequest.request_number.like(f"SR-{year}-%")
        ).order_by(desc(ServiceRequest.id)).first()

        next_seq = 1
        if last_request and last_request.request_number:
            try:
                parts = last_request.request_number.split("-")
                next_seq = int(parts[-1]) + 1
            except (ValueError, IndexError):
                next_seq = db.query(ServiceRequest).count() + 1

        return f"SR-{year}-{next_seq:04d}"

    @staticmethod
    def create_request(db: Session, request_in: RequestCreate) -> ServiceRequest:
        """Creates a new service request after verifying requester and category."""
        # 1. Validate Requester
        requester = db.query(User).filter(User.id == request_in.requester_id, User.is_active == True).first()
        if not requester:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Requester with ID {request_in.requester_id} not found or inactive."
            )

        # 2. Validate Category
        category = db.query(Category).filter(Category.id == request_in.category_id, Category.is_active == True).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {request_in.category_id} not found or inactive."
            )

        # 3. Calculate SLA targets
        now = datetime.utcnow()
        sla_hours = SLAService.get_sla_hours_for_priority(db, request_in.priority)
        sla_due_at = SLAService.calculate_sla_due_date(now, sla_hours, on_hold_seconds=0)
        request_number = RequestService.generate_request_number(db)

        # 4. Create entity
        db_request = ServiceRequest(
            request_number=request_number,
            subject=request_in.subject.strip(),
            description=request_in.description.strip(),
            category_id=request_in.category_id,
            priority=request_in.priority,
            status=RequestStatus.NEW,
            requester_id=request_in.requester_id,
            assigned_to_id=None,
            sla_target_hours=sla_hours,
            sla_due_at=sla_due_at,
            total_on_hold_seconds=0,
            created_at=now,
            updated_at=now
        )
        db.add(db_request)
        db.flush()

        # 5. Record Creation Audit Trail
        history_entry = RequestHistory(
            request_id=db_request.id,
            actor_id=request_in.requester_id,
            action_type=ActionType.CREATED,
            field_name="status",
            old_value=None,
            new_value=RequestStatus.NEW.value,
            remarks=f"Request created with priority {request_in.priority.value} and SLA target {sla_hours} hours."
        )
        db.add(history_entry)
        db.commit()
        db.refresh(db_request)
        return db_request

    @staticmethod
    def get_request(db: Session, request_id: int) -> ServiceRequest:
        """Fetch request by ID or raise 404."""
        request = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service request with ID {request_id} was not found."
            )
        return request

    @staticmethod
    def update_request(db: Session, request_id: int, update_in: RequestUpdate) -> ServiceRequest:
        """Updates subject, description, category, or priority of an active request."""
        db_request = RequestService.get_request(db, request_id)

        if db_request.status == RequestStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A closed request cannot be modified. Reopen the request first if modifications are required."
            )

        actor_id = update_in.actor_id or db_request.requester_id

        # Update Category if provided
        if update_in.category_id and update_in.category_id != db_request.category_id:
            category = db.query(Category).filter(Category.id == update_in.category_id, Category.is_active == True).first()
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found or inactive.")
            old_cat = db_request.category.name if db_request.category else str(db_request.category_id)
            db_request.category_id = update_in.category_id
            db.add(RequestHistory(
                request_id=db_request.id,
                actor_id=actor_id,
                action_type=ActionType.CATEGORY_CHANGED,
                field_name="category",
                old_value=old_cat,
                new_value=category.name,
                remarks="Category updated"
            ))

        # Update Priority & Recalculate SLA if changed
        if update_in.priority and update_in.priority != db_request.priority:
            old_priority = db_request.priority.value
            new_sla_hours = SLAService.get_sla_hours_for_priority(db, update_in.priority)
            db_request.priority = update_in.priority
            db_request.sla_target_hours = new_sla_hours
            db_request.sla_due_at = SLAService.calculate_sla_due_date(
                db_request.created_at, new_sla_hours, db_request.total_on_hold_seconds
            )
            db.add(RequestHistory(
                request_id=db_request.id,
                actor_id=actor_id,
                action_type=ActionType.PRIORITY_CHANGED,
                field_name="priority",
                old_value=old_priority,
                new_value=update_in.priority.value,
                remarks=f"Priority updated to {update_in.priority.value}; SLA target adjusted to {new_sla_hours}h."
            ))

        if update_in.subject:
            db_request.subject = update_in.subject.strip()
        if update_in.description:
            db_request.description = update_in.description.strip()

        db_request.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_request)
        return db_request

    @staticmethod
    def assign_request(db: Session, request_id: int, assign_in: RequestAssign) -> ServiceRequest:
        """Assign or reassign an open request to an active IT team member."""
        db_request = RequestService.get_request(db, request_id)

        if db_request.status == RequestStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A closed request cannot be assigned or reassigned."
            )

        # Validate IT Team member
        assignee = db.query(User).filter(User.id == assign_in.assigned_to_id, User.is_active == True).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected IT team member was not found or is currently inactive."
            )

        if assignee.role not in [UserRole.IT_SUPPORT, UserRole.IT_MANAGER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{assignee.full_name}' with role '{assignee.role.value}' cannot be assigned IT service requests."
            )

        old_assignee_name = db_request.assigned_to.full_name if db_request.assigned_to else "Unassigned"
        action_type = ActionType.REASSIGNED if db_request.assigned_to_id else ActionType.ASSIGNED

        db_request.assigned_to_id = assignee.id

        # If ticket was in NEW status, automatically advance to ASSIGNED
        if db_request.status == RequestStatus.NEW:
            db_request.status = RequestStatus.ASSIGNED

        db_request.updated_at = datetime.utcnow()

        db.add(RequestHistory(
            request_id=db_request.id,
            actor_id=assign_in.actor_id,
            action_type=action_type,
            field_name="assigned_to",
            old_value=old_assignee_name,
            new_value=assignee.full_name,
            remarks=assign_in.remarks or f"Assigned to {assignee.full_name} ({assignee.role.value})"
        ))

        db.commit()
        db.refresh(db_request)
        return db_request

    @staticmethod
    def update_status(db: Session, request_id: int, status_in: RequestStatusUpdate) -> ServiceRequest:
        """Transitions request through valid lifecycle states and manages on-hold SLA pauses."""
        db_request = RequestService.get_request(db, request_id)
        current_status = db_request.status
        target_status = status_in.new_status

        if current_status == target_status:
            return db_request

        # Closed status guard
        if current_status == RequestStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A closed request cannot change status directly. Use the reopen workflow if necessary."
            )

        # Enforce valid status transition matrix
        allowed_targets = RequestService.VALID_TRANSITIONS.get(current_status, set())
        if target_status not in allowed_targets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from '{current_status.value}' to '{target_status.value}'. Allowed transitions: {[s.value for s in allowed_targets]}"
            )

        # Enforce business rules
        if target_status == RequestStatus.RESOLVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="To resolve a request, please use the /resolve endpoint with required resolution details."
            )

        now = datetime.utcnow()

        # Handle On-Hold SLA pause mechanics
        if target_status == RequestStatus.ON_HOLD and current_status != RequestStatus.ON_HOLD:
            db_request.on_hold_started_at = now
        elif current_status == RequestStatus.ON_HOLD and target_status != RequestStatus.ON_HOLD:
            if db_request.on_hold_started_at:
                hold_duration = int((now - db_request.on_hold_started_at).total_seconds())
                db_request.total_on_hold_seconds += max(0, hold_duration)
                db_request.on_hold_started_at = None
                # Update due date with new total on hold
                db_request.sla_due_at = SLAService.calculate_sla_due_date(
                    db_request.created_at, db_request.sla_target_hours, db_request.total_on_hold_seconds
                )

        db_request.status = target_status
        db_request.updated_at = now

        db.add(RequestHistory(
            request_id=db_request.id,
            actor_id=status_in.actor_id,
            action_type=ActionType.STATUS_CHANGED,
            field_name="status",
            old_value=current_status.value,
            new_value=target_status.value,
            remarks=status_in.remarks or f"Status changed from {current_status.value} to {target_status.value}"
        ))

        db.commit()
        db.refresh(db_request)
        return db_request

    @staticmethod
    def resolve_request(db: Session, request_id: int, resolve_in: RequestResolve) -> ServiceRequest:
        """Marks request as Resolved with mandatory resolution details and resolver identity."""
        db_request = RequestService.get_request(db, request_id)

        if db_request.status == RequestStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A closed request is already finalized and cannot be resolved again."
            )

        if not resolve_in.resolution_details or not resolve_in.resolution_details.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resolution details are required before resolving this request."
            )

        # Validate resolver
        resolver = db.query(User).filter(User.id == resolve_in.resolved_by_id, User.is_active == True).first()
        if not resolver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resolver user not found or inactive."
            )

        now = datetime.utcnow()

        # If resolving from On Hold, wrap up on-hold duration
        if db_request.status == RequestStatus.ON_HOLD and db_request.on_hold_started_at:
            hold_duration = int((now - db_request.on_hold_started_at).total_seconds())
            db_request.total_on_hold_seconds += max(0, hold_duration)
            db_request.on_hold_started_at = None
            db_request.sla_due_at = SLAService.calculate_sla_due_date(
                db_request.created_at, db_request.sla_target_hours, db_request.total_on_hold_seconds
            )

        old_status = db_request.status.value
        db_request.status = RequestStatus.RESOLVED
        db_request.resolution_details = resolve_in.resolution_details.strip()
        db_request.resolved_by_id = resolve_in.resolved_by_id
        db_request.resolved_at = now
        db_request.updated_at = now

        db.add(RequestHistory(
            request_id=db_request.id,
            actor_id=resolve_in.resolved_by_id,
            action_type=ActionType.RESOLVED,
            field_name="status",
            old_value=old_status,
            new_value=RequestStatus.RESOLVED.value,
            remarks=f"Resolved by {resolver.full_name}. Resolution: {resolve_in.resolution_details.strip()}"
        ))

        db.commit()
        db.refresh(db_request)
        return db_request

    @staticmethod
    def close_request(db: Session, request_id: int, close_in: RequestClose) -> ServiceRequest:
        """Closes a resolved request."""
        db_request = RequestService.get_request(db, request_id)

        if db_request.status == RequestStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request is already closed."
            )

        if db_request.status != RequestStatus.RESOLVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot close an unresolved request. Current status is '{db_request.status.value}'. Only requests in 'RESOLVED' status can be closed."
            )

        now = datetime.utcnow()
        db_request.status = RequestStatus.CLOSED
        db_request.closed_at = now
        db_request.updated_at = now

        db.add(RequestHistory(
            request_id=db_request.id,
            actor_id=close_in.actor_id,
            action_type=ActionType.CLOSED,
            field_name="status",
            old_value=RequestStatus.RESOLVED.value,
            new_value=RequestStatus.CLOSED.value,
            remarks=close_in.remarks or "Request officially verified and closed."
        ))

        db.commit()
        db.refresh(db_request)
        return db_request

    @staticmethod
    def reopen_request(db: Session, request_id: int, reopen_in: RequestReopen) -> ServiceRequest:
        """Reopens a resolved or closed request with a documented reason."""
        db_request = RequestService.get_request(db, request_id)

        if db_request.status not in [RequestStatus.RESOLVED, RequestStatus.CLOSED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only RESOLVED or CLOSED requests can be reopened. Current status is '{db_request.status.value}'."
            )

        actor = db.query(User).filter(User.id == reopen_in.actor_id, User.is_active == True).first()
        if not actor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actor not found.")

        now = datetime.utcnow()
        old_status = db_request.status.value
        # Reopen to IN_PROGRESS if assigned, else ASSIGNED
        new_status = RequestStatus.IN_PROGRESS if db_request.assigned_to_id else RequestStatus.ASSIGNED

        db_request.status = new_status
        db_request.reopened_at = now
        db_request.closed_at = None
        db_request.updated_at = now

        db.add(RequestHistory(
            request_id=db_request.id,
            actor_id=reopen_in.actor_id,
            action_type=ActionType.REOPENED,
            field_name="status",
            old_value=old_status,
            new_value=new_status.value,
            remarks=f"Reopened by {actor.full_name}. Reason: {reopen_in.reason}"
        ))

        db.commit()
        db.refresh(db_request)
        return db_request

    @staticmethod
    def add_comment(db: Session, request_id: int, author_id: int, comment_text: str, is_internal: bool = False) -> RequestComment:
        """Adds a comment or work note to a service request."""
        db_request = RequestService.get_request(db, request_id)

        if db_request.status == RequestStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add comments to a closed request."
            )

        author = db.query(User).filter(User.id == author_id, User.is_active == True).first()
        if not author:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Author not found.")

        comment = RequestComment(
            request_id=request_id,
            author_id=author_id,
            comment=comment_text.strip(),
            is_internal=is_internal,
            created_at=datetime.utcnow()
        )
        db.add(comment)

        db.add(RequestHistory(
            request_id=request_id,
            actor_id=author_id,
            action_type=ActionType.COMMENT_ADDED,
            field_name="comments",
            old_value=None,
            new_value="New comment",
            remarks=f"{'Internal work note' if is_internal else 'Public update'} added by {author.full_name}"
        ))

        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def enrich_with_sla(request: ServiceRequest) -> Dict[str, Any]:
        """Converts ServiceRequest model and injects real-time SLA metrics."""
        sla_metrics = SLAService.compute_sla_metrics(request)
        return {
            "id": request.id,
            "request_number": request.request_number,
            "subject": request.subject,
            "description": request.description,
            "category_id": request.category_id,
            "priority": request.priority,
            "status": request.status,
            "requester_id": request.requester_id,
            "assigned_to_id": request.assigned_to_id,
            "resolution_details": request.resolution_details,
            "resolved_by_id": request.resolved_by_id,
            "resolved_at": request.resolved_at,
            "closed_at": request.closed_at,
            "reopened_at": request.reopened_at,
            "sla_target_hours": request.sla_target_hours,
            "sla_due_at": sla_metrics["effective_due_date"],
            "total_on_hold_seconds": request.total_on_hold_seconds,
            "created_at": request.created_at,
            "updated_at": request.updated_at,
            "category": request.category,
            "requester": request.requester,
            "assigned_to": request.assigned_to,
            "resolved_by": request.resolved_by,
            "sla_status": sla_metrics["sla_status"],
            "is_sla_breached": sla_metrics["is_sla_breached"],
            "sla_remaining_seconds": sla_metrics["sla_remaining_seconds"],
            "sla_progress_percent": sla_metrics["sla_progress_percent"],
            "comments": getattr(request, "comments", []),
            "history": getattr(request, "history", [])
        }
