# Permanent Non-Goals

## Purpose

This document defines concepts that SCHLUESSELKINDER OS must not implement.

These are not deferred features.
They are permanent boundaries.

## Permanently Disallowed Concepts

### Autonomous Publishing

Classification: `PERMANENTLY DISALLOWED`

The system must never publish without human approval.

Disallowed:

- auto-posting after evaluation pass
- scheduled posting without schedule review
- provider callbacks that publish on completion
- background workers that move material to public channels

### Score-Based Approval

Classification: `PERMANENTLY DISALLOWED`

The system must never approve material based on score.

Disallowed:

- score threshold approval
- high-score scheduling
- no-finding approval
- grade-based publishing
- automated promotion from `PASS`

### AI Approval Decisions

Classification: `PERMANENTLY DISALLOWED`

AI may never approve.

AI may later propose, evaluate, or flag.
Human governance remains the authority layer.

Disallowed:

- AI-written `ApprovalDecision`
- AI-mutated `ReviewItem.status`
- AI-generated final approval rationale
- AI override of reviewer decisions

### Engagement-First Optimization

Classification: `PERMANENTLY DISALLOWED`

The system must not optimize brand outputs for engagement before identity.

Disallowed as primary metrics:

- CTR
- reach
- virality
- watch time
- follower growth
- conversion velocity
- posting frequency

If performance metrics are introduced later, they must be secondary to brand constraints.

### Social Autopilot

Classification: `PERMANENTLY DISALLOWED`

Social integrations may never become autonomous campaign operators.

Disallowed:

- trend-chasing automation
- viral-sound selection
- caption autopilot
- automatic hashtag strategy
- auto-reply growth loops
- platform-native growth hacks

### Unofficial Scraping Automation

Classification: `PERMANENTLY DISALLOWED`

No unofficial scraping or brittle social automation.

Disallowed:

- browser-driven fake posting
- credential scraping
- unofficial social API use
- automated interaction loops
- account behavior that risks platform integrity

### Commerce Contamination Of Archive

Classification: `PERMANENTLY DISALLOWED`

The object archive must not become generic merch infrastructure.

Disallowed:

- Shopify
- WooCommerce
- generic merch-shop language
- stock urgency copy
- fake scarcity
- buyability inferred from `ReleaseStatus.ACTIVE`
- checkout controls inside archive semantics

Stripe and Printful may exist later only as explicitly bounded modules.

### Creator Economy Reframing

Classification: `PERMANENTLY DISALLOWED`

SCHLUESSELKINDER OS is not a creator platform.

Disallowed:

- creator dashboard framing
- audience growth workflows
- monetization playbooks
- personal brand tooling
- content calendar productivity framing
- engagement funnel language

### Dashboard KPI Culture

Classification: `PERMANENTLY DISALLOWED`

The system must not become a growth analytics product.

Disallowed:

- KPI dashboards centered on reach
- virality ranking
- conversion funnels as primary views
- social performance leaderboards
- content velocity reports

Inspection surfaces may show governance data only.

### Review Bypass

Classification: `PERMANENTLY DISALLOWED`

No material may move from proposal to execution without review.

Disallowed:

- evaluator pass as review substitute
- generated output as usable content
- schedule execution without schedule review
- provider output directly entering public channels

## Concepts Allowed Only With Hard Boundaries

These are not permanently disallowed, but require pre-execution hardening:

- AI provider adapters
- social posting APIs
- scheduling
- worker queues
- Stripe checkout
- Printful fulfillment
- analytics ingestion
- write-enabled review workflows

None of these may be implemented as convenience features.

## Permanent Language Bans

Avoid these as product/system language:

- autopilot
- viral
- growth hack
- creator studio
- campaign manager
- publish automatically
- optimize reach
- maximize engagement
- shop now
- unlock community
- content machine

These may appear only in red-team fixtures or forbidden-language docs.

## Permanent Boundary Statements

- Evaluation is not approval.
- Recommendation is not authority.
- Review is not execution.
- Score is not truth.
- Console is not an admin platform.
- Archive is not a generic shop.
- Channel work is not growth work.
- AI assistance is not governance authority.

## Conclusion

Permanent non-goals protect the cultural system from becoming a generic automation platform.

The safest future architecture is one where operational modules remain subordinate to:

- identity
- constraints
- graph coherence
- human review
- audit history
- institutional restraint
