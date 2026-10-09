from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.enums import Priority, RequestStatus, SLAStatus
from app.models.sla import SLAConfig
from app.models.request import ServiceRequest
from app.config import settings

class SLAService:
    @staticmethod
    def get_sla_hours_for_priority(db: Session, priority: Priority) -> float:
        """Fetches configured SLA resolution hours from database or fallback defaults."""
        config = db.query(SLAConfig).filter(SLAConfig.priority == priority, SLAConfig.is_active == True).first()
        if config:
            return config.resolution_sla_hours

        # Fallback values from settings
        fallback_map = {
            Priority.CRITICAL: float(settings.SLA_CRITICAL_HOURS),
            Priority.HIGH: float(settings.SLA_HIGH_HOURS),
            Priority.MEDIUM: float(settings.SLA_MEDIUM_HOURS),
            Priority.LOW: float(settings.SLA_LOW_HOURS),
        }
        return fallback_map.get(priority, 24.0)

    @staticmethod
    def calculate_sla_due_date(created_at: datetime, target_hours: float, on_hold_seconds: int = 0) -> datetime:
        """Calculates SLA due date based on created time, target duration, and any paused on-hold seconds."""
        total_seconds = int(target_hours * 3600) + on_hold_seconds
        return created_at + timedelta(seconds=total_seconds)

    @staticmethod
    def compute_sla_metrics(request: ServiceRequest, now: datetime = None) -> Dict[str, Any]:
        """
        Computes real-time SLA metrics for a service request:
        - sla_status
        - is_sla_breached
        - sla_remaining_seconds
        - sla_progress_percent
        """
        if now is None:
            now = datetime.utcnow()

        # Account for active on-hold time if currently On Hold
        current_on_hold_seconds = request.total_on_hold_seconds
        if request.status == RequestStatus.ON_HOLD and request.on_hold_started_at:
            active_pause = int((now - request.on_hold_started_at).total_seconds())
            if active_pause > 0:
                current_on_hold_seconds += active_pause

        # Recalculate dynamic due date with on-hold compensation
        effective_due_date = SLAService.calculate_sla_due_date(
            request.created_at,
            request.sla_target_hours,
            current_on_hold_seconds
        )

        total_allowed_seconds = request.sla_target_hours * 3600.0

        # Check if already resolved / closed
        if request.status in [RequestStatus.RESOLVED, RequestStatus.CLOSED]:
            resolution_time = request.resolved_at or request.closed_at or request.updated_at
            # Compare resolution time against SLA due date
            is_breached = resolution_time > effective_due_date
            sla_status = SLAStatus.RESOLVED_BREACHED if is_breached else SLAStatus.RESOLVED_WITHIN_SLA

            time_taken_seconds = max(0.0, (resolution_time - request.created_at).total_seconds() - current_on_hold_seconds)
            progress_percent = min(100.0, round((time_taken_seconds / total_allowed_seconds) * 100.0, 1)) if total_allowed_seconds > 0 else 100.0
            remaining_seconds = max(0.0, (effective_due_date - resolution_time).total_seconds())

            return {
                "sla_status": sla_status,
                "is_sla_breached": is_breached,
                "sla_remaining_seconds": remaining_seconds,
                "sla_progress_percent": progress_percent,
                "effective_due_date": effective_due_date
            }

        # Ticket is currently active/open
        elapsed_active_seconds = max(0.0, (now - request.created_at).total_seconds() - current_on_hold_seconds)
        remaining_seconds = (effective_due_date - now).total_seconds()

        is_breached = remaining_seconds < 0
        progress_percent = round((elapsed_active_seconds / total_allowed_seconds) * 100.0, 1) if total_allowed_seconds > 0 else 100.0

        if is_breached:
            sla_status = SLAStatus.SLA_BREACHED
        elif progress_percent >= settings.SLA_WARNING_THRESHOLD_PERCENT:
            sla_status = SLAStatus.APPROACHING_BREACH
        else:
            sla_status = SLAStatus.WITHIN_SLA

        return {
            "sla_status": sla_status,
            "is_sla_breached": is_breached,
            "sla_remaining_seconds": max(0.0, remaining_seconds) if not is_breached else remaining_seconds,
            "sla_progress_percent": max(0.0, progress_percent),
            "effective_due_date": effective_due_date
        }
