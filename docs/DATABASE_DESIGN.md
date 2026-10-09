# Database Design & Relational Schema

## 1. Entity-Relationship Overview

The database is designed with full 3rd Normal Form (3NF) relational principles, strict foreign key constraints, check constraints, and performance indexes.

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

    USERS {
        int id PK
        string username UK
        string email UK
        string full_name
        enum role
        string department
        boolean is_active
        datetime created_at
    }

    CATEGORIES {
        int id PK
        string name UK
        string description
        boolean is_active
        datetime created_at
    }

    SLA_CONFIGS {
        int id PK
        enum priority UK
        float resolution_sla_hours
        float response_sla_hours
        boolean is_active
        datetime updated_at
    }

    SERVICE_REQUESTS {
        int id PK
        string request_number UK
        string subject
        text description
        int category_id FK
        enum priority
        enum status
        int requester_id FK
        int assigned_to_id FK
        text resolution_details
        int resolved_by_id FK
        datetime resolved_at
        datetime closed_at
        datetime reopened_at
        float sla_target_hours
        datetime sla_due_at
        int total_on_hold_seconds
        datetime on_hold_started_at
        datetime created_at
        datetime updated_at
    }

    REQUEST_COMMENTS {
        int id PK
        int request_id FK
        int author_id FK
        text comment
        boolean is_internal
        datetime created_at
    }

    REQUEST_HISTORY {
        int id PK
        int request_id FK
        int actor_id FK
        enum action_type
        string field_name
        string old_value
        string new_value
        text remarks
        datetime created_at
    }
```

---

## 2. Table Specifications & Index Strategy

### `users`
- **Primary Key:** `id` (Auto Increment)
- **Unique Constraints:** `username`, `email`
- **Indexes:** `idx_users_role` (`role`), `idx_users_active` (`is_active`)

### `categories`
- **Primary Key:** `id` (Auto Increment)
- **Unique Constraints:** `name`
- **Indexes:** `idx_categories_active` (`is_active`)

### `sla_configs`
- **Primary Key:** `id` (Auto Increment)
- **Unique Constraints:** `priority`
- **Purpose:** Stores configurable SLA hours per priority (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).

### `service_requests`
- **Primary Key:** `id` (Auto Increment)
- **Unique Constraints:** `request_number` (`SR-YYYY-NNNN`)
- **Foreign Keys:**
  - `fk_req_category`: `category_id` $\rightarrow$ `categories.id` (`ON DELETE RESTRICT`)
  - `fk_req_requester`: `requester_id` $\rightarrow$ `users.id` (`ON DELETE RESTRICT`)
  - `fk_req_assigned`: `assigned_to_id` $\rightarrow$ `users.id` (`ON DELETE SET NULL`)
  - `fk_req_resolver`: `resolved_by_id` $\rightarrow$ `users.id` (`ON DELETE SET NULL`)
- **Composite & High-Performance Indexes:**
  - `idx_req_status_priority` (`status`, `priority`): Optimizes executive dashboard grouping.
  - `idx_req_assigned_status` (`assigned_to_id`, `status`): Optimizes IT technician workload queries.
  - `idx_req_requester_status` (`requester_id`, `status`): Accelerates requester ticket portal filtering.
  - `idx_req_sla_due` (`sla_due_at`): Speeds up real-time SLA breach and overdue monitoring.
  - `idx_req_created_at` (`created_at`): Enables fast time-series reporting.

### `request_comments`
- **Primary Key:** `id`
- **Foreign Keys:** `request_id` $\rightarrow$ `service_requests.id` (`ON DELETE CASCADE`), `author_id` $\rightarrow$ `users.id` (`ON DELETE RESTRICT`)
- **Indexes:** `idx_comm_request_created` (`request_id`, `created_at`)

### `request_history`
- **Primary Key:** `id`
- **Foreign Keys:** `request_id` $\rightarrow$ `service_requests.id` (`ON DELETE CASCADE`), `actor_id` $\rightarrow$ `users.id` (`ON DELETE SET NULL`)
- **Indexes:** `idx_hist_request_created` (`request_id`, `created_at`)
