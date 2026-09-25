# User stories

## Employee

**US-01 — Submit a request.** As an employee, I want to describe an IT or procurement
need so that it enters a documented approval process.

- Required fields are validated and cost is non-negative.
- The backend assigns requester, manager, request number, status, and due date.
- The new request begins in Pending Manager Approval.

**US-02 — Track and cancel.** As an employee, I want to see my request's current
status, SLA, decisions, fulfillment, and history, and cancel it before Manager review.

- Other employees' private requests are not visible by changing an ID.
- Cancellation is unavailable after the Manager decides.

## Manager

**US-03 — Decide assigned requests.** As a manager, I want a queue of my direct
reports' pending requests so that I can approve or reject them.

- Unrelated requests cannot be decided.
- Rejection requires a reason.
- Approval routes high-cost requests to Finance and lower-cost requests to Approved.

## Finance

**US-04 — Review threshold-routed requests.** As Finance, I want a shared queue of
requests requiring financial review so that I can record an approval or rejection.

- Low-cost requests cannot receive a Finance decision.
- Only one concurrent decision succeeds; the deciding user is recorded.

## Procurement

**US-05 — Take ownership.** As a Procurement operator, I want to claim an Approved
request so that responsibility for fulfillment is clear.

- Only one competing operator becomes owner.
- Starting records the actor, time, note, status, and audit event atomically.

**US-06 — Complete owned work.** As the assigned operator, I want to mark Processing
work complete so that the requester and management see its final state and SLA outcome.

- A different operator cannot complete it.
- Completion records the timestamp and audit event in the same transaction.

## Administrator / Management

**US-07 — Review operations.** As an administrator, I want global request visibility
and defined aggregate measures so that I can inspect workload, status, SLA, categories,
priorities, and recent submission volume.

- Non-Admin roles cannot access analytics.
- Admin remains read-only for business workflow actions.
- Empty denominators display an em dash rather than a misleading percentage.
