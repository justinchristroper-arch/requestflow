# RequestFlow UAT-style Acceptance Matrix

> Portfolio simulation only. These scenarios are derived from documented requirements and business rules. They are not evidence of a real business-user UAT session. "Verified" means the behavior is covered by the project's automated/backend/browser verification described in `testing.md`.

| ID | Business scenario | Requirement / rule | Preconditions | Test steps | Expected result | Verification status |
| --- | --- | --- | --- | --- | --- | --- |
| UAT-01 | Submit a valid request | FR-01, BR-01 | Employee is active and has an active Manager | Log in as Employee; enter valid request details; submit | Request is created; requester/manager/request number/status/due date are assigned; status = Pending Manager Approval | Verified |
| UAT-02 | Low-cost request skips Finance | FR-03, US-03, BR-02 | Request cost = Rp4,999,999; pending Manager | Manager approves | Request moves directly to Approved; no Finance decision is required | Verified |
| UAT-03 | Exact threshold requires Finance | FR-03, BR-02 | Request cost = Rp5,000,000; pending Manager | Manager approves | Request moves to Pending Finance Approval | Verified |
| UAT-04 | High-cost request completes Finance approval | FR-03, FR-05, BR-02 | Cost > Rp5,000,000; Manager approved | Finance approves | Request moves from Pending Finance Approval to Approved; decision actor/time recorded | Verified |
| UAT-05 | Manager rejection requires reason | FR-04, BR-03 | Assigned Manager; request pending Manager | Attempt blank rejection; then reject with reason | Blank reason is rejected; valid reason moves request to Rejected and records decision | Verified |
| UAT-06 | Finance rejection requires reason | FR-05, BR-03 | Request pending Finance | Attempt blank rejection; then reject with reason | Blank reason is rejected; valid reason moves request to Rejected and records decision | Verified |
| UAT-07 | Employee cancels before Manager decision | FR-06, BR-04 | Employee owns request; status Pending Manager Approval | Employee cancels | Request becomes Cancelled; pending Manager approval is closed; audit event is recorded | Verified |
| UAT-08 | Employee cannot cancel after Manager decision | FR-06, BR-04, BR-08 | Request has moved beyond Pending Manager Approval | Employee attempts cancellation | Cancellation is blocked; request remains in its current valid state | Verified |
| UAT-09 | Procurement takes ownership of Approved work | FR-07, FR-08, US-05, BR-05, BR-06 | Request status Approved | Procurement operator starts processing | Request becomes Processing; that operator becomes owner; timestamp/note/audit event recorded | Verified |
| UAT-10 | Competing Procurement operators cannot both own | NFR-04, BR-06 | One Approved request; two Procurement operators act concurrently | Both attempt Start Processing | Only one valid ownership transition succeeds; request has one owner | Verified |
| UAT-11 | Only assigned owner can complete | FR-08, US-06, BR-07 | Request is Processing and owned by Procurement A | Procurement B attempts completion; then A completes | B is blocked; A succeeds; status becomes Completed with completion timestamp and audit event | Verified |
| UAT-12 | Terminal states cannot continue | BR-08 | Request is Completed, Rejected, or Cancelled | Attempt another workflow transition | Transition is blocked and state does not change | Verified |
| UAT-13 | Employee cannot access another employee's private request | FR-12, NFR-02 | Employee A and Employee B have separate requests | Employee A changes request ID to B's private request | Detail/audit/action endpoints do not reveal B's request; invisible object returns not found | Verified |
| UAT-14 | Admin has visibility but no workflow override | FR-11 | Admin account; requests exist | Open global request/analytics views; attempt business transition | Admin can view global data/analytics but cannot approve, start, complete, or override workflow | Verified |
| UAT-15 | SLA priority deadlines are assigned consistently | FR-10, BR-09, BR-10, BR-11 | Create High, Medium, Low requests | Compare due dates to submission timestamp | Due dates are +1, +3, +5 calendar days respectively | Verified |
| UAT-16 | Due Soon and Breached boundaries are exact | FR-10, BR-12, BR-13 | Active request around deadline boundary | Evaluate at exactly 24h remaining, exact deadline, and first instant after | 24h through deadline = Due Soon; first instant after = Breached | Verified |
| UAT-17 | Completion timing classifies SLA outcome | FR-10, BR-14 | Processing request with known due date | Complete at exact deadline; complete another after deadline | Exact deadline = Completed On Time; later = Completed Late | Verified |
| UAT-18 | Audit history is chronological and meaningful | FR-09, BR-16 | Request moves through lifecycle | Submit, approve, process, complete; open audit history | Creation, routing/decisions, processing, and completion appear in chronological order with actor/context | Verified |
| UAT-19 | Management measures use defined formulas | FR-11 | Synthetic completed requests exist | Open Admin analytics | SLA Compliance and Average Resolution Hours match documented formulas; empty denominators show em dash | Verified |
| UAT-20 | Unauthorized role cannot perform another role's action | FR-12, NFR-02 | Valid logged-in user with wrong business role | Call decision/fulfillment action directly | Backend blocks the action even if UI navigation is bypassed | Verified |

## Acceptance note

For a real implementation, this matrix would be reviewed with named business stakeholders before execution. A real UAT cycle would add:
- business owner / tester;
- execution date;
- actual result;
- Pass / Fail / Blocked;
- defect or change-request reference;
- sign-off and approval.

The current matrix is portfolio evidence that requirements were translated into testable business scenarios.
