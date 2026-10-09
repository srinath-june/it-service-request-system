# Technical Evaluation & Architectural Q&A

This document provides structured, technical explanations for the design decisions and evaluation questions outlined in **Section 33** of the Challenge Specification.

---

### 1. Why did you choose this database structure?
- **Relational Integrity & 3NF:** Entities like `users`, `categories`, `sla_configs`, `service_requests`, `request_comments`, and `request_history` have well-defined cardinality (e.g. 1-to-many from requests to comments and history).
- **Auditability:** History is modeled as an append-only transaction ledger (`request_history`), guaranteeing full compliance and timeline reconstruction without relying on mutable state timestamps alone.
- **Dynamic SLA Modeling:** `sla_configs` decouples SLA values from hardcoded application logic, allowing runtime SLA adjustments.

---

### 2. Why did you choose FastAPI?
- **High Performance & Asynchronous I/O:** Built on Starlette and Uvicorn, FastAPI provides asynchronous execution and minimal latency.
- **Strong Typing & Data Validation:** Tight integration with Pydantic v2 enforces schema validation at runtime, catching malformed payloads, invalid enums, and missing required parameters before reaching the database.
- **Automated OpenAPI / Swagger Documentation:** Live interactive documentation is generated automatically at `/docs`, enabling rapid API testing and cross-team integration.

---

### 3. Why did you separate these tables (requests, history, comments)?
- **Separation of Concerns & Performance:** Keeping main ticket metadata in `service_requests` keeps row size compact and sequential scan fast during high-frequency list and dashboard filtering queries.
- **Unbounded Growth Isolation:** Comments and audit history records grow unboundedly per ticket. Placing them in separate tables with foreign keys and cascade rules prevents row bloat and preserves normalized 1:N relations.

---

### 4. Where is the SLA calculation performed?
- **Centralized Service Layer (`SLAService`):**
  - Business rules for SLA target durations, pause mechanics during `ON_HOLD`, warning thresholds (75% elapsed), and breach detections are encapsulated inside `app/services/sla_service.py`.
  - **Reasoning:** Centralizing calculation in the service layer guarantees consistency across REST API responses, periodic background workers, and management reporting queries without duplicated SQL snippets or client-side calculation drift.

---

### 5. Why is this validation on the backend?
- **Security & Integrity:** Client-side validation is easily bypassed via direct HTTP calls, curl, or automated scripts.
- **Data Consistency:** Business rules (e.g., "Assignee must be an active IT technician", "Resolution details mandatory before resolving", "Closed tickets immutable") represent enterprise invariants that the database and backend services must strictly enforce.

---

### 6. What happens if two users update the same request simultaneously?
- **Current Behavior:** Database-level ACID transactions with row-level locks protect individual field updates.
- **Enterprise Enhancement:** In high-concurrency production environments, we implement **Optimistic Concurrency Control (OCC)** by adding a `version` (or `updated_at`) integer column to `service_requests`. The update query checks `WHERE id = :id AND version = :expected_version`. If another user modified the ticket concurrently, the version check fails with `409 Conflict`, prompting the user to refresh.

---

### 7. How would you handle 100,000 service requests?
1. **Database Indexing:** We have established composite B-tree indexes on `(status, priority)`, `(assigned_to_id, status)`, `(sla_due_at)`, and `(created_at)`.
2. **Server-Side Pagination:** The API enforces `skip` and `limit` on all listing endpoints.
3. **Database Partitioning / Archiving:** For historical requests older than 2 years, table partitioning by year (`PARTITION BY RANGE (YEAR(created_at))`) or moving `CLOSED` tickets to an `archived_service_requests` cold-storage table.
4. **Read Replicas & Caching:** Redis caching for dashboard KPI summaries with a 30-second TTL.

---

### 8. What indexes would you add?
- `idx_req_status_priority` (`status`, `priority`) $\rightarrow$ For fast dashboard status/priority aggregates.
- `idx_req_assigned_status` (`assigned_to_id`, `status`) $\rightarrow$ For fast technician workload filters.
- `idx_req_requester_status` (`requester_id`, `status`) $\rightarrow$ For user self-service ticket portal.
- `idx_req_sla_due` (`sla_due_at`) $\rightarrow$ For real-time SLA breach alerting queries.
- `idx_req_created_at` (`created_at`) $\rightarrow$ For time-window reporting.

---

### 9. What happens if the database operation fails halfway through?
- **Atomicity via Unit of Work:** Every multi-step workflow operation (e.g., updating ticket status + creating audit history entry + logging work note) executes inside an atomic database transaction. If any step raises an error, `db.rollback()` executes, ensuring zero partial or corrupted state.

---

### 10. What would you change if the SLA rules changed?
- The system includes the `sla_configs` table and `/api/v1/sla/{priority}` endpoint. Modifying SLA resolution hours updates the configuration immediately for future calculations and priority changes without modifying application logic or redeploying code.

---

### 11. What would you improve if you had another day?
- **Phase 2 Expansion Features:**
  - Automated ticket assignment based on round-robin or technician queue depth.
  - Email / Slack webhook notifications on SLA breach alerts.
  - Multi-attachment file upload support (screenshots, logs).
  - Role-Based Access Control (RBAC) with JWT auth token sessions.
