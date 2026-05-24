# Admin Integration Strategy

How the internal SNUFFRAGA SOUNDSYSTEM operator console lands under
`schluesselkinder.de/admin` without leaking into the public commerce/project
surfaces and without exposing the inference service to the open internet.

This is the binding architectural contract for every later integration slice.
No live model code, no Dropbox, no GPT, no Stripe — those live behind the
contract layers described here.

## 1. Target Architecture

```text
schluesselkinder.de
  /                public brand site               (public, indexed)
  /shop            public commerce                 (public, indexed)
  /projekte        public projects                 (public, indexed)
  /admin           private operator OS             (auth, noindex)
    /soundsystem
      /lyrics
      /create               (planned)
      /master               (planned)
      /export               (planned)
    /brand                  (planned)
    /releases               (planned)
    /dropbox                (planned)
    /evaluation             (existing read-only inspection surface)
  /admin/api
    /soundsystem            (server-side proxy to inference)
```

`/admin` is **not** a separate product surface. It is an authenticated,
non-indexed module of the existing SCHLÜSSELKINDER web app. The AI music engine
is one of several internal tools hosted there.

Explicit non-goal for this architecture: `ai.schluesselkinder.de` as a separate
subdomain. Rejected because it would add deployment complexity, an extra auth
surface, cookies/CORS overhead, and would frame the engine as a standalone
product rather than an internal label tool.

## 2. Intent-First Interface

**Binding rule.** The operator console exposes creative outcomes, not model
names. The full intent vocabulary is documented in
[operator-interface-principles.md](./operator-interface-principles.md);
the short version is:

> No raw model name (MusicGen, Stable Audio Open, Tencent SongGeneration,
> YuE, ACE-Step, Kokoro, Qwen3-TTS, OpenVoice V2, Fish Speech, VoxCPM2,
> Piper, DiffSinger, OpenUtau, RVC, Demucs, SonicMaster, Matchering, etc.)
> appears in the primary `/admin/soundsystem/*` create flows. Models live
> in the registry, the library's provenance column, the license registry,
> the safety review surface, and the debug drawer — never in the buttons
> the operator presses to make something.

**Primary intents** (the buttons the operator presses):

```text
CREATE LOOP              short instrumental loop or rhythmic bed
CREATE SONG SKETCH       full-length structured song draft
CREATE STEM TRACK        single addressable lane (kick / bass / vocals / …)
CREATE VOICE TAG         short branded vocal stinger
CREATE SPOKEN VOCAL      narrator / spoken intro / podcast bed
CONVERT APPROVED VOICE   timbre transfer over a recorded, consented voice
SINGING EXPERIMENT       lyrics + melody → singing performance
MASTER TRACK             SoundGraph → loudness-shaped master per export profile
EXPORT PACK              frozen release bundle (audio + JSON + cover)
```

Each intent routes server-side to a provider group (see
[model-provider-strategy.md](./model-provider-strategy.md)). The operator
sees the intent, not the routing.

**Operator-debug exception.** A separate, gate-gated debug surface
(`/admin/soundsystem/debug`) lets a power operator override the
auto-selected provider and see model identity. This is for incident
debugging and model evaluation, not for the daily creative workflow.
Every override is recorded as an `audit_event`.

## 3. Admin Route Map

```text
/admin                              Operator Hub (index of internal modules)
/admin/soundsystem                  Soundsystem command grid (intent index)

# Intent surfaces — each presents the matching primary intent as a button.
/admin/soundsystem/loops            CREATE LOOP
/admin/soundsystem/songs            CREATE SONG SKETCH
/admin/soundsystem/stems            CREATE STEM TRACK
/admin/soundsystem/voice-tags       CREATE VOICE TAG
/admin/soundsystem/spoken           CREATE SPOKEN VOCAL
/admin/soundsystem/voice-convert    CONVERT APPROVED VOICE
/admin/soundsystem/singing          SINGING EXPERIMENT
/admin/soundsystem/master           MASTER TRACK
/admin/soundsystem/export           EXPORT PACK

# Authoring + management surfaces (existing or planned).
/admin/soundsystem/lyrics           Lyrics engine (shipped)
/admin/soundsystem/library          Output Library (universal index)
/admin/soundsystem/consent          Consent records manager
/admin/soundsystem/licenses         License registry browser
/admin/soundsystem/safety           Safety review queue
/admin/soundsystem/debug            Provider debug drawer (gated, audit-logged)

# Sibling admin modules.
/admin/brand                        Brand OS                     (future)
/admin/releases                     Release index                (future)
/admin/dropbox                      Dropbox sync hub             (future)
/admin/evaluation                   Read-only inspection surface (existing)
```

All other `/admin/*` routes are reserved. Each new module is added under this
namespace, not as a new top-level surface. Routes are named after the
creative outcome (`/loops`, `/songs`), never after a model.

## 4. Server-Side Inference Proxy

**Status: shipped in S9.** The proxy lives at
`apps/web/app/admin/api/soundsystem/[...path]/route.ts`. The browser only
ever calls relative `/admin/api/soundsystem/*`; the `_lib/inference.ts`
client picks the right base URL based on server-vs-client detection.

Browsers must not call the inference service directly in production.

```text
Browser
  -> /admin/api/soundsystem/<path>        (relative, same origin, gated)
       Next.js route handler (server-side)
         -> SOUNDSYSTEM_INFERENCE_URL/<path>   (private network or localhost)
              FastAPI inference service
                -> Postgres / scratch / future Dropbox
```

Required properties:

- The upstream URL (`SOUNDSYSTEM_INFERENCE_URL`) is **server-side only**. No
  `NEXT_PUBLIC_*` variant in production.
- The proxy lives under the gated `/admin` namespace so all middleware
  protections apply automatically.
- The proxy forwards method, path, query, and body verbatim.
- Sensitive request headers (`Authorization`, `Cookie`) are stripped before
  forwarding — the inference service has its own internal credentials
  surface later, separate from the operator's browser session.
- The proxy returns honest `502`/`503` JSON when upstream is unreachable;
  the operator console renders these as `INFERENCE UNREACHABLE`.
- Rate limits and audit logging are added on the proxy, not on the
  inference service, so every Admin-OS access is observable in one place.
- The proxy is the only route that ever holds inference credentials.

In local development the proxy may still resolve to `http://127.0.0.1:8010`,
and the existing `NEXT_PUBLIC_SOUNDSYSTEM_INFERENCE_URL` may stay as a
backward-compatible legacy fallback — but it must not be required in
production.

## 5. Auth & Gate

**Status: Phase 1 shipped in S9.** The middleware lives at
`apps/web/middleware.ts`; the shared helpers live at
`apps/web/app/admin/_lib/admin-gate.ts`.

Phase 1 (MVP, locks the door before any live ML):

- Server-side env `INTERNAL_CONSOLE_ENABLED=true|false`. When `false` or
  unset in production, all `/admin/*` routes return `404`.
- Basic auth in Next.js middleware:
  `ADMIN_BASIC_AUTH_USER` + `ADMIN_BASIC_AUTH_PASSWORD`.
- Fail closed: missing credentials in production → `404` (we hide the
  console's existence) or `401` with `WWW-Authenticate` when the gate is
  open but credentials are missing/invalid. Production posture without
  basic-auth env vars is `404`.
- Local dev fallback to `NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED` only when
  `NODE_ENV !== "production"`.

Phase 2 (when more than one operator is real):

- NextAuth/Auth.js with magic-link or Google OAuth.
- Operator roles: `owner`, `admin`, `operator`, `viewer`.
- Audit log records the authenticated `operator_id` on every mutating call.
- Phase 1's basic-auth env vars become deprecated, never both active at once.

Phase 3 (only if needed):

- A dedicated SSO vendor (Clerk / Auth0). Not chosen for Phase 1 because
  the SCHLÜSSELKINDER stack has deliberately stayed vendor-light so far.

## 6. Public/Private Separation

The public site and the operator OS share a codebase, **never the same
security logic**:

| Surface           | SEO       | Auth       | Cookies        | Caching     |
| ----------------- | --------- | ---------- | -------------- | ----------- |
| `/`, `/shop`, ... | indexed   | open       | minimal        | aggressive  |
| `/admin/*`        | noindex   | auth-only  | session-only   | none        |
| `/admin/api/*`    | noindex   | auth-only  | session-only   | no-store    |

Concrete requirements:

- Every admin response must include `X-Robots-Tag: noindex, nofollow,
  noarchive`. The middleware appends this header so individual routes can't
  forget.
- Admin pages must export `metadata.robots = { index: false, follow: false }`.
- The site's public navigation never links to `/admin/*`.
- The site's `robots.txt` explicitly disallows `/admin` and `/admin/api`.
- The soundsystem PWA manifest is scoped to `/admin/soundsystem/` and 404s
  when the gate is closed.
- No admin asset URL is exposed under a "sprechender" public path. Icons
  used by the soundsystem manifest live under `/admin/soundsystem/icon-*.png`,
  not the public `/brand/` namespace.

## 7. Model-Provider Categories

Audio generation is modelled as four orthogonal categories. The operator
console routes intents to the matching category; the category decides which
real provider runs.

| Category                         | Intent example                                      |
| -------------------------------- | --------------------------------------------------- |
| `text_to_music` / song generation | "warehouse riddim, 142 BPM, ritual vocal hook"      |
| `text_to_speech` / voice gen     | spoken intros, narrator beds, podcast tools          |
| `voice_clone` / voice conversion | character voices with explicit consent (internal)   |
| `singing_voice` / lyrics-to-song | full vocal performance from lyrics + reference      |

Each category gets a stable provider Protocol and a registry. The contract
layer is provider-agnostic; swapping MusicGen for Stable Audio Open does not
change the API or the UI.

Detailed candidate matrix lives in
[model-provider-strategy.md](./model-provider-strategy.md).

## 8. Model Registry

Every provider that can run inside SCHLÜSSELKINDER is declared once in the
**model registry** with stable metadata:

```text
ModelRegistry
  model_id              uuid
  display_name          "Stable Audio Open"
  category              text_to_music | text_to_speech | voice_clone | singing_voice
  vendor                "Stability AI"
  version               "1.0"
  license               reference into LicenseRegistry
  commercial_status     ready | conditional | research_only | blocked
  required_consent      none | operator_only | subject_consent
  safety_review_status  pending | approved | rejected
  default_runtime       local_gpu | runpod | mock
  created_at, updated_at
```

The registry is the only place where "which provider runs" is decided. Routes
and providers never read free-form env vars to pick a model. Per-category
defaults are stored as fields on the registry, not as code constants.

The registry is data, not code: a future slice persists it in Postgres
alongside `lyrics_projects`. Until then, an in-memory seed file is acceptable.

## 9. License Registry

A separate `LicenseRegistry` table catalogues the licenses we treat as
distinct legal regimes:

```text
LicenseRegistry
  license_id            uuid
  spdx_id               "Apache-2.0" | "MIT" | "CC-BY-NC-4.0" | "custom"
  source_url            primary license text
  permits_commercial    bool
  permits_distribution  bool
  permits_modification  bool
  requires_attribution  bool
  notes                 free text, e.g. weights-only restrictions
  reviewed_by           operator id
  reviewed_at           timestamptz
```

Every entry in `ModelRegistry` references one `LicenseRegistry` row. A model
without a verified license can never reach `commercial_status=ready`.

Specific risk classes the registry must capture honestly:

- **Code license vs. weights license mismatch.** A repository licensed as
  Apache-2.0 may ship weights under a non-commercial research license. Both
  must be recorded; the more restrictive wins.
- **Training-data provenance**. Where it matters for downstream rights
  (some text-to-music models), this is captured in `notes`.
- **Patent-encumbered formats**. Recorded so the export pipeline can avoid
  shipping them in release packages.

## 10. Consent Records

Voice generation and any reference-audio-driven workflow requires a per-
subject `ConsentRecord`:

```text
ConsentRecord
  consent_id            uuid
  subject_name          text                       (the human, not a stage name)
  subject_role          operator | session_artist | guest_artist | other
  scope                 text                       ("internal music drafts under SCHLUESSELKINDER")
  permitted_use         array of free-text + tags
  granted_at            timestamptz
  expires_at            timestamptz | null
  revoked_at            timestamptz | null
  proof_uri             text                       (signed PDF / video / email thread reference)
  reviewed_by           operator id
```

Provider/route rules:

- A `voice_clone` or `singing_voice` job that references a real human voice
  must cite a non-revoked `ConsentRecord` whose `permitted_use` covers the
  job's intent. No consent → preflight block, same shape as the existing
  `voice_likeness_requires_explicit_clearance` block.
- Operators are also subjects when they record their own voice — no shortcuts.
- Public-figure voices (named artists, public personas) are always blocked,
  regardless of consent paperwork. Internal posture: SCHLÜSSELKINDER does
  not produce content that imitates living artists, period.

## 11. Output Library

Every produced artifact (lyrics version, generation job, master, export
manifest) lands in a unified `OutputLibrary` view inside `/admin`:

- Lyrics versions are already typed (`LyricsVersion`); persisted in Postgres
  via `LyricsRepository`.
- Generation jobs persist via `GenerationJobRepository` (in-memory today).
- Master bus jobs persist via `MasterBusRepository` (in-memory today).

The `OutputLibrary` lists all of these with a uniform header (project key,
created, source, status, consent state, license bundle) and links to the
detail surfaces under `/admin/soundsystem/*`.

Slice ordering note: a real `OutputLibrary` page lands **after** every
repository has Postgres persistence. Until then, the lyrics surface stands in
as the only persistent corner.

## 12. Safety / Review Flow

Three independent gates run before any artifact can be marked release-ready:

```text
Preflight Safety (already exists for lyrics + generation)
  ↓
Provider-Local Filters (per-provider, e.g. SonicMaster's clipping check)
  ↓
Safety Review (operator-only step in /admin/soundsystem/export)
```

Detail per gate:

- **Preflight** rejects voice-likeness without clearance, blocks redline
  druck without explicit approval, blocks risky lyric filler patterns (see
  `lyrics_engine.detect_risky_filler`).
- **Provider-local** filters are run inside the provider adapter and recorded
  in `OutputProvenance.safety_notes`.
- **Safety Review** is a manual operator step. An artifact is only
  release-eligible after a `SafetyReviewStatus = approved` record has been
  attached.

Compliance schemas (`SafetyReviewStatus`, `BlockedPromptCategories`,
`OutputProvenance`) live in [compliance-foundation.md](./compliance-foundation.md).

## 13. Metadata & Provenance Requirements

Every artifact carries an `OutputProvenance` record summarising how it was
produced:

- `provider` — `ModelRegistry.model_id`
- `model_version` — exact version + checkpoint hash
- `prompt_tokens` — tokens consumed for prompt processing
- `completion_tokens` — tokens consumed for output (for LLM-driven steps)
- `safety_notes` — list of strings from the compiled prompt + provider filters
- `rewrite_strategy` — `manual | prompt_edit | selection_rewrite | provider_regen`
- `locked_sections_respected` — bool; required `true` for any version that
  derives from a parent with locked sections
- `raw_provider_trace_id` — opaque pointer to the upstream provider's
  request log (for non-human debugging)
- `license_bundle` — list of `LicenseRegistry.license_id` covering provider
  + reference inputs + dataset attribution
- `consent_records` — list of `ConsentRecord.consent_id` cited at preflight

The provenance record is the audit unit: every release-pipeline decision
points back to one provenance row.

## 14. Dropbox Integration Boundary

Dropbox is **not** the system of record. It is an export sink for finished
artifact bundles only. The boundary:

- Inference service writes only to local scratch + Postgres.
- Master bus + export pipeline produces a frozen bundle (audio + JSON +
  cover).
- The bundle is uploaded to Dropbox by a separate sync worker, never by an
  inference adapter.
- The sync worker is the only component holding Dropbox credentials.
- A Dropbox upload failure must not break the artifact. The bundle stays in
  local scratch and the sync is retried later.

Routes:

- `/admin/dropbox` shows the configured target folders, recent sync history,
  and failures. Read-only first, write actions later.
- No Dropbox call ever runs from the browser. All sync calls are server-side
  inside the admin namespace.

## 15. Release / Export Gate

A release candidate cannot leave the system unless every gate is green:

```text
release_eligible = (
  output_provenance.exists
  AND safety_review_status == approved
  AND license_bundle_complete
  AND consent_records_valid
  AND lyric_locked_sections_respected
  AND master_bus.export_ready
  AND dropbox_sync.status in (ok, deferred)
)
```

The release page (`/admin/soundsystem/export` and `/admin/releases`)
surfaces each gate's state. An operator can override locally with a written
justification, recorded in `audit_events`, but the override never becomes
silent.

## 16. Implementation Order

The strategy translates into the following minimum implementation order
(detailed in [roadmap.md](./roadmap.md)):

1. **Admin integration & proxy** — move `/admin` from build-flag visibility
   to real server-side gating; add the inference proxy; remove browser-side
   inference URL exposure.
2. **Compliance foundation tables** — `ModelRegistry`, `LicenseRegistry`,
   `ConsentRecord`, `OutputProvenance`, `SafetyReviewStatus` schemas + seed.
3. **Voice Lab mock** — first surface inside `/admin/soundsystem` that
   exercises the consent-and-provenance flow with a mock provider.
4. **Music provider router mock** — multi-provider routing layer (still
   mock-only) that the lyrics engine and future track engine consume.
5. **GPT-5.5 Lyrics Provider** — first non-mock provider, behind explicit
   env flag with fail-loud validation.
6. **Real model adapters** — one category at a time, gated by license and
   compliance checks.
7. **Dropbox sync worker** — separate from inference.
8. **Release pipeline** — closes the loop with the release-eligibility gate.

## 17. Non-Goals (Now)

- A separate `ai.schluesselkinder.de` subdomain.
- Public sign-up or invite flows under `/admin`.
- Real GPT/OpenAI/Anthropic calls.
- Real model checkpoint downloads or weight management.
- Dropbox writes.
- Commerce-side integration (Stripe, Printful, social automation).
- Customer-facing artifact display. Every output stays internal until the
  release pipeline approves it.
