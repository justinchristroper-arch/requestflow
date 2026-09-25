# SLA monitoring

SLA monitoring makes deadlines visible so operators can identify overdue requests
and prioritize work. It reports stored workflow data; it does not claim a measured
improvement in efficiency or business outcomes.

## Centralized rule

The existing calendar-day deadlines are unchanged: High = 1 day, Medium = 3 days,
Low = 5 days after submission. All stored timestamps are timezone-aware. The service
compares absolute instants; the interface displays dates in Asia/Jakarta.

`app/services/sla.py` owns a shared ordered decision table for both Python response
calculation and SQL classification. The Due Soon window is one constant: 24 hours.
No SLA status is stored in the database, and no migration is needed.

| Request state / condition | SLA state |
| --- | --- |
| Active, more than 24 hours remaining | ON_TRACK |
| Active, 0 through 24 hours remaining, inclusive | DUE_SOON |
| Active, deadline has passed | BREACHED |
| Completed at or before the due timestamp | COMPLETED_ON_TIME |
| Completed after the due timestamp | COMPLETED_LATE |
| Rejected, Cancelled, or reserved Draft | NOT_APPLICABLE |

Active means pending Manager, pending Finance, Approved, or Processing. Exactly
24 hours before the deadline is Due Soon. Exactly at the deadline is still Due Soon;
one microsecond afterward is Breached. Completion exactly at the deadline is on time.
High-priority requests therefore enter Due Soon immediately after submission.
Completed results remain stable as time passes. Rejected and cancelled requests are
not successful completions and never enter the compliance denominator.

Request list/detail/approval/Procurement responses include `sla_status` and
`completed_at`, alongside the existing `due_date`. Frontend badges map backend enum
values to labels; the browser does not recalculate the rule. Detail has a deadline
section and refresh action. Tables stack SLA and workflow status to avoid an extra
column; mobile also shows SLA below the request title. Approval queues show due date.

## Queue and refresh behavior

Procurement orders by SLA urgency (Breached, Due Soon, On Track), then priority
(High, Medium, Low), due date, submission timestamp, and ID. SQL applies this order
before pagination. Existing approval queue order stays oldest first.

SLA is recalculated when the API is read. Open pages are snapshots, not ticking
countdowns: reload or use Refresh SLA status / Refresh queue to obtain current state.
There is no scheduler, persistent breach flag, reminder, escalation, or audit event
for the passage of time. Read-only SLA calculation does not mutate the workflow.

## Compliance

SLA Compliance = Completed On Time ÷ Completed SLA-applicable Requests × 100.
All valid completed requests are applicable because they have a due date and
completion timestamp. Active, Draft, Rejected, and Cancelled requests are excluded.
With zero completed requests, the API returns null and the dashboard shows an em dash,
not a misleading 0% or 100%. API percentages round to two decimals; UI shows one.

Fixed-time tests cover every boundary, timezone equivalents, Python/SQL agreement,
queue ordering, and changes in read-time state without changing stored workflow data.
