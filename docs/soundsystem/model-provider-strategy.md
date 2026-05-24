# Model Provider Strategy

Provider categorisation, candidate models, and the activation rules each model
must clear before it can drive a SCHLÜSSELKINDER release.

This doc is the binding contract for which models are even considered. It is
not a list of integrations — no real model code lands without:

1. A `ModelRegistry` row with `commercial_status = ready`.
2. A `LicenseRegistry` reference whose `permits_commercial` matches our use.
3. A `safety_review_status = approved` record from an operator.
4. The corresponding `required_consent` recorded in `ConsentRecord` where
   applicable.

The full compliance surface lives in
[compliance-foundation.md](./compliance-foundation.md). The intent-first
interface posture is documented in
[operator-interface-principles.md](./operator-interface-principles.md).

## Intent-First Routing

Every operator interaction starts with a **creative intent** — never with a
model name. The Intent Router resolves the intent to a provider group, the
group resolves to an active adapter via the `ModelRegistry`, and the adapter
hides the model implementation behind a stable Protocol.

```text
Operator Intent (UI button)
  ↓
Intent Router            (server-side; pure function over ModelRegistry)
  ↓
Provider Group           (one of seven; defined below)
  ↓
Active Adapter           (one model implementation per group + per env config)
  ↓
Model Implementation     (MusicGen | Stable Audio Open | Kokoro | …)
```

Model names appear in:

- `ModelRegistry` (admin browser)
- `LicenseRegistry` (license browser)
- `OutputProvenance` (library detail)
- `SafetyReviewStatus` records
- The optional `/admin/soundsystem/debug` drawer (provider override + audit log)

Model names **never** appear in the primary `CREATE *` create flows. The
operator presses `CREATE LOOP` — they do not press `Run MusicGen`.

### Intent-to-Provider Mapping

| Intent                    | Route segment           | Provider group(s)                                            | Notes |
| ------------------------- | ----------------------- | ------------------------------------------------------------ | ----- |
| `CREATE LOOP`             | `/loops`                | `music_loop_provider`                                        | Short instrumental loops; SoundGraph ingredient |
| `CREATE SONG SKETCH`      | `/songs`                | `full_song_experimental_provider`                            | Research-only by default; never auto-released   |
| `CREATE STEM TRACK`       | `/stems`                | `music_loop_provider` + Demucs (separation post-step)        | Single addressable lane; bypasses full-song flow |
| `CREATE VOICE TAG`        | `/voice-tags`           | `voice_tts_provider` (short / branded)                        | Branded vocal stinger                            |
| `CREATE SPOKEN VOCAL`     | `/spoken`               | `voice_tts_provider` (long-form)                             | Narrator / podcast / spoken-word bed             |
| `CONVERT APPROVED VOICE`  | `/voice-convert`        | `voice_clone_provider` (consent-gated)                       | Requires non-revoked `ConsentRecord`             |
| `SINGING EXPERIMENT`      | `/singing`              | `singing_voice_provider`                                     | Lyrics + melody → vocal performance              |
| `MASTER TRACK`            | `/master`               | Master Bus (SonicMaster + Matchering adapters)               | Mode + profile per Master Bus contract           |
| `EXPORT PACK`             | `/export`               | Export pipeline (no model call)                              | Release-eligibility gate; downloads/upload sync  |
| `WRITE LYRICS`            | `/lyrics`               | Lyrics provider (mock today; future GPT-5.5 / Claude)        | Persisted via `LyricsRepository`                 |

Two extra non-generative adapter classes are referenced by the table:

- **Demucs** — source separation. Runs as a post-step for `CREATE STEM TRACK`
  when the source provider doesn't emit individual lanes.
- **SonicMaster / Matchering** — mastering. Wrapped in the Master Bus
  contract layer ([master-bus.md](./master-bus.md)); operator picks
  `MASTERING_MODE` + `EXPORT_PROFILE`, never the engine.

### AUTO Routing as the Default

Every intent ships with `provider_mode = AUTO`. The router picks the active
adapter for the group based on:

```text
1. ModelRegistry rows for the group where commercial_status = ready
2. Sorted by ModelRegistry.priority (operator-tunable)
3. Sorted by ModelRegistry.cost_estimate ascending (tiebreaker)
4. First match wins
```

If no `ready` adapter is registered for a group, the router falls back to the
mock adapter — and the surface labels itself as such (`READY · MOCK` chip,
same pattern as today's `WRITE_LYRICS` tile). It never falls back to a
non-`ready` adapter silently.

### Provider Override (Debug Drawer Only)

`/admin/soundsystem/debug` exposes an explicit override:

```text
intent          CREATE LOOP
provider_mode   AUTO | <specific adapter id>
reason          required free-text justification
```

Selecting a specific provider records an `audit_event` with:

```text
operator_id, intent, provider_group, selected_provider, reason, created_at
```

The override is per-request, never sticky. The default flow always returns
to AUTO routing.

### Adapter Pattern

Each provider group is backed by a Python Protocol that the adapters
implement. The Protocol shape (one per group) is defined in the
inference service and consumed by the Intent Router. The adapters are the
**only** places that touch model SDKs, weight downloads, or vendor APIs.

```python
class MusicLoopProvider(Protocol):
    name: str                                   # adapter id, not UI label
    model_registry_id: UUID                     # links to ModelRegistry
    supported_sample_rates: tuple[int, ...]
    max_duration_seconds: int

    async def generate_loop(self, request: LoopRequest) -> LoopArtifact: ...
    async def get_status(self, job_id: str) -> ProviderStatus: ...
    async def is_available(self) -> bool: ...
    def estimate_cost(self, duration_seconds: int) -> float: ...
```

Equivalent Protocols exist for `HighFidelityClipProvider`,
`FullSongExperimentalProvider`, `VoiceTtsProvider`, `VoiceCloneProvider`,
`SingingVoiceProvider`, `OfflineFallbackProvider`. The lyrics engine's
existing `MusicEngineProvider` is the precedent.

Adapter activation is a registry write, not a code change to the route
handlers. Routes never `import MusicGenAdapter` — they ask the registry for
the active `music_loop_provider`.

## Provider Groups

Seven groups separate the audio generation surface by *intent*, not by
*vendor*. The provider router picks one group per intent; the registry picks
one provider per group.

| Group                              | Intent                                                       |
| ---------------------------------- | ------------------------------------------------------------ |
| `music_loop_provider`              | Short loop-first instrumental beds (drums, bass, percussion) |
| `high_fidelity_clip_provider`      | Short polished clips, FX, ambience, transitions              |
| `full_song_experimental_provider`  | Full-length structured songs                                 |
| `voice_tts_provider`               | Plain text-to-speech for narrator beds, podcast intros       |
| `voice_clone_provider`             | Voice conversion / cloning with explicit consent             |
| `singing_voice_provider`           | Lyrics-to-song singing performance                            |
| `offline_fallback_provider`        | Deterministic local fallback when no GPU / no network        |

## Risk Tiers

A simple three-tier scheme:

| Tier  | Meaning                                                                   |
| ----- | ------------------------------------------------------------------------- |
| `green`  | Permissive license, low ambiguity, clear consent posture, safe defaults |
| `amber`  | Some license/consent caveat; requires operator review per use            |
| `red`    | Cannot ship in a commercial release without explicit additional work     |

## Group 1 — `music_loop_provider`

### Use case
Short instrumental loops and beds that compose into a SoundGraph. Output is
deliberately not a full song; the SoundGraph engine takes loops as ingredients.

### Candidates

| Model                | Tier   | License posture                       | Status               |
| -------------------- | ------ | ------------------------------------- | -------------------- |
| **MusicGen / AudioCraft** | amber | Code MIT, weights research/CC-BY-NC (`facebook/musicgen-*`) | research-only until weights cleared |
| **Stable Audio Open**     | amber | Stability AI Community License; commercial use conditional on terms     | requires legal review for commercial |
| **Mock provider**         | green | n/a — local deterministic stub        | always available     |

### Required checks before activation
- `LicenseRegistry` entry verified per checkpoint (code vs. weights). Weight
  licenses that forbid commercial use → blocked for releases, allowed only
  for internal drafts marked `release_eligible = false`.
- A representative `OutputProvenance.safety_notes` test set covering at
  least: empty prompt, redline druck, artist-imitation prompt.
- A mock-vs-real A/B comparison documented; mock must remain a working
  fallback so the SoundGraph contract is exercised in CI.

### Why for SNUFFRAGA
SoundGraph is explicitly stem-first. Loop providers feed clean, separable
loops that the existing 12-lane model knows how to address. MusicGen and
Stable Audio Open both produce loop-friendly output at usable lengths.

### Why not (yet)
Both candidates ship under licenses that need explicit legal review. Until
license review lands, this group runs the mock provider only.

## Group 2 — `high_fidelity_clip_provider`

### Use case
Short polished clips — risers, impacts, FX swells, transitions, ambience
beds. Length under ~30 s. Quality bar above the loop tier.

### Candidates

| Model                | Tier   | License posture                       | Status               |
| -------------------- | ------ | ------------------------------------- | -------------------- |
| **Stable Audio Open**     | amber | Stability AI Community License        | conditional          |
| **MusicGen Audio (32 kHz)** | amber | Code MIT, weights CC-BY-NC for some checkpoints | research-only         |
| **Mock provider**         | green | local deterministic stub              | always available     |

### Required checks before activation
- Sample-rate handling tested against Master Bus contract (44.1 / 48 / 96 kHz).
- `OutputProvenance` includes the source clip's checkpoint hash, not just
  the model name.
- A documented internal use-case for each clip type (FX, ambience, transition)
  before opening the route to operators.

### Why for SNUFFRAGA
Dub FX Lab and atmosphere lanes consume exactly this shape of asset.

### Why not (yet)
Same license review as Group 1. We do not silently drop into commercial use
on a checkpoint we have not reviewed.

## Group 3 — `full_song_experimental_provider`

### Use case
Full-length structured songs from a prompt + section plan. Output is
internal-only experiments by default — never shipped without manual
post-production and Master Bus pass.

### Candidates

| Model                       | Tier  | License posture                         | Status               |
| --------------------------- | ----- | --------------------------------------- | -------------------- |
| **ACE-Step**                | amber | Custom research license; commercial unclear   | research-only        |
| **Tencent SongGeneration**  | red   | Provider TOS / API-only access          | not a build candidate today |
| **YuE (instrumental mode)** | amber | Code Apache-2.0, weights varies per checkpoint | research-only        |
| **Mock provider**           | green | local deterministic stub                | always available     |

### Required checks before activation
- License + provenance check (especially for ACE-Step weights).
- Hard rule: every output of this group lands in the system with
  `release_eligible = false` until manually re-mastered through the Master
  Bus contract.
- A test prompt set demonstrating that named-artist prompts are rejected
  by the prompt engine's negative-prompt suppression.

### Why for SNUFFRAGA
The lyrics engine, SoundGraph and Master Bus contracts already model the
"experiment first, master later" flow. Full-song models slot in cleanly as
research tools.

### Why not (yet)
Output quality and license ambiguity. We do not let a research-tier output
walk into a release without a Master Bus + Safety Review pass.

## Group 4 — `voice_tts_provider`

### Use case
Spoken text — narrator beds, podcast intros, voice-overs for internal
release-process tools. Not singing.

### Candidates

| Model               | Tier  | License posture                  | Status                       |
| ------------------- | ----- | -------------------------------- | ---------------------------- |
| **Kokoro**          | green | Apache-2.0 (model + weights)     | commercially viable          |
| **Qwen3-TTS**       | amber | Apache-2.0 code; weight terms vary by release   | review per checkpoint        |
| **Piper**           | green | MIT, offline, multilingual voices    | commercially viable, also offline fallback |
| **Seed-TTS**        | red   | Reference / benchmark only       | not a build candidate        |
| **XTTS-v2**         | red   | Coqui Public Model License; non-commercial restrictions | not a commercial candidate |
| **F5-TTS pretrained**| red   | Research / pretrained-weight constraints     | not a commercial candidate   |

### Required checks before activation
- Voice catalogue: every voice exposed in the UI is a named entry with a
  recorded license + provenance. No anonymous voice models in the catalogue.
- Operators may upload their own voice samples for fine-tuning only with a
  `ConsentRecord` whose `subject = operator`.
- Latency and quality benchmarks documented per voice before exposure.

### Why for SNUFFRAGA
Kokoro is the strongest cleanly-licensed option in 2026 for English/German
narration. Piper is the right offline fallback because it ships
local-runnable voices under MIT.

### Why not Seed-TTS / XTTS-v2 / F5-TTS pretrained
- **Seed-TTS** is a benchmark and reference model, not a deployment
  candidate. Treating it as buildable is a category error.
- **XTTS-v2** ships under the Coqui Public Model License which restricts
  commercial use; commercial parity is the entire point of the operator OS.
- **F5-TTS pretrained** weights carry research-only restrictions. Training
  our own from scratch is a different conversation.

## Group 5 — `voice_clone_provider`

### Use case
Voice conversion or cloning of a specific human voice. Strictly **internal
and consent-only**.

### Candidates

| Model            | Tier   | License posture                | Status                       |
| ---------------- | ------ | ------------------------------ | ---------------------------- |
| **OpenVoice V2** | amber  | MIT codebase; weights with attribution requirements          | consent-only        |
| **Fish Speech**  | amber  | Apache-2.0 code; commercial use of pretrained weights conditional       | consent-only        |
| **VoxCPM2**      | amber  | Provider-specific license; review per release | consent-only        |
| **RVC WebUI**    | red    | Codebase varies; public RVC models are routinely produced without subject consent  | private/consent-only; no public RVC models |

### Required checks before activation
- Mandatory `ConsentRecord` per subject, per scope, per project.
- Public-figure voices: always blocked. There is no operator override.
- Public-internet RVC voice models are never imported. Voices used here are
  recorded by the operator or by an explicitly-consenting session artist,
  with the recording itself archived alongside the consent record.
- The cloning operation records `OutputProvenance.consent_records` —
  outputs without a citation cannot leave the system.

### Why for SNUFFRAGA
Character-voice work for the SHIBARI KAWAII persona, internal alt-takes,
operator demos. All produced under explicit consent.

### Why not without consent
Voice cloning without consent is a legal and ethical red line. The system
must make it physically inconvenient to bypass — preflight blocks rather
than warning messages.

## Group 6 — `singing_voice_provider`

### Use case
Lyrics + melody → full singing performance. Drives the vocal lanes in
SoundGraph (`vocals_main`, `vocals_adlibs`).

### Candidates

| Model            | Tier  | License posture                                 | Status               |
| ---------------- | ----- | ----------------------------------------------- | -------------------- |
| **YuE (vocal)**  | amber | Code Apache-2.0; weights vary per checkpoint    | research-only        |
| **DiffSinger**   | amber | Permissive code; voicebank licenses vary        | requires voicebank review |
| **OpenUtau**     | amber | Tooling (MIT); voicebanks under separate license    | tooling-only candidate |

### Required checks before activation
- Voicebank registry per character. No anonymous singing-voice models.
- The same `ConsentRecord` rule applies if a real human singer's voicebank
  is involved.
- Output goes through Master Bus before any "vocal performance" claim is
  attached to a release.

### Why for SNUFFRAGA
Vocal performance is the highest-value missing piece in the existing chain.
SHIBARI KAWAII tracks today rely on operator-recorded vocals — a credible
singing-voice provider unlocks higher-volume experimentation while staying
inside the consent boundary.

### Why not (yet)
Voicebank licensing is per-voicebank and the catalogue requires real
curation. Until that work is done, no provider in this group is activated.

## Group 7 — `offline_fallback_provider`

### Use case
Deterministic, no-network, no-GPU fallback so the operator console keeps
working when external services are down or unavailable.

### Candidates

| Model           | Tier  | License        | Status                |
| --------------- | ----- | -------------- | --------------------- |
| **Piper TTS**   | green | MIT            | shipped offline       |
| **Mock provider (current)** | green | local code | always available   |

### Required checks before activation
- Must run with no external dependencies beyond what the inference service
  already ships.
- Must produce a deterministic output for a given prompt (already true for
  the existing mock; required for Piper voicebank selection).

### Why for SNUFFRAGA
The lyrics engine's mock provider already establishes the "always-available
fallback" pattern. Piper TTS adds the same posture for text-to-speech.

## Activation Workflow (per provider)

A provider moves from "candidate" to "activated" along a fixed sequence:

```text
1. ModelRegistry seed entry        commercial_status = research_only
2. License review                  LicenseRegistry row, permits_* recorded
3. Internal smoke test             via /admin/soundsystem (mock-routable)
4. Safety review                   SafetyReviewStatus = approved
5. Provider adapter shipped        behind explicit env flag (e.g.
                                   SOUNDSYSTEM_MUSIC_PROVIDER=stable_audio)
6. Audit ride                      first 10 outputs reviewed manually
7. Promotion                       commercial_status = ready
```

No step is skipped. A provider with `commercial_status` other than `ready`
must never appear as a default in the operator UI.

## Hard No-Go List

The following are **never** activated under SCHLÜSSELKINDER, regardless of
operator preference:

- Public-figure / named-artist voice cloning. No exceptions.
- Random public RVC voice models scraped from the internet.
- Any model whose dataset includes obviously-non-consensual voice data
  (deepfake catalogues, scraped phone-recording corpora, etc.).
- Any pretrained checkpoint without a verifiable license source URL.
- Any model that requires sending our prompts or audio to an external
  service whose terms we have not reviewed and accepted.

## Implementation Status (S12, 2026-05-17)

The Music Provider Router (S12) ships the mock contract:

- `app/music_router.py` — `MusicRouterRepository` Protocol,
  intent→group mapping for all six music intents, mock adapter keys.
- Every intent routes via `route_intent()` to a `MusicProviderGroup`.
  The selected adapter is always `mock_*` — readiness = `MOCK_ONLY`.
- `run_music_job()` runs compliance preflight, produces deterministic
  artifact paths, and emits `OutputProvenance` (always `review_needed`).
- `/admin/soundsystem/music-router` renders intent tiles (no model
  names), recent jobs, and provenance badges.
- The `ProviderRouter` Protocol consults `ModelRegistry` for future
  real adapters — the swap is local to `route_intent()` + the group
  mapping dict. No route handler changes required.

No real model adapters are active. Outputs are `review_needed` by
default. Provider names remain registry/debug-only.

## Cross-References

- [admin-integration-strategy.md](./admin-integration-strategy.md) — host
  surface for these providers.
- [compliance-foundation.md](./compliance-foundation.md) — schemas behind
  every "required check" above.
- [roadmap.md](./roadmap.md) — slice sequence for activating providers.
- [sound-model.md](./sound-model.md) — what the providers ultimately drive.
- [master-bus.md](./master-bus.md) — the mandatory final step before any
  output of these providers can be considered for release.
