# Operator Interface Principles

The binding UI posture for every surface under `schluesselkinder.de/admin`.
These principles override any provider's recommended UI patterns. They apply
to every soundsystem surface, and to any future admin module that consumes
AI generation.

## 1. The UI Speaks Creative Outcomes, Not Model Names

The operator console presents **intents**. The operator presses a button that
describes what they want to make. The button never names a model.

Canonical primary intents:

```text
CREATE LOOP              short instrumental loop or rhythmic bed
CREATE SONG SKETCH       full-length structured song draft
CREATE STEM TRACK        single addressable lane (kick / bass / vocals / …)
CREATE VOICE TAG         short branded vocal stinger
CREATE SPOKEN VOCAL      narrator / spoken intro / podcast bed
CONVERT APPROVED VOICE   timbre transfer over a consented voice
SINGING EXPERIMENT       lyrics + melody → singing performance
WRITE LYRICS             versioned, lockable lyrics drafts
MASTER TRACK             SoundGraph → loudness-shaped master
EXPORT PACK              frozen release bundle for distribution
```

Each intent corresponds to one route under `/admin/soundsystem/` and one
provider group on the backend. Intents are versioned in code (the
`COMMAND_INTENTS` table for the soundsystem command grid, extended in
follow-up slices). New intents are added by adding rows, not by adding
buttons that reference models.

### What is banned from the create flows

The following strings are **never** rendered on a primary create surface:

```text
MusicGen / AudioCraft        Stable Audio Open
Tencent SongGeneration       YuE                    ACE-Step
Kokoro                       Qwen3-TTS              Fish Speech
VoxCPM2                      OpenVoice V2           Piper
DiffSinger                   OpenUtau               RVC
Demucs                       SonicMaster            Matchering
GPT-5.5                      Claude                 OpenAI
```

This list grows over time. Adding a new provider does not change the rule:
the operator surface stays intent-named, the provider stays implementation
detail.

## 2. Model Complexity Lives Behind the Intent Router

The operator hands the request to a single Intent Router. The router resolves
the provider group, picks an active adapter, and runs it.

```text
Operator Intent
  → CompliancePreflight   (compliance-foundation.md §12)
  → Intent Router
  → Provider Group
  → Active Adapter
  → Model Implementation
```

No route handler imports a model SDK directly. Adapters do. The route handler
asks the registry for the active adapter for an intent's group; it does not
care which adapter it gets back.

This separation is enforced architecturally:

- `/admin/soundsystem/loops` → posts to `/admin/api/soundsystem/intents/loop`
- Server-side route → `intent_router.route(LOOP_INTENT, request)`
- Router → `ModelRegistry.get_active("music_loop_provider")`
- Adapter → runs the model, returns artifact + provenance

If a future operator wants to know "which model produced this loop", they
read it on the Library detail page, not the create page.

## 3. Default Provider Mode is AUTO

Every intent ships with `provider_mode = AUTO`. AUTO means:

```text
1. Filter ModelRegistry rows by provider group.
2. Keep rows where commercial_status = ready.
3. Sort by ModelRegistry.priority, then cost_estimate.
4. Pick the first.
5. If none, fall back to the registered mock adapter.
   The surface labels itself READY · MOCK.
```

AUTO is the only mode operators see in the standard flow. The intent form
has no model dropdown. Provider behavior is a registry decision, not a
form field.

## 4. Advanced Provider Override Lives Behind the Debug Drawer

A separate, gate-gated debug surface (`/admin/soundsystem/debug`) exposes:

- The list of registered adapters per group.
- The current `priority` and `commercial_status` of each.
- A per-request override: choose a specific adapter, with a mandatory
  free-text reason.

Override constraints:

- Per-request only. Never sticky. The next request returns to AUTO.
- Mandatory `reason` field. The reason is written to `audit_events`.
- The override target must still satisfy CompliancePreflight (license,
  consent, commercial-status checks). Override does not bypass safety.
- The debug drawer is hidden from the standard operator hub. It is opened
  via a deliberate keyboard shortcut or a dedicated `/admin/soundsystem/debug`
  link from the hub footer.

This is the only place model names appear in a UI control. Even here, the
button still describes a creative outcome (`Run CREATE LOOP with
<adapter>`), not a model action.

## 5. Every Output Lands in the Library

`/admin/soundsystem/library` is the universal output index. Every produced
artifact — regardless of intent — surfaces here with one schema:

```text
output_id
artifact_kind             lyrics_version | loop | song_sketch | stem_track |
                          voice_tag | spoken_vocal | voice_conversion |
                          singing_experiment | master | export_pack
created_at
operator_id
intent                    the operator-facing intent name
prompt                    free-text input (if any)
seed                      deterministic seed (if any)
provider                  ModelRegistry.model_id            (provenance only)
model_version             exact model checkpoint hash       (provenance only)
license_bundle            LicenseRegistry.license_id[]      (provenance only)
consent_records           ConsentRecord.consent_id[]        (provenance only)
duration_seconds          if audio
commercial_status         approved | review_needed | not_allowed
safety_review_status      pending | approved | rejected | needs_changes
audio_path                local scratch path (if audio)
download_actions          available export formats
```

The Library is the only place where every artifact converges. Surfaces that
generate artifacts also list them inline (e.g. the lyrics version timeline)
but the Library is the canonical index.

## 6. Provenance Metadata is Mandatory

Every artifact carries an `OutputProvenance` record before it is visible in
the Library. An adapter that returns without writing provenance fails the
request and the artifact is quarantined, not displayed.

Mandatory fields (full schema in [compliance-foundation.md §3](./compliance-foundation.md)):

```text
provider
model_version
prompt_tokens             when LLM stages are involved
completion_tokens         when LLM stages are involved
safety_notes
rewrite_strategy
locked_sections_respected
raw_provider_trace_id     audit-only opaque pointer
license_bundle
consent_records
```

The Library's "details" view surfaces these honestly. This is the only place
in the UI where model names appear in operator-readable form, and they
appear as audit metadata, not as controls.

## 7. Release Compliance is Mandatory

Every `EXPORT PACK` artifact passes the release-eligibility gate before it
can leave the system. The gate is the predicate from
[compliance-foundation.md §10](./compliance-foundation.md):

```text
release_eligible = (
  output_provenance.exists
  AND model_registry[provider].commercial_status = ready
  AND safety_review_status = approved
  AND license_bundle_all_permit_commercial
  AND consent_records_all_valid_for_release_pack_export
  AND locked_sections_respected
  AND master_bus.export_ready
  AND dropbox_sync.status IN (ok, deferred)
)
```

Each `AND` term renders as a row on the export surface. The operator sees
exactly which gate is open or closed. The only overridable gate is
`dropbox_sync`, and an override requires a written justification recorded
as an `audit_event`.

## 8. Honest States Over Optimistic States

The UI never fabricates state to look busier than it is. Specific rules:

- **Unwired**: a surface that has no backend yet renders the `AWAITING WIRE`
  chip. No fake forms, no fake progress bars.
- **Mock**: a surface routed through a mock adapter renders the
  `READY · MOCK` chip and explicit copy:
  > "Mock provider active. No live model is running."
- **Unreachable**: when the inference service can't be reached, the
  surface renders `INFERENCE UNREACHABLE` with a recovery hint. It never
  silently retries with stale data.
- **Session-scoped**: when the lyrics repository (or any repository) is in
  `in_memory` mode, the banner reads:
  > "Session-scoped: versions are stored in the running inference process
  > and disappear on restart."
- **No releaseable claim**: every export surface carries:
  > "Export is a contract artifact, not a release-ready distribution package."

This is the same posture documented in the lyrics engine surface; it
generalises to every future admin surface.

## 9. Public Site Boundaries

The operator console must never:

- Be linked from a public surface (`/`, `/shop`, `/projekte`, ...).
- Be indexed (`X-Robots-Tag: noindex, nofollow, noarchive` on every
  response; `metadata.robots = { index: false, follow: false }` on every
  admin page).
- Expose `NEXT_PUBLIC_*` env vars that leak the inference URL,
  database URL, or any vendor key.
- Render admin assets under public-looking paths. PWA manifests, icons,
  and other admin artefacts live under `/admin/soundsystem/*`, never
  under `/brand/*` or `/static/*`.

Any breach of these rules is a release-blocker.

## 10. Verbs the Operator Hears, Routes the Operator Sees

Cross-reference table:

| UI label (intent)         | Route                                  | Provider group                              |
| ------------------------- | -------------------------------------- | ------------------------------------------- |
| `CREATE LOOP`             | `/admin/soundsystem/loops`             | `music_loop_provider`                       |
| `CREATE SONG SKETCH`      | `/admin/soundsystem/songs`             | `full_song_experimental_provider`           |
| `CREATE STEM TRACK`       | `/admin/soundsystem/stems`             | `music_loop_provider` + Demucs              |
| `CREATE VOICE TAG`        | `/admin/soundsystem/voice-tags`        | `voice_tts_provider` (short)                |
| `CREATE SPOKEN VOCAL`     | `/admin/soundsystem/spoken`            | `voice_tts_provider` (long-form)            |
| `CONVERT APPROVED VOICE`  | `/admin/soundsystem/voice-convert`     | `voice_clone_provider`                      |
| `SINGING EXPERIMENT`      | `/admin/soundsystem/singing`           | `singing_voice_provider`                    |
| `WRITE LYRICS`            | `/admin/soundsystem/lyrics`            | Lyrics provider (mock today)                |
| `MASTER TRACK`            | `/admin/soundsystem/master`            | Master Bus (SonicMaster / Matchering)       |
| `EXPORT PACK`             | `/admin/soundsystem/export`            | Export pipeline                              |

Routes are intent-named. The right column is provenance, not control.

## 11. Tone and Copy

The intent-first principle extends to the operator console's voice:

- Use imperative creative verbs: `BUILD VARIANTS`, `APPLY`, `LOCK`, `EXPORT`.
- Avoid SaaS-style "Welcome", "Get started", or onboarding copy. The
  operator is already inside the system; nothing needs to be sold.
- State current state honestly. `AWAITING WIRE` and `MOCK PROVIDER` are
  features, not bugs.
- Operator chips use machine language (`QUEUE ARMED`, `SAFETY HOLD`,
  `STEMS READY`) but never reference vendor language (`Powered by Suno`).

## 12. Implementation Notes (non-binding sketch)

- Intent definitions live in a single registry on the backend, exposed
  via `/v1/intents` (analogous to today's `/v1/capabilities`).
- The frontend reads `/v1/intents` to render the operator hub and each
  create surface. Adding an intent is a backend registry write, not a
  scattered UI edit.
- The provider mapping is the Intent Router's responsibility, not the
  intent registry's. The router is consulted at request time, not at
  build time, so registry updates take effect without a redeploy.
- Generated TS types (slice 8) extend to include the intent registry
  payload so the frontend cannot drift from the backend's intent
  vocabulary.

## 13. Cross-References

- [admin-integration-strategy.md](./admin-integration-strategy.md) — host
  architecture and route map.
- [model-provider-strategy.md](./model-provider-strategy.md) — provider
  groups, intent-to-provider mapping, adapter pattern.
- [compliance-foundation.md](./compliance-foundation.md) — preflight
  ordering, consent / license / provenance gates.
- [roadmap.md](./roadmap.md) — slice sequence.
- [lyrics-engine.md](./lyrics-engine.md) — first surface to fully enact
  these principles (intent-named, consent-aware, provenance-mandatory).
