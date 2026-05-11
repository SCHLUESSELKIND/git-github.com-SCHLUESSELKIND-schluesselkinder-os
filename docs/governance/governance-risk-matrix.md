# Governance Risk Matrix

## Purpose

This matrix identifies governance risks after Sprint 10.5.

It does not authorize implementation.
It records where the system could lose institutional integrity later.

Severity:

- `CRITICAL`: can create publication, approval, or brand authority leakage.
- `HIGH`: can weaken review boundaries or evaluation accuracy.
- `MEDIUM`: can create drift, ambiguity, or operator confusion.
- `LOW`: should be monitored but is not immediately dangerous.

## Risk Matrix

| Risk | Severity | Likelihood | Affected Layer | Current Guardrail | Gap |
| --- | --- | --- | --- | --- | --- |
| `ReviewItem.status` becomes treated as full approval truth | CRITICAL | Medium | Review Governance | Docs distinguish status from decision history | No DB or API invariant prevents shortcuts |
| `ApprovalDecision` append-only rule is broken by future write routes | CRITICAL | Medium | Review Governance | Docs state append-only design | No technical guardrail yet |
| `GenerationOutputEvaluation` is treated as approval evidence | HIGH | Medium | Controlled Generation | Docs say output is not approval | Model name sounds authoritative |
| `GenerationRequestStatus.REVIEW_ACCEPTED` implies approval | HIGH | Medium | Controlled Generation | No output `APPROVED` status | Status wording can drift toward authority |
| Detector categories exceed seeded `ForbiddenEnergy` records | HIGH | High | Evaluation, Brand Intelligence | Calibration fixtures cover new categories | DB-backed evaluator may not check missing categories |
| Scores become interpreted as approval readiness | HIGH | Medium | Evaluation | Reports state no approval authority | Numeric scores invite decision shortcuts |
| Internal console is deployed without auth | HIGH | Low now, Medium later | Web Console | Env flag gate | Env flag is not access control |
| Future execution layer posts after `PASS` | CRITICAL | Medium later | Future Execution | PASS docs require review | No execution layer yet, but risk is structural |
| Graph compatibility remains descriptive | HIGH | Medium | Content Graph | Compatibility records exist | Validator emits findings for limited relation types |
| Subject key convention splits between raw and prefixed forms | MEDIUM | High | Review, Graph, Generation | Docs define convention | Current seeds use mixed styles |
| Brand rules remain interpretive | MEDIUM | High | Brand Intelligence | Rule codes exist | Some statements lack deterministic checks |
| Rule weights imply precision | MEDIUM | Medium | Scoring | Weight field exists | Evaluator uses weights lightly |
| Red-team fixtures overfit current detector terms | MEDIUM | Medium | Calibration | Deterministic tests exist | Term-matching can miss paraphrases |
| Future social channels pull system toward engagement logic | HIGH | Medium later | Channel Rules, Future Execution | Docs reject engagement-first scoring | Future integrations may reintroduce growth incentives |
| `/admin` route naming invites SaaS/admin mental model | LOW | Medium | Web Console | UI copy is inspection-focused | Route naming still says admin |
| `PromptSection` invites provider-ready prompt thinking | MEDIUM | Medium later | Controlled Generation | Docs define planning-only records | Name carries model-execution implications |

## Authority Leakage Risks

Authority can centralize accidentally in:

- `ReviewItem.status`
- `GenerationRequest.status`
- `GenerationOutputEvaluation.verdict`
- evaluation report `score.normalized`
- internal console views that visually privilege `PASS`
- future operational code that checks only one field

Required future rule:

No operational action may depend on a single status, score, or evaluator verdict.

Any future execution path must require:

- explicit human decision history
- current review status
- no blocking evaluator findings
- review-bound subject identity
- immutable audit trail

## Detector And Seed Drift

Current concern:

Sprint 10.5 detectors include more categories than the Sprint 5 seed data.

Detector-only categories include:

- `FAKE_LUXURY`
- `HYPE_LANGUAGE`
- `ARCHIVE_INCOHERENCE`
- `CREATOR_ECONOMY_LANGUAGE`
- `EXCESSIVE_EXPLANATION`
- `MOTIVATIONAL_FASHION`
- `OVER_LOGOING`
- `ROPEFACE_DOMINANCE`
- `TIKTOK_BAIT`
- `TREND_CHASING`

Risk:

Fixture evaluation can fail correctly while DB-backed route evaluation misses these categories if they are not seeded.

## Review Truth Ambiguity

Review truth is currently defined as:

- `ReviewItem` for materialized state
- append-only `ApprovalDecision` for history

Ambiguity appears when:

- `ReviewItem.status` is read without decisions
- stored evaluation records are presented beside approval records
- `GenerationOutput.status` is used as a gate
- `PASS` is visually treated as success

The system must keep approval truth separate from:

- scoring
- evaluation
- generation placeholders
- console inspection
- channel readiness

## Growth Incentive Risks

Growth language can enter through:

- TikTok channel rules
- future social integrations
- performance dashboards
- campaign reporting
- operator requests for reach
- content templates

Do not introduce primary metrics for:

- CTR
- reach
- virality
- watch time
- follower growth
- creator productivity
- publishing throughput

If performance metrics are introduced later, they must be secondary and subordinate to brand-governance constraints.

## Boundary Strength

Strong today:

- no write routes for generation, review, or evaluation
- no provider SDKs
- no workers
- no scheduler
- no posting
- no commerce
- evaluation reports have explicit authority flags

Weak by convention:

- append-only approval history
- no operational use of `PASS`
- no use of scores as approvals
- subject key normalization
- internal console access boundary
- generation planning records are non-executable

## Matrix Conclusion

The architecture is currently safe because it is non-operational.

The most dangerous future moment is not AI provider integration.
It is the first write-enabled workflow that interprets review, generation, and evaluation records.

That workflow must be designed as a governance system, not as an automation feature.
