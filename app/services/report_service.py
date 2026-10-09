from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from datetime import datetime

from app.models.enums import Priority, RequestStatus, SLAStatus, UserRole
from app.models.user import User
from app.models.category import Category
from app.models.request import ServiceRequest
from app.schemas.report import DashboardMetrics, CountByGroup, AssigneeWorkload
from app.services.sla_service import SLAService

class ReportService:
    @staticmethod
    def get_dashboard_metrics(db: Session) -> DashboardMetrics:
        """Generates comprehensive management metrics and analytics."""
        all_requests = db.query(ServiceRequest).all()
        now = datetime.utcnow()

        total = len(all_requests)
        total_open = 0
        total_resolved = 0
        total_closed = 0
        unassigned = 0
        sla_breached_open = 0
        sla_breached_total = 0
        approaching_sla = 0
        critical_open = 0
        high_open = 0

        # Grouping dictionaries
        priority_counts = {p.value: 0 for p in Priority}
        category_map = {c.id: c.name for c in db.query(Category).all()}
        category_counts = {name: 0 for name in category_map.values()}
        status_counts = {s.value: 0 for s in RequestStatus}

        # Assignee tracking
        it_users = db.query(User).filter(
            User.role.in_([UserRole.IT_SUPPORT, UserRole.IT_MANAGER, UserRole.ADMIN]),
            User.is_active == True
        ).all()
        assignee_stats: Dict[int, Dict[str, Any]] = {
            u.id: {
                "user_id": u.id,
                "name": u.full_name,
                "open_tickets": 0,
                "resolved_tickets": 0,
                "sla_breached_tickets": 0
            }
            for u in it_users
        }
        unassigned_workload = {
            "user_id": None,
            "name": "Unassigned",
            "open_tickets": 0,
            "resolved_tickets": 0,
            "sla_breached_tickets": 0
        }

        resolved_or_closed_within_sla_count = 0
        total_finished = 0

        for req in all_requests:
            # Category & Priority & Status tally
            p_val = req.priority.value if hasattr(req.priority, "value") else str(req.priority)
            s_val = req.status.value if hasattr(req.status, "value") else str(req.status)
            c_name = category_map.get(req.category_id, "Unknown")

            priority_counts[p_val] = priority_counts.get(p_val, 0) + 1
            category_counts[c_name] = category_counts.get(c_name, 0) + 1
            status_counts[s_val] = status_counts.get(s_val, 0) + 1

            # Compute SLA
            metrics = SLAService.compute_sla_metrics(req, now)
            is_breached = metrics["is_sla_breached"]
            sla_status = metrics["sla_status"]

            is_open = req.status in [RequestStatus.NEW, RequestStatus.ASSIGNED, RequestStatus.IN_PROGRESS, RequestStatus.ON_HOLD]

            if is_open:
                total_open += 1
                if req.assigned_to_id is None:
                    unassigned += 1
                if is_breached:
                    sla_breached_open += 1
                if sla_status == SLAStatus.APPROACHING_BREACH:
                    approaching_sla += 1
                if req.priority == Priority.CRITICAL:
                    critical_open += 1
                elif req.priority == Priority.HIGH:
                    high_open += 1
            elif req.status == RequestStatus.RESOLVED:
                total_resolved += 1
            elif req.status == RequestStatus.CLOSED:
                total_closed += 1

            if is_breached:
                sla_breached_total += 1

            if req.status in [RequestStatus.RESOLVED, RequestStatus.CLOSED]:
                total_finished += 1
                if not is_breached:
                    resolved_or_closed_within_sla_count += 1

            # Assignee workload
            if req.assigned_to_id and req.assigned_to_id in assignee_stats:
                if is_open:
                    assignee_stats[req.assigned_to_id]["open_tickets"] += 1
                else:
                    assignee_stats[req.assigned_to_id]["resolved_tickets"] += 1
                if is_breached:
                    assignee_stats[req.assigned_to_id]["sla_breached_tickets"] += 1
            elif not req.assigned_to_id:
                if is_open:
                    unassigned_workload["open_tickets"] += 1
                else:
                    unassigned_workload["resolved_tickets"] += 1
                if is_breached:
                    unassigned_workload["sla_breached_tickets"] += 1

        # SLA compliance calculation
        compliance_rate = round((resolved_or_closed_within_sla_count / total_finished * 100.0), 1) if total_finished > 0 else 100.0

        # Convert to schema items
        by_priority = [
            CountByGroup(
                label=k,
                count=v,
                percentage=round((v / total * 100.0), 1) if total > 0 else 0.0
            )
            for k, v in priority_counts.items()
        ]

        by_category = [
            CountByGroup(
                label=k,
                count=v,
                percentage=round((v / total * 100.0), 1) if total > 0 else 0.0
            )
            for k, v in category_counts.items()
        ]

        by_status = [
            CountByGroup(
                label=k,
                count=v,
                percentage=round((v / total * 100.0), 1) if total > 0 else 0.0
            )
            for k, v in status_counts.items()
        ]

        by_assignee = [AssigneeWorkload(**data) for data in assignee_stats.values()]
        if unassigned_workload["open_tickets"] > 0 or unassigned_workload["resolved_tickets"] > 0:
            by_assignee.append(AssigneeWorkload(**unassigned_workload))

        return DashboardMetrics(
            total_requests=total,
            total_open_requests=total_open,
            total_resolved_requests=total_resolved,
            total_closed_requests=total_closed,
            unassigned_requests=unassigned,
            sla_breached_open_requests=sla_breached_open,
            sla_breached_total_requests=sla_breached_total,
            approaching_sla_breach_requests=approaching_sla,
            critical_open_requests=critical_open,
            high_open_requests=high_open,
            sla_compliance_rate_percent=compliance_rate,
            by_priority=by_priority,
            by_category=by_category,
            by_status=by_status,
            by_assignee=by_assignee
        )
