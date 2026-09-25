# API documentation

FastAPI publishes the complete generated OpenAPI UI at `/docs` while the backend is
running. This document is a map of the business API rather than a duplicate schema reference.

All protected routes require `Authorization: Bearer <JWT>`. JSON responses use typed
Pydantic schemas. Validation returns 422; missing/invalid identity 401; unauthorized
role 403; invisible object 404; and stale/invalid workflow state 409.

## Authentication

| Method and path | Purpose |
| --- | --- |
| `POST /auth/login` | Verify email/password and return JWT plus safe user profile |
| `GET /auth/me` | Reload the active authenticated user |

## Requests and approvals

| Method and path | Purpose |
| --- | --- |
| `POST /requests` | Create a request using the authenticated requester |
| `GET /requests` | Paginate requests visible to the role; optional `own` filter |
| `GET /requests/{id}` | Request, approvals, SLA, fulfillment, and allowed actions |
| `PATCH /requests/{id}/cancel` | Cancel an eligible request owned by the actor |
| `GET /approvals/pending` | Manager or Finance pending queue |
| `POST /requests/{id}/manager-approval` | Assigned Manager approve/reject |
| `POST /requests/{id}/finance-approval` | Finance approve/reject a routed request |

## Procurement and audit

| Method and path | Purpose |
| --- | --- |
| `GET /procurement/queue` | Approved/Processing operational queue |
| `POST /requests/{id}/start-processing` | Claim and begin an Approved request |
| `POST /requests/{id}/complete` | Assigned owner completes Processing work |
| `GET /requests/{id}/audit` | Chronological events subject to request visibility |

## Analytics and health

| Method and path | Purpose |
| --- | --- |
| `GET /analytics/summary` | Admin-only KPIs and chart data |
| `GET /api/health` | Process liveness; no database query |
| `GET /api/health/ready` | Process plus PostgreSQL readiness |

Request bodies cannot set server-owned fields such as requester, request number,
status, manager, owner, timestamps, or audit actor. See [request management](request-management.md),
[workflow engine](workflow-engine.md), and the live `/docs` UI for exact fields.
