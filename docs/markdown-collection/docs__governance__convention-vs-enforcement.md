# Convention vs Enforcement

## Purpose

This document separates governance rules that are currently conventions from rules that are technically enforced.

The goal is to avoid false confidence before operational power exists.

## Classification Key

### IMMEDIATE HARDENING

Conventions that should be clarified or tested now.

### PRE-EXECUTION HARDENING

Conventions that must become enforcement before write routes, provider calls, scheduling, posting, workers, or commerce.

### DOCUMENTATION ONLY

Conventions that can remain documented while the system stays read-only.

### ACCEPTABLE AMBIGUITY

Conventions that are tolerable now and do not justify churn.

### PERMANENTLY DISALLOWED

Concepts that must never become implementation goals.

## Enforced Today

### Evaluation Report Authority Flags

Status: enforced by TypeScript types and Zod contracts.

Current guarantees:

- `reviewRequired: true`
- `usableWithoutReview: false`
- `approvalAuthority: false`

Classification: `IMMEDIATE HARDENING`

Reason:

This must remain enforced permanently.

### Read-Only API Routes

Status: currently enforced by route surface.

Current guarantees:

- generation routes are GET only
- review routes are GET only
- evaluation routes are GET only
- content graph routes are GET only
- brand intelligence routes are GET only

Classification: `IMMEDIATE HARDENING`

Reason:

Any write route must be explicitly approved as a governance sprint.

### GenerationOutput Requires ReviewItem

Status: enforced by Prisma schema.

Current guarantee:

- `GenerationOutput.reviewItemId` is required.

Classification: `IMMEDIATE HARDENING`

Reason:

Generated or placeholder material must stay review-bound.

### No `GenerationOutputStatus.APPROVED`

Status: enforced by enum.

Classification: `IMMEDIATE HARDENING`

Reason:

Output material cannot be its own approval source.

## Convention Today

### Append-Only Approval Decisions

Status: documented convention.

Current gap:

Future code could update or delete decisions unless explicitly prevented.

Classification: `PRE-EXECUTION HARDENING`

Required before writes:

- no update route for decisions
- no delete route for decisions
- database or repository policy for immutable records
- correction records instead of mutation

### ReviewItem.status Is Not Full Approval Truth

Status: documented convention.

Current gap:

Future code could check only `ReviewItem.status`.

Classification: `PRE-EXECUTION HARDENING`

Required before writes:

- transition policy
- decision history check
- actor identity
- status and decision consistency validation

### PASS Is Not Approval

Status: enforced in report text and tests, but still culturally vulnerable.

Current gap:

Future UI or workflow code could treat `PASS` as success.

Classification: `IMMEDIATE HARDENING`

Required:

- keep visual treatment restrained
- test no route uses `PASS` as execution gate
- document PASS as inspection-only everywhere

### Score Is Not Truth

Status: documented convention.

Current gap:

Future UI can overemphasize score.

Classification: `IMMEDIATE HARDENING`

Required:

- score display policy
- findings-first report layout
- no score thresholds for workflow

### Subject Key Normalization

Status: documented convention.

Current gap:

Seeds mix raw domain codes and prefixed review keys.

Classification: `IMMEDIATE HARDENING`

Required:

- define canonical subject key mapping
- decide whether raw domain codes remain allowed for `MusicRelease`
- prevent future alternate forms

### Detector And Seed Alignment

Status: partially enforced by fixtures, not aligned with DB seed.

Current gap:

Detector terms exceed seeded `ForbiddenEnergy`.

Classification: `IMMEDIATE HARDENING`

Required:

- align seed records or document detector-only categories
- ensure DB-backed evaluation and fixture-backed evaluation share expected coverage

### Stored Evaluation Records Are Not Approval

Status: documented convention.

Current gap:

Model naming and route exposure can imply authority.

Classification: `IMMEDIATE HARDENING`

Required:

- label as inspection records in docs and UI
- never show beside approval without explicit boundary text

### Internal Console Is Not Admin Platform

Status: UI/design convention.

Current gap:

Route path and future needs can pull it toward admin workflows.

Classification: `PRE-EXECUTION HARDENING`

Required before production:

- access control strategy
- no action controls
- no workflow mutations
- consider route naming hardening

## Documentation Only For Now

### Score Axis Precision

Status: known limitation.

Classification: `DOCUMENTATION ONLY`

Reason:

The score model is coarse but safe while non-operational.

### Graph Validation Completeness

Status: known limitation.

Classification: `DOCUMENTATION ONLY`

Reason:

Graph checks are visible. More enforcement should wait for a specific validation sprint.

### `PromptSection` Naming

Status: acceptable planning name with docs.

Classification: `ACCEPTABLE AMBIGUITY`

Reason:

There is no provider execution and docs say sections are not provider-ready prompts.

## Permanently Disallowed

These must never move from convention to implementation:

- evaluator approves content
- score triggers publishing
- worker posts without human review
- AI writes approval decisions
- social metrics override brand constraints
- archive status implies commerce availability
- internal console becomes growth dashboard

Classification: `PERMANENTLY DISALLOWED`

## Enforcement Roadmap

Before any write-enabled workflow:

1. Enforce append-only decisions.
2. Define status transition policy.
3. Require actor identity.
4. Validate status and decision consistency.
5. Keep evaluation reports advisory.
6. Keep stored evaluations as inspection records.
7. Prevent score-based gates.
8. Protect internal console access.

Before any provider-enabled workflow:

1. Add provider boundary contract.
2. Add secret isolation.
3. Add dry-run mode.
4. Add review-bound output quarantine.
5. Prove no provider output can publish directly.

## Conclusion

The current system is safe because operational capability is absent.

The next risk is not missing functionality.
The next risk is confusing convention for enforcement.
