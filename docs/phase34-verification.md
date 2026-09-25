# Phases 3 and 4 verification

Completed locally on 25 September 2026. Python 3.12/FastAPI and PostgreSQL 17 run
through Docker Compose. The frontend uses Node 24. Browser scenarios ran in headless
Microsoft Edge via Playwright, using the real API and persisted demo users.

## Commands and results

| Command/check | Result |
| --- | --- |
| `docker compose up -d --build --wait` | Backend and PostgreSQL healthy |
| `docker compose exec backend alembic upgrade head` | Revision 0002 applied, existing users retained |
| `docker compose exec backend alembic current` | 0002 (head) |
| `docker compose exec backend alembic check` | No new upgrade operations detected |
| `docker compose exec backend python -m pytest -q -p no:cacheprovider` | **57 passed**, one pre-existing Starlette/HTTPX warning |
| `npm.cmd --prefix frontend run build` | TypeScript and production build passed |
| `npm.cmd --prefix frontend run lint` | Passed without warnings |

Tests include all prior authentication/health tests. New cases cover creation,
server-owned-field spoofing, money/input validation, all priority due dates, visibility,
manager assignment, pagination, cancellation, threshold boundary at Rp5,000,000,
rejection reasons, Finance order, forbidden roles, duplicate decisions, reserved and
terminal states, duplicate-stage constraints, and rollback on a simulated Finance
insert failure.

Migration tests exercise a fresh database schema from zero, downgrade from 0002
to 0001 while retaining users, full downgrade to base, and re-upgrade. Temporary
schemas are isolated from public demo data. The concurrency test uses independent
connections: four simultaneous submissions receive distinct numbers; two competing
Manager decisions and two competing Finance decisions each yield one success and
one 409, with exactly one row per approval stage.

## Real browser scenarios

| Scenario | Verified result | Persisted request |
| --- | --- | --- |
| A: Employee submits Rp2,000,000; Manager approves | Approved; Finance Not required | REQ-2026-0001 |
| B: Employee submits Rp10,000,000; Manager then Finance approve | Pending Finance between decisions, then Approved; both named decisions visible | REQ-2026-0002 |
| C: Manager rejects with reason | Employee sees Rejected and the exact reason | REQ-2026-0003 |
| D: Employee cancels before Manager review | Cancelled, removed from queue; stale Manager approval returns 409 | REQ-2026-0004 |

Additional checks passed:

- Role-aware navigation for Employee, Manager, Finance, and Admin.
- Browser refresh displays updated request states while retaining authentication.
- An employee's direct HTTP attempt to approve returns 403.
- Admin can view all requests but receives no approval actions.
- Empty Manager queue after all eligible decisions; no cancelled items remain.
- A simulated delayed 503 displays loading then an error; retry recovers the list.
- Detail and list at 390px width stay within the viewport (table scrolls internally).
- Window refocus preserves an unsaved request form while revalidating identity.
- A later detail refresh does not repeat the one-time submission message.
- No runtime or unexpected console errors. Deliberately tested 403/409 and injected
  503 responses were expected and excluded from unexpected-error reporting.

Screenshots and machine-readable browser results are in ignored `artifacts/`:
`phase34-low-value.png`, `phase34-high-value.png`, `phase34-detail-mobile.png`,
`phase34-list-mobile.png`, and `phase34-browser-results.json`.
The local browser verification scripts also remain there; they use this machine's
bundled Playwright installation and Edge executable, not a new application dependency.

## Files added or changed

Added backend:

- `app/models/request.py`, `app/models/approval.py`
- `app/schemas/request.py`, `app/api/requests.py`
- `app/services/requests.py`, `workflow.py`, `approvals.py`, `rules.py`
- `migrations/versions/0002_requests_approvals.py`
- `tests/test_requests.py`, `tests/test_concurrency.py`

Changed backend: `app/models/__init__.py`, `app/main.py`, and `tests/test_migrations.py`.

Added frontend:

- `src/pages/Dashboard.tsx`, `RequestList.tsx`, `CreateRequest.tsx`,
  `RequestDetail.tsx`, `ApprovalQueue.tsx`
- `src/requests/types.ts`, `display.ts`, `components.tsx`
- `src/lib/useApi.ts`, `useResource.ts`

Changed frontend: `src/App.tsx`, `Workspace.tsx`, `index.css`, `lib/api.ts`,
`auth/context.ts`, `auth/AuthProvider.tsx`, and `pages/Login.tsx`.
The shell styling and authentication architecture were retained. The overview
content moved to Dashboard so the same shell could wrap the new pages.

Documentation: updated root README and docs index/authentication notes; added
`request-management.md`, `workflow-engine.md`, and this verification record.

## Remaining limits

The existing Starlette warning concerns deprecated HTTPX TestClient integration;
the suite passes. Public-deployment hardening from Phase 2 (rate limiting, token
storage/revocation review, HTTPS, dependency review) still applies.

The top-level demo manager has no assigned manager and cannot submit until configured.
Manager reassignment, request editing/resubmission, gapless numbering, and network-level
submission idempotency are not provided. These choices are documented in the model
and workflow notes. No Phase 5 processing or Phase 6 full audit trail was added.
