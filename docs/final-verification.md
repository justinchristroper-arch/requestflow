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

Hosted verification is pending because this machine has no authenticated Railway or
Vercel CLI session and the repository has no Git remote. No live URL is claimed.

| Check | Status |
| --- | --- |
| Frontend URL | Pending account-backed Vercel deployment |
| Backend URL / health / readiness | Pending Railway deployment |
| Production migration and seed | Pending Railway project/database |
| Demo authentication and scenarios A/B/C | Pending hosted URLs |
| Protected-route refresh, mobile, console, CORS, HTTPS | Pending hosted URLs |

Deployment files, variables, release order, migrations, explicit idempotent seeds,
SPA routing, security headers, and verification steps are ready in
[deployment.md](deployment.md). This report must be updated with actual URLs and
observations after authentication and deployment; placeholders must not be published
as successful results.

## Security sanity

- Real local `.env` files, platform metadata, build/test artifacts, logs, caches, and
  dependencies are ignored.
- Repository candidate files were checked for common token/private-key/database-file
  patterns without printing secret values. Only the documented PostgreSQL example and
  its deployment test matched; no private-key/token pattern or local database file matched.
- Production secrets are runtime/build environment values; none are embedded in the SPA.
- Exact CORS origins, protected APIs, role/object authorization, generic server errors,
  and audit protections are covered by automated tests.
- The documented demo password is intentionally public and must be used only for
  synthetic accounts.

## Known limitations

JWT localStorage exposure, no token revocation, no login throttling, no independent
security audit, database-owner access, shared demo credentials, no notification or
escalation, calendar-day SLA, and a development-oriented local Compose environment.

## Publication status

The source, documentation, tests, screenshots, and deployment configuration are ready
for GitHub review. Public-demo readiness remains conditional on deploying both hosts,
running the hosted scenarios, recording real URLs, and repeating the public security
sanity checks.
