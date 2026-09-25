# RequestFlow portfolio case study

## Problem

This case study begins with a simulated organization handling internal IT and
procurement needs through chat, email, and spreadsheets. The assumed process makes
status, routing, ownership, decision history, SLA risk, and management reporting
difficult to manage consistently. It is a portfolio scenario, not a claim about a
specific company.

## Analysis

I separated the problem into actors, decisions, hand-offs, business states, data,
and controls. The key branch is cost: requests below Rp5,000,000 skip Finance, while
requests at or above it require Finance approval. Cancellation is valid only before
Manager decision. Procurement must explicitly take ownership before completion.

The analysis artifacts include AS-IS/TO-BE flows, stakeholder needs, a mini-BRD,
traceable functional/non-functional requirements, user stories, rules, KPI formulas,
and explicit exclusions.

## Proposed solution

RequestFlow centralizes each request and presents the next authorized action to the
appropriate role. A React SPA provides the workflow UI, a FastAPI modular monolith
owns validation and authorization, and PostgreSQL stores transactional state and
append-only history. Admin analytics provide defined operational views without giving
Admin a business-action override.

## Process redesign

The TO-BE process replaces forwarded messages with explicit states: Pending Manager
Approval, optional Pending Finance Approval, Approved, Processing, and Completed.
Rejected and Cancelled are terminal branches. SLA is calculated from timestamps at
read time, so no scheduled process is needed to maintain a duplicate status field.

## System design

The database relates users, manager assignments, requests, approval stages, and audit
events. A PostgreSQL sequence supplies concurrency-safe request numbers. Workflow
services lock rows and commit the decision, state, owner/timestamps, and audit events
together. Exact decimal money avoids threshold ambiguity.

JWT authentication identifies a user, while every protected call reloads their active
role from PostgreSQL. Backend rules enforce role, object visibility, stage assignment,
state, and Procurement ownership. Frontend role-based navigation improves usability
but does not act as the security boundary.

## Implementation

The application implements request submission/list/detail/cancellation, Manager and
Finance decisions, Procurement fulfillment, audit history, SLA classification,
responsive role workspaces, and Admin KPIs/charts. Alembic revisions create and evolve
the schema. Docker Compose provides repeatable local services; Railway/Vercel files
prepare the same application for public-demo hosting.

## Testing

The verified suite covers authentication, object-level authorization, malicious
payloads, exact Finance/SLA boundaries, transaction rollback, audit protection,
analytics formulas, migrations, and concurrent creation/decisions/ownership. Browser
tests exercise real low/high-cost lifecycles, rejection/cancellation, session races,
error states, and eight screens at four viewport widths. See [testing.md](testing.md)
for current counts and reproduction steps.

## Result

The resulting system can take a synthetic request from submission through conditional
approval, owned fulfillment, completion, audit review, SLA classification, and
aggregate reporting. It gives each demo role a focused workspace and rejects direct
API attempts that violate role, ownership, or workflow rules.

This result describes delivered capability. No production pilot was run, so the
project makes no claim about time saved, adoption, ROI, or compliance improvement.

## Limitations

JWTs are stored in localStorage; there is no token revocation, login throttling, MFA,
SSO, notification, escalation, or independent security audit. Database owners can
alter stored records. Calendar days ignore business hours and holidays. Demo accounts
are shared and synthetic. This is portfolio software, not enterprise production software.

## What this project demonstrates

| Perspective | Evidence |
| --- | --- |
| Business Analyst | AS-IS/TO-BE modeling, stakeholder analysis, mini-BRD, requirements, user stories, business rules, acceptance criteria, KPI definitions |
| IT Consultant | Problem framing, modular architecture, process automation, technology tradeoffs, authorization boundaries, auditability, deployment design |
| IT Intern / Software | React/TypeScript UI, FastAPI/SQLAlchemy API, PostgreSQL/Alembic, JWT/Argon2id, transactional workflow, automated tests, Docker and hosting preparation |

The project is designed to be discussed from all three perspectives while keeping
its scope and evidence honest.
