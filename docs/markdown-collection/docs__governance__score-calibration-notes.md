# Score Calibration Notes

## Purpose

This document reviews the current signal score model after Sprint 10.5.

The goal is to prevent score misuse before operational power exists.

Scores are not:

- approval
- performance forecasts
- engagement metrics
- reach metrics
- virality metrics
- publishability guarantees
- automation gates

Scores are conservative inspection signals.

## Current Score Model

The evaluator computes eight axes:

- `IDENTITY_PROTECTION`
- `SYMBOLIC_RESTRAINT`
- `INSTITUTIONAL_CONSISTENCY`
- `CULTURAL_CREDIBILITY`
- `PRESSURE_WITHOUT_NOISE`
- `ARCHIVE_COHERENCE`
- `RULE_ADHERENCE`
- `REVIEW_READINESS`

Current behavior:

- each axis has max score `10`
- baseline is `10` when scoring rules exist
- baseline is `8` when no scoring rules exist
- blocker findings subtract `6`
- warning findings subtract `2`
- normalized score is total divided by max
- any blocker makes grade `BLOCKED`

## Strengths

- Simple and deterministic.
- Conservative blockers dominate grade.
- No engagement, reach, CTR, virality, watch time, or follower-growth axes.
- Findings remain more important than score.
- `PASS` still requires review.

## Weaknesses

### Axis Over-Correlation

Forbidden-energy findings degrade:

- identity protection
- cultural credibility
- pressure without noise
- rule adherence

This is directionally correct, but it means many red-team failures produce similar score shapes.

Risk:

Operators may see different failures as equivalent because score profiles are too similar.

### Rule Weights Are Underused

`SignalScoringRule.weight` exists in the database, but the current evaluator uses total active rule weight only to decide baseline.

Risk:

The presence of weights can imply calibration precision that does not exist yet.

### Normalized Score Can Mislead

A report can be `FAIL` and still show a normalized score above 60.

This is acceptable only if operators understand:

- verdict is more important than normalized score
- blocker findings are hard stops
- no score equals approval

Risk:

Future UI could visually privilege score over findings.

### Axis Names Include Interpretive Concepts

These axes are strategically correct but not fully machine-grounded:

- cultural credibility
- pressure without noise
- institutional consistency

Risk:

Future logic may try to automate subjective judgment without enough deterministic signals.

## Calibration Rules

Do:

- treat blockers as hard stops
- inspect finding codes before score
- keep score secondary to review
- assert score ranges in deterministic fixtures
- monitor axis correlation
- require explicit degraded axes in fixtures

Do not:

- optimize score for engagement
- compare scores across channels as performance data
- use score as approval
- use score as publishing readiness
- add social performance to score axes
- add growth metrics to score axes

## Recommended Audit Questions

For each fixture:

1. Which finding caused the verdict?
2. Which rule code dominated?
3. Which axes degraded?
4. Did unrelated axes degrade too?
5. Did the score range stay stable?
6. Is the report still review-bound?
7. Is the result too permissive?
8. Is the result too brittle?

## Score Stability Risks

Risk: detector terms change and scores shift silently.

Guardrail:

- fixture expected score ranges
- expected finding codes
- expected degraded axes

Risk: a new finding source degrades only `RULE_ADHERENCE`.

Guardrail:

- audit `affectsAxis()` whenever adding a source

Risk: warnings accumulate without changing verdict.

Guardrail:

- review warning count thresholds before operational use

Risk: normalized score becomes UI centerpiece.

Guardrail:

- display verdict and dominant finding before score
- label score as inspection only

## Future Calibration Work

Potential future improvements:

- make axis impact explicit per finding
- let findings declare affected axes
- document expected axis behavior by finding code
- distinguish blocker severity from score penalty
- add score profile snapshots for fixture classes
- add conflict score impacts separately from content drift impacts

Do not add these until the current governance audit is accepted.

## Non-Negotiable Boundary

No score may ever mean:

- approved
- publishable
- scheduled
- ready for posting
- commercially ready
- high-performing
- likely to grow

Score means only:

The evaluator found more or fewer governance issues under the current deterministic rule set.
