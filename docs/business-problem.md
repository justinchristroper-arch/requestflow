# Business problem

RequestFlow models a portfolio business scenario: an organization receives internal
IT and procurement requests through chat, email, and spreadsheets. It does not claim
that a named company uses this process or has these problems.

In the assumed process, the employee describes a need in one channel, a manager records
an approval in another, and Finance or Procurement receives forwarded information.
The requester then follows up manually. Each participant may have only part of the
history, and management must reconstruct status from several sources.

This creates plausible operational risks:

- request records are fragmented or duplicated;
- the requester cannot see a reliable current status or owner;
- high-cost requests may be routed inconsistently;
- approval and fulfillment delays require manual follow-up;
- decision reasons and timestamps are difficult to audit;
- SLA risk becomes visible late; and
- management reporting requires manual spreadsheet work.

## Opportunity

A small workflow application can establish one record, apply the same routing rules,
show ownership and status, preserve meaningful actions, calculate SLA state, and
aggregate operational data. RequestFlow demonstrates that proposed future state.

The project validates software behavior, not real-company impact. It does not claim
measured savings, faster approvals, improved compliance, or return on investment.
Those outcomes would require a real baseline, controlled rollout, and agreed measures.

See the [assumed AS-IS process](as-is-process.md), [implemented TO-BE process](to-be-process.md),
and [business requirements](business-requirements.md).
