# Final verification

Verification date: 25 September 2026 (Asia/Jakarta).

## Local

| Check | Result |
| --- | --- |
| Backend | **116 passed**, one existing Starlette/HTTPX TestClient deprecation warning |
| Frontend production build | Passed; 621 modules transformed |
| Frontend lint | Passed with no reported issues |
| Alembic drift | No new upgrade operations detected |
| Schema | Revision 0003; no Phase 11/12 schema change |
| Demo user seed | 5 accounts ready; existing passwords/status preserved |
| Analytics seed | 0 added; existing fixtures preserved |
| Portfolio screenshots | 8 synthetic-data views generated and visually reviewed |
| Browser regression | **5 groups passed**, 55.2 seconds; no unexpected runtime errors |

The browser run covers both critical low/high-cost lifecycles, rejection, cancellation,
all authenticated screens at four widths, error/empty/loading states, and session races.
The production Docker stage installs runtime dependencies only; Compose selects the
development stage for pytest. Railway-compatible database/CORS aliases have a focused
test and are included in the 116-test result.

## Hosted

| Check | Status |
| --- | --- |
| Frontend | [https://requestflow-one.vercel.app](https://requestflow-one.vercel.app) — Vercel production deployment Ready |
| Backend | [https://requestflow-api-production.up.railway.app](https://requestflow-api-production.up.railway.app) — Railway deployment Success |
| Interactive API docs | [https://requestflow-api-production.up.railway.app/docs](https://requestflow-api-production.up.railway.app/docs) — HTTP 200 |
| Health and database readiness | `/api/health` and `/api/health/ready` both HTTP 200 |
| Production migration | Production startup runs `alembic upgrade head`; schema-backed readiness and seed completed |
| Demo initialization | 5 accounts and 30 synthetic analytics records added; one-time flag removed afterward |
| Demo authentication | Employee login returned the expected role and a bearer token |
| Scenario A | Low-cost request passed Employee → Manager → Procurement → Completed |
| Scenario B | High-cost request passed Employee → Manager → Finance → Procurement → Completed |
| Scenario C | Admin dashboard rendered against hosted analytics data |
| Full hosted browser suite | **5 groups passed in 1.8 minutes** against the public URLs |
| Responsive / sessions | 1440, 1280, 768, and 390 px, deep links, refresh, logout, expiry, and cross-tab logout passed |
| Browser/runtime | HTTPS throughout; no mixed-content or unexpected console errors reported |

The hosted browser suite also exercised rejection, cancellation, audit ordering,
role-specific pages, confirmation handling, validation, loading/empty/recovery states,
and stale-session races. It added clearly labeled synthetic regression requests to the
public demo database; it did not delete existing records.

## Security sanity

- Real local `.env` files, platform metadata, build/test artifacts, logs, caches, and
  dependencies are ignored.
- Repository candidate files were checked for common token/private-key/database-file
  patterns without printing secret values. Only the documented PostgreSQL example and
  its deployment test matched; no private-key/token pattern or local database file matched.
- Production secrets are runtime/build environment values; none are embedded in the SPA.
- The live bundle and `/.env` response contain no `JWT_SECRET`, `DATABASE_URL`, or
  `POSTGRES_PASSWORD` markers.
- The exact Vercel production origin succeeds in CORS preflight; an unapproved origin
  is rejected with HTTP 400.
- Unauthenticated request data returns HTTP 401, unknown-route responses expose no
  stack markers, and the hosted multi-role suite preserves RBAC boundaries.
- Railway reports a private database service host and no public PostgreSQL TCP proxy.
- The documented demo password is intentionally public and must be used only for
  synthetic accounts.

## Known limitations

JWT localStorage exposure, no token revocation, no login throttling, no independent
security audit, database-owner access, shared demo credentials, no notification or
escalation, calendar-day SLA, and a development-oriented local Compose environment.

## Publication status

The source, documentation, tests, screenshots, deployment configuration, and public
demo are ready for a portfolio. Git history is initialized with meaningful commits and
publication files are clean. No Git remote was supplied or configured, so this report
does not claim a public GitHub repository URL; the repository is ready to push without
history rewriting when the owner chooses its GitHub location.
