# Database design

PostgreSQL stores four main entities. SQLAlchemy declares the models and Alembic
revisions 0001–0003 create the schema.

```mermaid
erDiagram
    USER ||--o{ USER : manages
    USER ||--o{ REQUEST : submits
    USER ||--o{ REQUEST : processes
    REQUEST ||--o{ APPROVAL : has
    USER ||--o{ APPROVAL : decides
    REQUEST ||--o{ AUDIT_LOG : records
    USER ||--o{ AUDIT_LOG : acts

    USER {
      int id PK
      string email UK
      string hashed_password
      enum role
      int manager_id FK
      boolean is_active
    }
    REQUEST {
      int id PK
      string request_number UK
      int requester_id FK
      int processing_owner_id FK
      enum category
      enum priority
      decimal estimated_cost
      enum status
      datetime due_date
      datetime processing_started_at
      datetime completed_at
    }
    APPROVAL {
      int id PK
      int request_id FK
      int approver_id FK
      enum approval_type
      enum status
      string comment
      datetime decided_at
    }
    AUDIT_LOG {
      int id PK
      int request_id FK
      int actor_id FK
      enum action
      enum previous_status
      enum new_status
      string details
      datetime created_at
    }
```

## Relationships and constraints

- `users.manager_id` is a nullable self-reference. One manager can have many direct
  reports; a user cannot be their own manager.
- `requests.requester_id` identifies the owner. `processing_owner_id` is required
  only for Processing/Completed requests.
- `approvals` has one row per request and stage through a unique constraint. Manager
  stages have an assigned approver; Finance records the authorized user who decides.
- `audit_logs.actor_id` is nullable because an automatic system event can have no
  human actor. Each event retains its request and optional previous/new state.
- Cost uses `NUMERIC(15,2)`, not floating point. Checks require non-negative values
  and consistent processing/completion timestamps.

## Request numbers

The PostgreSQL `request_number_seq` allocates the numeric portion of display values
such as `REQ-2026-0042`. A sequence stays safe under concurrent inserts and may leave
gaps after rollback. A gap is expected sequence behavior, not evidence of deleted data.
The counter does not reset each calendar year.

## Audit protection

The API exposes no audit mutation endpoint. Revision 0003 adds database protections
against ordinary update, delete, and truncate operations. A database owner retains
the ability to change the database, so this is append-only application history rather
than cryptographically tamper-proof storage.
