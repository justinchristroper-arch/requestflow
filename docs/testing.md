# Testing RequestFlow

Run from the repository root with the local PostgreSQL/API stack available:

```powershell
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend run lint
docker compose exec backend python -m pytest -q -p no:cacheprovider
docker compose exec backend alembic check
```

Rebuild the backend image after editing tests or migrations; only application code is
bind-mounted. Backend tests use real PostgreSQL in temporary schemas, with rollback
between cases. Migration tests exercise fresh upgrade, downgrade, and re-upgrade in
an isolated schema. They do not downgrade the working demo database.

The final local run passed all **116 backend tests**, including the original 106 and
the Phase 9/10 hardening suite.
Coverage includes authentication, inactive identities, role and object visibility,
spoofed fields, invalid input, exact decimal Finance thresholds, SLA boundaries,
terminal states, ownership, transaction rollback, audit protection, seeds, and migrations.
Concurrent tests cover unique request numbers, repeated decisions, opposing Manager
decisions, competing Procurement operators, and repeated completion. Sequence gaps
after rollback are expected and do not indicate missing request data.

## Authorization matrix

All permissions below are enforced by the API, independently of navigation visibility.

| Role | Read access | Create / cancel | Decisions | Fulfillment | Global analytics |
| --- | --- | --- | --- | --- | --- |
| Employee | Own requests and audit | Create with active manager; cancel eligible own request | No | No | No |
| Manager | Own and direct reports | Create with active manager; cancel eligible own request | Assigned pending Manager stage | No | No |
| Finance | Requests routed to Finance, including history | No | Pending Finance stage only | No | No |
| Procurement | Approved, Processing, Completed | No | No | Start Approved; complete only own Processing | No |
| Admin | All requests and audit | No | No | No | Yes |

Invisible request IDs return 404 for detail, audit, cancellation, both decision
endpoints, start, and completion. A visible object does not grant permission to act:
wrong business roles return 403; stale or incompatible workflow states return 409.
Tests also cover invalid JWT issuer/audience, future issue time, malformed subject,
expired tokens, inactive users, and denied CORS preflights.

Deployment configuration is also tested: Railway-style `DATABASE_URL` selects the
psycopg driver, `CORS_ALLOWED_ORIGINS` overrides local origins, and production mode is
parsed without changing the local `POSTGRES_*` / `CORS_ORIGINS` path.

## Browser regression

Start Vite and the seeded local API first. Use synthetic demo accounts only.

```powershell
npm.cmd --prefix frontend run test:e2e
```

Windows uses installed Microsoft Edge. On other systems install Playwright Chromium
from `frontend` with `npx playwright install chromium`. `PLAYWRIGHT_CHANNEL` can
override the browser and `E2E_BASE_URL` can override the default
`http://127.0.0.1:5173`. The frontend's API configuration must point to the matching
demo backend. Set `E2E_API_URL` to override direct test API calls (default
`http://localhost:8000`) and `E2E_DEMO_PASSWORD` if demo passwords were changed.
The suite does not start or stop application servers.

Five test groups cover:

1. Low/high cost approval through completion, Manager/Finance rejection, cancellation,
   audit ordering, literal HTML text, confirmation cancellation, and double clicks.
2. All authenticated screens at 1440, 1280, 768, and 390 pixels; role restrictions,
   five SLA states, chart rendering, and mobile title width.
3. Form validation and focus, draft preservation on window focus, loading, empty state,
   error redaction, and retry recovery.
4. A delayed old-session 401 after a new login.
5. Cross-tab logout and malformed/expired token cleanup.

The full suite creates **five clearly labeled `[Regression 9/10]` requests** and
retains them for inspection. Do not run it against real business data. Repeated
runs add another five; no automatic data deletion is performed. Responsive-only
verification can be repeated without adding requests:

```powershell
npm.cmd --prefix frontend run test:e2e -- --grep 'four responsive widths'
```

Use the existing analytics demo seed for populated charts. Active SLA fixtures age;
when a state is absent, the browser test substitutes a controlled response for that
display check. Backend tests establish actual SLA calculations and exact boundaries.
Network failure/empty/session-race checks also use controlled responses. Lifecycle
tests use the real API and database.

Verification screenshots and failure images go under ignored `artifacts/phase910-tests`.
Traces are disabled because they may contain credentials or bearer tokens. Treat
screenshots as local evidence; inspect before sharing. No unexpected browser runtime
errors were reported in the verified lifecycle and responsive runs.

## Performance checks and limits

The query-count regression compares one and nine request rows after expiring ORM
state: list queries remain constant and at most five SELECTs, audit at most four,
analytics at most two, including authentication. Existing eager loading and SQL
aggregation remain in place. This guards the measured paths against obvious N+1
regressions; it is not a production load test. Analytics remains a separate lazy
frontend bundle. React effects retain cleanup and fetch cancellation; mutations
have synchronous duplicate-submit guards.

One existing Starlette/HTTPX TestClient deprecation warning remains. The browser
runner may also report conflicting NO_COLOR/FORCE_COLOR environment settings;
that affects console coloring, not application behavior.
