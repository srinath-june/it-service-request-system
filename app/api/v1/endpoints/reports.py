from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.report import DashboardMetrics
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Management Reports & Analytics"])

@router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Get full IT Management Dashboard statistics:
    - Total, Open, Resolved, Closed, Unassigned, Breached, Approaching
    - Workload and metrics grouped by Priority, Category, Status, and Assignee
    - SLA Compliance rate calculation
    """
    return ReportService.get_dashboard_metrics(db)
