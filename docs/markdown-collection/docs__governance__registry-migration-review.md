# Registry Migration Review

## Status

Migration SQL generated for review only.

Not applied.

The Registry Foundation migration remains pending until a separate explicit apply approval is given.

## Generation Method

The SQL was generated via `prisma migrate diff` because `prisma migrate dev --create-only` is blocked in the non-interactive Codex environment.

No production database was used.
No production database URL was assumed.
No substitute production-like database was invented.

The local development database used for diff generation was:

```text
postgresql://<local-user>@localhost:5432/schluesselkinder_dev
```

The existing baseline migrations were applied to that local development database before the diff was generated. The new Registry Foundation migration was not applied.

## Migration File

```text
packages/db/prisma/migrations/20260511000000_registry_foundation_references/migration.sql
```

## SQL Review Findings

- additive only
- no `DROP`
- no `RENAME`
- no `INSERT`
- no seed data
- no provider URLs
- nullable `artistKey`
- nullable `trackKey`
- `sourceAuthority` defaults to `false`
- `SUPERSEDES` is absent

Created enums:

- `Platform`
- `VerificationState`
- `ChannelVisibility`
- `LineageType`

Created tables:

- `ChannelPresence`
- `ExternalReference`
- `DistributionReference`
- `MusicReleaseLineage`
- `TrackLineage`

Altered existing tables:

- `Artist` receives nullable `artistKey`
- `Track` receives nullable `trackKey`

The migration contains no fake SoundCloud or Spotify URLs. SoundCloud and Spotify only appear as `Platform` enum values.

## Manual Exclusion

The raw Prisma diff produced an out-of-scope `RenameIndex` operation for `CampaignWorldVisualEnvironment`.

It was intentionally excluded because it is unrelated to Registry Foundation and would introduce unnecessary migration drift.

Excluded operation:

```sql
ALTER INDEX "CampaignWorldVisualEnvironment_campaignWorldId_visualEnvironmen"
RENAME TO "CampaignWorldVisualEnvironment_campaignWorldId_visualEnviro_key";
```

This exclusion keeps the Registry Foundation migration limited to the approved additive scope.

## Remaining Guardrails

`ExternalReference` still requires a later one-target enforcement strategy before any write path exists.

Intended invariant:

```text
one ExternalReference -> exactly one target entity
```

Current migration does not add a database check constraint for this rule because that constraint was not part of the approved Phase 3A SQL generation scope.

`sourceAuthority` is defaulted to `false`, but future write paths must still prevent it from becoming provider authority.

## Apply Gate

Do not apply until explicitly approved.

Pending next decision:

```text
Dev-apply Registry Foundation migration: yes/no
```

If approved later, apply only to the local/dev PostgreSQL database first. Do not apply to production or deployment databases in this phase.
