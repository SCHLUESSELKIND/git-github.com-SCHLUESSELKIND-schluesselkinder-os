# Registry Schema Patch Review

## Status

Schema patch prepared.

No migration has been generated.
No migration has been applied.
No seed data has been changed.
No runtime API code has been changed.
No route has been added.
No provider integration has been added.

This document is the migration-readiness review for the approved additive registry foundation schema patch.

## Additive Changes Prepared

Changed file:

- `packages/db/prisma/schema.prisma`

Additive identity hardening:

- added optional `Artist.artistKey String? @unique`
- added optional `Track.trackKey String? @unique`

Additive enums:

- `Platform`
- `VerificationState`
- `ChannelVisibility`
- `LineageType`

`LineageType` currently includes:

- `ORIGINAL`
- `VARIANT`
- `EDIT`
- `MIX`
- `REMIX`
- `REMASTER`
- `FRAGMENT`
- `RELATED`

`SUPERSEDES` is intentionally excluded. Supersession remains a later historical governance layer, not part of Proposal 1.

Additive model candidates now present in schema:

- `ChannelPresence`
- `ExternalReference`
- `DistributionReference`
- `MusicReleaseLineage`
- `TrackLineage`

Existing canonical models were reused:

- `Artist`
- `MusicRelease`
- `Track`

No duplicate `Release` model was introduced.

## Why No Migration Was Applied

The patch is a prepared schema change only.

Migration remains blocked because the next gate must explicitly approve database changes. This preserves the current governance sequence:

```text
proposal -> schema patch review -> migration approval -> migration generation -> migration review -> migration apply
```

No migration should be generated or applied until the approval question at the end of this document is answered.

## Prisma Validate Result

Command run:

```bash
DATABASE_URL='postgresql://user:pass@localhost:5432/schluesselkinder' pnpm --filter @schluesselkinder/db exec prisma validate
```

Result:

```text
The schema at prisma/schema.prisma is valid
```

Note:

The originally requested command below does not work in this repository because `@schluesselkinder/db` has no `prisma` package script:

```bash
pnpm --filter @schluesselkinder/db prisma validate
```

The equivalent `pnpm --filter @schluesselkinder/db exec prisma validate` path was used instead.

Observed warning:

- `package.json#prisma` configuration is deprecated and should eventually move to a Prisma config file.

This warning is unrelated to the registry schema patch.

## Migration Generation Blocker

Migration generation was attempted only after approval, but did not complete because no local/dev `DATABASE_URL` was available.

No production database URL was assumed.
No substitute database was invented.
No Docker fallback was possible in this environment.

Result:

- no migration folder was created
- no migration was applied
- schema patch remains pending
- next attempt requires a local or dev PostgreSQL `DATABASE_URL`

Approved retry shape once a local/dev database is available:

```bash
DATABASE_URL='postgresql://<dev-user>:<dev-pass>@<dev-host>:<dev-port>/<dev-db>' \
pnpm --filter @schluesselkinder/db exec prisma migrate dev --name registry_foundation_references
```

## Test And Build Result

Commands run:

```bash
pnpm test
pnpm build
```

Results:

- `pnpm test` passed.
- `pnpm build` passed.

The build still lists admin routes as dynamic web routes. Admin exposure remains a separate runtime/governance issue and was not changed in this schema patch.

## One-Target Limit Of ExternalReference

`ExternalReference` currently supports optional links to:

- `Artist`
- `MusicRelease`
- `Track`
- `ObjectRelease`
- `ChannelPresence`

Intended invariant:

```text
one ExternalReference -> exactly one target entity
```

Current limitation:

Prisma schema shape alone does not enforce "exactly one nullable target is set" across multiple optional relation columns.

Required before writes are introduced:

- database check constraint in a reviewed migration, or
- strict runtime validator before any mutation path exists, preferably both

Current risk is contained because there are no write routes, no seed changes, no provider imports, and no runtime mutation path for these models.

## sourceAuthority=false Guardrail

`sourceAuthority` is present on:

- `ExternalReference`
- `DistributionReference`

Current default:

```prisma
sourceAuthority Boolean @default(false)
```

Governance invariant:

```text
external platform reference != registry authority
provider capability != provider authority
```

Future enforcement recommendation:

- keep default `false`
- add regression coverage that no seed/runtime path sets it to `true`
- consider a database check constraint if governance decides this field must remain permanently false

This field exists to make the boundary explicit, not to grant providers authority.

## Risks Before Migration

Migration risks to review before generating a migration:

- nullable unique fields create database indexes; confirm target Postgres behavior and expected existing-null handling
- enum creation is additive but still affects generated Prisma Client types
- new relation tables are empty until a controlled backfill or manual registry entry phase exists
- `ExternalReference` one-target invariant is not database-enforced yet
- `DistributionReference` can currently point to either a `MusicRelease` or a `Track`; target rules need approval before writes
- `sourceAuthority` can technically be set to `true` by future writers unless a stronger constraint is added
- no canonical key backfill policy has been applied yet
- no release-key decision was made for `MusicRelease.releaseCode`
- no object key cleanup was performed for `ObjectRelease.releaseId`
- no seed data exists for SoundCloud or Spotify references

Out-of-scope risks intentionally not handled here:

- admin/internal-console exposure
- runtime registry routes
- website embeds
- provider SDKs
- OAuth
- webhooks
- queues
- workers
- analytics
- GPT draft models
- commerce and fulfillment models
- asset upload/storage pipeline

## Approval Checklist Before Migration Generation

Confirm before running any migration command:

- `artistKey` remains optional-first.
- `trackKey` remains optional-first.
- `MusicRelease.releaseCode` remains unchanged.
- `ObjectRelease.releaseId` remains unchanged.
- `SUPERSEDES` remains excluded from `LineageType`.
- no seed data is added.
- no provider URLs, IDs, handles, or fake records are introduced.
- no runtime writes are introduced.
- one-target enforcement strategy is accepted as a post-schema guardrail.
- `sourceAuthority=false` guardrail is accepted.

## Explicit Approval Question

Generate a migration now?

Proposed command only after explicit approval:

```bash
pnpm --filter @schluesselkinder/db exec prisma migrate dev --name registry_foundation_references
```

Until approved, the correct answer is:

```text
No migration generation.
No migration apply.
```
