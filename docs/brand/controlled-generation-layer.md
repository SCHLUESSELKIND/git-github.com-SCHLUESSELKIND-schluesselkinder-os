# Controlled Generation Layer

## Purpose

Sprint 8 creates the backend planning layer for constrained AI-assisted generation.

It does not call AI providers, execute prompts, generate media, schedule posts, publish content, or automate any workflow.

The layer converts:

- Brand Intelligence
- Content Graph
- Approval Governance
- Track and release context
- Channel rules

into controlled generation briefs, constraint bundles, placeholder requests, review-bound placeholder outputs, and stored evaluation records.

## Boundary

Allowed:

- prompt and brief composition records
- generation request records
- generation output placeholder records
- constraint bundles
- channel-specific composition profiles
- stored rule evaluation records
- forbidden-energy detection records
- binding outputs to `ReviewItem`
- read-only inspection APIs

Not allowed:

- external AI integration
- real prompt execution
- uploads
- file generation
- media rendering
- social APIs
- scheduler
- cron jobs
- autopublish
- admin UI
- auth
- commerce
- workers
- execution logic

## Approval Truth

`GenerationOutput` is never its own approval source.

Approval truth lives only in:

- `ReviewItem`
- `ApprovalDecision`

`GenerationOutput.status` describes review-bound material state only:

- `GENERATED_PLACEHOLDER`
- `REVIEW_REQUIRED`
- `REVIEW_REJECTED`
- `REVIEW_ARCHIVED`

There is intentionally no `APPROVED` output status.

## Required Review Binding

Every `GenerationOutput` requires a `reviewItemId`.

This prevents unreviewed outputs from becoming usable and keeps all future generation artifacts inside the human governance layer.

## Generator Inputs

A future generator may see only normalized, review-safe inputs:

- artist, track, and release metadata
- campaign worlds
- mood references
- visual environments
- symbolic asset `referenceKey` values
- fragments and channel fragments
- Brand Intelligence rules
- Content Graph compatibility
- Channel rules
- Review context through `ReviewItem`

It must not see:

- secrets
- raw environment values
- credentials
- provider tokens
- upload paths
- storage metadata
- social account tokens
- arbitrary repository content

## Constraint Bundles

`ConstraintBundle` groups mandatory generation constraints.

Initial bundle:

- `CB-SK-CORE-GENERATION`

Constraint sources:

- `BRAND_RULE`
- `VISUAL_RULE`
- `LANGUAGE_RULE`
- `FORBIDDEN_ENERGY`
- `CHANNEL_RULE`
- `SIGNAL_SCORING_RULE`
- `CONTENT_GRAPH_COMPATIBILITY`
- `REVIEW_GOVERNANCE`
- `MANUAL`

Constraints are data records. They are not executable validators yet.

## Prompt Sections

`PromptSection` stores controlled brief sections.

These are not provider-ready prompt payloads. They are planning records that describe which context and constraints future generation must include.

Prompt sections should stay direct and operational.

Avoid:

- provider-specific instructions
- model names
- token settings
- hidden chain instructions
- executable prompt payloads

## Channel Composition

`ChannelCompositionProfile` defines channel-specific output shape.

Examples:

- `CCP-WEBSITE-INSTITUTIONAL`
- `CCP-INSTAGRAM-FRAGMENT`

These profiles define structure and tone, not posting behavior.

## Evaluation Records

`GenerationOutputEvaluation` stores findings against constraints.

Sprint 8 does not run evaluators. It only stores evaluation records.

Evaluation detail must be clear and operational:

- `Chair environment is present as required campaign-world anchor.`
- `Ropeface must remain secondary and cannot become institutional identity.`

Avoid art criticism, atmospheric language, or vague creative notes.

## API Surface

Read-only routes:

- `GET /generation`
- `GET /generation/briefs`
- `GET /generation/briefs/:briefKey`
- `GET /generation/constraint-bundles`
- `GET /generation/channel-composition-profiles`
- `GET /generation/requests`
- `GET /generation/requests/:requestKey`
- `GET /generation/outputs`
- `GET /generation/outputs/:outputKey`
- `GET /generation/outputs/:outputKey/evaluations`

No write routes exist in Sprint 8.

## Non-Goals

- No AI provider SDKs.
- No real generation.
- No prompt execution.
- No media generation.
- No file output.
- No scheduler.
- No posting.
- No workers.
- No execution logic.
- No auth.
- No admin UI.
- No commerce.
