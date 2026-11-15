# RequestFlow Business Analyst Evidence Pack

> Portfolio simulation only. This pack organizes the analysis evidence behind RequestFlow. It does not claim a real-company rollout, measured ROI, or production UAT.

## 1. Business problem

RequestFlow models a hypothetical organization handling internal IT and procurement requests through chat, email, and spreadsheets. The assumed process creates fragmented records, unclear status and ownership, inconsistent cost-based routing, manual follow-up, weak auditability, late SLA visibility, and manual management reporting.

### Business objective

Create one request record, apply consistent routing rules, expose status and ownership, preserve decision history, calculate SLA state, and provide defined operational analytics.

## 2. Stakeholders and needs

| Stakeholder | Primary need | Responsibility in the process |
| --- | --- | --- |
| Employee | Submit and track a request clearly | Provide complete details; cancel only while eligible |
| Manager | Decide direct-report requests | Approve or reject assigned requests |
| Finance | Review higher-cost requests consistently | Decide requests routed at or above the threshold |
| IT / Procurement | Fulfill approved work with clear ownership | Take ownership, process, and complete requests |
| Administrator / Management | See workload, SLA, and outcomes | Review global data and analytics without bypassing workflow controls |

## 3. AS-IS process

Assumed manual flow:

```text
Employee identifies need
  -> chat/email to Manager
  -> Manager decides manually
  -> details forwarded
  -> Finance review considered manually
  -> IT / Procurement receives request
  -> work performed
  -> completion communicated manually

Requester repeatedly follows up for status.
```

### Main AS-IS pain points

- No single source of truth for request state.
- Approval and rejection history is difficult to reconstruct.
- Employees depend on manual follow-up.
- Handoffs can omit context or duplicate records.
- Finance routing can depend on memory.
- Deadline risk is not calculated consistently.
- Management reporting requires manual reconciliation.

## 4. TO-BE process

Implemented workflow:

```text
Employee submits
  -> Pending Manager Approval
     -> Reject -> Rejected
     -> Cancel before decision -> Cancelled
     -> Approve
        -> Cost >= Rp5,000,000?
           -> Yes -> Pending Finance Approval
                     -> Reject -> Rejected
                     -> Approve -> Approved
           -> No  -> Approved
  -> Procurement takes ownership
  -> Processing
  -> Assigned owner completes
  -> Completed
```

### Process redesign decisions

- The authenticated user becomes the requester automatically.
- The request is routed to the requester's active assigned manager.
- The exact cost threshold determines whether Finance is required.
- Procurement must explicitly take ownership before completion.
- Workflow and audit events are committed together.
- SLA is derived from timestamps using centralized rules.
- Admin gets global visibility but no workflow override.

## 5. Requirements traceability

The mini-BRD contains 12 functional and 9 non-functional requirements. Representative requirements are below.

| Requirement | Business purpose | Acceptance evidence |
| --- | --- | --- |
| FR-01 - authenticated user with active manager can submit | Establish a controlled intake | Request is created with requester, manager, request number, status, and due date assigned |
| FR-03 - cost >= Rp5,000,000 requires Finance | Apply consistent financial control | Rp4,999,999 skips Finance; Rp5,000,000 enters Finance |
| FR-04 - assigned Manager can approve/reject | Keep decision ownership explicit | Unrelated requests cannot be decided; rejection requires a reason |
| FR-06 - requester can cancel only before Manager decision | Prevent invalid late cancellation | Cancellation is available only in Pending Manager Approval |
| FR-08 - Procurement starts Approved and owner completes Processing | Make fulfillment ownership visible | One operator becomes owner; non-owner completion is blocked |
| FR-09 - meaningful workflow actions are recorded | Preserve traceability | Creation, decisions, routing, processing, completion appear chronologically |
| FR-10 - SLA state is calculated from timestamps | Expose deadline risk consistently | Active and completed states match centralized time boundaries |
| FR-11 - Admin sees global analytics without override | Separate monitoring from operational authority | Admin can read analytics but cannot perform business transitions |
| FR-12 - backend enforces role/object access | Prevent UI-only authorization | Direct API calls still respect role and object visibility |

## 6. User stories and acceptance criteria

### US-03 - Manager decision

**As a Manager, I want a queue of my direct reports' pending requests so that I can approve or reject them.**

Acceptance criteria:
- Unrelated requests cannot be decided.
- Rejection requires a reason.
- Approval sends high-cost requests to Finance.
- Approval sends lower-cost requests directly to Approved.

### US-05 - Procurement ownership

**As a Procurement operator, I want to claim an Approved request so that fulfillment responsibility is clear.**

Acceptance criteria:
- Only an Approved request can be started.
- One competing operator becomes owner.
- Starting records actor, time, note, status, and audit event atomically.

## 7. Business rules

Key rules:
- **Finance threshold:** cost at or above Rp5,000,000 requires Finance; lower cost skips Finance.
- **Rejection reason:** Manager and Finance rejection require a non-blank reason.
- **Cancellation:** requester may cancel only before Manager decision.
- **Processing entry:** only Approved may enter Processing.
- **Procurement ownership:** the operator who starts becomes the owner.
- **Completion:** only the assigned owner may complete.
- **Terminal states:** Completed, Rejected, and Cancelled cannot continue.
- **SLA deadlines:** High = 1 calendar day, Medium = 3, Low = 5.
- **Due Soon:** exactly 24 hours remaining through the exact deadline.
- **Breached:** first instant after the deadline.
- **Completion timing:** at or before deadline = Completed On Time; later = Completed Late.

## 8. KPI and SLA definitions

Admin reporting includes:
- Total Requests
- Pending Approvals
- Processing
- Completed
- Rejected
- SLA Compliance
- Average Resolution Hours
- Category / Priority / Status / SLA / Monthly charts

**SLA Compliance = Completed On Time / All Completed SLA-applicable Requests x 100%**

**Average Resolution Hours = completed_at - created_at**

Rejected and Cancelled requests are excluded from SLA compliance.

## 9. UAT-style acceptance coverage

A dedicated portfolio acceptance matrix maps business scenarios to requirements and expected outcomes. It is intentionally labeled UAT-style because no real business-user acceptance session was performed.

Key scenarios include:
- low-cost approval path;
- exact Rp5,000,000 Finance boundary;
- high-cost Finance approval/rejection;
- Manager rejection with reason;
- eligible and ineligible cancellation;
- Procurement ownership and competing operator behavior;
- completion by assigned owner only;
- unauthorized object access;
- SLA boundary behavior; and
- Admin analytics visibility without workflow override.

See [UAT-style acceptance matrix](uat-matrix.md).

## 10. Validation evidence

Verified project baseline:
- 116 backend tests passed against PostgreSQL.
- Frontend production build passed.
- Frontend lint passed.
- Five browser regression groups passed.
- Responsive checks covered 1440, 1280, 768, and 390 pixel widths.
- Tests cover exact Finance and SLA boundaries, role/object authorization, rejection/cancellation, ownership, concurrency, rollback, audit protections, analytics formulas, and migrations.

These results validate implementation behavior, not real-world business impact.

## 11. Scope and limitations

In scope: request intake, Manager/Finance approval, cancellation, Procurement ownership/completion, audit history, SLA state, Admin analytics, responsive UI, API, migrations, and automated regression tests.

Out of scope: notifications, escalation, inventory, purchase orders, payments, SSO, multi-tenancy, AI, predictive analytics, and external integrations.

Important evidence boundary:
- no real-company pilot;
- no measured time savings;
- no measured adoption;
- no ROI claim;
- no compliance improvement claim;
- no real business-user UAT.

## 12. What this demonstrates for a Business Analyst role

RequestFlow demonstrates a full analysis chain:

**Business problem -> stakeholder needs -> AS-IS -> pain points -> TO-BE -> business rules -> requirements -> user stories -> acceptance criteria -> KPI/SLA definitions -> validation -> documented limitations**

The implementation is used as evidence that the proposed process and rules can be translated into a working system, while keeping business claims separate from software verification.
