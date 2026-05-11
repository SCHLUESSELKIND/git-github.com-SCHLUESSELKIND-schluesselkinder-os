# Future Capability Danger Map

## Purpose

This document maps future capabilities by governance danger.

It does not approve implementation.
It defines what must be true before operational power is added.

## Danger Levels

- `GREEN`: low operational danger if kept read-only.
- `YELLOW`: safe only with strict boundaries.
- `ORANGE`: can mutate state or shape external output; requires governance hardening first.
- `RED`: can publish, spend money, expose accounts, or create irreversible external effects.

## Capability Map

| Capability | Danger | Why It Is Dangerous | Required Before Implementation |
| --- | --- | --- | --- |
| Static governance audit docs | GREEN | No runtime effect | None |
| Deterministic audit tests | GREEN | No mutation if pure | Test boundary review |
| Read-only inspection routes | YELLOW | Can expose sensitive internal context | Access strategy before production |
| Internal console views | YELLOW | Can be mistaken for admin control | No action buttons, access boundary |
| Review write routes | ORANGE | Can alter governance state | Auth, append-only enforcement, audit trail |
| Approval decisions | ORANGE | Can authorize future execution | Immutable history, actor identity, status rules |
| RuleViolation write flows | ORANGE | Can shape future decisions | source/ruleCode discipline, no vague findings |
| Provider prompt assembly | ORANGE | Can turn planning records into executable payloads | prompt boundary review, no secrets, review binding |
| AI provider calls | RED | Produces new material and may leak context | provider adapter boundary, red-team pass, no secrets |
| Media generation | RED | Can create publish-like assets | review binding, storage boundary, asset quarantine |
| Scheduler | RED | Creates delayed execution path | approval gate, cancel path, audit trail |
| TikTok/Instagram posting | RED | External public publication | explicit human approval, account scopes, failure states |
| SoundCloud/Spotify integration | ORANGE | Metadata/account authority risk | read-only first, token vault, rate-limit strategy |
| Stripe checkout | RED | Money movement | commerce domain model, webhooks, reconciliation |
| Printful fulfillment | RED | Physical fulfillment and cost | paid-state reconciliation, fulfillment review |
| Worker system | RED | Hidden background execution | job model, idempotency, kill switch, audit logs |
| Cron jobs | RED | Autonomous repeated execution | scheduler governance, explicit dry-run mode |
| Analytics dashboards | ORANGE | Can introduce growth incentives | brand-first metric hierarchy |

## Operational Power Boundaries

No future capability may bypass:

- review binding
- human approval history
- evaluation reports
- forbidden-energy checks
- content graph compatibility
- audit logging
- secret isolation

No future capability may treat these as approval:

- `PASS`
- high score
- no findings
- `GenerationRequest.status`
- `GenerationOutput.status`
- stored evaluation records
- console visibility

## Dangerous First Writes

The first write-enabled workflow is the most important future risk.

Danger signs:

- a route named `approve` without append-only decision history
- a route that updates `ReviewItem.status` without creating `ApprovalDecision`
- a route that creates `GenerationOutput` without `reviewItemId`
- a route that stores provider output without quarantine status
- a route that schedules anything without schedule review
- a route that publishes after evaluator `PASS`

## Execution Readiness Minimums

Before any execution layer exists, the system needs:

1. Auth and actor identity.
2. Append-only approval enforcement.
3. Immutable decision audit trail.
4. Explicit state transition rules.
5. Review binding on every generated artifact.
6. No provider secrets in DB or docs.
7. Dry-run-only provider adapters.
8. Kill switch for workers and schedulers.
9. Human-readable and machine-readable failure states.
10. Proof that `PASS` cannot trigger execution.

## Provider Adapter Risks

AI provider adapter risks:

- leaking brand docs or secrets
- prompt sections becoming executable without review
- generated material treated as usable
- provider output bypassing red-team calibration
- hidden model settings creating inconsistent results

Social provider adapter risks:

- access-token leakage
- accidental posting
- rate-limit failure
- platform language contaminating brand rules
- engagement metrics becoming primary

Commerce provider risks:

- object archive becomes product catalog
- payment state becomes release state
- fulfillment starts without review
- SKU and stock language contaminates public pages

## Centralization Risks

Authority can centralize in:

- one operator account
- one status field
- one score threshold
- one provider adapter
- one scheduler
- one background worker
- one dashboard action

Hard rule:

Operational authority must be distributed across review history, evaluation results, explicit state transitions, and actor identity.

## Capabilities To Delay

Delay until governance is stronger:

- AI provider calls
- image generation
- caption generation
- post scheduling
- social posting
- worker queues
- cron jobs
- approval buttons
- publish buttons
- commerce checkout
- fulfillment automation

## Safe Next Capabilities

Safest next work remains:

- retrospective documentation
- static governance audits
- terminology hardening
- seed/detector alignment planning
- score calibration tests
- graph validation coverage tests
- authority-boundary tests

## Danger Map Conclusion

The architecture is currently strong because it lacks operational power.

The first dangerous capability is not AI generation.
The first dangerous capability is any write path that converts inspection into action.

Future work should continue to add judgment before adding power.
