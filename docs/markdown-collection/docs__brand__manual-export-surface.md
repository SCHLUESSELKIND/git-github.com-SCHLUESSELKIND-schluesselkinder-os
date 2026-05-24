# Manual Export Surface

Sprint layer: manual export surface.

Purpose: assemble portable inspection packages from existing review-bound material. The surface prepares structured JSON and text bundles for a human operator to inspect outside the API.

Manual export means portable inspection only.

It does not create public authority, platform handoff, timed release, external transfer, file output, or workflow action.

## Boundary Literals

Every response and export object must carry:

- `reviewRequired: true`
- `approvalAuthority: false`
- `publishAuthority: false`
- `humanCommitRequired: true`
- `automationAllowed: false`
- `externalDelivery: false`
- `manualExportPrepared: true`
- `portableArtifactOnly: true`
- `distributionAuthority: false`
- `publishReady: false`

`publishReady: false` is permitted only as a negative control.

## Routes

- `GET /exports/health`
- `GET /exports/packages/generation-outputs/:outputKey`
- `GET /exports/packages/generation-briefs/:briefKey`
- `GET /exports/review-snapshots/:reviewKey`

There are no mutation routes in this layer.

## Package Contents

An export package contains:

- review snapshot
- evaluation snapshot
- constraint snapshot
- asset manifest
- portable JSON bundle
- portable text bundle
- manual artifacts

The package is a response body only. The server does not write files, create archives, persist export records, or contact external systems.

## Asset Manifest

The asset manifest is symbolic only.

Allowed fields:

- asset code
- title
- source type
- reference key
- campaign world relation
- compatibility verdict

Disallowed fields:

- filesystem paths
- transfer targets
- CDN locations
- storage service names
- media measurement fields
- binary inspection metadata
- external destinations
- background process identifiers
- repeat attempt states
- platform action fields
- audience metric fields

## Snapshot Semantics

Review snapshot:

- shows review state and append-only decision history
- does not create approval
- carries `snapshotImpliesApproval: false`

Evaluation snapshot:

- shows stored evaluation findings
- does not define truth
- carries `snapshotImpliesTruth: false`
- carries `passImpliesApproval: false`

Constraint snapshot:

- shows active constraint instructions
- does not unlock action

Asset manifest:

- shows symbolic content graph references
- does not point to files or platforms

## Required Distinctions

- exported does not equal authorized
- portable does not equal public
- review snapshot does not equal approval
- evaluation snapshot does not equal truth
- manual export does not equal external transfer
- package existence does not equal permission

## Permanent Boundaries

This layer must not add:

- Prisma models
- schema changes
- persistence
- database writes
- mutation routes
- external calls
- file writing
- provider SDKs
- social APIs
- timed release logic
- public channel handoff
- background jobs
- cron processes
- auth workflows
- admin workflows
- commerce

## Terminology

Use:

- manual export
- review package
- snapshot
- bundle
- portable artifact
- asset manifest
- human commit required

Avoid operational language that implies external transfer, public use, platform handoff, or autonomous action.

The field names `publishAuthority`, `publishReady`, `externalDelivery`, and `distributionAuthority` exist only as explicit negative controls.
