# Management dashboard and analytics

The dashboard converts request data into workload, completion, demand, and timeliness
information. It helps a reviewer identify a backlog, high-demand categories, and
requests needing attention. It does not establish causal business improvements,
industry benchmarks, or compliance certifications.

## Scope and authorization

`GET /analytics/summary` is Admin-only. The backend checks an active authenticated
user's current database role. All other roles receive 403, and unauthenticated or
inactive users receive 401. No optional team-level analytics were added.

Admin's Dashboard is the management view. Other roles retain the operational overview
and their authorized request screens. Charts are loaded lazily for Admin so ordinary
request users do not download the chart bundle. Recharts provides responsive SVG
charts and tooltips; each chart also has exact counts in an expandable text list.

## KPI definitions (all time)

| Metric | Definition |
| --- | --- |
| Total Requests | Every stored request, including Draft, Rejected, Cancelled |
| Pending Approval | PENDING_MANAGER_APPROVAL + PENDING_FINANCE_APPROVAL |
| Processing | PROCESSING only; Approved is not included |
| Completed | COMPLETED only |
| Rejected | REJECTED only |
| Completed On Time | Completed with completed_at <= due_date |
| SLA Compliance % | Completed On Time / Completed × 100 |
| Average Resolution Hours | AVG(completed_at - created_at) in hours, completed only |

No completed requests means null compliance and null average, displayed as an em dash.
Rejected/cancelled requests remain visible in total and status counts, but are excluded
from both completion-based metrics. Average resolution measures the entire lifecycle,
including approval and waiting time, not just Procurement handling time. The API
rounds the average to two decimals; the UI shows one decimal hour.

## Query design

The service uses SQL COUNT/FILTER, GROUP BY, AVG, and timestamp arithmetic. Category,
priority, workflow status, and SLA breakdowns are SQL grouped aggregates. Only the
small aggregate results are returned to Python; it does not load all request rows.

One SQL statement with scalar aggregate subqueries provides a consistent PostgreSQL
statement snapshot across KPIs and charts. A single supplied `as_of` instant drives
SQL SLA classification. Python fills missing enum buckets/months with zeros and
calculates the documented percentage from aggregate counts. `as_of` is returned
for the snapshot label. There is no cache or permanently stored SLA flag.

Monthly trend counts submissions by their creation month in **Asia/Jakarta**, for
the current calendar month and five preceding months. Empty months are zero-filled,
including across year boundaries. The current month is partial. KPI cards and the
other four breakdowns remain all-time, so totals can exceed the six-month trend.
No date filtering or complex BI controls were added.

The screen has a refresh action, loading/error/retry behavior, and a no-data state.
Charts show monthly volume, category, priority, SLA status, and workflow status.
Empty charts show a message rather than misleading geometry or divide-by-zero output.

## Explicit analytics demo seed

After normal migrations, run:

```powershell
docker compose exec backend python -m app.services.seed_analytics --demo
```

For a reproducible reference time:

```powershell
docker compose exec backend python -m app.services.seed_analytics --demo --as-of 2026-09-25T00:00:00+00:00
```

It adds 30 requests labeled `[DEMO Analytics v1 NN]`, across five categories, three
priorities, low/high values, six months, pending approval, Approved, Processing,
Completed, Rejected, and Cancelled states. Twelve are completed: six on time and six
late. There are six pending approvals, three approved, three processing, three
rejected, and three cancelled. The seed-only completion rate is 50%; the dashboard
includes existing requests too, so its percentage can differ.

The same reference time produces the same fixture schedule. The default reference is
current UTC rounded down to the hour. An advisory transaction lock serializes seed
runs; existing labeled fixtures are skipped, including if a later reference is given.
Existing user-created requests, passwords, and active settings are not overwritten.
Title collisions with unrelated content stop the transaction. Rerunning does not
refresh deadlines: active demo records naturally become overdue as time passes.

The seed reuses submission and workflow services with explicitly supplied historical
timestamps, building real approval, ownership, and audit records in one transaction.
HTTP clients cannot supply those internal service timestamps. No audit rows are edited.
Seeded histories are synthetic and clearly labeled. No hundreds of filler rows,
new seed table, external integration, or schema migration is needed.

## Validation and remaining scope

Tests check known counts, null handling, percentage denominator, resolution hours,
groupings, Jakarta month boundaries, zero-filled months, role restrictions, Python/SQL
SLA equivalence, and additive/idempotent seed behavior. Browser checks compare KPI
cards to independently aggregated request responses and verify mobile and empty/error
states. See phase78-verification.md for final results.

No notifications, n8n, escalation, AI, inventory, purchasing, external integrations,
or multi-tenancy are implemented.

Library reference: [Recharts installation](https://github.com/recharts/recharts/blob/main/README.md).
