# Business rules

| ID | Rule | Implemented behavior |
| --- | --- | --- |
| BR-01 | Manager assignment | Submission requires an active requester with an active assigned manager. |
| BR-02 | Finance threshold | Estimated cost at or above **Rp5,000,000** requires Finance approval. Lower costs skip Finance. |
| BR-03 | Rejection reason | Manager and Finance rejection require a non-blank reason. |
| BR-04 | Cancellation | The requester may cancel only while awaiting Manager approval. The pending Manager approval is closed as Cancelled. |
| BR-05 | Processing entry | Only an Approved request may enter Processing. |
| BR-06 | Procurement ownership | The Procurement user who starts processing becomes the owner. Competing starts cannot create two owners. |
| BR-07 | Completion | Only the assigned Procurement owner may complete a Processing request. |
| BR-08 | Terminal states | Completed, Rejected, and Cancelled requests cannot continue through workflow endpoints. |
| BR-09 | High-priority deadline | Due one calendar day after submission. |
| BR-10 | Medium-priority deadline | Due three calendar days after submission. |
| BR-11 | Low-priority deadline | Due five calendar days after submission. |
| BR-12 | Due Soon | Applies from exactly 24 hours remaining through the exact deadline. |
| BR-13 | Breached | Applies at the first instant after the deadline for an active request. |
| BR-14 | Completion timing | Completion at or before the deadline is Completed On Time; later is Completed Late. |
| BR-15 | SLA exclusion | Draft, Rejected, and Cancelled are Not Applicable. |
| BR-16 | Audit | Creation, cancellation, decisions, Finance routing, processing, and completion append audit events in the same transaction. |
| BR-17 | Request numbering | PostgreSQL allocates unique `REQ-YYYY-NNNN` display numbers from a sequence. Gaps are allowed. |

Rules are enforced by backend services and database constraints where structural
enforcement is practical. The browser presents allowed actions but is not the security boundary.
