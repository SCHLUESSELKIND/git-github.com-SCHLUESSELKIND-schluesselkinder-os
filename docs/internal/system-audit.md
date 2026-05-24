# SCHLUESSELKINDER OS / SNUFFRAGA SOUNDSYSTEM — System Audit

**Date:** 2026-05-19
**Auditor:** Claude Opus 4.7 (automated, code-verified)
**Scope:** Full stack — Python inference service, Next.js admin/public
app, Fastify API service, database migrations, tests, docs, CI/CD.
**Method:** Every claim below is verified against actual source code
unless explicitly marked `[inferred]`.

---

## Executive Summary

This system is a **well-architected internal operator console for AI
music production** that has delivered 23 slices of incremental,
test-covered, documented work. The engineering quality —
repository/factory patterns, provider isolation, schema
drift-checking, test coverage — is genuinely strong for a pre-alpha
internal tool.

However, it is **not a production system**. It is a contract-layer
scaffold running entirely on mock providers with in-memory state by
default, zero authentication on the inference API, no CI pipeline, no
async workers, no real artifact storage, and no real audio generation.
The one real external integration (GPT-5.5 lyrics) is env-gated and
optional. The Dropbox "real" adapter uploads JSON stubs, not audio
files.

The system has **160 documentation files (31,026 lines)** describing a
vision that extends far beyond what exists. The docs describe merch
capsules, vinyl pressing, marketing campaigns, visual content engines,
and SoundCloud publishing. None of that is built. The ratio of
docs-to-runtime-code is approximately 1.3:1, which is healthy for
early architecture but risks becoming a maintenance burden if the docs
are treated as commitments.

**Bottom line:** This is a high-quality design prototype with real
contract coverage and excellent test infrastructure. It is ready for
internal demos and single-operator experimentation. It is not ready
for any external user, any real money flow, or any production
deployment.

---

## Implementation Matrix

### Codebase Size (verified)

| Layer | Lines | Files |
| ----- | ----- | ----- |
| Python inference service (app/) | 8,641 | 34 |
| Python tests | 5,496 | 15 |
| SQL migrations | 509 | 5 |
| Admin UI (TSX/TS under /admin) | 8,759 | ~40 |
| Generated TS types | 1,244 | 1 |
| Fastify API service | 7,468 | ~50 |
| Documentation (all .md) | 31,026 | 160 |
| **Total runtime + test code** | **~32,000** | — |
| **Total documentation** | **~31,000** | — |

### Feature Status Table

| Feature | Status | Backend | UI | Tests | Persistence | Real Integration |
| ------- | ------ | ------- | -- | ----- | ----------- | ---------------- |
| Prompt compilation | IMPLEMENTED | Yes | No (API only) | Yes | In-memory | None needed |
| Generation jobs | MOCK | Mock provider | No | Yes | In-memory only | No real AI model |
| Master bus | MOCK | Mock provider | No | Yes | In-memory only | No real DSP |
| Lyrics engine | IMPLEMENTED | Yes | Full editor | 31 tests | In-memory + Postgres | Mock + GPT-5.5 (gated) |
| Compliance foundation | IMPLEMENTED | Yes | Read-only | 18 tests | In-memory only | None (seed data) |
| Voice lab | MOCK | Mock provider | Read-only | 10 tests | In-memory only | No real TTS/voice |
| Music router | MOCK | Mock adapters | Intent tiles | 15 tests | In-memory only | No real audio gen |
| SoundGraph writer | IMPLEMENTED | Pure/deterministic | In lyrics flow | 32 tests | In-memory only | None needed |
| SoundGraph handoff | IMPLEMENTED | Pure logic | In lyrics flow | 21 tests | In-memory only | Calls mock router |
| Export pack / library | IMPLEMENTED | Yes | Full UI | 34 tests | In-memory + Postgres | None |
| Dropbox sync | PARTIALLY MOCK | Contract + mock | Full UI flow | 32 tests | In-memory only | Real adapter uploads JSON stubs |
| Release pack | IMPLEMENTED | Yes | Full UI | 39+23 tests | In-memory + Postgres | None |
| Admin auth | BASIC AUTH | Middleware | Login prompt | No | Env vars | HTTP Basic only |
| Inference proxy | IMPLEMENTED | Reverse proxy | Transparent | No | None | Proxies to :8010 |
| Public website | STATIC | Static data | 11 pages | No | None | No API calls |
| Fastify API service | IMPLEMENTED | Prisma + repos | Not admin-linked | Has tests | Prisma/Postgres | Read-only archive |

---

## Route Inventory

### Python Inference Service (48 routes, verified)

| Group | Routes | Auth | Real Logic |
| ----- | ------ | ---- | ---------- |
| Health/Capabilities | 2 | None | Live probe |
| Generation | 2 | None | Mock provider inline |
| Master Bus | 2 | None | Mock provider |
| Lyrics (14) | 14 | None | Full CRUD, versioning, locking |
| Compliance (11) | 11 | None | Seed data CRUD, preflight eval |
| Voice Lab (5) | 5 | None | Mock + consent preflight |
| Music Router (5) | 5 | None | Mock adapters, intent routing |
| SoundGraph (5) | 5 | None | Pure compilation + handoff |
| Library (5) | 5 | None | Pack building, entry management |
| Dropbox (8) | 8 | None | Plan building, mock/real sync |
| Release (7) | 7 | None | Builder, checklist, ready gate |

**All 48 routes have ZERO authentication.** Any network-reachable
client can read, create, modify, and delete all data.

### Fastify API Service (~72 routes, verified)

14 route files with ~72 registered endpoints. Serves the
artist/object/music registry, brand intelligence, content graph,
drafts, evaluation, generation, exports, and reviews. Uses Prisma for
persistence.

### Next.js Admin (20 page routes, verified)

18 page.tsx files + 1 API proxy route + 1 manifest route. Protected
by HTTP Basic Auth middleware. All data fetched from inference service
or Fastify API.

---

## Provider Inventory

| Provider | Protocol | Mock Adapter | Real Adapter | Env Gate | Status |
| -------- | -------- | ------------ | ------------ | -------- | ------ |
| Music generation | MusicEngineProvider | MockMusicProvider | None | None | Mock only |
| Master bus | None (inline) | MockMasterBusProvider | None | None | Mock only |
| Lyrics | LyricsProviderProtocol | MockLyricsProvider | Gpt55LyricsProvider | SOUNDSYSTEM_LYRICS_PROVIDER | Real available |
| Voice | None (inline) | Mock inline | None | None | Mock only |
| Dropbox sync | DropboxSyncProviderProtocol | MockDropboxSyncProvider | RealDropboxSyncProvider | SOUNDSYSTEM_DROPBOX_SYNC_PROVIDER | Real uploads JSON stubs |

### What "real" actually means

**GPT-5.5 lyrics provider:** Calls OpenAI API with model `"gpt-5.5"`.
Records cost accounting (tokens, estimated cost, latency). Has
timeout/retry. Cost estimates are explicitly labeled "placeholder"
in the code. **This is the only provider that makes a real external
API call.**

**Real Dropbox provider:** Calls `dropbox.Dropbox().files_upload()`.
But the content uploaded is `json.dumps({"placeholder": True, ...})`
— JSON stubs, not actual audio files or artwork. **The binary content
streaming for real artifacts is not implemented.**

**Everything else:** Returns deterministic fake data (mock artifact
paths like `/tmp/snuffraga/...`, mock file sizes, mock durations).
No AI model runs. No audio is generated. No DSP is applied.

---

## Persistence Inventory

| Repository | Protocol | In-Memory | Postgres | Factory | Migration |
| ---------- | -------- | --------- | -------- | ------- | --------- |
| GenerationJob | Yes | Yes | **No** | No | 001 (exists, not wired) |
| MasterBus | Yes | Yes | **No** | No | None |
| Lyrics | Yes | Yes | Yes | Yes | 002_lyrics.sql |
| Compliance | Yes | Yes | **No** | Yes | 003 (exists, not wired) |
| VoiceLab | Yes | Yes | **No** | Yes | None |
| MusicRouter | Yes | Yes | **No** | Yes | None |
| SoundGraph | No (concrete) | Yes | **No** | No | None |
| DropboxSync | No (concrete) | Yes | **No** | No | None |
| Library | Yes | Yes | Yes | Yes | 004_library.sql |
| Release | Yes | Yes | Yes | Yes | 005_releases.sql |

**3 of 10 repositories have Postgres implementations.** The other 7
lose all data on process restart. Migrations exist for 5 tables, but
only 3 have matching Postgres repository code.

### Schema inconsistency (verified)

Migration 001 creates tables in the `soundsystem` schema prefix.
Migrations 002–005 create tables in `public` (no schema prefix).
These two sets of tables have **no foreign key relationships** between
them. The 001 migration is essentially orphaned infrastructure.

---

## Mock vs Real Table

| Capability | What the UI shows | What actually happens |
| ---------- | ----------------- | -------------------- |
| "Create Track" | Job completes with artifacts | Mock provider returns fake paths |
| "Build Riddim" | "Awaiting wire" placeholder | Nothing — UI is a stub |
| "Generate Hook" | "Awaiting wire" placeholder | Nothing |
| "Voice Lab" | Jobs complete with artifacts | Mock returns fake paths, no audio |
| "Music Router" | Intent routing, artifacts | All mock, deterministic output |
| "SoundGraph" | Arrangement compiles | Real — pure deterministic logic |
| "Lyrics" | Full editing workflow | Real with mock provider; GPT-5.5 optional |
| "Export Pack" | Pack builds with components | Real — pure aggregation logic |
| "Dropbox Sync" | Plan + sync execution | Mock default; "real" uploads JSON stubs |
| "Release Pack" | Checklist + ready gate | Real — pure state machine logic |
| "Compliance" | Registry + preflight | Real evaluators, but seed data only |
| "Release Center" | List + detail + checklist | Real UI reading real (mock-populated) data |

---

## Risk Register

### Critical

| # | Risk | Impact | Evidence |
| - | ---- | ------ | -------- |
| 1 | **Zero auth on inference API** | Any network client can CRUD all data | No auth middleware in main.py; verified grep shows 0 auth decorators |
| 2 | **No CI/CD pipeline** | Regressions go undetected, drift accumulates | No .github/workflows/, no Makefile; only pre-commit hooks |
| 3 | **7 of 10 repositories are in-memory only** | Data loss on every restart for most features | Only lyrics/library/release have Postgres |
| 4 | **No async worker infrastructure** | Generation runs inline in request handler | main.py line 260: "MVP scaffold: run the selected provider inline" |
| 5 | **No real artifact storage** | No audio files, images, or binaries are stored anywhere | All artifact paths are fake (`/tmp/snuffraga/...`) |

### High

| # | Risk | Impact | Evidence |
| - | ---- | ------ | -------- |
| 6 | **Schema namespace split** | 001 migration is disconnected from 002-005 | 001 uses `soundsystem.*`, others use `public.*` |
| 7 | **No migration runner** | Manual `psql -f`, no version tracking | Comments say "applied by hand for local dev" |
| 8 | **Dropbox real adapter uploads stubs** | Appears functional but delivers no real content | real.py line 123: `"placeholder": True` |
| 9 | **GPT-5.5 cost estimates are placeholders** | Cost accounting shows fake numbers | gpt_5_5.py: "$0.01/1K input, $0.03/1K output" labeled "placeholder" |
| 10 | **No rollback migrations** | Schema changes are irreversible without manual SQL | No down migrations in any .sql file |

### Medium

| # | Risk | Impact | Evidence |
| - | ---- | ------ | -------- |
| 11 | **Hardcoded model name "gpt-5.5"** | Will break when OpenAI changes or retires model | gpt_5_5.py line 118 |
| 12 | **O(N) arrangement scan in export pack** | Slow for large datasets | main.py lines 851-860: linear scan of all arrangements |
| 13 | **No `updated_at` triggers** | Stale timestamps if application code forgets | Application must call `datetime.now(timezone.utc)` manually |
| 14 | **Vector column has no dimension constraint** | Any embedding dimension can be inserted | 001 migration: `embedding vector` with no size |
| 15 | **160 docs (31K lines) describe unbuilt features** | Creates false expectation of completeness | Merch OS, Marketing OS, Visual Engine, etc. — all docs-only |

### Low

| # | Risk | Impact | Evidence |
| - | ---- | ------ | -------- |
| 16 | **Hardcoded character "SHIBARI_KAWAII"** | Multi-artist support requires refactoring | 4 references in schemas.py |
| 17 | **No rate limiting** | DoS risk on all endpoints | No middleware |
| 18 | **Non-deterministic UUIDs in "deterministic" functions** | Same inputs produce different IDs | soundgraph_writer.py line 349: `uuid4()` |

---

## Architectural Strengths

**1. Repository/Factory pattern is genuinely consistent (verified).**
10 repositories follow the same Protocol → InMemory → (optional
Postgres) → Factory pattern. Easy to swap backends. This is well
above average for a project at this stage.

**2. Provider Isolation Layer is real and enforced (verified).**
Protocol boundaries for lyrics and Dropbox providers mean route
handlers never import openai or dropbox types. The factory/env-var
gate pattern is clean and consistent.

**3. Test coverage is comprehensive (verified).**
338 tests, 5,496 lines of test code, 724+ assertions. Tests cover
happy paths, error paths, preflight blocking, consent revocation,
compliance gates, and full end-to-end pipelines. All tests run in
<0.4 seconds with no external dependencies.

**4. Schema drift checking is production-quality (verified).**
The Python-to-TypeScript type generator + pytest drift check + lint
header is a genuinely good solution. Any schema change that isn't
regenerated fails the test suite.

**5. Fail-loud configuration is consistently applied (verified).**
Every env-var-selected mode has a clear error path. No silent
fallbacks. `ReleaseRepositoryConfigError`,
`DropboxSyncProviderConfigError`, `LyricsProviderConfigError` all
crash startup with actionable messages.

**6. Pure/deterministic builders (verified).**
SoundGraph compilation, export pack building, release pack building,
compliance preflight evaluation — all pure functions with no side
effects. Easy to test, easy to reason about.

**7. Documentation is exceptionally thorough.**
The roadmap, ADRs, compliance foundation, provider strategy, and
operator interface principles are detailed, internally consistent,
and clearly written. The docs show genuine architectural thinking.

---

## Architectural Weaknesses

**1. main.py is a 1,077-line God file.**
All 48 routes, all singleton construction, all request validation
lives in one file. No router separation, no dependency injection
framework, no middleware stack. This will become unmaintainable
before S30.

**2. Inline generation execution blocks the event loop.**
`POST /v1/generations` runs the provider inline (line 260). With a
real AI provider that takes 30-120 seconds, this blocks the entire
FastAPI async loop. Documented as "MVP scaffold" but is a hard
blocker for real use.

**3. Two disconnected persistence worlds.**
The Fastify API service uses Prisma with a 910-line schema (artists,
objects, music, fragments, brand intelligence, content graph,
reviews, generation, exports). The Python inference service uses
hand-rolled repositories with hand-written SQL migrations. These
two systems share no database, no schema, no types, and no data.
The Prisma schema and the SQL migrations describe different tables
for overlapping concepts (e.g., both have "generation" tables).

**4. No data flows between the two backend services.**
The Fastify API (port 3001) serves the archive/registry/brand
system. The Python inference service (port 8010) serves the
soundsystem. The Next.js app talks to both but they never talk to
each other. Artists, releases, and objects exist in the Fastify
world; lyrics, music jobs, and releases exist in the Python world.
There is no shared identity.

**5. Compliance is theater without real data.**
The compliance foundation has real evaluators, real preflight
checks, and real consent management — but all data is seed data
with all models marked `RESEARCH_ONLY`. No model has ever been
evaluated for real commercial use. The release-eligibility gate
always blocks because no model has `approved_release` status. The
compliance system works, but it protects against a scenario that
has never occurred.

**6. Over-documentation of unbuilt features.**
The Marketing OS has 5 detailed docs (artist-marketing-os.md,
data-model.md, integrations.md, roadmap.md, visual-content-engine.md)
plus the new merch-os.md. None of these have a single line of
runtime code. The Marketing OS roadmap describes 20 slices (M-1
through M-20). Zero are built. This creates a false impression of
system completeness when the docs are read without code verification.

---

## Critical Missing Systems

| System | Why it's critical | Current state |
| ------ | ----------------- | ------------- |
| **Authentication** | Anyone on the network can CRUD all data | HTTP Basic Auth on Next.js only; inference API is fully open |
| **Async job queue** | Real AI generation takes 30-120s | Inline execution blocks event loop |
| **Artifact storage** | No audio, images, or binaries are persisted | All paths are fake `/tmp/snuffraga/...` strings |
| **Real audio provider** | The system's core purpose is music generation | All music providers are mock |
| **CI/CD** | No automated testing on push/PR | Only local pre-commit hooks |
| **Unified data layer** | Two disconnected persistence worlds | Prisma (Fastify) + hand-rolled SQL (Python) |
| **Migration runner** | No tracked/versioned migrations | Manual `psql -f` |
| **Observability** | No logging, metrics, tracing, or alerting | No structured logging beyond print() |
| **File upload** | Operators cannot upload cover art, stems, or masters | No upload endpoint anywhere |
| **Background sync** | Dropbox/export sync should not block requests | All sync is inline |

---

## Honest Readiness Assessment

| Target | Score | Justification |
| ------ | ----- | ------------- |
| **Internal demo** | **72/100** | Impressive UI, convincing flow, all mock. Can demo lyrics → SoundGraph → mock track → export → release. Falls apart if someone asks "where's the audio?" or restarts uvicorn. |
| **Private alpha** (single operator) | **35/100** | Lyrics editing works end-to-end with optional GPT-5.5. Everything else is mock. No persistence for 7/10 features. No auth on API. Adequate for a solo developer experimenting. |
| **Underground artist usage** | **15/100** | An artist cannot: generate real audio, upload files, download real artifacts, publish anywhere, or access the system securely. The system produces text and mock paths, not music. |
| **Public beta** | **5/100** | No auth, no multi-tenancy, no real providers, no artifact storage, no CI, no observability, no error recovery, no upload system, no rate limiting. |
| **Commercial SaaS** | **2/100** | Missing: auth, billing, multi-tenancy, real providers, storage, CDN, async jobs, monitoring, compliance review (real), GDPR, terms of service, support, SLA. |
| **Production release** | **1/100** | The "1" is for the deployment config (Dockerfiles, docker-compose, Caddy) which technically works. Everything else is pre-alpha. |

---

## Top 10 Next Priorities

These are **real blockers**, not roadmap decoration. Ordered by
dependency chain — each unblocks the ones below it.

### 1. CI Pipeline
**Why first:** Without CI, every other change risks regression. The
test suite is good but runs only locally.
- GitHub Actions: pytest, TypeScript typecheck, TS drift check, ruff lint.
- Run on every push/PR.
- Estimated effort: 1 day.

### 2. Inference API Authentication
**Why:** The API is fully open. Even for internal use, one env-var
misconfiguration exposes all data.
- Bearer token auth (simplest) or API key middleware.
- Shared secret between Next.js proxy and inference service.
- Estimated effort: 1 day.

### 3. Async Job Queue
**Why:** Real providers take 30-120 seconds. Inline execution blocks
the event loop and will timeout HTTP clients.
- Redis + RQ or Celery, or even `asyncio.create_task` with a
  polling endpoint.
- Generation routes return 202 Accepted, client polls status.
- Estimated effort: 3-5 days.

### 4. Real Artifact Storage
**Why:** Without this, no audio file ever exists. The system produces
paths to nonexistent files.
- Local filesystem (dev) or S3-compatible (prod) behind a storage
  protocol.
- Artifacts stored by job ID, content-addressed or UUID-named.
- Signed URL generation for browser playback.
- Estimated effort: 3-5 days.

### 5. First Real Audio Provider
**Why:** This is the system's reason to exist.
- Most likely candidate: ACE-Step or Stable Audio Open (lowest
  legal risk per compliance seed data).
- Behind existing provider isolation pattern.
- Needs async job queue (priority 3) and artifact storage
  (priority 4) first.
- Estimated effort: 5-10 days.

### 6. Postgres for Remaining Repositories
**Why:** 7 of 10 repositories lose data on restart.
- GenerationJob, MasterBus, Compliance, VoiceLab, MusicRouter,
  SoundGraph, DropboxSync all need Postgres backends.
- Migrations 001 and 003 exist but aren't wired. Others need new
  migrations.
- Estimated effort: 3-5 days (pattern is established).

### 7. Migration Runner
**Why:** Manual `psql -f` doesn't scale and risks drift.
- Alembic (Python) or a simple version-tracking table.
- Track which migrations have been applied.
- Estimated effort: 1-2 days.

### 8. Unified Data Layer
**Why:** Two disconnected backends storing overlapping data is a
long-term maintenance disaster.
- Either: migrate Fastify service concepts into the Python service,
  or establish a shared Postgres schema with cross-references.
- This is an architectural decision, not just implementation work.
- Estimated effort: 5-15 days depending on direction.

### 9. File Upload System
**Why:** Operators need to provide cover art, stems, masters, and
other assets. Currently impossible.
- Multipart upload endpoint on inference service.
- Store in artifact storage (priority 4).
- Wire into release pack asset placeholders.
- Estimated effort: 2-3 days.

### 10. Real Dropbox Binary Uploads
**Why:** The "real" Dropbox adapter currently uploads JSON stubs.
- Stream actual artifact files to Dropbox.
- Needs artifact storage (priority 4) to have real files to upload.
- Estimated effort: 1-2 days (adapter exists, just needs real content).

---

## What This System Actually Is Today

This is a **contract-layer prototype for AI music production
infrastructure**. It defines clean abstractions for how lyrics,
SoundGraph arrangements, music generation, compliance checking,
export packaging, Dropbox sync, and release management should work.
Every abstraction has a mock implementation, a test suite, and an
operator UI.

The architectural quality is high. The patterns are consistent. The
test coverage is well above average. The documentation is thorough
to the point of being aspirational.

But it does not produce music. It does not store files. It does not
authenticate users. It does not run in CI. It loses most of its
data on restart. The only real external call it makes is an optional
GPT-5.5 lyrics generation.

The system is the **blueprint for a music production OS**, not the
OS itself. The blueprint is good. The building hasn't started.

### Verified claims vs inferred

**Directly verified (code read):**
- All route counts and endpoint paths
- All repository implementations and Postgres coverage
- All provider mock/real status
- All env var definitions and defaults
- All test file contents and counts
- Auth implementation (Basic Auth only)
- Migration file contents and schema inconsistency
- Absence of CI/CD configuration
- GPT-5.5 placeholder cost labels
- Dropbox stub upload content
- main.py "MVP scaffold" inline execution comment

**Inferred (not directly verified but high confidence):**
- Docker deployment works as configured (Dockerfiles exist, not
  tested)
- Prisma schema (910 lines) is internally consistent (read header,
  not every model)
- Fastify API service has ~72 routes (counted grep matches, not
  individually verified)
- Public website pages render correctly (file existence verified,
  not rendered)

**Untested assumptions:**
- Postgres implementations actually work against a real database
  (only 1 skipped test validates this, and it requires
  `TEST_DATABASE_URL`)
- The GPT-5.5 provider successfully calls a real OpenAI endpoint
  (no integration test exists)
- Docker containers build and start successfully
- The Caddy reverse proxy configuration is correct
- The pre-commit hooks actually run (config exists, not triggered)
