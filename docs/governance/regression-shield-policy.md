# Regression Shield Policy

## Purpose

The regression shield converts governance boundaries into failing tests.

It is not an operational policy runtime.

It is not a workflow engine.

It is a static guard against accidental drift.

## Shield Scope

The shield checks:

- route surface
- dependency surface
- authority flags
- boundary literals
- frozen terminology in runtime surfaces
- hidden transfer/storage fields
- capability diff

## Protected Runtime Surfaces

The initial protected surfaces are:

- `services/api/src/contracts`
- `services/api/src/routes`
- `services/api/src/drafts`
- `services/api/src/exports`

These are the current places where inspection surfaces can drift into action semantics.

## Explicit Exclusions

The shield may exclude:

- governance documentation
- risk matrices
- forbidden-language documentation
- detector fixtures
- red-team calibration cases
- tests that intentionally construct forbidden strings for assertions

Exclusions must exist to preserve detection and documentation, not to hide capability drift.

## Fail-Fast Rules

The shield must fail on:

- non-GET route registration
- protected provider dependency
- worker or timed execution dependency
- storage or transfer dependency
- positive authority flag
- missing boundary literal
- frozen runtime terminology
- hidden transfer/storage field
- score-as-truth phrasing
- PASS-as-approval phrasing
- package/export-as-action phrasing

## Maintenance Rules

When a new inspection surface is added:

1. Add it to protected roots.
2. Add boundary literals.
3. Add terminology rules.
4. Add authority leak tests.
5. Document allowed exceptions.

When a new operational capability is proposed:

1. Do not weaken the shield.
2. Add escalation docs first.
3. Expand the shield before implementing capability.
4. Keep permanent non-goals permanent.

## Conclusion

The shield should make misuse harder.

It should not make the system more powerful.
