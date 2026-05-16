# Evaluation + Rule Engine

Sprint 9 adds conservative validation for SCHLUESSELKINDER generation material.

The engine is not creative.
The engine is not an engagement optimizer.
The engine is a cold validator that protects the brand system before human review.

## Authority Boundary

Evaluation reports have no approval authority.

Every report must state:

- `reviewRequired: true`
- `usableWithoutReview: false`
- `approvalAuthority: false`

Approval truth remains only in:

- `ReviewItem`
- append-only `ApprovalDecision`

No evaluation verdict equals approval.

## Verdict Meanings

`PASS` means no blocking findings were detected. Human review is still required.

`WARNING` means non-blocking concerns were detected. Human review is still required.

`FAIL` means the material is blocked before approval review.

## Engine Functions

Sprint 9 implements pure TypeScript evaluator functions:

- `resolveConstraints()`
- `detectForbiddenEnergy()`
- `validateGraphCompatibility()`
- `computeSignalScore()`
- `evaluateGenerationOutput()`

The functions receive plain objects and return plain objects.

They do not write to the database.
They do not create `RuleViolation`, `ApprovalDecision`, `ReviewItem`, or `GenerationOutputEvaluation` rows.

## Evaluation Axes

Scores are brand-first:

- identity protection
- symbolic restraint
- institutional consistency
- cultural credibility
- pressure without noise
- archive coherence
- rule adherence
- review readiness

Scores must never optimize for:

- CTR
- reach
- virality
- watchtime
- engagement-first growth

Future performance metrics may exist later only as secondary signals weighted against brand constraints.

## Finding Language

Findings must be concrete and technical.

Good:

- `Matched forbidden term "neon gradient" for CYBERPUNK_OVERLOAD.`
- `RUNE_KEY_SYMBOL is required for ROOM_AFTER_LIGHT, but it is not present in the evaluated material.`
- `ROPEFACE_ARTIST_STAMP is forbidden in COLD_ARCHIVE, but it is present in the evaluated material.`

Bad:

- `The visual tension feels wrong.`
- `This lacks underground aura.`
- `The mood is not authentic enough.`

The system may identify violations.
It may not perform art criticism.

## Read-Only API

Sprint 9 exposes read-only inspection routes:

- `GET /evaluation/health`
- `GET /evaluation/generation/outputs/:outputKey`
- `GET /evaluation/generation/briefs/:briefKey`
- `GET /evaluation/rules/constraints/:bundleCode`

There are no POST routes.
There is no evaluator persistence.
There is no workflow execution.

## Non-Goals

Sprint 9 does not implement:

- AI generation
- prompt execution
- provider SDKs
- workers
- posting
- scheduling
- social APIs
- admin UI
- auth
- commerce
- database mutation from evaluator execution
- engagement-first scoring
- virality, CTR, or reach optimization
