# Authority Boundaries

## Purpose

This document defines what can and cannot carry authority inside SCHLUESSELKINDER OS.

The goal is to prevent future code from confusing inspection, recommendation, review, approval, and execution.

## Critical Distinctions

### Evaluation Is Not Approval

Evaluation can inspect material.

Evaluation cannot approve material.

Evaluation outputs:

- findings
- verdict
- score
- graph checks
- resolved constraints
- explanation

None of these grant authority.

### Recommendation Is Not Authority

A recommendation can inform a human reviewer.

It cannot:

- change review status
- create approval
- schedule work
- publish content
- trigger provider calls
- change release state

### Review Is Not Execution

Review is a governance gate.

Review can:

- accept
- reject
- request revision
- archive

Review cannot itself:

- post
- schedule
- generate
- fulfill
- charge
- mutate external systems

### Score Is Not Truth

Score is a diagnostic compression of findings.

Score cannot become:

- approval threshold
- publishing threshold
- social performance target
- conversion target
- automated decision

### Console Is Not Admin Platform

The internal evaluation console is an inspection surface.

It is not:

- workflow control
- approval UI
- campaign manager
- creator tool
- scheduler
- publishing surface
- commerce admin

## Approved Authority Sources

Only these may carry review authority:

1. `ReviewItem`
   - current materialized review state
   - not full history

2. `ApprovalDecision`
   - append-only decision history
   - source of review action history

Both are required to understand approval state.

Neither should be used alone for operational execution.

## Non-Authority Sources

These must never carry approval authority:

- `EvaluationReport.verdict`
- `SignalScore.normalized`
- `SignalScore.grade`
- `GenerationOutput.status`
- `GenerationRequest.status`
- `GenerationOutputEvaluation.verdict`
- `ConstraintBundle`
- `PromptSection`
- `ChannelCompositionProfile`
- internal console visibility
- red-team fixture pass/fail
- absence of findings

## Required Future Execution Gate

If execution is ever implemented, it must require a compound gate.

Minimum gate:

```text
review item exists
approval decision exists
current review status allows next step
no blocking evaluation findings
subject key matches expected entity
artifact remains review-bound
actor is authenticated
operation is auditable
```

No single field may satisfy this gate.

## Authority Leakage Patterns

Dangerous patterns:

- `if report.verdict === "PASS" then publish`
- `if score > 85 then schedule`
- `if output.status === "REVIEW_REQUIRED" then show approve button`
- `if request.status === "REVIEW_ACCEPTED" then call provider`
- `if review.status === "APPROVED" then execute without checking decisions`
- `if no violations exist then mark usable`

These patterns are permanently invalid.

## Review State Boundary

`ReviewItem.status` is materialized current state.

It may summarize:

- pending
- approved
- rejected
- needs revision
- archived

It must not replace:

- decision history
- actor identity
- timestamped decision records
- rationale
- rule violation context

## Evaluation Boundary

Every evaluation report must preserve:

- `reviewRequired: true`
- `usableWithoutReview: false`
- `approvalAuthority: false`

Any report missing these flags is invalid for governance use.

## Stored Evaluation Boundary

Stored evaluation records are inspection records.

They are not:

- approval records
- live evaluator truth
- current review state
- execution permission
- publishability records

Stored records should be treated as historical evidence only.

## Console Boundary

The console may display:

- findings
- constraints
- graph checks
- score breakdown
- raw JSON
- fixture cases

The console may not provide:

- approve
- reject
- publish
- schedule
- generate
- retry
- post
- fulfill
- charge

Any future action controls belong outside the current console concept and require a separate governance sprint.

## Boundary Classification

| Boundary | Classification |
| --- | --- |
| Evaluation vs approval | IMMEDIATE HARDENING |
| Stored evaluation vs approval | IMMEDIATE HARDENING |
| Review status vs decision history | PRE-EXECUTION HARDENING |
| Score vs authority | IMMEDIATE HARDENING |
| Console vs admin platform | PRE-EXECUTION HARDENING |
| Recommendation vs workflow action | PRE-EXECUTION HARDENING |
| Execution without human decision | PERMANENTLY DISALLOWED |

## Conclusion

Authority must remain narrow.

Inspection can inform review.
Review can inform future execution.
Execution must never be inferred from inspection.
