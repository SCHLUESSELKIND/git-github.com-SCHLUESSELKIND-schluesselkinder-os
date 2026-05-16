# Hardening Roadmap

## Purpose

This roadmap orders governance hardening work without adding operational capability.

It separates what should happen now from what must wait until execution work is explicitly approved.

## Phase 1: Immediate Hardening

Classification: `IMMEDIATE HARDENING`

Goal:

Remove semantic contradictions that already exist in the read-only system.

Work:

1. Align forbidden-energy detector categories with seeded `ForbiddenEnergy` records.
2. Clarify stored evaluations as inspection records only.
3. Review `GenerationRequestStatus.REVIEW_ACCEPTED` naming.
4. Normalize or document `subjectKey` prefixes.
5. Remove or quarantine older subjective finding examples from docs.
6. Update governance docs to state that recommendation is not authority.

Allowed:

- docs
- seed planning
- naming proposals
- deterministic tests
- read-only validation checks

Not allowed:

- schema changes without explicit approval
- write routes
- auth
- execution
- provider SDKs

## Phase 2: Pre-Execution Hardening

Classification: `PRE-EXECUTION HARDENING`

Goal:

Prepare the system for future write-capable workflows without creating execution.

Required before any operational workflow:

1. Append-only enforcement plan for `ApprovalDecision`.
2. Review state transition policy.
3. Actor identity model.
4. Immutable audit trail requirements.
5. RuleViolation write policy.
6. Generation output quarantine policy.
7. Provider adapter safety contract.
8. Internal console access policy.
9. Graph validation completeness review.
10. Score display policy.

Allowed:

- design docs
- ADRs
- tests for current read-only guarantees
- migration proposals

Not allowed:

- actual provider calls
- scheduler
- posting
- workers
- execution jobs
- commerce flows

## Phase 3: Write Boundary Design

Classification: `PRE-EXECUTION HARDENING`

Goal:

Design write routes before implementation.

Rules:

- no write route may update `ReviewItem.status` without creating an `ApprovalDecision`
- no generated output may exist without a `ReviewItem`
- no evaluation report may be persisted as approval
- no status field may authorize execution alone
- no operator action may bypass rule violation history

Deliverables before implementation:

- state transition table
- actor permission table
- append-only enforcement strategy
- failure-state map
- audit log shape
- rollback and correction policy

## Phase 4: Provider Adapter Readiness

Classification: `PRE-EXECUTION HARDENING`

Goal:

Define provider boundaries before adding provider SDKs.

Required before AI provider calls:

- prompt boundary review
- secret isolation policy
- input allowlist
- output quarantine
- red-team validation gate
- no automatic promotion from output to usable content

Required before social APIs:

- account permission strategy
- dry-run mode
- explicit publish approval
- schedule review requirement
- failure and retry policy
- no engagement-first optimization

Required before Stripe or Printful:

- object archive to commerce mapping
- payment state separation
- fulfillment state separation
- no public shop language drift

## Phase 5: Permanent Non-Goals Enforcement

Classification: `PERMANENTLY DISALLOWED`

Goal:

Prevent future backlog contamination.

Disallowed forever:

- autonomous publishing
- score-based approval
- AI approval decisions
- engagement-first optimization
- virality-first content ranking
- social autopilot
- scraping-based posting
- unofficial social automation
- commerce availability inferred from archive status

## Roadmap Dependencies

Do not start provider or execution work until these are resolved:

1. Approval and evaluation separation is mechanically enforced.
2. Review write rules exist.
3. Detector and seed categories are aligned.
4. Subject key convention is stable.
5. Graph validation gaps are known.
6. Internal console exposure is controlled.
7. Scores have display and interpretation rules.

## Roadmap Non-Expansion Rule

Hardening work should reduce ambiguity.

It should not add:

- new product surfaces
- new operational powers
- new automation pathways
- new external dependencies
- new dashboard concepts

## Roadmap Conclusion

The correct order remains:

1. clarify authority
2. harden terminology
3. align rules and detectors
4. enforce review invariants
5. only then design limited write workflows
6. only then consider provider adapters

Execution is not the next phase.
Governance hardening remains the next phase.
