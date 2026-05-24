# SNUFFRAGA SOUNDSYSTEM Roadmap

The binding slice sequence from "lyrics console under in-memory mock" to
"release pipeline with real providers under `schluesselkinder.de/admin`".

Each slice is intentionally small and produces a contract layer that the
next slice consumes. No slice unblocks itself by skipping safety, license,
or persistence work.

This roadmap supersedes the high-level sketch in
[execution-order.md](./execution-order.md) and the deployment-flavoured
notes in [roadmap-deployment.md](./roadmap-deployment.md) where they
disagree.

## Status Markers

| Marker | Meaning |
| ------ | ------- |
| ✅ shipped       | Code + tests + docs in `main` |
| 🟡 in progress  | Planned and approved; no code yet |
| ⬜ queued       | Approved sequence position, not yet started |
| ⏸  deferred    | Out of scope until prerequisites land |

## Shipped Foundation

| Slice | Surface | Notes |
| ----- | ------- | ----- |
| ✅ S1 | Repo scaffold, ADR-0005 | TypeScript monorepo + Python inference scaffold |
| ✅ S2 | Persistent job repository | `GenerationJobRepository` Protocol + in-memory impl |
| ✅ S3 | SOUNDGRAPH + MASTER BUS contracts | 12-lane stem model, mastering modes, export profiles |
| ✅ S4 | LYRICS ENGINE backend | 7 section types, mock provider, locking, manual edit, selection rewrite |
| ✅ S5 | LYRICS ENGINE UI | 3-column operator console under `/admin/soundsystem/lyrics` |
| ✅ S6 | Selection rewrite UI + local Blob exports | Apply variant flow + downloadable `lyrics.txt` / `lyrics.json` / SoundGraph manifest |
| ✅ S7 | Postgres-backed `LyricsRepository` | Env-selected mode (`in_memory` / `postgres`) + capabilities-exposed, `current_version_id` cache, fail-loud |
| ✅ S8 | Generated TS types from Pydantic | Local Python reflector, drift-checked by pytest |
| ✅ S9 | Admin Integration & Inference Proxy | Server-side `/admin` gate (Basic Auth + `INTERNAL_CONSOLE_ENABLED`), inference proxy at `/admin/api/soundsystem/*`, browser stops seeing the inference URL, intent-named Operator Hub, robots noindex |

## Next Slices (in order)

### ✅ S9 — Admin Integration & Inference Proxy

(Shipped — see [admin-integration-strategy.md](./admin-integration-strategy.md) §4–§5.)

Move `/admin` from build-flag visibility to a real authenticated surface
under `schluesselkinder.de/admin`. Stop exposing the inference URL to the
browser.

Scope:
- `/admin` Operator Hub page (links into existing modules).
- Next.js middleware: server-side `INTERNAL_CONSOLE_ENABLED`, basic auth
  via `ADMIN_BASIC_AUTH_USER` + `ADMIN_BASIC_AUTH_PASSWORD`, fail-closed,
  `X-Robots-Tag: noindex, nofollow, noarchive` on every `/admin/*`
  response.
- Server-side inference proxy under `/admin/api/soundsystem/[...path]`
  consuming the server-only `SOUNDSYSTEM_INFERENCE_URL`.
- Client-side `inference.ts` uses relative `/admin/api/soundsystem/*`;
  server components keep direct URL access.
- Deprecate `NEXT_PUBLIC_SOUNDSYSTEM_INFERENCE_URL` (still accepted as
  legacy in dev, never required in production).
- Public navigation does not link to `/admin/*`. `robots.txt` disallows
  `/admin` and `/admin/api`.

Out of scope: NextAuth/OAuth (Phase 2), audit log persistence (S10).

Acceptance gates:
- Browser dev-tools network tab shows only relative `/admin/api/...`
  calls in production builds.
- All existing operator surfaces (lyrics index, project view, version
  editor) work unchanged through the proxy.
- Disabling the gate returns `404` consistently (page + API + manifest).

### ✅ S10 — Compliance Foundation Schemas (shipped)

Implement the data model from
[compliance-foundation.md](./compliance-foundation.md) as Postgres tables
and Pydantic models, seeded with the existing in-code provider list.

Shipped:
- `app/schemas.py` — 9 StrEnums + 12 BaseModels for license, model,
  consent, provenance, audit, preflight, release-eligibility, summary.
- `app/compliance_seed.py` — stable UUID5 seed for the canonical mock
  provider set; no real model is marked `approved_release`.
- `app/compliance_repository.py` — `ComplianceRepository` Protocol +
  `InMemoryComplianceRepository` factory.
- `app/compliance_preflight.py` — pure evaluators for preflight (blocked
  prompt categories, consent gates) and release-eligibility.
- `db/003_compliance.sql` — idempotent Postgres migration (applied by
  hand for local dev; Postgres-backed repository lands in S10b).
- 10 routes under `/v1/compliance/*` + 3 capabilities fields
  (`compliance_repository_mode`, `compliance_registry_available`,
  `compliance_preflight_available`).
- Read-only admin surface at `/admin/soundsystem/safety` exposing the
  registry + license tables through the gated inference proxy.
- 18 compliance tests on top of the existing suite (64 passing total).

Scope:
- Postgres migrations for `license_registry`, `model_registry`,
  `consent_record`, `output_provenance`, `safety_review_status`,
  `audit_events`.
- Pydantic schemas + repository Protocols for each.
- Seed data for current providers (mock + reserved placeholders for the
  GPT-5.5 and music-router slices).
- Wire the lyrics engine and master bus mock providers to emit
  `OutputProvenance` rows.

Out of scope: UI browser surfaces for these tables (S12), real provider
adapters.

Acceptance gates:
- `pytest` exercises the contract layer end-to-end against in-memory
  repositories; live-postgres test covers the new tables when
  `TEST_DATABASE_URL` is set.
- Every generation and master-bus job produces a provenance row in tests.

### ✅ S11 — Voice Lab Mock (shipped)

First surface to exercise the consent-and-provenance flow with a
controlled mock voice provider. No real model code.

Shipped:
- `app/schemas.py` — `VoiceJobStatus`, `VoiceJobKind`, `VoiceTag`,
  `VoiceTagCreateRequest`, `VoiceJob`, `VoiceJobCreateRequest`,
  `VoiceLabSummary` + `voice_lab_available` capability flag.
- `app/voice_lab_repository.py` — `VoiceLabRepository` Protocol +
  `InMemoryVoiceLabRepository` factory.
- `app/voice_provider.py` — mock voice provider: runs preflight,
  produces deterministic artifact path, emits `OutputProvenance` with
  consent citation.
- `compliance_repository.py` extended with `revoke_consent_record`.
- 7 routes: `/v1/voice-lab/{summary,tags,jobs,jobs/{job_id}}` +
  `/v1/compliance/consent-records/{consent_id}/revoke`.
- `/admin/soundsystem/voice-lab` — read-only operator surface showing
  consent records, voice tags, and job history.
- `/admin/soundsystem/consent` — consent record manager (list active +
  revoked).
- Command grid tile: CHARACTER_VOICE → "Voice Lab" marked ready.
- 10 voice lab tests (74 total passing).

Acceptance gates (all met):
- A consent-less voice job blocks at preflight with a codified error.
- A revoked consent record immediately blocks new jobs that cite it.
- Existing lyrics engine flows are unaffected (test_lyrics.py unchanged).

Out of scope: real Kokoro / Piper / OpenVoice / Fish Speech integration.

### ✅ S12 — Music Provider Router Mock (shipped)

A registry-driven router that selects a provider per generation intent.
All-mock; locks the routing contract before real adapters land.

Shipped:
- `app/schemas.py` — `MusicIntentKind` (6 intents), `MusicJobStatus`,
  `MusicProviderGroup`, `MusicArtifactType`, `MusicRouterReadiness`,
  `MusicGenerationRequest`, `MusicArtifactManifest`,
  `MusicRouterDecision`, `MusicJob`, `MusicRouterSummary` +
  `music_router_available`, `music_router_mode`,
  `available_music_intents` capability fields.
- `app/music_router.py` — `MusicRouterRepository` Protocol +
  `InMemoryMusicRouterRepository`, intent→group mapping, mock adapter
  selection, `run_music_job` (preflight → artifacts → provenance).
- 5 routes: `/v1/music-router/{summary,jobs,jobs/{job_id},
  jobs/{job_id}/artifacts}`.
- `/admin/soundsystem/music-router` — intent-named tiles (CREATE LOOP,
  CREATE SONG SKETCH, etc.), recent jobs, provenance badges.
- Command grid: CREATE_TRACK tile → "Create Track" marked ready, routed
  to `/admin/soundsystem/music-router`.
- 15 music router tests (89 total passing).

Acceptance gates (all met):
- Each intent maps to the correct provider group (6 dedicated tests).
- Lyrics surface passes its full test suite unchanged.
- Preflight blocks named-artist prompts for music jobs.
- `commercial_status` is never `approved_release` for mock outputs.
- Every completed job writes provenance.

Out of scope: real ACE-Step, MusicGen, Stable Audio Open integrations.

### ✅ S13 — First Real Provider Boundary (shipped)

First non-mock provider in the SOUNDSYSTEM. GPT-5.5 lyrics behind
Provider Isolation Layer with four hard rules.

Delivered:
- **Provider Isolation Layer**: `LyricsProviderProtocol` in
  `app/providers/lyrics/__init__.py`; factory `build_lyrics_provider()`
  reads `SOUNDSYSTEM_LYRICS_PROVIDER` (mock | gpt_5_5). Route handlers
  never see `openai` types.
- **Cost Accounting**: every GPT-5.5 call records `prompt_tokens`,
  `completion_tokens`, `estimated_cost_usd`, `latency_ms`,
  `raw_provider_trace_id` in provenance.
- **Hard Timeout**: `SOUNDSYSTEM_LYRICS_TIMEOUT_MS` (default 30 000 ms),
  `SOUNDSYSTEM_LYRICS_MAX_RETRIES` (default 2). No admin UI freeze.
- **Shadow Prompt Logging**: `raw_operator_prompt`,
  `system_prompt_version` (`gpt55-lyrics-v1.0`),
  `safety_transformations` persisted in `OutputProvenance`.
- `Gpt55LyricsProvider` class with lazy openai import, system prompt,
  JSON response format, per-call `last_call_meta` dict.
- Config: `LyricsProviderMode`, `LyricsProviderConfigError`,
  `openai_api_key()`, `lyrics_provider_timeout_ms()`,
  `lyrics_provider_max_retries()`.
- 19 new tests (config, factory, protocol conformance, cost fields).
- Mock re-export shim (`app/providers/lyrics/mock.py`) preserves
  backwards compatibility.
- TS types regenerated, 108 tests passing.

### ✅ S14 — SoundGraph Manifest Writer (shipped)

Compiles LyricsVersion into editable production structure. The bridge
between text lyrics and audio generation.

Delivered:
- `SoundGraphArrangement` schema: arrangement_id, lyrics_version_id,
  bpm, time_signature, key_signature, total_bars, regions, energy_map,
  lane_assignments.
- `ArrangementRegion`: section→region mapping with role, bar_start,
  bar_count, vocal_entry, energy, lanes_active, lanes_muted.
- `VocalEntry` enum: none, main, adlibs, whisper, spoken.
- `EnergyLevel` enum: low, medium, high, peak, drop.
- `RegionRole` enum: intro, verse, pre_chorus, chorus, bridge,
  breakdown, drop, outro.
- `LaneAssignment`: per-lane active region list.
- 4 energy profiles: standard, slow_build, peak_early, flat.
- Lane rules: warehouse/dub genre conventions (12-lane model).
- Bar override support per section type (clamped 1–64).
- `compile_soundgraph()` — pure, deterministic, no external calls.
- `SoundGraphRepository` — in-memory store with by-lyrics-version index.
- 4 routes: `POST /v1/soundgraph/compile`,
  `GET /v1/soundgraph/arrangements/{id}`,
  `GET /v1/soundgraph/by-lyrics-version/{id}`,
  `GET /v1/soundgraph/arrangements`.
- Capabilities: `soundgraph_writer_available`.
- 32 new tests, 140 total passing.

### ✅ S15 — SoundGraph → Music Router Handoff (shipped)

Closes the text-to-production-plan-to-mock-track loop. A lyrics project
can now: generate lyrics → build SoundGraph → start music router job.

Delivered:
- `soundgraph_handoff.py`: intent resolution, prompt compilation from
  arrangement, lane extraction, duration estimation, full handoff executor.
- Intent resolution rules: vocals → CREATE_SONG_SKETCH, short no vocals
  → CREATE_LOOP, breakdown → BUILD_RIDDIM, default → CREATE_STEM_TRACK.
- `compile_handoff_prompt()` builds structured prompt from arrangement
  (BPM, key, energy arc, section breakdown).
- `extract_requested_lanes()` / `extract_locked_lanes()` — derives
  from arrangement lane_assignments + locked regions.
- `estimate_duration_seconds()` — bars × beats_per_bar / bpm × 60.
- `SoundGraphHandoffRequest` / `SoundGraphHandoffResult` schemas.
- Route: `POST /v1/soundgraph/handoff`.
- End-to-end test: Lyrics → SoundGraph → Handoff → Music Job + artifacts
  + provenance chain verified.
- 21 new tests, 161 total passing.

### ✅ S16 — Operator UI Flow: Lyrics → SoundGraph → Music Job (shipped)

Admin UI for the complete text-to-production flow. No API-thinking for
the operator — button-driven workflow from lyrics to mock track.

Delivered:
- `SoundGraphFlow` component in lyrics version page (right column,
  above export).
- 3-stage UI: idle → soundgraph built → track complete.
- Idle: BPM, key, energy profile inputs + BUILD SOUNDGRAPH button.
- SoundGraph: arrangement summary (bars, sections, vocal/instr count,
  lanes) + region list with energy/vocal badges + SEND TO MUSIC ROUTER
  button.
- Complete: job card with status/intent/duration/lanes/provenance,
  artifact list, collapsible compiled prompt preview.
- Client helpers: `compileSoundgraph()`, `soundgraphHandoff()`,
  `getSoundgraphArrangement()`, `getSoundgraphByLyricsVersion()`,
  `listSoundgraphArrangements()`.
- TS types re-exported: ArrangementRegion, EnergyLevel, EnergyMapPoint,
  LaneAssignment, RegionRole, SoundGraphArrangement, SoundGraphHandoffResult,
  SoundGraphWriteResult, VocalEntry.
- TypeScript: zero errors.

### ✅ S17 — Export Pack / Project Library (shipped)

Bundles a completed MusicJob with its full lineage into a single exportable
project pack, and maintains an in-memory project library for catalogue
browsing.

Deliverables:
- `ExportPack`, `ExportPackComponent`, `ExportPackCreateRequest`,
  `ExportPackStatus`, `ProjectLibraryEntry`, `ProjectLibrarySummary`
  schemas in Pydantic + generated TS types.
- `app/export_pack.py` — pure `build_export_pack()` compiler,
  `build_library_entry()`, `ProjectLibraryRepository` (in-memory).
- Routes: `POST /v1/library/packs`, `GET /v1/library/packs/{pack_id}`,
  `GET /v1/library/entries`, `GET /v1/library/entries/{entry_id}`,
  `GET /v1/library/summary`.
- `export_pack_available` capability flag.
- 34 tests: slugify, pack building (with/without lyrics/arrangement/provenance),
  library entry, repository CRUD, route 404s, capabilities, full e2e pipeline.
- UI: EXPORT AS PROJECT PACK button in SoundGraphFlow `complete` stage,
  `ExportPackSummary` component in `exported` stage showing pack title,
  component list, BPM, key, intent, duration, pack ID.
- Client helpers: `createExportPack()`, `getExportPack()`,
  `listLibraryEntries()`, `getLibraryEntry()`, `getLibrarySummary()`.
- Acceptance: Ein Music Job kann als internes Release/Project Pack
  exportiert werden.

### ✅ S18 — Project Library UI (shipped)

Admin page at `/admin/soundsystem/library` to browse and inspect export packs.

Deliverables:
- `library/page.tsx` — server-rendered library page with summary grid
  (total packs, entries, with lyrics/arrangement/provenance), pack list
  with intent badge, BPM, key, duration, component/artifact counts,
  lineage badges (LYRICS / ARRANGEMENT / PROVENANCE), slug, timestamp.
- `library/[pack_id]/page.tsx` — pack detail view with metadata grid,
  lineage section (job/lyrics/arrangement/provenance IDs), component table
  (type chip, label, path), notes, collapsible "Inspect JSON" raw view.
- "Library" added to `COMMAND_INTENTS` in side rail navigation.
- Pack list entries link to detail pages.
- Error state (inference unreachable / pack not found).
- Acceptance: Ein aus dem Flow erzeugter Export Pack erscheint in der
  Library und kann geöffnet werden.

### ✅ S19 — Persistent Project Library (shipped)

Dual-mode library repository (in-memory / Postgres) so export packs
survive uvicorn restarts when running against a real database.

Deliverables:
- `app/library_repository.py` — `LibraryRepository` Protocol,
  `InMemoryLibraryRepository`, `PostgresLibraryRepository` (psycopg_pool,
  JSONB components, connection-pooled queries), `build_library_repository()`
  factory.
- `app/config.py` — `LibraryRepositoryMode` enum,
  `SOUNDSYSTEM_LIBRARY_REPOSITORY` env var, `library_repository_mode()`.
- `db/004_library.sql` — idempotent migration: `library_packs` +
  `library_entries` tables with indexes.
- `library_repository_mode` in CapabilitiesResponse.
- Backwards-compatible `ProjectLibraryRepository` alias in `export_pack.py`.
- 21 tests: config (5), factory (2), in-memory (9), compat alias (2),
  routes (3 incl. full e2e).
- Acceptance: Ein Export Pack bleibt nach uvicorn restart in
  /admin/soundsystem/library sichtbar (in Postgres mode).

### ✅ S20 — Dropbox Export Sync (shipped)

Mock Dropbox sync contract: deterministic folder plan from ExportPack,
sync job lifecycle, no real Dropbox API.

Deliverables:
- `DropboxSyncStatus`, `DropboxFolderEntry`, `DropboxExportPlan`,
  `DropboxSyncJob`, `DropboxExportPlanCreateRequest`, `DropboxSyncSummary`
  schemas in Pydantic + generated TS types.
- `app/dropbox_sync.py` — `build_export_plan()` (deterministic folder
  structure), `create_sync_job()`, `mark_ready_for_sync()`,
  `mock_execute_sync()`, `DropboxSyncRepository` (in-memory).
- Routes: `POST /v1/dropbox/plans`, `GET /v1/dropbox/plans/{plan_id}`,
  `GET /v1/dropbox/plans/by-pack/{pack_id}`, `GET /v1/dropbox/jobs`,
  `GET /v1/dropbox/jobs/{sync_id}`, `POST /v1/dropbox/jobs/{sync_id}/ready`,
  `POST /v1/dropbox/jobs/{sync_id}/execute`, `GET /v1/dropbox/summary`.
- `dropbox_sync_available` capability flag.
- 32 tests: folder name sanitization, plan building (deterministic,
  custom root, entries, directories, size hints), sync lifecycle
  (create/ready/execute/fail), repository CRUD, route 404s,
  capabilities, full e2e pipeline.
- UI: `DropboxExportFlow` client component in pack detail page —
  CREATE DROPBOX EXPORT PLAN → folder tree view → MARK READY FOR SYNC
  → EXECUTE SYNC (MOCK) → synced status with file counts.
- Client helpers: `createDropboxExportPlan()`, `getDropboxPlan()`,
  `getDropboxPlanByPack()`, `listDropboxJobs()`, `getDropboxJob()`,
  `markDropboxJobReady()`, `executeDropboxSync()`, `getDropboxSyncSummary()`.
- Acceptance: Ein persistentes Export Pack kann eine reproduzierbare
  Dropbox-Ordnerstruktur erzeugen.

### ✅ S21 — Real Dropbox Adapter Boundary (shipped)

Provider Isolation Layer for Dropbox sync — env-gated real adapter.

- `DropboxSyncProviderProtocol` in `app/providers/dropbox/__init__.py`.
- Mock adapter (default): `app/providers/dropbox/mock.py`.
- Real Dropbox SDK adapter: `app/providers/dropbox/real.py`.
- Factory: `build_dropbox_sync_provider()` — reads
  `SOUNDSYSTEM_DROPBOX_SYNC_PROVIDER` (mock | dropbox).
- Hard rules: mock default, no silent fallback, fail-loud without token,
  upload-only (never deletes), writes only files from ExportPlan.
- Config: `DropboxSyncProviderMode`, `DROPBOX_ACCESS_TOKEN` env var,
  `DropboxSyncProviderConfigError` for startup failure.
- `dropbox_sync_provider_mode` exposed in capabilities response.
- Route `/v1/dropbox/jobs/{sync_id}/execute` now uses provider instead
  of direct `mock_execute_sync` — both mock and real path exercised.
- 27 tests: config (9), factory (4), mock provider (4), real provider
  boundary with patched SDK (8), route integration (2).
- Acceptance: Mock bleibt default. Real Dropbox kann explizit aktiviert
  werden. Ohne Token startet der Service nicht. Mit Token kann ein
  ExportPlan hochgeladen werden.

### ✅ S22 — Release Pack / SoundCloud Handoff (shipped)

ExportPack → ReleasePack with distribution metadata.

- Schemas: `ReleasePackStatus`, `ComplianceChecklistItem`, `SocialCopy`,
  `ReleaseAssetPlaceholder`, `ReleasePack`, `ReleasePackCreateRequest`,
  `ReleasePackSummary` in `app/schemas.py`.
- Pure builder: `build_release_pack()` in `app/release_pack.py` — generates
  title, description, social copy (SoundCloud/TikTok/Instagram), compliance
  checklist (6 items), asset placeholders (4 types), Dropbox release target.
- Lifecycle: DRAFT → READY (gated by compliance_passed=True).
- Compliance checklist: `update_checklist_item()` toggles per-code,
  `compliance_passed` auto-recalculates. `mark_release_ready()` rejects
  unless all items pass.
- In-memory `ReleasePackRepository` with store/get/get_by_pack/list/update/summary.
- Routes: `POST /v1/releases`, `GET /v1/releases`, `GET /v1/releases/{release_id}`,
  `GET /v1/releases/by-pack/{pack_id}`, `POST /v1/releases/{release_id}/checklist/{code}`,
  `POST /v1/releases/{release_id}/ready`, `GET /v1/releases/summary`.
- `release_pack_available` capability flag.
- UI: `ReleasePackFlow` client component — CREATE RELEASE PACK → metadata view
  → social copy → compliance checklist (toggle items) → MARK RELEASE READY.
- Client helpers: `createReleasePack()`, `getReleasePack()`, `getReleaseByPack()`,
  `listReleases()`, `updateReleaseChecklist()`, `markReleaseReady()`,
  `getReleaseSummary()`.
- 39 tests: builder (11), social copy (5), compliance checklist (6),
  repository (6), routes (10), e2e lifecycle (1).
- Acceptance: Ein Library Pack kann in ein Release Pack umgewandelt werden
  mit Titel, Artist, Beschreibung, Social Copy, Compliance Status,
  Export Checklist und Dropbox Target.

### ✅ S23 — Release Pack Persistence (shipped)

Dual-mode release repository — survives uvicorn restart in Postgres mode.

- Config: `ReleaseRepositoryMode`, `SOUNDSYSTEM_RELEASE_REPOSITORY` env var,
  `release_repository_mode()` in `app/config.py`.
- `ReleaseRepository` Protocol in `app/release_repository.py` with
  `InMemoryReleaseRepository` and `PostgresReleaseRepository`.
- Factory: `build_release_repository()` — reads env, fails loud without URL.
- Migration: `db/005_releases.sql` — `release_packs` table with JSONB columns
  for social_copy, compliance_checklist, assets. FK to library_packs.
- `release_repository_mode` exposed in capabilities response.
- Backwards-compat alias: `ReleasePackRepository` in `release_pack.py`.
- 23 tests: config (5), factory (2), InMemoryReleaseRepository (10),
  backwards-compat (2), route integration (3), e2e lifecycle (1).
- Acceptance: Ein Release Pack bleibt nach uvicorn restart sichtbar
  und behält Checklist-/Ready-Status.

### ⬜ S24 — Real Model Adapters (per category)

One category at a time, each gated by license + compliance review. Each
adapter ships behind its own `SOUNDSYSTEM_*_PROVIDER` env flag.

Suggested order:
1. `offline_fallback_provider` — Piper TTS.
2. `voice_tts_provider` — Kokoro (license: Apache-2.0, lowest risk).
3. `music_loop_provider` — first to need legal review for commercial use.
4. `high_fidelity_clip_provider` — close cousin of (3); same legal
   considerations.
5. `voice_clone_provider` — only after the consent surface is real.
6. `singing_voice_provider` — most coupled to vocal-lane work; lands
   alongside SoundGraph polish.
7. `full_song_experimental_provider` — research-only by default; never
   default-on.

Each item is its own slice. None starts until S10–S14 are in.

### ⬜ S15 — Dropbox Sync Worker

Internal sync worker that uploads finished artifact bundles to Dropbox.
Separate from the inference service. Browser never holds Dropbox
credentials.

Scope:
- Worker process that pulls `release_eligible = true` bundles from
  Postgres + scratch.
- Uploads to per-project Dropbox folders.
- Writes audit events on every upload + every failure.
- `/admin/dropbox` shows configured target folders, recent sync history,
  and failures (read-only first).

Out of scope: Dropbox writes from any other surface, real-time sync,
two-way sync.

Acceptance gates:
- Dropbox failure does not break the artifact (it stays in scratch +
  Postgres).
- No Dropbox credentials in any frontend or NEXT_PUBLIC env var.

### ⬜ S16 — Release / Export Pipeline

Closes the loop. Implements the `release_eligible` predicate from
[compliance-foundation.md](./compliance-foundation.md) and exposes it on
the `/admin/soundsystem/export` + `/admin/releases` surfaces.

Scope:
- Each release-eligibility gate is wired to a real column / computed
  predicate.
- Operator override (Dropbox-only) records an `audit_event` with a
  written justification.
- A release bundle is a frozen tuple of (lyrics version, generation job,
  master bus job, cover image, prompt history, safety report,
  provenance chain).

Acceptance gates:
- A bundle missing any gate cannot be marked released.
- The Dropbox sync worker picks up only release-eligible bundles.

## Deferred (post-S16)

| Slice | Surface | Why deferred |
| ----- | ------- | ------------ |
| ⏸ NextAuth/OAuth | `/admin` auth Phase 2 | Basic auth is enough until more than one operator is real |
| ⏸ Public Stripe / Printful integration | commerce surfaces | Out of scope per ADR-0005; admin OS is internal |
| ⏸ Real-time queue (Redis / RQ / Celery) | inference workers | Local + in-process is enough for the operator console |
| ⏸ Public Suno / SoundCloud / Spotify upload | distribution | Manual delivery is intentional until the release pipeline is hardened |

## Cross-Cutting Constraints (every slice)

These never relax:

- **No silent fallbacks.** A misconfigured env var fails at startup with a
  clear error, not a quiet revert to mock.
- **No browser-side secrets.** API keys, Dropbox tokens, Postgres URLs
  never appear in `NEXT_PUBLIC_*` variables.
- **No fake live state.** UI panels that depend on a live signal show
  honest `UNREACHABLE` / `NOT CONFIGURED` states instead of fabricated
  data.
- **No GPT/Claude/OpenAI calls until S13.** And then only behind an
  explicit env flag.
- **No Dropbox writes until S15.** And then only from the worker, never
  from inference or the browser.
- **No public-figure / named-artist voice work, ever.**
- **Locked sections are byte-for-byte preserved across every regeneration.**
- **Generated TS types are committed; drift fails CI** (S8 enforcement).

## Slice Sizing

A "slice" is the unit at which we ship: a single PR-sized change that
leaves the system in a coherent state. Each slice above is one PR or one
short series of related PRs. If a planned slice runs to >800 lines of
changed code or touches more than ~10 files, it splits.

## Cross-References

- [admin-integration-strategy.md](./admin-integration-strategy.md) —
  binding architecture for S9.
- [compliance-foundation.md](./compliance-foundation.md) — binding data
  model for S10, S11, S16.
- [model-provider-strategy.md](./model-provider-strategy.md) — provider
  groups consumed by S12 and S14.
- [sound-model.md](./sound-model.md) — SoundGraph contract referenced
  throughout.
- [master-bus.md](./master-bus.md) — mandatory final pass before any
  release-pipeline output (S16).
- [lyrics-engine.md](./lyrics-engine.md) — the slice surface that
  exercises most of the contracts today.
