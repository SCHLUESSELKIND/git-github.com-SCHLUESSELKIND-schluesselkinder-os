# Claude Code Handoff: SNUFFRAGA SOUNDSYSTEM

## Workspace

```bash
cd /Users/thomasfrerich/schluesselkinder-os
```

## Read First

1. `AGENTS.md`
2. `docs/soundsystem/sound-model.md`
3. `docs/soundsystem/operator-console.md`
4. `docs/soundsystem/prompt-engine.md`
5. `docs/soundsystem/generation-pipeline.md`
6. `services/soundsystem-inference/README.md`
7. `apps/web/app/admin/soundsystem/`

## Current State

SNUFFRAGA SOUNDSYSTEM is an internal, stem-first AI music operating system slice inside the SCHLUESSELKINDER OS monorepo.

Implemented in this branch:

- Internal architecture pack under `docs/soundsystem/`.
- `SNUFFRAGA SOUNDGRAPH` model definition.
- FastAPI inference scaffold under `services/soundsystem-inference/`.
- In-memory generation job repository.
- Mock-only provider registry.
- Two-call provider contract: `start()` then `get_status()`.
- Prompt compiler with safety notes.
- Mock artifact generation for local tests.
- Initial Postgres/pgvector SQL artifact.
- Internal Next.js operator console under `/admin/soundsystem`.
- Soundsystem design tokens exported from `@schluesselkinder/brand/soundsystem-tokens.css`.
- Markdown collection at `docs/markdown-collection/` for review/context handoff.

## Non-Negotiable Boundaries

- No live external provider calls yet.
- No Redis/BullMQ yet.
- No Dropbox implementation yet.
- No Supabase client wiring yet.
- No RunPod launcher yet.
- No Stripe, Clerk, commerce, checkout, Printful, Shopify, or social automation.
- No unauthorized artist cloning.
- No voice likeness without explicit clearance.
- No fake rights claims.
- No destructive stem overwrite.

## Product Model

Do not build a Suno clone.

The intended model is:

```text
Prompt -> Stem Plan -> Generated Takes -> Editable Stem Graph -> Mix/Export
```

The full stereo mix is an artifact. The source of truth is the editable SoundGraph:

- prompt versions
- tempo map
- arrangement sections
- stem lanes
- regions
- effect racks
- automation
- generation takes
- safety reports
- export packages

Required lanes:

- `kick`
- `drums`
- `percussion`
- `bass`
- `music`
- `lead`
- `vocals_main`
- `vocals_adlibs`
- `fx`
- `atmosphere`
- `return_delay`
- `return_reverb`

The user must be able to ask:

```text
Only change the bass.
Only change the percussion.
Only change the hook vocal.
Keep everything else locked.
```

Edits must create new takes, not overwrite existing material.

## Local Build

Install dependencies:

```bash
pnpm install
```

Check the TypeScript monorepo:

```bash
pnpm typecheck
pnpm build
```

Check the Python inference service:

```bash
cd /Users/thomasfrerich/schluesselkinder-os/services/soundsystem-inference
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m compileall app
pytest
```

Run local services:

```bash
# Terminal 1
cd /Users/thomasfrerich/schluesselkinder-os
pnpm dev:web

# Terminal 2
cd /Users/thomasfrerich/schluesselkinder-os
pnpm dev:api

# Terminal 3
cd /Users/thomasfrerich/schluesselkinder-os/services/soundsystem-inference
source .venv/bin/activate
uvicorn app.main:app --reload --port 8010
```

Operator console is gated by:

```bash
NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=true
```

Open:

```text
/admin/soundsystem
```

## Suggested Next Patch

Implement the first real SoundGraph data layer in the Python inference service while keeping everything mock/local.

Tasks:

1. Add typed schema models:
   - `StemLaneType`
   - `StemSourceType`
   - `EffectDeviceType`
   - `TempoControls`
   - `DruckControls`
   - `EffectRack`
   - `StemLanePlan`
   - `StemPlan`
   - `SoundGraphManifest`

2. Extend `GenerationRequest` with optional:
   - tempo controls
   - druck controls
   - requested effect devices
   - target lane
   - locked lanes

3. Extend prompt compilation so it returns:
   - compiled prompt text
   - negative prompt
   - safety notes
   - engine hints
   - stem plan
   - tempo metadata
   - druck metadata
   - effect rack suggestions

4. Extend `MockMusicProvider` so its artifact paths include all required stem lanes.

5. Add a `stem_manifest_json` artifact path.

6. Add tests for:
   - default stem plan contains all required lanes
   - tempo, druck, and effect devices survive prompt compilation
   - locked lanes are accepted by request schema
   - mock generation returns all required stem paths
   - capabilities still expose mock provider health

## Claude Code Prompt

```text
You are Claude Code running with Opus Max.

Workspace:
cd /Users/thomasfrerich/schluesselkinder-os

Read first:
- AGENTS.md
- docs/soundsystem/claude-code-handoff.md
- docs/soundsystem/sound-model.md
- docs/soundsystem/prompt-engine.md
- docs/soundsystem/generation-pipeline.md
- services/soundsystem-inference/
- apps/web/app/admin/soundsystem/

Goal:
Implement the next internal SNUFFRAGA SOUNDGRAPH data layer.

Constraints:
- This is internal-only.
- Do not build a Suno clone.
- No live external API calls.
- No Redis/BullMQ.
- No Dropbox/Supabase/RunPod implementation yet.
- No Stripe, Clerk, commerce, Printful, Shopify, or social automation.
- No unauthorized artist or voice likeness cloning.
- Keep all behavior mock/local.
- Preserve existing user changes.

Implementation:
1. Extend the Python inference schemas with SoundGraph stem, tempo, druck, and effect-rack models.
2. Extend GenerationRequest with optional tempo/druck/effects/target-lane/locked-lanes.
3. Extend prompt compilation output with stem plan, tempo metadata, druck metadata, and effect rack suggestions.
4. Extend MockMusicProvider to return all required stem lane paths plus a stem manifest path.
5. Add focused pytest coverage for the new model behavior.
6. Update README/docs only if the new behavior needs explanation.

Validation:
- python -m compileall services/soundsystem-inference/app
- pytest services/soundsystem-inference/tests
- pnpm typecheck
- pnpm build
- git diff --check

Before final response:
- Review your own diff.
- List changed files.
- Mention tests run.
- Mention risks and follow-up work.
```

## Last Known Validation

These checks were run successfully before handoff:

```bash
python3 -m compileall -q services/soundsystem-inference/app
pytest services/soundsystem-inference/tests
pnpm typecheck
pnpm build
git diff --check
```

`pnpm build` produced `/admin/soundsystem`, `/admin/soundsystem/[action]`, and `/admin/soundsystem/manifest.webmanifest` routes successfully.
