# Approval + Review System

## Purpose

Sprint 7 adds the human review structure around the Content Graph.

The future Signal Engine must never move from moodboard to content, from content to schedule, or from schedule to publishing without a human approval record.

Sprint 7 stores review intent, comments, violations, and historical decisions only.

## Review Stages

- `MOODBOARD_REVIEW`
- `CONTENT_REVIEW`
- `SCHEDULE_REVIEW`

These stages represent human review gates. They do not execute transitions.

## Review Status

`ReviewItem.status` is the current materialized review state.

- `PENDING`
- `APPROVED`
- `REJECTED`
- `NEEDS_REVISION`
- `ARCHIVED`

Sprint 7 does not implement status transitions. Future authenticated workflows may update this field, but only while preserving decision history.

## Append-Only Decisions

`ApprovalDecision` is the historical decision log.

Approval decisions are append-only by design:

- Do not overwrite decision records.
- Do not delete decision records.
- Do not treat the latest decision as disposable state.
- Do not mutate old decisions to match current status.

The current status lives on `ReviewItem`. The historical record lives in `ApprovalDecision`.

## Review Items

`ReviewItem` is intentionally generic enough to support future moodboards, generated content, schedule plans, and campaigns.

It stores:

- review key
- stage
- current status
- subject type
- subject key
- title
- summary
- optional links to current Sprint 6 graph entities

Known subject links may point to:

- `MusicRelease`
- `Track`
- `CampaignWorld`
- `Asset`
- `ReleaseFragment`
- `ChannelFragment`

Future subject types remain symbolic until their models exist.

## Subject Key Convention

`subjectKey` values must be stable, uppercase, and hyphenated.

Use fixed prefixes:

- `SKM-003` for music releases.
- `CW-ROOM-AFTER-LIGHT` for campaign worlds.
- `AST-RUNE-KEY-SYMBOL` for assets.
- `SKR-MOODBOARD-SKM-003` for review items.

Do not introduce alternate forms such as `skm003`, `SK-M-003`, `release_skm003`, or natural-language labels as keys.

Future AI, scoring, analytics, and integration layers must reference these normalized keys exactly.

## Rule Violations

`RuleViolation` stores source and `ruleCode` without hard foreign keys.

Allowed sources:

- `BRAND_RULE`
- `VISUAL_RULE`
- `LANGUAGE_RULE`
- `FORBIDDEN_ENERGY`
- `CHANNEL_RULE`
- `SIGNAL_SCORING_RULE`
- `CONTENT_GRAPH_COMPATIBILITY`
- `MANUAL`

This keeps the review layer flexible while Brand Intelligence and Content Graph rules continue to evolve.

`RuleViolation.detail` must stay operational and explicit.

Good:

- `Ropeface used as institutional masterbrand symbol.`
- `Channel fragment uses commerce CTA before object archive approval.`
- `Asset combination violates required rune/key hierarchy.`

Avoid:

- poetic art-direction language
- vague creative critique
- atmospheric interpretation
- subjective mood commentary

Future validators and approval histories need clear findings, not criticism prose.

## API Surface

Read-only routes:

- `GET /reviews`
- `GET /reviews/:reviewKey`
- `GET /reviews/stages`
- `GET /reviews/statuses`
- `GET /reviews/:reviewKey/decisions`
- `GET /reviews/:reviewKey/comments`
- `GET /reviews/:reviewKey/violations`

Planned but not implemented:

- `POST /reviews`
- `POST /reviews/:reviewKey/decisions`
- `POST /reviews/:reviewKey/comments`
- `POST /reviews/:reviewKey/violations`

Write routes require future authenticated workflows.

## Non-Goals

- No auth.
- No admin UI.
- No AI generation.
- No prompt generation.
- No scheduling.
- No posting.
- No campaign execution.
- No state transitions.
- No processors.
- No automation.
- No TikTok or Instagram integration.
- No SoundCloud or Spotify integration.
- No Stripe or Printful.
- No mutable approval history.
