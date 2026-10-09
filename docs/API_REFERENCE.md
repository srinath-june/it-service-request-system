# REST API Reference Documentation

Base URL: `http://localhost:8000/api/v1`  
Interactive OpenAPI / Swagger UI: `http://localhost:8000/docs`

---

## 1. Service Requests Endpoints

### `POST /requests`
Create a new service request.
- **Request Body:**
  ```json
  {
    "subject": "VPN connection failure",
    "description": "Cannot connect to company VPN from home network",
    "category_id": 3,
    "priority": "HIGH",
    "requester_id": 5
  }
  ```
- **Response (201 Created):** Returns full `RequestResponse` object with calculated SLA deadline.

---

### `GET /requests`
List all service requests with rich filtering, search, and pagination.
- **Query Parameters:**
  - `status`: `NEW`, `ASSIGNED`, `IN_PROGRESS`, `ON_HOLD`, `RESOLVED`, `CLOSED`
  - `priority`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
  - `category_id`: Integer
  - `assigned_to_id`: Integer
  - `unassigned_only`: Boolean (`true`/`false`)
  - `requester_id`: Integer
  - `sla_breached_only`: Boolean (`true`/`false`)
  - `search`: String (searches subject, description, ticket number)
  - `skip`: Integer (default `0`)
  - `limit`: Integer (default `100`)

---

### `GET /requests/{id}`
Retrieve complete request details, including nested comments list and full chronological audit history.
- **Response (200 OK):** `RequestDetailResponse`

---

### `PUT /requests/{id}`
Update mutable fields (subject, description, category, priority) on an active ticket.
- **Note:** Updates to priority automatically recalculate SLA targets and due dates.
- **Forbidden:** Closed requests cannot be modified.

---

### `POST /requests/{id}/assign`
Assign or reassign a request to an IT support staff member.
- **Request Body:**
  ```json
  {
    "assigned_to_id": 1,
    "actor_id": 3,
    "remarks": "Assigned to network specialist"
  }
  ```
- **Validation:** Assignee must be active and have role `IT_SUPPORT`, `IT_MANAGER`, or `ADMIN`. Automatically transitions `NEW` tickets to `ASSIGNED`.

---

### `POST /requests/{id}/status`
Transition request lifecycle state.
- **Request Body:**
  ```json
  {
    "new_status": "ON_HOLD",
    "actor_id": 1,
    "remarks": "Waiting for user laptop serial number"
  }
  ```
- **Validation:** Strictly enforces allowed state transition matrix. Manages SLA pausing when entering/leaving `ON_HOLD`.

---

### `POST /requests/{id}/resolve`
Mark ticket as Resolved.
- **Request Body:**
  ```json
  {
    "resolved_by_id": 1,
    "resolution_details": "Replaced faulty RAM module and ran diagnostic suite."
  }
  ```
- **Validation:** `resolution_details` is mandatory and cannot be empty.

---

### `POST /requests/{id}/close`
Officially close a resolved request.
- **Request Body:**
  ```json
  {
    "actor_id": 5,
    "remarks": "Requester confirmed issue resolved"
  }
  ```
- **Validation:** Cannot close unresolved requests.

---

### `POST /requests/{id}/reopen`
Reopen a closed or resolved request.
- **Request Body:**
  ```json
  {
    "actor_id": 5,
    "reason": "Display started flickering again this morning"
  }
  ```

---

### `POST /requests/{id}/comments`
Add a user update or internal IT work note.
- **Request Body:**
  ```json
  {
    "author_id": 1,
    "comment": "Ordered replacement parts from vendor PO #4912",
    "is_internal": true
  }
  ```

---

## 2. Dynamic SLA Configuration Endpoints

### `GET /sla`
List all SLA resolution and response targets across priority tiers.

### `PUT /sla/{priority}`
Update SLA resolution hours dynamically for a specific priority (e.g. `CRITICAL`).
- **Request Body:**
  ```json
  {
    "resolution_sla_hours": 3.5,
    "response_sla_hours": 0.5
  }
  ```

---

## 3. Management Reports & Dashboard Endpoints

### `GET /reports/dashboard`
Returns executive KPI statistics, SLA breach counts, compliance rates, and breakdowns by priority, category, status, and IT assignee.
