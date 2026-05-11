# Drift Risk Report

## Purpose

This report identifies semantic, aesthetic, governance, and operational drift vectors after Sprint 10.5.

The system must remain:

- conservative
- review-bound
- interpretable
- non-autonomous
- non-engagement-driven
- culturally coherent

## Primary Drift Vectors

### Aesthetic Drift

Known risks:

- cyberpunk overload
- neon gradient language
- internet occult motifs
- horror props
- creepy object language
- AI moodboard collage
- fake luxury
- over-logoing
- Ropeface dominance

Current guardrails:

- public brand system docs
- forbidden-energy detector terms
- red-team fixtures
- content graph compatibility records

Weakness:

The detector is term-based. It can miss paraphrases and visual drift that is not described in text.

### Language Drift

Known risks:

- startup SaaS language
- community marketing
- creator economy phrasing
- TikTok bait
- motivational fashion
- fake hype
- excessive explanation
- lifestyle cliches
- conversion copy

Current guardrails:

- language system
- language rules
- forbidden-energy detector terms
- calibration fixtures

Weakness:

Some strategic terms are still interpretive:

- credible
- iconic
- pressure
- restraint
- publishable
- cultural

These should guide humans, but findings should remain technical.

### Governance Drift

Known risks:

- `PASS` treated as approval
- `ReviewItem.status` treated as full review truth
- `GenerationOutputEvaluation` treated as approval evidence
- `GenerationRequest.status` treated as operational permission
- stored placeholder output treated as generated content

Current guardrails:

- explicit authority flags in evaluation reports
- approval docs
- output status lacks `APPROVED`
- no write routes

Weakness:

Most authority separation is documented and tested at API level, but future write workflows could bypass the intent.

### Score Drift

Known risks:

- normalized score becomes visual priority
- score becomes approval proxy
- score becomes performance proxy
- score axes become engagement axes
- high score hides blocker meaning

Current guardrails:

- no engagement axes
- calibration score ranges
- explicit review flags

Weakness:

Score model is coarse. Different failures can produce similar score profiles.

### Graph Drift

Known risks:

- compatibility records become descriptive metadata
- required relationships are not enforced
- visual environment mismatches do not produce findings
- track mood compatibility is not fully validated
- release campaign world mismatch is under-enforced

Current guardrails:

- compatibility records
- graph checks in evaluation reports
- conflict detector

Weakness:

Checks are more complete than findings.
Operators can see a relationship but may not get a blocking finding.

### Operational Drift

Known risks:

- scheduler before governance hardening
- posting before review workflow
- provider SDKs before constraint resolution
- auth/admin added as product dashboard
- social API work pulls in growth metrics
- worker system creates hidden execution paths

Current guardrails:

- sprint docs repeatedly exclude execution
- no runtime operational code exists

Weakness:

The moment write routes arrive, documentation alone is not enough.

## Detector Vs Seed Drift

Sprint 10.5 detector categories are broader than current seeded forbidden-energy records.

This creates two realities:

- fixture-based evaluation can detect all calibration categories
- DB-backed route evaluation detects only categories present in `ForbiddenEnergy`

Risk:

Operators may believe the evaluator is broader than it is in DB-backed contexts.

Required future work:

- align seeds with detector categories
- audit category naming
- decide whether all detector categories should become Brand Intelligence records

## Semantic Drift Vectors

Terms that can move the system toward product/growth language:

- campaign
- creator
- audience
- channel
- generation
- request
- accepted
- dashboard
- active
- score
- performance

These words are not banned, but they require boundary definitions.

## Authority Drift Vectors

Fields that can accidentally centralize authority:

- `ReviewItem.status`
- `ApprovalDecision.type`
- `GenerationRequest.status`
- `GenerationOutput.status`
- `GenerationOutputEvaluation.verdict`
- `EvaluationReport.verdict`
- `SignalScore.normalized`

Rule:

No single field should ever authorize execution.

## Cultural Drift Vectors

Risk terms:

- premium lifestyle
- creator economy
- underground community
- drop hype
- limited stock
- viral sound
- trend alert
- shop now
- join us
- unlock
- discover
- personal brand

These should remain red-team inputs, not product language.

## Drift Report Conclusion

The system is currently protected because it is read-only and non-operational.

The strongest drift risks are:

1. treating evaluation as approval
2. treating planning records as execution inputs
3. treating score as performance
4. treating channel work as growth work
5. letting social platform language contaminate the brand system
6. relying on seeded data that is narrower than detector coverage

The next hardening step should clarify authority and terminology before any write-enabled workflow.
