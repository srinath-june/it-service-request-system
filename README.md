# IT Service Request Management System

A centralized, production-grade IT Service Request Management System built for organizational technology operations. It enables employees to raise IT tickets and empowers IT support staff and managers to process, track, assign, resolve, and close requests with dynamic SLA tracking and comprehensive management reporting.

---

## 1. Project Overview

The system addresses organizational challenges regarding missing requests, lack of ownership, untracked SLA breaches, and unstructured history by providing:
- **Centralized Service Request Intake:** Categorized by Hardware, Software, Network, Access/Permission, Email, etc.
- **Priority-Driven SLA Lifecycle:** Automatic calculation of SLA due dates based on priority (`CRITICAL` 4h, `HIGH` 8h, `MEDIUM` 24h, `LOW` 48h).
- **On-Hold SLA Pausing:** Pauses the SLA countdown when waiting on requester actions and dynamically recalculates effective SLA deadlines.
- **State Machine Enforcement:** Strict lifecycle transitions (`NEW` $\rightarrow$ `ASSIGNED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `ON_HOLD` $\rightarrow$ `RESOLVED` $\rightarrow$ `CLOSED`).
- **Complete Audit Trail & History:** Chronological audit logging of every status transition, assignment change, priority update, and comment.
- **Executive Analytics Dashboard:** Real-time visibility into open tickets, SLA breaches, approaching breaches, compliance rates, category distribution, and IT technician workload.
- **Dynamic SLA Configuration:** Modify resolution SLA targets per priority at runtime without modifying application logic.

---

## 2. Technology Stack

- **Backend:** Python 3.10+ with **FastAPI** (High-performance ASGI framework with Pydantic v2 type safety and auto-generated OpenAPI/Swagger documentation).
- **ORM & Data Layer:** **SQLAlchemy 2.0** with connection pooling and schema management.
- **Database:** **MariaDB / MySQL** (with zero-setup SQLite fallback supported via `.env`).
- **Frontend:** Responsive Single-Page Application (SPA) built with **HTML5, CSS3, Bootstrap 5, FontAwesome, and Chart.js**.
- **Testing:** **Pytest** with automated functional, validation, SLA, and workflow tests.
- **Database Driver:** `PyMySQL` and `cryptography`.

---

## 3. Setup & Installation Guide

### Prerequisites
- Python 3.10 or higher
- (Optional) MariaDB / MySQL Server 10.5+

### Step 1: Clone or Extract Repository
```bash
cd it-service-request-system
```

### Step 2: Create & Activate Virtual Environment
```bash
# Windows:
python -m venv venv
venv\Scripts\activate

# Linux / macOS:
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Database
The project includes a `.env` file pre-configured for instant zero-setup SQLite development:
```ini
# Default SQLite:
DATABASE_URL=sqlite:///./it_service_system.db

# Or MariaDB / MySQL (Hackathon Specification):
# DATABASE_URL=mysql+pymysql://it_user:it_password@localhost:3306/it_service_db
```

#### If using MariaDB / MySQL:
1. Run the DDL script located at `sql/schema.sql`:
   ```bash
   mysql -u root -p < sql/schema.sql
   mysql -u root -p < sql/seed_data.sql
   ```
2. Update the `DATABASE_URL` in `.env`.

### Step 5: Initialize Schema & Seed Data
```bash
python seed.py
```

### Step 6: Start Application Server
```bash
python run.py
```
- 🌐 **Web Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- 📖 **Interactive Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 🩺 **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 4. Database Design & Architecture

### Entity Relationship Diagram
```mermaid
erDiagram
    USERS ||--o{ SERVICE_REQUESTS : "requests"
    USERS ||--o{ SERVICE_REQUESTS : "assigned_to"
    USERS ||--o{ SERVICE_REQUESTS : "resolved_by"
    USERS ||--o{ REQUEST_COMMENTS : "authors"
    USERS ||--o{ REQUEST_HISTORY : "acts_on"
    CATEGORIES ||--o{ SERVICE_REQUESTS : "categorizes"
    SERVICE_REQUESTS ||--o{ REQUEST_COMMENTS : "contains"
    SERVICE_REQUESTS ||--o{ REQUEST_HISTORY : "tracks"
    SLA_CONFIGS
```

### Key Relational Tables:
1. `users`: Stores Employees, IT Technicians, IT Managers, and Admins.
2. `categories`: Manageable IT request classifications (Hardware, Software, Network, Access, Email, Other).
3. `sla_configs`: Dynamic resolution/response SLA targets per priority.
4. `service_requests`: Core ticket entity with SLA targets, due dates, resolution details, and pause trackers.
5. `request_comments`: Public updates and internal IT technician work notes.
6. `request_history`: Immutable chronological audit trail recording all actions, state transitions, old/new values, and actor IDs.

---

## 5. API Reference Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/requests` | Raise a new IT service request |
| `GET` | `/api/v1/requests` | Query & filter requests (search, status, priority, category, assignee, SLA breach) |
| `GET` | `/api/v1/requests/{id}` | Get full request details with comments, history & computed SLA metrics |
| `PUT` | `/api/v1/requests/{id}` | Update active request fields (subject, description, category, priority) |
| `POST` | `/api/v1/requests/{id}/assign` | Assign or reassign ticket to an active IT team member |
| `POST` | `/api/v1/requests/{id}/status` | Transition lifecycle status with transition validation |
| `POST` | `/api/v1/requests/{id}/resolve` | Mark ticket as Resolved (Mandatory resolution details) |
| `POST` | `/api/v1/requests/{id}/close` | Officially close a resolved request |
| `POST` | `/api/v1/requests/{id}/reopen` | Reopen a resolved/closed request with justification |
| `POST` | `/api/v1/requests/{id}/comments` | Add public comment or internal technician work note |
| `GET` | `/api/v1/requests/{id}/history` | Retrieve complete audit trail for a ticket |
| `GET` | `/api/v1/users` | List users / staff |
| `GET` | `/api/v1/categories` | List categories |
| `GET` | `/api/v1/sla` | List SLA target hours per priority |
| `PUT` | `/api/v1/sla/{priority}` | Dynamically update SLA resolution hours |
| `GET` | `/api/v1/reports/dashboard` | Aggregated executive KPIs, compliance rate, and breakdowns |

---

## 6. Business Rules & Assumptions

1. **SLA Calculation Model:**
   - The SLA clock begins at `created_at`.
   - **On Hold Suspension:** Placing a ticket in `ON_HOLD` pauses the SLA clock. The pause duration is credited to `total_on_hold_seconds`, extending the `sla_due_at` timestamp dynamically.
   - **Priority Update:** Changing priority automatically updates the SLA target hours and shifts the due date accordingly.
2. **Strict Transition Rules:**
   - `NEW` cannot transition directly to `CLOSED` or `RESOLVED` without being processed.
   - Only `RESOLVED` tickets can be moved to `CLOSED`.
   - `resolution_details` are mandatory to mark a ticket `RESOLVED`.
   - Closed requests cannot be modified without being formally reopened.
3. **Reopening Assumption:**
   - Reopening a resolved or closed ticket requires a mandatory justification and transitions the ticket back to `IN_PROGRESS` (or `ASSIGNED` if unassigned).
4. **Assignment Rules:**
   - Only active users with role `IT_SUPPORT`, `IT_MANAGER`, or `ADMIN` can be assigned tickets. Standard `EMPLOYEE` users cannot take ownership.

---

## 7. Automated Testing Suite

Execute the full automated pytest suite:
```bash
python -m pytest -v
```

### Test Coverage Summary:
- ✅ `test_create_request_success`: Verifies request generation, number formatting (`SR-YYYY-NNNN`), default priority, and SLA target assignment.
- ✅ `test_list_requests_and_filters`: Validates multi-attribute filtering, category filters, and substring search queries.
- ✅ `test_get_request_details`: Validates retrieval of nested comments, history, and SLA countdowns.
- ✅ `test_complete_ticket_lifecycle`: Verifies end-to-end flow: `NEW` $\rightarrow$ `ASSIGNED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `ON_HOLD` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `RESOLVED` $\rightarrow$ `CLOSED` $\rightarrow$ `REOPEN`.
- ✅ `test_validation_missing_required_fields`: Confirms rejection of empty subjects/descriptions (HTTP 422).
- ✅ `test_validation_invalid_assignee_role`: Prevents assigning tickets to standard employees or inactive staff.
- ✅ `test_validation_invalid_status_transition`: Prevents closing an unresolved ticket (HTTP 400).
- ✅ `test_validation_resolve_without_details`: Rejects resolve attempts without resolution text.
- ✅ `test_validation_modify_closed_request`: Rejects edits or comments on finalized closed requests.
- ✅ `test_sla_hours_assignment_by_priority`: Validates 4h Critical, 8h High, 24h Medium, 48h Low SLA allocation.
- ✅ `test_sla_configuration_update_dynamically`: Validates runtime SLA modification via API.
- ✅ `test_dashboard_metrics`: Verifies calculation of total open, breached, unassigned, and compliance rates.

---

## 8. Known Limitations & Future Improvements

### Known Limitations
- Email and SMS delivery for SLA breach notifications is currently logged and tracked via UI/API rather than dispatched to an external SMTP server.
- File attachments (screenshots/crash dumps) are referenced via text URLs rather than binary S3/Blob storage.

### Future Improvements (Phase 2 Ready)
- **Automated Round-Robin Assignment:** Automatically balance unassigned requests across active IT agents based on workload.
- **Webhook & Slack/Teams Integration:** Real-time push notifications for Critical SLA alerts.
- **JWT Authentication & RBAC:** Session tokens and fine-grained role authorization.
