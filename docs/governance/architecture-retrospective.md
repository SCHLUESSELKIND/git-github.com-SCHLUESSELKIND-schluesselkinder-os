# Architecture Retrospective

## Purpose

This document reviews the SCHLUESSELKINDER OS architecture after Sprint 10.5.

The goal is institutional self-critique before operational power exists.

This phase does not add:

- Prisma models
- API routes
- auth
- admin workflows
- provider SDKs
- generation logic
- execution logic
- posting or scheduling
- workers
- persisted audit reports
- engagement or growth metrics

## Layer Review

### Sprint 4: Backend Foundation

Strengths:

- Archive-first release state avoids generic shop or publish terms.
- Object releases remain archive-only.
- Read-only API boundary is clear.

Weaknesses:

- `ReleaseStatus.ACTIVE` is useful but broad. It can later be misread as commercial availability, public publishing, or operational readiness.
- `ObjectRelease.type` and `ObjectRelease.mark` are strings. This is flexible, but weakly controlled.
- The foundation has no explicit invariant that commerce fields must stay absent until a future commerce sprint.

Risk:

- Future commerce work could treat the object archive as a product catalog unless the cultural/archive boundary is restated before Stripe and Printful work.

### Sprint 5: Brand Intelligence

Strengths:

- Voice profiles are separated from audience personas.
- Rules are machine-addressable by code.
- Forbidden-energy records create a clear drift-control surface.

Weaknesses:

- Several rule statements are still interpretive, for example cultural credibility and label publishability.
- `SignalScoringRule.weight` is stored but not deeply reflected in the evaluator yet.
- Current seed `ForbiddenEnergy` records lag behind the Sprint 10.5 detector categories.

Risk:

- The system can appear more machine-readable than it is. Some rules are structured records but not operationally testable yet.

### Sprint 6: Content Graph

Strengths:

- Compatibility verdicts distinguish `REQUIRED`, `ALLOWED`, `DISCOURAGED`, and `FORBIDDEN`.
- `Asset.referenceKey` remains symbolic.
- Ropeface is correctly modeled as artist-specific secondary identity.

Weaknesses:

- Graph validation emits findings for only some relation types.
- Visual environment compatibility is checked but not strongly enforced.
- Track and release compatibility are represented, but output validation does not yet produce findings for many mismatch cases.

Risk:

- The graph can become descriptive metadata instead of a hard constraint system unless validation coverage expands.

### Sprint 7: Approval + Review Governance

Strengths:

- `ApprovalDecision` is separate from `ReviewItem.status`.
- Decision history is append-only by design.
- Review routes are read-only.

Weaknesses:

- Append-only is a documented rule, not a database-enforced invariant.
- `ReviewItem.status.APPROVED` can become a shortcut authority if future code treats it without checking decision history.
- `subjectKey` convention is documented, but current seeded keys do not consistently use the recommended prefixes.

Risk:

- Future authenticated workflows could centralize approval authority in mutable status fields.

### Sprint 8: Controlled Generation

Strengths:

- No provider integration exists.
- Generation outputs require `reviewItemId`.
- `GenerationOutputStatus` intentionally has no `APPROVED`.

Weaknesses:

- `GenerationRequestStatus.REVIEW_ACCEPTED` can sound like approval.
- `GenerationOutputEvaluation` can be misread as evaluator truth if surfaced without authority disclaimers.
- `PromptSection` is controlled brief text, but the word prompt carries operational gravity.

Risk:

- Future teams may treat planning records as executable prompts unless naming and docs are hardened.

### Sprint 9: Evaluation + Rule Engine

Strengths:

- Evaluation reports are pure TypeScript.
- Reports always expose `reviewRequired: true`, `usableWithoutReview: false`, and `approvalAuthority: false`.
- No DB mutation occurs during evaluation.

Weaknesses:

- Scores are source-penalty based and can move multiple axes together.
- Forbidden-energy detection is deterministic but term-based and brittle.
- Rule text from Brand Intelligence is not deeply parsed.

Risk:

- A normalized score can look more precise than the evaluator currently is.

### Sprint 10: Internal Evaluation Console

Strengths:

- Console is read-only.
- It is positioned as inspection, not administration.
- It exposes raw JSON and no approval controls.

Weaknesses:

- `NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED` is visibility gating, not authentication.
- The route path uses `/admin`, which can invite future admin-product thinking.

Risk:

- If deployed with the flag enabled, the console is not protected by production-grade access control.

### Sprint 10.5: Calibration + Red-Team Regression

Strengths:

- Deterministic fixtures protect against evaluator drift.
- Red-team categories cover many known corruption vectors.
- Calibration does not persist reports or add routes.

Weaknesses:

- Detector categories are not yet aligned with seeded DB categories.
- Fixtures assert score ranges, but the score model is still coarse.
- Negative fixture text necessarily contains forbidden language, so report-term checks must be carefully scoped.

Risk:

- Calibration can create confidence in coverage while DB-backed evaluation remains narrower.

## Cross-Layer Contradictions

1. Detector coverage is broader than seeded forbidden-energy records.
2. Subject key convention recommends prefixed keys, but existing records often use raw domain codes.
3. `ReviewItem.status` is current materialized state, but future code may treat it as full approval truth.
4. `GenerationOutputEvaluation` exists as stored records, while Sprint 9 evaluator reports are intentionally not persisted.
5. `GenerationRequestStatus.REVIEW_ACCEPTED` conflicts with the stronger rule that approval truth lives only in review governance.

## Current Integrity Posture

The system is conservative and non-operational today.

The main risk is not current execution.
The main risk is future teams treating structured planning records as authority, or treating scores as decisions.

## Immediate Retrospective Conclusion

Before any operational sprint, the architecture needs:

- seed and detector alignment
- terminology hardening
- explicit authority boundaries around stored evaluations
- graph validation coverage review
- score model calibration notes
- a documented danger map for future execution powers

These are governance clarifications, not product expansion.
