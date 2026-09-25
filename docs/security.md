# Security boundaries and portfolio limitations

RequestFlow is a local portfolio demonstration, not independently audited enterprise
software. Use synthetic data with the publicly documented demo credentials.

## Implemented protections

- Passwords are hashed with Argon2id; API profiles exclude password hashes.
- JWT validation fixes the supported algorithm and verifies signature, expiry,
  issuer, audience, and subject. Protected calls reload the active user and role
  from PostgreSQL. Client role claims are not authorization.
- Backend role checks and request visibility protect detail, audit, and every
  mutation. Invisible IDs return 404; visible but unauthorized operations return
  403. Admin has read access, not a workflow override.
- Input schemas reject spoofed server-owned fields, invalid enums, blank/oversized
  text, and invalid money. Decimal costs preserve the exact Rp5,000,000 boundary.
- Row locks serialize workflow changes. Status, approval, owner, timestamps, and
  audit events commit together; failures roll back. Database constraints enforce
  stage uniqueness and structural invariants.
- Audit endpoints are read-only. PostgreSQL protections reject ordinary audit
  updates, deletes, and truncation. Database owners can disable protections or
  alter records; this is not tamper-proof storage against privileged operators.
- Secrets come from environment configuration; weak/placeholder signing secrets
  are rejected. Environment files and generated artifacts are Git-ignored.
- CORS accepts explicit environment-configured HTTP(S) origins; wildcard origins,
  credentials in URLs, paths, queries, and fragments are rejected. Supply origins
  without trailing slashes. Cookies/credentialed CORS are disabled. CORS is a
  browser boundary, not protection against direct API clients.

## Phase 9/10 fixes

API responses now send `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`,
and `Referrer-Policy: no-referrer`. Validation responses retain field locations and
messages but omit submitted inputs and internal contexts, avoiding password/input
echoes. Unexpected exceptions are logged server-side and return a generic 500
message without stack traces or database details. Logs still require restricted
access because server diagnostics can contain sensitive operational information.

Frontend requests retain their initiating token identity. Obsolete responses cannot
overwrite current-session data or clear a different user's new session. Login and
workflow controls guard duplicate submissions. Native confirmation dialogs put
initial focus on Go back and support Escape before submission. These UX controls
supplement the API's transaction and authorization checks.

User-entered content remains React text; the lifecycle browser test verifies a
literal HTML payload does not execute. There is no raw HTML rendering requirement.

## Known limitations

- JWTs remain in localStorage, so an injected script could steal them. There is no
  server-side token revocation or refresh-token infrastructure. Logout removes the
  browser token but a copied token remains valid until expiry, unless account
  deactivation or signing-key replacement invalidates access.
- There is no login throttling, password reset, registration, MFA, or SSO.
- The application is not independently security audited; passing regression tests
  is evidence for the tested boundaries, not proof that every vulnerability is absent.
- The local Compose setup and database-owner privileges are development choices.
  Demo credentials are public. Do not store personal, confidential, or purchasing data.
- Backend direct dependencies are pinned; a complete transitive lock is deferred.

## Production deployment review

Before public hosting, configure HTTPS for frontend and API, an explicit frontend
origin allowlist, private database networking and least-privilege database access,
strong platform-managed secrets, restricted logs, and login/abuse rate limits.
Configure frontend security headers at the hosting/reverse-proxy layer: a tested
Content-Security-Policy (including frame-ancestors), nosniff, referrer policy, and
HTTPS-only HSTS after HTTPS is correctly deployed. The API headers above do not
secure the separately served frontend HTML. Review the session design before using
sensitive data; HttpOnly/Secure cookies would also require a deliberate CSRF design.

These are deployment recommendations, not claims of installed production controls.
No hosting, external service, or new authentication architecture was introduced in
Phase 9/10. See [testing](testing.md) for the enforced role matrix and reproducible checks.
