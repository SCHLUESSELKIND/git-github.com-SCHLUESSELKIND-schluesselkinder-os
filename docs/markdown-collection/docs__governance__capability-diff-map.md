# Capability Diff Map

## Purpose

This map freezes what SCHLUESSELKINDER OS can currently do and what it explicitly cannot do.

Any increase in capability must pass governance escalation before implementation.

## Current Capability Surface

### Public Web

- public editorial website
- static public routes
- internal evaluation console gated by environment flag
- no mutation controls
- no external platform actions

### API

- read-only archive endpoints
- read-only brand intelligence endpoints
- read-only content graph endpoints
- read-only review inspection endpoints
- read-only generation inspection endpoints
- read-only evaluation endpoints
- read-only draft package endpoints
- read-only manual export endpoints

All API route registrations are expected to be `GET`.

### Database

- Prisma schema for institutional records
- seed data
- migrations through explicit developer commands
- no runtime write workflows
- no authority mutation API

### Evaluation

- deterministic evaluation functions
- fixture-based calibration
- static governance regression suite
- no provider calls
- no external actions
- no approval authority

### Draft And Manual Export

- portable response bodies
- review snapshots
- evaluation snapshots
- symbolic asset manifests
- manual artifacts as JSON/text strings
- no file writing
- no external transfer
- no workflow action

## Explicit Non-Capabilities

The system currently cannot:

- mutate review state over API
- create approval decisions over API
- call AI providers
- call social platforms
- call commerce providers
- run background jobs
- execute timed workflows
- write export files
- store export packages
- upload assets
- hand off material to external platforms
- optimize for audience acquisition

## Escalation Required

Governance escalation is required before:

- any non-GET route
- any provider SDK
- any worker or queue runtime
- any timed execution runtime
- any external API client
- any auth workflow
- any authority persistence workflow
- any file transfer or storage workflow
- any UI control that mutates institutional state

## Permanently Disallowed

These are not future features:

- autonomous public channel actions
- score-based approval
- evaluation-as-approval
- AI-authored approval decisions
- audience-growth-first optimization
- unofficial social automation
- object archive becoming generic shop infrastructure

## Regression Shield

The governance regression suite must fail when:

- route surface expands beyond GET
- protected dependency classes appear
- authority flags become positive
- boundary literals are missing
- runtime terminology drifts toward operational action
- hidden transfer/storage fields appear

The shield is not a workflow engine. It exists to stop accidental capability drift.
