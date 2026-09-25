# Business requirements document

## 1. Background

RequestFlow is a portfolio case study for a hypothetical organization whose internal
IT and procurement requests are coordinated across chat, email, and spreadsheets.

## 2. Problem statement

Fragmented records make status, routing, ownership, deadlines, and decision history
difficult to see consistently. Manual consolidation also limits management reporting.

## 3. Objectives

Centralize requests, automate approval routing, expose ownership and status, retain
traceable history, calculate SLA state, and provide defined management analytics.
These are project objectives, not measured claims of improvement.

## 4. Stakeholders

Employee, Manager, Finance, IT / Procurement, and Administrator / Management.
Responsibilities are detailed in [stakeholders.md](stakeholders.md).

## 5. Scope

### In scope

Authentication; manager relationships; request submission, visibility and cancellation;
conditional Manager/Finance approval; Procurement ownership and completion; audit
history; SLA calculation; Admin analytics; responsive web UI; REST API; migrations;
demo data; and automated regression tests.

### Out of scope

Registration, password reset, notifications, escalation, inventory, purchase orders,
payments, SSO, multi-tenancy, AI, predictive analytics, and external-system integration.

## 6. Business rules

The normative rules are centralized in [business-rules.md](business-rules.md), including
the Rp5,000,000 Finance threshold, cancellation window, ownership, state transitions,
deadline calculation, and SLA boundaries.

## 7. Functional requirements

| ID | Requirement | Implementation evidence |
| --- | --- | --- |
| FR-01 | The system shall allow authenticated users with an active manager to submit an internal request. | `POST /requests`; Create Request page |
| FR-02 | The system shall route a submitted request to the requester's assigned Manager. | Manager approval row and pending queue |
| FR-03 | Requests costing at least Rp5,000,000 shall require Finance approval. | Central threshold rule and boundary tests |
| FR-04 | An assigned Manager shall approve or reject a pending request; rejection requires a reason. | Manager decision endpoint and queue |
| FR-05 | Finance shall approve or reject requests routed to Finance; rejection requires a reason. | Finance decision endpoint and queue |
| FR-06 | The requester shall cancel their own request only before the Manager decides. | Cancellation endpoint and allowed-action response |
| FR-07 | Approved requests shall be available to Procurement for fulfillment. | Procurement queue |
| FR-08 | Procurement shall move a request from Approved to Processing and the assigned owner from Processing to Completed. | Start/complete endpoints with row locking |
| FR-09 | The system shall record meaningful workflow actions in chronological audit history. | Audit service and `GET /requests/{id}/audit` |
| FR-10 | The system shall calculate the current or completed SLA state from timestamps. | SLA service and badges |
| FR-11 | Admin shall view global requests and operational analytics without a workflow override. | Admin visibility and `GET /analytics/summary` |
| FR-12 | Each role shall see only the requests and actions authorized by backend policy. | Role and object-level tests |

## 8. Non-functional requirements

| ID | Requirement | Implemented evidence |
| --- | --- | --- |
| NFR-01 | Passwords must use a purpose-built password hash. | Argon2id via pwdlib |
| NFR-02 | Authentication and authorization must be enforced in the backend. | Validated JWT plus database role/object checks |
| NFR-03 | Workflow mutations and related audit events must be transactionally consistent. | Service transaction boundaries and rollback tests |
| NFR-04 | Concurrent decisions must preserve one valid state. | Row locks, constraints, concurrency tests |
| NFR-05 | Important actions must remain auditable to ordinary application/database roles. | Read-only API and PostgreSQL mutation protections |
| NFR-06 | The interface should support 1440, 1280, 768, and 390-pixel browser widths. | Browser regression suite |
| NFR-07 | Secrets and deployment endpoints must be environment-configured. | Pydantic settings and Vite build environment |
| NFR-08 | Database changes must use versioned migrations. | Alembic revisions 0001–0003; no `create_all` startup |
| NFR-09 | API failures must avoid exposing submitted secrets or internal exceptions. | Sanitized validation and generic server errors |

## 9. Success criteria

- Both low- and high-cost lifecycle scenarios complete through valid roles.
- Rejection, cancellation, ownership, and invalid transitions behave as documented.
- Role/object access is enforced through direct API calls.
- Audit and SLA information matches workflow timestamps.
- Admin measures match their written definitions.
- Automated backend, frontend, migration, and browser checks pass.
- A public demo can be deployed with synthetic data and no committed secrets.

These criteria validate the implementation; they do not establish real business ROI.

## 10. Assumptions

- Each submitting user has at most one assigned manager.
- One organization, currency context (Indonesian Rupiah), and Jakarta reporting timezone apply.
- Finance operates a shared queue; the first valid decision records its actor.
- Calendar-day deadlines are sufficient for this scenario; holidays/business hours are absent.
- Demo users and data are synthetic.

## 11. Out of scope

The product scope is frozen. Future considerations are listed in the README and do
not represent delivered requirements.
