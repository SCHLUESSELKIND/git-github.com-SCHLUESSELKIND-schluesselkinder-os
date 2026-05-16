# Brand Intelligence System

## Purpose

The Brand Intelligence System turns SCHLUESSELKINDER strategy into machine-readable backend rules for the future Signal Engine.

Sprint 5 does not score, generate, schedule, publish, automate, or integrate with external platforms. It only stores the rules that future campaign work must pass before approval.

## Concept Boundaries

Audience psychology is who the system resonates with.

Voice profiles are how the system speaks.

Rules define what the engine may or may not do.

Scoring rules define how future outputs will be evaluated.

## Audience Psychology

Audience personas describe emotional state, aesthetic attraction, behavior, rejection patterns, and resonance. They are not marketing segments and not ad targeting profiles.

Seed personas:

- `POST_CLUB_ISOLATION`
- `ARCHIVE_MINDED_UNDERGROUND_OBSERVER`
- `EMOTIONALLY_RESTRAINED_MUSIC_OBSESSIVE`
- `BRUTALIST_FASHION_MINIMALIST`
- `AFTERHOURS_ROMANTICISM_WITHOUT_SOFTNESS`

These records answer:

- Who feels the signal?
- What state are they in?
- What visual and musical pressure attracts them?
- What tone breaks credibility?
- Why does SCHLUESSELKINDER resonate?

## Voice Profiles

Voice profiles define system speech modes. They are not audience personas.

Seed profiles:

- `MASTERBRAND`: institutional SCHLUESSELKINDER voice.
- `FIRST_ARTIST`: SHIBARI KAWAII dossier voice.
- `OBJECT_ARCHIVE`: closed object archive voice.

These records answer:

- Which part of the system is speaking?
- How cold, sparse, and institutional should the language be?
- Which mode should future campaign text inherit?

## Rules

Rules are hard constraints and directional checks for generated campaign ideas, captions, visuals, and posts.

Rule groups:

- `BrandRule`: core identity rules.
- `VisualRule`: image, symbol, layout, and motif rules.
- `LanguageRule`: copy, vocabulary, and rhythm rules.
- `ForbiddenEnergy`: high-risk drift patterns.
- `ChannelRule`: channel-specific behavior boundaries.

Severity:

- `REQUIRED`: must pass.
- `WARNING`: allowed only with review.
- `DISCOURAGED`: tolerated only when explicitly justified.

## Scoring Rules

Signal scoring rules define the future evaluation frame. Sprint 5 stores the rules but does not execute scoring.

Future outputs should be evaluated for:

- iconic restraint
- chair/rune protection
- language sparsity
- forbidden-energy avoidance
- cultural credibility
- tension without noise

Future scoring must not override human approval. It should surface findings before approval, not publish anything.

## Non-Goals

- No AI generation.
- No scoring execution.
- No campaign engine.
- No TikTok or Instagram integration.
- No Spotify or SoundCloud integration.
- No Stripe or Printful.
- No automation.
- No admin UI.
- No publishing.

## API Surface

Read-only routes:

- `GET /brand-intelligence`
- `GET /brand-intelligence/rules`
- `GET /brand-intelligence/visual-rules`
- `GET /brand-intelligence/language-rules`
- `GET /brand-intelligence/forbidden-energy`
- `GET /brand-intelligence/audience-personas`
- `GET /brand-intelligence/voice-profiles`
- `GET /brand-intelligence/channel-rules`
- `GET /brand-intelligence/scoring-rules`

## Approval Principle

The future campaign engine must never publish from generated output alone.

Every campaign path remains:

Track or object signal.
Moodboard proposal.
Human approval.
Content proposal.
Human approval.
Schedule review.
Publish only after approval.
