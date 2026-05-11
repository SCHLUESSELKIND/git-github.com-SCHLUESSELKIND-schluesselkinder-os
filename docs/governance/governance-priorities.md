# Governance Priorities

## Purpose

This document classifies governance hardening work after the architecture retrospective.

It does not add runtime capability.
It defines priority and classification before operational power exists.

## Classification Key

### IMMEDIATE HARDENING

Must be addressed before the next structural backend sprint.

These items protect current interpretation of the system and prevent near-term semantic drift.

### PRE-EXECUTION HARDENING

Must be completed before any write-enabled, provider-enabled, scheduled, or posting-capable workflow.

These items can wait while the system remains read-only.

### DOCUMENTATION ONLY

Known risk that should remain documented for now.

No implementation should occur until an approved sprint requires it.

### ACCEPTABLE AMBIGUITY

Ambiguity that is tolerable because the system is currently non-operational and the term is contained.

Monitor, but do not churn.

### PERMANENTLY DISALLOWED

Concepts that must not become part of SCHLUESSELKINDER OS.

These are not backlog items.

## Priority Table

| Item | Classification | Reason |
| --- | --- | --- |
| Evaluation must never imply approval | IMMEDIATE HARDENING | This is the central governance boundary. |
| `PASS` must remain review-bound | IMMEDIATE HARDENING | PASS can be visually or procedurally misread as success. |
| `approvalAuthority: false` must remain constant | IMMEDIATE HARDENING | Report authority must be impossible to reinterpret. |
| Detector and seed categories must be reconciled | IMMEDIATE HARDENING | Current route-backed evaluation can be narrower than fixture-backed calibration. |
| Stored evaluations must be labeled as inspection records | IMMEDIATE HARDENING | `GenerationOutputEvaluation` can be mistaken for approval evidence. |
| Subject key convention must be clarified | IMMEDIATE HARDENING | Mixed key formats can corrupt future review and evaluation references. |
| `REVIEW_ACCEPTED` terminology must be reviewed | IMMEDIATE HARDENING | It can sound like approval authority. |
| Append-only approval enforcement | PRE-EXECUTION HARDENING | Current rule is documented, but future write routes need enforcement. |
| Auth and actor identity | PRE-EXECUTION HARDENING | Needed before any write route, not before docs. |
| Review state transition policy | PRE-EXECUTION HARDENING | Required before status mutation exists. |
| Provider adapter boundary | PRE-EXECUTION HARDENING | Required before AI, social, commerce, or analytics integrations. |
| Worker and scheduler kill switches | PRE-EXECUTION HARDENING | Required before background execution exists. |
| Internal console access control | PRE-EXECUTION HARDENING | Required before any production exposure. |
| Graph validation expansion | PRE-EXECUTION HARDENING | Required before generated artifacts can advance through review. |
| Score axis calibration refinement | DOCUMENTATION ONLY | Current scoring is conservative and non-operational. |
| `/admin/evaluation` route naming | ACCEPTABLE AMBIGUITY | UI is read-only and gated; route churn is not urgent. |
| `PromptSection` naming | ACCEPTABLE AMBIGUITY | Docs define it as planning text, not provider-ready payload. |
| `ReleaseStatus.ACTIVE` | ACCEPTABLE AMBIGUITY | Safe while disconnected from commerce availability. |
| Engagement optimization | PERMANENTLY DISALLOWED | Conflicts with identity protection. |
| Autonomous publishing | PERMANENTLY DISALLOWED | Conflicts with human governance. |
| AI-generated approval decisions | PERMANENTLY DISALLOWED | Approval authority must remain human. |
| Social autopilot | PERMANENTLY DISALLOWED | Creates brand and account risk. |
| Score-based publishing | PERMANENTLY DISALLOWED | Score is inspection, not truth. |

## Highest-Priority Decisions

### 1. Approval Authority Must Stay Narrow

Only these concepts may carry approval truth:

- `ReviewItem` as current materialized review state
- append-only `ApprovalDecision` as historical decision record

Nothing else may become approval authority.

### 2. Evaluation Must Stay Advisory

Evaluation can:

- find issues
- compute scores
- explain blockers
- detect drift
- recommend review attention

Evaluation cannot:

- approve
- publish
- schedule
- unlock execution
- override human review

### 3. Scores Are Secondary

Scores can summarize rule pressure.

Scores cannot become:

- approval threshold
- publishing threshold
- channel performance target
- growth target
- operator ranking system

### 4. Read-Only Surfaces Must Stay Read-Only

Inspection routes and console views cannot gain mutation controls by incremental convenience.

Any write route belongs to a separately approved governance sprint.

### 5. Future Execution Must Be Treated As Dangerous

Execution includes:

- provider calls
- media generation
- scheduling
- posting
- worker jobs
- commerce checkout
- fulfillment
- analytics-driven optimization

Execution requires governance hardening first.

## Current Priority Conclusion

The system does not need expansion.

The next hardening work should resolve the highest semantic risks:

1. detector and seed consistency
2. approval/evaluation terminology
3. subject key normalization
4. stored evaluation labeling
5. append-only enforcement strategy before write routes
