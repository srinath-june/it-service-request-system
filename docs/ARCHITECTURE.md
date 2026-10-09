# System Architecture & Design Documentation

## 1. High-Level Architectural Overview

The **IT Service Request Management System** is built using a modern **Layered Service-Oriented Architecture (SOA)** with clear separation of concerns across presentation, API routing, business domain services, data access / ORM, and persistence layers.

```mermaid
flowchart TD
    subgraph Client ["Client Layer"]
        Browser["Responsive Web Dashboard (SPA)<br/>(HTML5 / CSS3 / Bootstrap 5 / Chart.js)"]
        Swagger["Swagger UI / OpenAPI 3.0<br/>(/docs)"]
    end

    subgraph API ["REST API Layer (FastAPI)"]
        Router["API Router (v1)"]
        ReqEP["/requests Endpoints"]
        UserEP["/users Endpoints"]
        CatEP["/categories Endpoints"]
        SlaEP["/sla Endpoints"]
        RepEP["/reports Endpoints"]
    end

    subgraph Services ["Business Logic Layer"]
        ReqService["RequestService<br/>(State Machine, Validation, Audit Trail)"]
        SlaService["SLAService<br/>(Dynamic SLA Clock, On-Hold Pausing)"]
        RepService["ReportService<br/>(Aggregations, Compliance %, Workload)"]
    end

    subgraph Data ["Data & Persistence Layer"]
        ORM["SQLAlchemy ORM 2.0<br/>(Entities & Relationships)"]
        DB[("MariaDB / MySQL<br/>(Relational Storage with Indexes & Foreign Keys)")]
    end

    Browser --> Router
    Swagger --> Router
    Router --> ReqEP & UserEP & CatEP & SlaEP & RepEP
    ReqEP --> ReqService
    UserEP & CatEP & SlaEP --> ORM
    RepEP --> RepService
    ReqService --> SlaService & ORM
    RepService --> SlaService & ORM
    ORM --> DB
```

---

## 2. Request Lifecycle State Machine

The system enforces strict lifecycle state transitions to guarantee operational integrity. Requests cannot jump between inappropriate states (e.g. `NEW` directly to `CLOSED`).

```mermaid
stateDiagram-v2
    [*] --> NEW: Employee raises request
    
    NEW --> ASSIGNED: IT Manager/Agent assigns ticket
    NEW --> IN_PROGRESS: IT Agent takes ownership directly
    NEW --> ON_HOLD: Waiting for requester details
    
    ASSIGNED --> IN_PROGRESS: Work begins
    ASSIGNED --> ON_HOLD: Waiting for third-party/parts
    ASSIGNED --> ASSIGNED: Reassignment to another agent
    
    IN_PROGRESS --> ON_HOLD: SLA clock paused
    IN_PROGRESS --> RESOLVED: Resolved (Mandatory details recorded)
    IN_PROGRESS --> ASSIGNED: Reassigned to specialist
    
    ON_HOLD --> IN_PROGRESS: Information provided (SLA resumes)
    ON_HOLD --> ASSIGNED: Reassigned while on hold
    ON_HOLD --> RESOLVED: Issue resolved after on-hold info
    
    RESOLVED --> CLOSED: Requester/Manager confirms resolution
    RESOLVED --> IN_PROGRESS: Requester reopens ticket
    
    CLOSED --> IN_PROGRESS: Formal Reopening (Reason mandatory)
    CLOSED --> [*]
```

### Transition Matrix & Enforcement Rules
| From State | Allowed Target States | Mandatory Requirements / Constraints |
| :--- | :--- | :--- |
| **`NEW`** | `ASSIGNED`, `IN_PROGRESS`, `ON_HOLD` | Assignee must belong to IT Team (`IT_SUPPORT`, `IT_MANAGER`, `ADMIN`). |
| **`ASSIGNED`** | `IN_PROGRESS`, `ON_HOLD`, `ASSIGNED` | Reassignment updates audit log with old and new technician. |
| **`IN_PROGRESS`** | `ON_HOLD`, `RESOLVED`, `ASSIGNED` | Cannot transition to `CLOSED` directly without resolution. |
| **`ON_HOLD`** | `IN_PROGRESS`, `ASSIGNED`, `RESOLVED` | Pauses SLA countdown; elapsed hold time is recorded into `total_on_hold_seconds`. |
| **`RESOLVED`** | `CLOSED`, `IN_PROGRESS` (Reopen) | `resolution_details` and `resolved_by_id` are strictly enforced. |
| **`CLOSED`** | `IN_PROGRESS` (Reopen only) | Closed tickets are immutable; cannot be edited or commented on without explicit Reopening. |

---

## 3. SLA Calculation & Real-Time Monitoring Engine

### SLA Parameters (Default Hackathon Spec)
- **Critical:** 4 hours resolution SLA
- **High:** 8 hours resolution SLA
- **Medium:** 24 hours resolution SLA
- **Low:** 48 hours resolution SLA

### Dynamic Calculation Model
1. **Clock Initialization:** The SLA clock starts immediately at `created_at`.
2. **On-Hold Compensation:** When a ticket enters `ON_HOLD`, `on_hold_started_at` is timestamped. Upon leaving `ON_HOLD`, the elapsed hold duration is added to `total_on_hold_seconds`.
$$\text{SLA Due Date} = \text{Created At} + \text{SLA Target Duration} + \text{Total On-Hold Duration}$$
3. **Breach Determination:**
   - **For Open Tickets:** $\text{Is Breached} = \text{Current UTC Time} > \text{SLA Due Date}$.
   - **Approaching Breach Warning:** Triggered when $\ge 75\%$ of the allotted SLA time has elapsed.
   - **For Resolved/Closed Tickets:** Evaluated by checking if $\text{Resolved At} \le \text{SLA Due Date}$.
4. **Dynamic Configuration:** SLA target hours per priority are stored in the database (`sla_configs` table) and can be modified at runtime via the `/api/v1/sla` API without redeploying code.
