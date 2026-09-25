# Audit trail — Phase 6

Every meaningful workflow transition is recorded in an immutable audit trail for
traceability. Here, immutable means append-only through the application and ordinary
SQL UPDATE, DELETE, and TRUNCATE, which PostgreSQL triggers reject. There are no
API routes to edit/delete events. This is not tamper-proof against database owners
who can disable triggers or alter/drop tables, and is not a compliance certification.

## Model and event vocabulary

AuditLog stores an ID, request foreign key, nullable actor foreign key, constrained
action enum, nullable previous/new status, optional details, and a UTC timestamp.
Request and actor foreign keys restrict deletion. A composite index supports history
ordered by request, timestamp, and ID. IDs resolve ties, including the two events
written during Finance routing. Actor responses expose only ID, name, and email.
Actor identity is linked to User; display names/emails reflect the current profile,
not a historical snapshot. The actor ID and event data remain unchanged.

| Action | Meaning |
| --- | --- |
| REQUEST_CREATED | Submission and initial pending Manager state |
| REQUEST_CANCELLED | Requester cancelled before review |
| MANAGER_APPROVED / MANAGER_REJECTED | Assigned Manager decision |
| FINANCE_APPROVAL_REQUIRED | System explanation of the cost threshold rule |
| FINANCE_APPROVED / FINANCE_REJECTED | Finance decision |
| PROCESSING_STARTED | Procurement took ownership and started |
| REQUEST_COMPLETED | Assigned operator completed fulfillment |
| HISTORY_BASELINE | Migration enabled auditing for an existing request |

Actor events carry previous/new status. The Finance routing event has actor=null,
no duplicated status transition, and factual cost/threshold details. Exactly
Rp5,000,000 requires Finance. Approval comments, rejection reasons, and operational
notes appear as plain-text details. Failed attempts do not become workflow events.
No redundant generic STATUS_CHANGED event is emitted.

## Atomic writes

`services/audit.py` centralizes event creation and flushes without committing.
Submission and the existing centralized workflow service call it using their own
Session. Routes commit after successful mutation and serialization. Session failure
rolls back status, approvals, ownership, timestamps, and all related events together.
The same request lock serializes competing approvals and fulfillment actions.
Tests inject failures after event insertion, including the second system-routing
event, and verify that no partial workflow or audit changes survive rollback.

## Visibility and timeline

`GET /requests/{id}/audit` reuses request visibility: own requests for Employees,
own/current direct reports for Managers, routed requests for Finance, fulfillment
requests for Procurement, and all requests for Admin. Inactive or unauthenticated
users cannot read history. Invisible requests return 404.

The detail timeline fetches this endpoint, displays oldest first in Jakarta time,
and labels system events as System. Shared frontend action labels avoid duplicating
raw enum mappings. The timeline includes loading/error/retry and empty states,
wraps long notes on mobile, and refreshes after a successful workflow action.

## Legacy history and limits

Revision 0003 adds one factual HISTORY_BASELINE per pre-existing request, stating
its state at migration time. Earlier actions were not logged; the migration does
not invent their actors or timestamps. Existing approval records remain visible.
New requests have complete submission-to-terminal-state event histories.

Triggers protect stored events from ordinary edits/deletes/truncation. They do not
force arbitrary external SQL request updates to produce events; all supported
mutations must go through the workflow services. The local development database
role owns the schema. Deployment hardening and separation of migration/runtime
privileges remain future work. No hash-chain, external ledger, or certification
is claimed.

Reference: [PostgreSQL trigger semantics](https://www.postgresql.org/docs/17/sql-createtrigger.html).
