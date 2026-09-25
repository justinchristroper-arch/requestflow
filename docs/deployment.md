# Deployment guide

The intended public-demo topology keeps the existing architecture:

```text
Browser → Vercel static React SPA → Railway FastAPI service → Railway PostgreSQL
```

No production credentials belong in Git. The repository contains examples and
platform configuration only.

## Current public deployment

- Frontend: [https://requestflow-one.vercel.app](https://requestflow-one.vercel.app)
- API: [https://requestflow-api-production.up.railway.app](https://requestflow-api-production.up.railway.app)
- OpenAPI: [https://requestflow-api-production.up.railway.app/docs](https://requestflow-api-production.up.railway.app/docs)

The Railway database is reachable by the API over its private service host. No public
PostgreSQL TCP proxy or public database domain is configured.

## Railway backend and database

1. Create a Railway project and PostgreSQL service.
2. Create a backend service from this repository with root directory `/backend` and
   config path `/backend/railway.json`.
3. Reference PostgreSQL's `DATABASE_URL` in the backend service.
4. Set a generated JWT secret and the final Vercel origin.

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
JWT_SECRET=<generated value of at least 32 random bytes>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ALLOWED_ORIGINS=["https://requestflow-one.vercel.app"]
ENVIRONMENT=production
```

`railway.json` describes a pre-deploy migration, Uvicorn start, and
`/api/health/ready` check. The Railway CLI upload used for the current deployment did
not apply those deploy fields, so the production Docker command is the authoritative
path: `start-production.sh` applies the same idempotent Alembic upgrade before Uvicorn.
The application never creates tables with SQLAlchemy `create_all`.

For the first public-demo deployment, temporarily set `INITIALIZE_DEMO=true`. The
production start script applies migrations and runs these idempotent seed commands:

```text
python -m app.services.seed --demo
python -m app.services.seed_analytics --demo
```

After that deployment succeeds, remove `INITIALIZE_DEMO`. The current deployment used
the flag once to create five demo users and 30 analytics records, then removed it.
Normal restarts therefore migrate and start without seeding. The seeds preserve
existing records, while the explicit toggle keeps initialization intent visible.

Generate a public Railway domain, then verify `/api/health`, `/api/health/ready`, and
optionally `/docs`. Keep the PostgreSQL TCP domain private unless a controlled
administrative connection is required.

## Vercel frontend

Create a Vercel project with root directory `frontend`. Vite's normal commands apply:

```text
Build command: npm run build
Output directory: dist
Install command: npm ci
```

Set this build variable for Production (and Preview when the preview backend permits it):

```text
VITE_API_URL=https://requestflow-api-production.up.railway.app
```

`frontend/vercel.json` rewrites browser routes to `index.html`, so refresh works on
`/login`, `/requests`, and `/requests/{id}`. It also adds static-response security
headers. The backend CORS allowlist must contain the exact final Vercel origin without
a path or trailing slash.

## Release order

1. Provision PostgreSQL and backend variables.
2. Deploy backend; migrate, seed once, and verify readiness.
3. Deploy frontend with the backend URL.
4. Replace backend CORS with the final Vercel production origin and redeploy if needed.
5. Run hosted browser scenarios and public security checks.
6. Add verified URLs to README and `final-verification.md`—never placeholders.

## Hosted verification

Use the same five demo roles and synthetic data. Test low-cost and high-cost
lifecycles, dashboard, refresh/deep links, logout, mobile, CORS, HTTPS, and browser
errors. Confirm the frontend bundle contains the public API URL but no JWT secret,
password configuration, or database URL. The documented demo password is public by design.

Railway's repository config format is currently supported but scheduled for platform
deprecation after 1 December 2026; review Railway's Infrastructure as Code migration
guide before deployments after that date.
