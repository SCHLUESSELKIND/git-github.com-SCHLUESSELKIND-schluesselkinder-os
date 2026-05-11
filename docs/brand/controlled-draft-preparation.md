# Controlled Draft Preparation

Sprint layer: controlled draft preparation.

Purpose: convert existing generation briefs and review-bound generation output placeholders into manually copyable draft packages. This layer prepares material for human inspection only. It does not approve, deliver, queue, or authorize public use.

## Boundary Literals

Every draft response must carry these literals:

- `reviewRequired: true`
- `approvalAuthority: false`
- `publishAuthority: false`
- `humanCommitRequired: true`
- `automationAllowed: false`
- `externalDelivery: false`

Every manual export artifact must carry:

- `manualExportPrepared: true`
- `publishReady: false`
- `humanCommitRequired: true`

The legacy readiness field name is intentionally disallowed. Manual preparation must not drift into readiness language.

## Scope

Allowed:

- draft packages
- channel proposals
- manual export artifacts
- review summaries
- constraint summaries
- read-only inspection routes
- deterministic formatting

Disallowed:

- Prisma models
- persistence
- database writes
- mutation routes
- provider SDKs
- generation calls
- prompt execution
- workers
- cron processes
- social APIs
- auth
- admin workflows
- performance metrics
- audience acquisition optimization

## Routes

- `GET /drafts/health`
- `GET /drafts/packages/generation-outputs/:outputKey`
- `GET /drafts/packages/generation-briefs/:briefKey`

There are no `POST`, `PUT`, `PATCH`, or `DELETE` routes in this layer.

## Package Shape

A draft package includes:

- source key
- subject key
- channel
- review summary
- constraint summary
- stored evaluation summary
- channel proposal
- manual export artifacts

The stored evaluation summary is informational only. A `PASS` verdict means no blocking evaluation finding was stored for the referenced material. It does not mean approval.

Approval truth remains only in:

- `ReviewItem`
- append-only `ApprovalDecision`

Draft packages never create approval truth.

## Human Commit Boundary

Manual export artifacts exist so a human can inspect and copy material into another controlled process. The package cannot contact an external channel and cannot trigger delivery.

Required distinctions:

- evaluation does not equal approval
- recommendation does not equal authority
- draft does not equal accepted content
- manual export does not equal public readiness
- score does not equal truth

## Terminology

Use:

- draft
- proposal
- package
- manual export
- review summary
- constraint summary

Avoid operational readiness terms that imply external delivery, timed release, autonomous operation, or audience acquisition.

The field names `publishAuthority` and `publishReady` exist only as explicit negative controls.
