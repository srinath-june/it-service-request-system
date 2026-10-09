import sys
import os
from datetime import datetime, timedelta

from app.database import SessionLocal, engine, Base
from app.models.enums import UserRole, Priority, RequestStatus, ActionType, SLAStatus
from app.models.user import User
from app.models.category import Category
from app.models.sla import SLAConfig
from app.models.request import ServiceRequest
from app.models.comment import RequestComment
from app.models.history import RequestHistory
from app.services.sla_service import SLAService

def seed_database():
    """Initializes schema and seeds baseline and demo data."""
    print("Creating tables in database...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("Database already contains records. Skipping initial seeding.")
            return

        print("Seeding Users...")
        users_data = [
            # IT Team Members
            {"username": "alex.chen", "email": "alex.chen@company.com", "full_name": "Alex Chen", "role": UserRole.IT_SUPPORT, "department": "IT Operations"},
            {"username": "sarah.jenkins", "email": "sarah.j@company.com", "full_name": "Sarah Jenkins", "role": UserRole.IT_SUPPORT, "department": "IT Operations"},
            {"username": "marcus.vance", "email": "marcus.v@company.com", "full_name": "Marcus Vance", "role": UserRole.IT_MANAGER, "department": "IT Management"},
            {"username": "admin.sys", "email": "admin@company.com", "full_name": "System Administrator", "role": UserRole.ADMIN, "department": "Infrastructure"},
            # Employees / Requesters
            {"username": "emily.watson", "email": "emily.w@company.com", "full_name": "Emily Watson", "role": UserRole.EMPLOYEE, "department": "Finance"},
            {"username": "david.kim", "email": "david.k@company.com", "full_name": "David Kim", "role": UserRole.EMPLOYEE, "department": "Marketing"},
            {"username": "priya.sharma", "email": "priya.s@company.com", "full_name": "Priya Sharma", "role": UserRole.EMPLOYEE, "department": "Human Resources"},
            {"username": "jordan.lee", "email": "jordan.l@company.com", "full_name": "Jordan Lee", "role": UserRole.EMPLOYEE, "department": "Sales"},
        ]
        created_users = {}
        for u in users_data:
            user_obj = User(**u)
            db.add(user_obj)
            db.flush()
            created_users[u["username"]] = user_obj

        print("Seeding Categories...")
        categories_data = [
            {"name": "Hardware", "description": "Laptops, monitors, keyboards, docking stations, printers"},
            {"name": "Software", "description": "OS issues, standard software licenses, application bugs"},
            {"name": "Network", "description": "Wi-Fi connectivity, VPN access, LAN ports, bandwidth issues"},
            {"name": "Access / Permission", "description": "Shared drive access, database permissions, system logins"},
            {"name": "Email", "description": "Outlook, distribution lists, mailbox size, spam issues"},
            {"name": "Other", "description": "General technology requests and inquiries"}
        ]
        created_categories = {}
        for c in categories_data:
            cat_obj = Category(**c)
            db.add(cat_obj)
            db.flush()
            created_categories[c["name"]] = cat_obj

        print("Seeding SLA Configurations (per Challenge Spec: Critical 4h, High 8h, Medium 24h, Low 48h)...")
        sla_data = [
            {"priority": Priority.CRITICAL, "resolution_sla_hours": 4.0, "response_sla_hours": 0.5},
            {"priority": Priority.HIGH, "resolution_sla_hours": 8.0, "response_sla_hours": 1.0},
            {"priority": Priority.MEDIUM, "resolution_sla_hours": 24.0, "response_sla_hours": 2.0},
            {"priority": Priority.LOW, "resolution_sla_hours": 48.0, "response_sla_hours": 4.0},
        ]
        for s in sla_data:
            db.add(SLAConfig(**s))
        db.flush()

        print("Seeding Demo Service Requests across lifecycle states & SLA conditions...")
        now = datetime.utcnow()

        # Ticket 1: Critical Production VPN Outage (Assigned, Approaching Breach)
        created_t1 = now - timedelta(hours=3.2) # 3.2h out of 4h SLA = 80% elapsed (Approaching Breach)
        due_t1 = created_t1 + timedelta(hours=4)
        req1 = ServiceRequest(
            request_number="SR-2026-0001",
            subject="VPN Gateway Authentication Failure for Finance Team",
            description="Multiple finance members cannot access the ERP system via GlobalProtect VPN during monthend closing.",
            category_id=created_categories["Network"].id,
            priority=Priority.CRITICAL,
            status=RequestStatus.IN_PROGRESS,
            requester_id=created_users["emily.watson"].id,
            assigned_to_id=created_users["alex.chen"].id,
            sla_target_hours=4.0,
            sla_due_at=due_t1,
            total_on_hold_seconds=0,
            created_at=created_t1,
            updated_at=now - timedelta(minutes=45)
        )
        db.add(req1)
        db.flush()

        db.add(RequestHistory(
            request_id=req1.id, actor_id=created_users["emily.watson"].id,
            action_type=ActionType.CREATED, field_name="status",
            old_value=None, new_value=RequestStatus.NEW.value,
            remarks="Critical request submitted", created_at=created_t1
        ))
        db.add(RequestHistory(
            request_id=req1.id, actor_id=created_users["marcus.vance"].id,
            action_type=ActionType.ASSIGNED, field_name="assigned_to",
            old_value="Unassigned", new_value="Alex Chen",
            remarks="High priority incident assigned to Senior Ops", created_at=created_t1 + timedelta(minutes=15)
        ))
        db.add(RequestHistory(
            request_id=req1.id, actor_id=created_users["alex.chen"].id,
            action_type=ActionType.STATUS_CHANGED, field_name="status",
            old_value=RequestStatus.ASSIGNED.value, new_value=RequestStatus.IN_PROGRESS.value,
            remarks="Investigating RADIUS server cluster logs", created_at=created_t1 + timedelta(minutes=25)
        ))
        db.add(RequestComment(
            request_id=req1.id, author_id=created_users["alex.chen"].id,
            comment="Identified expired SAML token cert on gateway 2. Rotating certificate now.",
            is_internal=False, created_at=created_t1 + timedelta(minutes=40)
        ))

        # Ticket 2: High Priority - Laptop Screen Flickering (Unassigned, Within SLA)
        created_t2 = now - timedelta(hours=2)
        due_t2 = created_t2 + timedelta(hours=8)
        req2 = ServiceRequest(
            request_number="SR-2026-0002",
            subject="Dell Latitude display blacking out intermittently",
            description="External monitor works fine, but internal display goes completely black when tilting hinge.",
            category_id=created_categories["Hardware"].id,
            priority=Priority.HIGH,
            status=RequestStatus.NEW,
            requester_id=created_users["david.kim"].id,
            assigned_to_id=None,
            sla_target_hours=8.0,
            sla_due_at=due_t2,
            total_on_hold_seconds=0,
            created_at=created_t2,
            updated_at=created_t2
        )
        db.add(req2)
        db.flush()
        db.add(RequestHistory(
            request_id=req2.id, actor_id=created_users["david.kim"].id,
            action_type=ActionType.CREATED, field_name="status",
            old_value=None, new_value=RequestStatus.NEW.value,
            remarks="Hardware request submitted", created_at=created_t2
        ))

        # Ticket 3: Medium Priority - Payroll Drive Permission (Overdue / Breached)
        created_t3 = now - timedelta(hours=36) # 36h out of 24h SLA = Breached
        due_t3 = created_t3 + timedelta(hours=24)
        req3 = ServiceRequest(
            request_number="SR-2026-0003",
            subject="Read/Write Access to Q4 HR Payroll Share",
            description="Need access to the secured HR compensation spreadsheet for quarterly bonus auditing.",
            category_id=created_categories["Access / Permission"].id,
            priority=Priority.MEDIUM,
            status=RequestStatus.ASSIGNED,
            requester_id=created_users["priya.sharma"].id,
            assigned_to_id=created_users["sarah.jenkins"].id,
            sla_target_hours=24.0,
            sla_due_at=due_t3,
            total_on_hold_seconds=0,
            created_at=created_t3,
            updated_at=created_t3 + timedelta(hours=1)
        )
        db.add(req3)
        db.flush()
        db.add(RequestHistory(
            request_id=req3.id, actor_id=created_users["priya.sharma"].id,
            action_type=ActionType.CREATED, field_name="status",
            old_value=None, new_value=RequestStatus.NEW.value,
            remarks="Access request created", created_at=created_t3
        ))
        db.add(RequestHistory(
            request_id=req3.id, actor_id=created_users["sarah.jenkins"].id,
            action_type=ActionType.ASSIGNED, field_name="assigned_to",
            old_value="Unassigned", new_value="Sarah Jenkins",
            remarks="Claimed by Sarah", created_at=created_t3 + timedelta(hours=1)
        ))

        # Ticket 4: Low Priority - New Mouse Request (On Hold waiting for shipment)
        created_t4 = now - timedelta(hours=10)
        due_t4 = created_t4 + timedelta(hours=48)
        req4 = ServiceRequest(
            request_number="SR-2026-0004",
            subject="Ergonomic vertical mouse for workstation",
            description="Requesting Logitech MX Vertical mouse as recommended by workplace ergonomics assessment.",
            category_id=created_categories["Hardware"].id,
            priority=Priority.LOW,
            status=RequestStatus.ON_HOLD,
            requester_id=created_users["jordan.lee"].id,
            assigned_to_id=created_users["alex.chen"].id,
            sla_target_hours=48.0,
            sla_due_at=due_t4,
            total_on_hold_seconds=0,
            on_hold_started_at=now - timedelta(hours=4),
            created_at=created_t4,
            updated_at=now - timedelta(hours=4)
        )
        db.add(req4)
        db.flush()
        db.add(RequestHistory(
            request_id=req4.id, actor_id=created_users["alex.chen"].id,
            action_type=ActionType.STATUS_CHANGED, field_name="status",
            old_value=RequestStatus.IN_PROGRESS.value, new_value=RequestStatus.ON_HOLD.value,
            remarks="Waiting for supplier delivery confirmation", created_at=now - timedelta(hours=4)
        ))
        db.add(RequestComment(
            request_id=req4.id, author_id=created_users["alex.chen"].id,
            comment="Placed order with vendor #PO-9821. Expected delivery in 2 business days.",
            is_internal=False, created_at=now - timedelta(hours=4)
        ))

        # Ticket 5: Resolved Ticket (Resolved within SLA)
        created_t5 = now - timedelta(hours=18)
        resolved_t5 = created_t5 + timedelta(hours=5.5) # 5.5h < 24h SLA
        due_t5 = created_t5 + timedelta(hours=24)
        req5 = ServiceRequest(
            request_number="SR-2026-0005",
            subject="Docker Desktop License Activation Failure",
            description="Docker desktop reports commercial license expired after recent workstation reimaging.",
            category_id=created_categories["Software"].id,
            priority=Priority.MEDIUM,
            status=RequestStatus.RESOLVED,
            requester_id=created_users["david.kim"].id,
            assigned_to_id=created_users["sarah.jenkins"].id,
            resolution_details="Re-allocated corporate license key via SSO portal and cleared cached Docker credentials.",
            resolved_by_id=created_users["sarah.jenkins"].id,
            resolved_at=resolved_t5,
            sla_target_hours=24.0,
            sla_due_at=due_t5,
            total_on_hold_seconds=0,
            created_at=created_t5,
            updated_at=resolved_t5
        )
        db.add(req5)
        db.flush()
        db.add(RequestHistory(
            request_id=req5.id, actor_id=created_users["sarah.jenkins"].id,
            action_type=ActionType.RESOLVED, field_name="status",
            old_value=RequestStatus.IN_PROGRESS.value, new_value=RequestStatus.RESOLVED.value,
            remarks="Resolved by Sarah Jenkins. License verified.", created_at=resolved_t5
        ))

        # Ticket 6: Closed Ticket
        created_t6 = now - timedelta(days=3)
        resolved_t6 = created_t6 + timedelta(hours=3)
        closed_t6 = resolved_t6 + timedelta(hours=24)
        due_t6 = created_t6 + timedelta(hours=8)
        req6 = ServiceRequest(
            request_number="SR-2026-0006",
            subject="Email distribution list setup for 'Product-Launch-2026'",
            description="Create distribution list including marketing, product, and QA lead emails.",
            category_id=created_categories["Email"].id,
            priority=Priority.HIGH,
            status=RequestStatus.CLOSED,
            requester_id=created_users["david.kim"].id,
            assigned_to_id=created_users["marcus.vance"].id,
            resolution_details="Distribution list 'product-launch-2026@company.com' created with requested members and moderation rules.",
            resolved_by_id=created_users["marcus.vance"].id,
            resolved_at=resolved_t6,
            closed_at=closed_t6,
            sla_target_hours=8.0,
            sla_due_at=due_t6,
            total_on_hold_seconds=0,
            created_at=created_t6,
            updated_at=closed_t6
        )
        db.add(req6)
        db.flush()
        db.add(RequestHistory(
            request_id=req6.id, actor_id=created_users["david.kim"].id,
            action_type=ActionType.CLOSED, field_name="status",
            old_value=RequestStatus.RESOLVED.value, new_value=RequestStatus.CLOSED.value,
            remarks="Closed after requester confirmed distribution list is functioning.", created_at=closed_t6
        ))

        db.commit()
        print("Database seeded successfully with users, categories, SLA configs, and demo service requests!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
