# Phase 2 verification

Verified locally on 24 September 2026 using Node 24, Python 3.12 in Docker,
and PostgreSQL 17. The existing Phase 1 shell was retained.

| Command/check | Result |
| --- | --- |
| `node scripts/setup-env.mjs` | Existing configuration preserved, secret not printed |
| `docker compose up -d --build --wait` | API and PostgreSQL healthy |
| `docker compose exec backend alembic upgrade head` | Users schema at revision 0001 |
| `docker compose exec backend alembic current` | 0001 (head) |
| `docker compose exec backend alembic check` | No new upgrade operations detected |
| `docker compose exec backend python -m app.services.seed --demo` (twice) | Exactly 5 users persisted; employee linked to manager |
| `docker compose exec backend python -m pytest -q -p no:cacheprovider` | 18 passed, 1 existing dependency warning |
| `npm.cmd --prefix frontend run build` | TypeScript and Vite production build passed |
| `npm.cmd --prefix frontend run lint` | Passed without warnings |
| Git ignore check | Local `.env` and `frontend/.env` excluded |

## Backend coverage

- Argon2id hashes are salted; correct passwords succeed and incorrect passwords fail.
- Valid login and `/auth/me` return safe profile data, including manager information.
- Unknown email and incorrect password return the same 401 message.
- Missing/invalid tokens, wrong signatures/algorithms, expired tokens, missing claims,
  and out-of-range subjects are rejected.
- Inactive users cannot sign in or use existing tokens; deleted users are rejected.
- Role dependency denies employees, permits listed manager/admin roles, and reads
  current database roles rather than trusting a token role.
- Seed repeats preserve passwords/active flags and do not duplicate users.
- CORS accepts the configured browser origin and Authorization header.
- A temporary PostgreSQL schema passes fresh upgrade → downgrade → upgrade, including
  enum removal. Development users are not dropped by the migration test.

## Browser verification

- Visiting `/` without a session redirects to `/login`.
- Incorrect password displays `Invalid email or password.`
- Employee login opens `/` with `Jamie Employee` and `EMPLOYEE` visible.
- Reload retains authentication after `/auth/me` succeeds.
- Logout removes the persisted token and returns to login; revisiting `/` stays protected.
- A malformed stored token is removed and displays the session-expired/invalid notice.
- A token with a future expiry but invalid signature is rejected by the API, removed,
  and returns the browser to login.
- Desktop and 390 × 844 mobile login render without a Vite error overlay or horizontal overflow.
- No browser runtime or console errors; only expected Vite and React development messages.

Local screenshots are in ignored `artifacts/`: `phase2-login.png`,
`phase2-login-mobile.png`, and `phase2-workspace.png`.

## Known warning and limits

Starlette reports that HTTPX integration in TestClient is deprecated. This warning
predates Phase 2 and does not fail tests. Upgrade the test-client stack together
later rather than suppressing it.

This phase does not claim production readiness. localStorage exposure, lack of
server-side token revocation and login throttling, and deployment hardening are
documented in [authentication design](authentication.md).
