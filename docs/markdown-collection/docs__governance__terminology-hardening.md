# Terminology Hardening

## Purpose

Terminology controls future behavior.

Ambiguous names can create authority leakage before code does.
This document identifies naming risks after Sprint 10.5.

## Naming Principles

Use names that make boundaries obvious:

- inspection, not administration
- evaluation, not approval
- placeholder, not generated asset
- review-bound, not usable
- constraint, not prompt execution
- signal quality, not growth performance
- archive object, not product

Avoid names that imply:

- publication readiness
- autonomous execution
- approval authority
- social growth
- commerce readiness
- creator productivity
- operational throughput

## Terms To Preserve

Keep:

- `ReviewItem`
- `ApprovalDecision`
- `reviewRequired`
- `usableWithoutReview`
- `approvalAuthority`
- `REVIEW_REQUIRED`
- `REVIEW_REJECTED`
- `REVIEW_ARCHIVED`
- `SIGNAL_PENDING`
- `CLOSED`
- `ARCHIVED`
- `ConstraintBundle`
- `ForbiddenEnergy`
- `CompatibilityVerdict`
- `GenerationOutputStatus` values without `APPROVED`

These terms reinforce governance.

## Terms With Drift Risk

### `GenerationRequestStatus.REVIEW_ACCEPTED`

Risk:

The term can be interpreted as approval, even if it only means planning material passed a review gate.

Potential future hardening:

- `REVIEW_BOUND`
- `REVIEW_ACKNOWLEDGED`
- `READY_FOR_FUTURE_EXECUTION_REVIEW`

Do not change yet without migration planning.
Record the ambiguity now.

### `GenerationOutputEvaluation`

Risk:

The model name can sound like evaluation truth.
Stored records may be mistaken for live evaluator output or approval proof.

Potential future hardening:

- `StoredEvaluationFinding`
- `PlanningEvaluationRecord`
- `OutputInspectionRecord`

Any UI must label this as stored inspection data, not approval.

### `/admin/evaluation`

Risk:

The route path uses admin language even though the surface is an inspection console.

Potential future hardening:

- `/internal/evaluation`
- `/internal/inspection`
- `/archive/evaluation`

Do not add routing churn unless the project decides to rename the internal surface.

### `PromptSection`

Risk:

Prompt can imply provider-ready prompt payload.

Current guardrail:

Docs say `PromptSection` is controlled brief text, not executable prompt payload.

Potential future hardening:

- `BriefSection`
- `InstructionSection`
- `PlanningSection`

### `ACTIVE`

Risk:

`ReleaseStatus.ACTIVE` can imply public, for-sale, published, or campaign-running.

Current meaning:

Archive-visible or current release state.

Potential future hardening:

- add docs around `ACTIVE`
- avoid using `ACTIVE` as commerce availability
- never map `ACTIVE` to buyability

### `APPROVED`

Risk:

`ReviewStatus.APPROVED` is valid review state, but it can become dangerous if used without decision history.

Guardrail:

Any future write path must pair current status with append-only `ApprovalDecision`.

## Subject Key Convention

Current documentation recommends:

- `SKM-003`
- `CW-ROOM-AFTER-LIGHT`
- `AST-RUNE-KEY-SYMBOL`
- `SKR-MOODBOARD-SKM-003`

Current seed behavior includes raw domain keys such as:

- `COLD_ARCHIVE`
- `ROOM_AFTER_LIGHT`
- `SKM-003`

Risk:

Mixed key forms can create duplicate references, broken joins, and evaluator ambiguity.

Hardening proposal:

- keep canonical domain codes as domain model codes
- require `subjectKey` to use explicit prefixes for review and generation subjects
- document mapping from domain codes to subject keys

Example:

```text
CampaignWorld.code: ROOM_AFTER_LIGHT
ReviewItem.subjectKey: CW-ROOM-AFTER-LIGHT
Asset.code: RUNE_KEY_SYMBOL
ReviewItem.subjectKey: AST-RUNE-KEY-SYMBOL
MusicRelease.releaseCode: SKM-003
ReviewItem.subjectKey: SKM-003
```

## Terms To Avoid In Future Features

Avoid:

- dashboard
- campaign manager
- creator studio
- growth engine
- viral
- reach optimizer
- content engine
- autopublish
- smart scheduler
- approval score
- ready to publish
- publishable without review
- launch campaign
- shop now
- conversion
- funnel
- audience growth
- engagement target

If a term is operationally necessary later, define it against governance boundaries before implementation.

## Machine-Readable Language Rules

Weak terms:

- credible
- iconic
- tension
- pressure
- restraint
- cultural
- publishable

These can stay in strategy docs, but evaluator findings should use machine-readable terms:

- matched forbidden term
- required asset missing
- forbidden asset present
- required mood missing
- missing review binding
- unresolved rule code
- contradictory compatibility verdict
- score axis degraded by blocker

## Hardening Priority

High priority:

1. Rename or document `REVIEW_ACCEPTED`.
2. Normalize `subjectKey` conventions.
3. Clarify `GenerationOutputEvaluation` as stored inspection records.
4. Keep `PASS` visually and semantically non-approving.
5. Prevent `ACTIVE` from becoming commerce availability.

Medium priority:

1. Consider `/internal/evaluation` naming later.
2. Consider `BriefSection` instead of `PromptSection` before provider integration.
3. Replace interpretive finding language in older docs.

## Conclusion

The architecture is technically bounded.
The naming layer is the next drift surface.

Before operational power exists, terminology should be hardened so future code cannot easily confuse:

- evaluation with approval
- planning with execution
- archive with commerce
- inspection with administration
- signal quality with growth performance
