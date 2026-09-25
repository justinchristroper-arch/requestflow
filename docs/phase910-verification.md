# Phase 9/10 verification

Verified locally on 25 September 2026. Scope: existing UX polish and application
regression/security hardening. No major features, architecture replacement, Phase 11
documentation package, or Phase 12 deployment was introduced.

## Results

| Check | Result |
| --- | --- |
| Original backend baseline | 106 passed |
| Expanded PostgreSQL suite | 115 passed, 50.42 seconds |
| Frontend TypeScript + production build | Passed, including browser-test type checking |
| Frontend lint | Passed |
| Full browser suite | 5 groups passed, 57.6 seconds |
| Responsive rerun after mobile header fix | 1 group passed, 36.3 seconds |
| Browser runtime errors | No unexpected errors in lifecycle/responsive verification |
| Alembic drift | No new upgrade operations detected |
| Migration sanity | Fresh upgrade/downgrade/re-upgrade covered in isolated-schema suite |
| Schema version | 0003; no new migration needed |
| Analytics seed rerun | 0 added; existing records retained |

The full browser run created only five labeled regression requests: low-cost and
high-cost completions, Manager rejection, Finance rejection, and cancellation.
The focused responsive rerun added none. Test-generated records remain local.
Existing demo data was preserved; active SLA dates naturally age.

## UX review

Login copy now describes the complete workflow and duplicate login is guarded.
The authenticated shell retains visible identity/role/logout, active navigation,
a collapsible mobile menu, and keyboard skip-to-content. Overview provides relevant
role tasks instead of development health diagnostics.

My Requests, both approval queues, Procurement, and analytics use consistent page
headings, useful empty states, and contextual loading/error recovery. Forms associate
labels and error descriptions, show required fields and exact Rupiah previews, focus
the first invalid field, and preserve drafts when window focus changes.

Request detail emphasizes status/SLA and actionable controls. Approval stages include
Procurement and remain understandable through text, independent of color. One native
confirmation dialog protects each mutation, supports Escape before submission, starts
focus on Go back, and restores focus. Rejection still requires a reason. Audit history
visually distinguishes automatic events from named human actions.

All eight authenticated screens were checked at 1440, 1280, 768, and 390 pixels.
Tables scroll within their containers; charts render at all four widths. Visual
inspection caught a narrow mobile detail title despite no page overflow: badges now
stack beneath the title on mobile, and a width assertion prevents that regression.
Build/lint and the responsive group were rerun after this correction.

Local verification images are in ignored `artifacts/phase910-tests`. Strong future
portfolio captures are the Admin dashboard, a completed high-value detail/audit,
My Requests, and populated approval/Procurement queues. Choose readable synthetic
records instead of test payloads for public portfolio screenshots.

## Authorization and hardening

See [the role matrix and test setup](testing.md). Coverage verifies every request-ID
endpoint against unrelated employees/managers, visible-object cross-role attempts,
requester/status spoofing, Finance routing, Procurement ownership, terminal states,
malformed/expired credentials, inactive users, exact money and SLA boundaries,
competing actions, atomic rollback, and ordinary audit mutation protection.

The main frontend issue found was an obsolete-session response race: a delayed 401
could clear a newly signed-in user. Token-identity checks now discard obsolete
results, with a browser regression reproducing the sequence. Error hardening prevents
submitted values appearing in validation responses and internal exceptions appearing
in 500 responses. CORS configuration now rejects wildcard/non-origin values.

No tested object-level bypass or workflow corruption was reproduced. This is not
an independent security audit. LocalStorage JWT exposure, no server-side revocation,
no login throttling, database-owner tampering, and development-oriented hosting remain
documented in [security.md](security.md). No production security certification is claimed.

Query-count checks show no request-list growth from one to nine records; list/audit/
analytics stay within five/four/two SELECTs respectively, including authentication.
The React review checked effect cleanup, obsolete-response handling, submission
guards, semantic labels, keyboard focus, component reuse, and the existing lazy
analytics bundle. No new charting or UI framework was added.

Remaining warnings: existing Starlette/HTTPX TestClient deprecation, and the browser
runner's harmless NO_COLOR/FORCE_COLOR environment warning. Application build/lint
and browser runtime checks showed no outstanding errors.

## Files changed in this batch

The repository is currently untracked, so Git cannot distinguish this batch from
earlier phases. This implementation inventory identifies Phase 9/10 changes:

- Backend: `backend/app/config.py`, `backend/app/main.py`;
  `backend/tests/test_hardening.py` (new), `backend/tests/test_concurrency.py`.
- Authentication: `frontend/src/auth/AuthProvider.tsx`, `frontend/src/auth/context.ts`,
  `frontend/src/lib/useApi.ts`.
- Shared UI: `frontend/src/components/PageHeader.tsx`, `EmptyState.tsx`,
  `ConfirmationDialog.tsx` (new components), plus `frontend/src/requests/components.tsx`,
  `frontend/src/Workspace.tsx`, `frontend/src/requests/AuditTimeline.tsx`,
  and `frontend/src/index.css`.
- Pages: `frontend/src/pages/Login.tsx`, `Overview.tsx`, `CreateRequest.tsx`,
  `RequestList.tsx`, `RequestDetail.tsx`, `ApprovalQueue.tsx`, `ProcurementQueue.tsx`,
  and `ManagementDashboard.tsx`.
- Browser quality gates: `frontend/e2e/regression.spec.ts`, `frontend/playwright.config.ts`,
  `frontend/tsconfig.e2e.json` (new), `frontend/tsconfig.json`, `frontend/package.json`,
  and `frontend/package-lock.json`.
- Documentation: `README.md`, `docs/testing.md`, `docs/security.md`, and this report.

Next: Phase 11 business/technical portfolio documentation; Phase 12 deployment,
environment configuration, HTTPS/origin/header controls, and hosted verification.
