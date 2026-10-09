from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class CountByGroup(BaseModel):
    label: str
    count: int
    percentage: Optional[float] = 0.0

class AssigneeWorkload(BaseModel):
    user_id: Optional[int] = None
    name: str
    open_tickets: int
    resolved_tickets: int
    sla_breached_tickets: int

class DashboardMetrics(BaseModel):
    total_requests: int
    total_open_requests: int
    total_resolved_requests: int
    total_closed_requests: int
    unassigned_requests: int
    sla_breached_open_requests: int
    sla_breached_total_requests: int
    approaching_sla_breach_requests: int
    critical_open_requests: int
    high_open_requests: int
    sla_compliance_rate_percent: float

    # Breakdowns
    by_priority: List[CountByGroup]
    by_category: List[CountByGroup]
    by_status: List[CountByGroup]
    by_assignee: List[AssigneeWorkload]
