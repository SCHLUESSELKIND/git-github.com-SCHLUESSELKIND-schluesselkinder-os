# Evaluation Calibration + Red-Team Regression

Sprint 10.5 hardens the Evaluation + Rule Engine without adding operational capability.

This layer is calibration only.
It does not generate, publish, schedule, persist, approve, or mutate workflow state.

## Purpose

The calibration layer stress-tests whether the evaluator remains conservative.

It checks:

- identity protection
- symbolic restraint
- institutional consistency
- cultural credibility
- pressure without noise
- archive coherence
- rule adherence
- review readiness

Scores are not engagement metrics.
They must not optimize for CTR, reach, virality, watch time, follower growth, or trend capture.

## Authority Boundary

Calibration does not create approval.

Every evaluated report must keep:

- `reviewRequired: true`
- `usableWithoutReview: false`
- `approvalAuthority: false`

`PASS` means no blocking finding was detected.
It still requires human review.

`WARNING` means non-blocking findings exist.
It still requires human review.

`FAIL` means material is blocked before approval review.

Approval truth remains only in:

- `ReviewItem`
- append-only `ApprovalDecision`

## Implementation Boundary

Calibration lives under:

```text
services/api/src/evaluation/calibration/
```

It contains:

- fixture schema
- red-team fixture library
- deterministic fixture runner
- report comparison helper
- rule conflict detector
- explanation helper

It does not add:

- Prisma models
- persisted reports
- API mutation routes
- UI pages
- freeform prompt surfaces
- freeform input
- provider SDKs
- external calls
- workers
- cron jobs
- posting or scheduling
- auth or admin workflows
- commerce

## Red-Team Categories

The regression library covers:

- `CYBERPUNK_OVERLOAD`
- `STARTUP_SAAS`
- `FAKE_LUXURY`
- `MEME_IRONY`
- `TIKTOK_BAIT`
- `OVER_LOGOING`
- `ROPEFACE_DOMINANCE`
- `AI_MOODBOARD`
- `HYPE_LANGUAGE`
- `TREND_CHASING`
- `CREATOR_ECONOMY_LANGUAGE`
- `MOTIVATIONAL_FASHION`
- `EXCESSIVE_EXPLANATION`
- `ARCHIVE_INCOHERENCE`

Each fixture defines:

- expected verdict
- expected finding codes
- expected degraded axes
- expected dominant rule
- expected score range
- terms that must not appear in reports

## Deterministic Fixture Rules

Fixtures must be plain TypeScript objects.

They must not call:

- network
- database
- provider SDKs
- filesystem writes
- clocks or random sources

Fixture assertions should be specific enough to catch drift, but not so brittle that harmless formatting changes break calibration.

Stable assertions include:

- verdict
- finding codes
- authority flags
- degraded axes
- score range
- dominant rule code

## Conflict Detection

The conflict detector is pure TypeScript.

It reports structural problems such as:

- compatibility records marked both `REQUIRED` and `FORBIDDEN`
- compatibility records marked both `REQUIRED` and `DISCOURAGED`
- required constraints pointing at missing rule codes
- forbidden-energy categories without deterministic detector terms
- missing scoring rules

Conflict reports are diagnostic only.
They do not write `RuleViolation` records.

## Explainability

The explainability helper derives a compact inspection layer from an evaluation report.

It exposes:

- dominant finding
- dominant rule
- degraded axes
- graph compatibility summary
- score breakdown
- verdict reason

It preserves the same authority boundary:

- review required
- not usable without review
- no approval authority

## Finding Language

Findings and calibration failures must be concrete and technical.

Good:

- `Matched forbidden term "logo wall" for OVER_LOGOING.`
- `ROOM_AFTER_LIGHT -> RUNE_KEY_SYMBOL is marked REQUIRED and FORBIDDEN.`
- `Constraint Missing rule reference references missing ruleCode MISSING_RULE_CODE.`

Bad:

- `Rule failed for unspecified reasons.`
- `Output is not acceptable.`
- `Score is low.`

The evaluator protects boundaries.
It does not perform art criticism.
