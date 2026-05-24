# SNUFFRAGA SOUNDSYSTEM Inference

Internal FastAPI scaffold for AI music generation workflows.

This service currently includes:

- health endpoint
- capabilities endpoint (engines, intents, prompt modules, stem lanes, effect devices, mastering modes, export profiles, lyrics section types, lyrics sources)
- modular prompt compiler with stem plan, tempo, druck, and effect rack output
- 12-lane SoundGraph stem model (`kick` → `return_reverb`)
- in-memory generation job scaffold
- provider registry with mock fallback
- two-call provider contract: `start()` and `get_status()`
- SNUFFRAGA MASTER BUS contract layer with mock provider and in-memory repository
- SNUFFRAGA LYRICS ENGINE contract layer with versioned drafts, manual edits, selection variants, and SoundGraph export manifest
- Compliance Foundation (S10): license/model/consent/provenance/audit registries, preflight + release-eligibility evaluators, 10 `/v1/compliance/*` routes, in-memory repository seeded research-only
- Voice Lab Mock (S11): consent-gated voice tag/spoken vocal/voice convert flow with mock provider emitting provenance + consent citations
- Music Provider Router Mock (S12): intent-driven routing (6 intents), mock adapters for all provider groups, deterministic artifacts, provenance on every completed job
- First Real Provider Boundary (S13): GPT-5.5 lyrics provider behind Provider Isolation Layer (Protocol), cost accounting (prompt_tokens/completion_tokens/estimated_cost_usd/latency_ms), hard timeout (env-configurable), shadow prompt logging (raw_operator_prompt/system_prompt_version/safety_transformations), factory-selected via SOUNDSYSTEM_LYRICS_PROVIDER env var
- SoundGraph Manifest Writer (S14): compiles LyricsVersion → SoundGraphArrangement (regions, vocal entries, lane assignments, energy maps), pure/deterministic, 4 energy profiles, 12-lane genre conventions, bar overrides, in-memory repository
- SoundGraph → Music Router Handoff (S15): closes the text-to-production loop — arrangement → intent resolution → prompt compilation → music router job → artifacts → provenance chain
- Export Pack / Project Library (S17): bundles completed MusicJob + Artifacts + LyricsVersion + SoundGraphArrangement + OutputProvenance into exportable project packs with library entries, slug-based catalogue, component inventory, duration estimation
- Persistent Project Library (S19): dual-mode library repository (in-memory / Postgres) behind `SOUNDSYSTEM_LIBRARY_REPOSITORY` env var, `db/004_library.sql` migration, psycopg_pool connection pooling, JSONB component storage, survives uvicorn restarts in Postgres mode
- Dropbox Export Sync (S20): deterministic folder plan builder from ExportPack, sync job lifecycle (PLANNED → READY_FOR_SYNC → SYNCED), mock provider (no real Dropbox API), in-memory repository, operator UI with folder tree view
- Real Dropbox Adapter Boundary (S21): Provider Isolation Layer for Dropbox sync — `DropboxSyncProviderProtocol`, mock adapter (default), real Dropbox SDK adapter behind `SOUNDSYSTEM_DROPBOX_SYNC_PROVIDER=dropbox` + `DROPBOX_ACCESS_TOKEN`, fail-loud without token, no silent fallback, upload-only (never deletes), factory-selected at startup
- Release Pack / SoundCloud Handoff (S22): ExportPack → ReleasePack with title, artist, description, social copy (SoundCloud/TikTok/Instagram), compliance checklist (6 items, all-must-pass gate), asset placeholders (cover/master/preview/stems), Dropbox release target, DRAFT → READY lifecycle, operator UI with checklist toggle + mark-ready flow
- Release Pack Persistence (S23): dual-mode release repository (in-memory / Postgres) behind `SOUNDSYSTEM_RELEASE_REPOSITORY` env var, `db/005_releases.sql` migration, psycopg_pool connection pooling, JSONB storage for social_copy/checklist/assets, survives uvicorn restarts in Postgres mode
- API Auth (S25): API key authentication with `SOUNDSYSTEM_API_KEY` env var, `X-API-Key` header, dev operator fallback, auth dependency injection
- Job Queue (S26): async job queue with configurable concurrency, FIFO scheduling, job lifecycle (QUEUED → RUNNING → COMPLETED/FAILED), worker pool, retry policy
- Artifact Storage (S27): local filesystem artifact storage with path traversal protection, deterministic storage keys, base64 upload/download, artifact lifecycle (PLANNED → STORED), summary stats
- Artifact Bridge (S28): MusicJob → Artifact bridge — automatic artifact creation from completed jobs, provenance linking, batch artifact generation from job outputs
- Postgres Artifact Registry + Signed URL Policy (S29): dual-mode artifact metadata registry (in-memory / Postgres) behind `SOUNDSYSTEM_ARTIFACT_REGISTRY` env var, `db/006_artifacts.sql` migration, psycopg_pool connection pooling, HMAC-SHA256 signed download URLs behind `SOUNDSYSTEM_ARTIFACT_ACCESS_MODE` (direct/signed), token generation + validation, download-link route, file bytes never stored in Postgres
- Artifact Admin UI (S30): read-only artifact storage inspector in admin console, summary grid, kind breakdown, artifact detail page with signed download link, storage key hidden under debug, ARTIFACT_LIBRARY command intent
- Cover Upload Pipeline (S31): first real operator asset upload — cover artwork PNG/JPG via base64, Pillow dimension validation (min 1400x1400 px, square required, recommended 3000x3000 px), SVG/WebP rejected, stored through ArtifactStorage as `cover_art` kind, attached to ReleasePack asset placeholder with `artifact_id`, upload UI in Release Center detail view, no audio upload yet, no publishing yet
- Audio Master Upload Pipeline (S32): second operator asset upload — WAV audio masters via base64, stdlib `wave` header validation (channels, sample rate, bit depth, duration), MP3/AAC/FLAC/M4A rejected, max 120 MB, warnings for mono/16-bit/44.1kHz/long duration, stored through ArtifactStorage as `audio_master` kind, metadata (channels/sample_rate/bit_depth/duration) returned in response, upload UI with metadata display in Release Center detail view
- Stem Pack Upload Pipeline (S33): third operator asset upload — stem pack ZIP archives via base64, stdlib `zipfile` validation (path traversal blocked, no encrypted entries, no absolute paths, max 64 files, max 1 GB uncompressed, allowed extensions: .wav/.aiff/.aif/.txt/.json/.md), RAR/7z/TAR rejected, max 250 MB, warnings for no audio stems/no manifest/large uncompressed, stored through ArtifactStorage as `stem_pack` kind, entry manifest returned in response, upload UI with file list preview in Release Center detail view, no stem generation, no extraction UI, no chunked upload yet
- Release Export ZIP Builder (S34): deterministic release export ZIP from ReleasePack uploaded assets (cover art, audio master, stem pack) plus release metadata, social copy, and manifest.json with SHA-256 checksums, partial exports allowed with warnings, fails if all assets missing, stored via ArtifactStorage as `export_pack` kind, export UI with build button + entry list + warnings + artifact link in Release Center detail view, no publishing, no distribution provider
- S3/R2 Artifact Storage Adapter (S35): optional S3-compatible storage backend behind `SOUNDSYSTEM_ARTIFACT_STORAGE=s3`, supports Cloudflare R2/AWS S3/MinIO, lazy boto3 import (local mode never touches it), path-style addressing for R2/MinIO, presigned GET URLs or public base URL for downloads, no deletes, no bucket listing, no arbitrary keys, credentials never exposed in logs/errors/UI, `[s3]` pip extra for boto3
- SoundCloud Publishing Adapter Boundary (S36): provider-gated SoundCloud publishing contract with mock provider default. Mock provider returns deterministic metadata previews and marks jobs as `published_mock`. Real provider boundary exists but always returns BLOCKED status (OAuth not implemented). Routes: `POST /v1/soundcloud/preview`, `POST /v1/soundcloud/jobs`, `GET /v1/soundcloud/jobs`, `GET /v1/soundcloud/jobs/{job_id}`, `POST /v1/soundcloud/jobs/{job_id}/publish-mock`, `GET /v1/soundcloud/summary`. SoundCloud Handoff UI in Release Center detail view with preview → create job → mock publish flow. No real SoundCloud API calls, no OAuth, credentials never exposed.
- Merch Capsule Contract (S37): merch commerce contract layer that converts a ReleasePack into capsule/drop planning objects with mock provider export. Product philosophy: 70% unavailable, 20% limited, 10% always-on, max 5 active products per capsule. Three provider groups: apparel (Printful), premium drop (Gelato), vinyl (elasticStage/DISC_ARCHIVE). Routes: `POST /v1/merch/capsules`, `GET /v1/merch/capsules`, `GET /v1/merch/capsules/{id}`, `POST /v1/merch/capsules/{id}/lock`, `POST /v1/merch/capsules/{id}/export-mock`, `GET /v1/merch/summary`. Merch Capsule panel in Release Center detail view with build → lock → export mock flow. No real Printful/TikTok Shop/Shopify API calls. TikTok Shop is top-of-funnel only. Provider names appear in operations/debug surfaces, not primary create flow.
- Ditto Distribution Contract (S38): distribution pack lifecycle, mock provider, no real distributor API calls
- Shopify Draft Export (S39): product draft export contract, mock Shopify API adapter
- Printful Sync Contract (S40): print-on-demand sync, mock Printful adapter
- TikTok Shop Adapter Boundary (S41): TikTok Shop listing contract, mock adapter, no real TikTok API
- Merch Provider Aggregation (S42): cross-provider merch status aggregation dashboard
- Campaign OS (S43): campaign lifecycle (DRAFT → PLANNING → ACTIVE → COMPLETE → ARCHIVED), channel task management, campaign builder from release
- Vinyl Release Contract (S44/S45): vinyl pressing lifecycle with manual handoff, no manufacturing orders, deterministic export payloads
- Campaign Timeline / Calendar UI (S48): campaign list + detail pages with channel lanes, task cards, timeline feed
- Analytics Event Graph Foundation (S49): unified internal analytics model — AnalyticsEvent schema, InMemoryAnalyticsRepository, aggregation (heat/viral scores), 7 API routes, 46 tests, Intelligence page, INTELLIGENCE intent tile
- Intelligence Engine (S50): deterministic correlation layer — viral moment detection, audience heatmaps, revenue correlations, timeline fusion, 5 API routes, 50 tests, deep analytics dashboard upgrade. **No ML. No AI inference. No predictive models. No provider API calls.** All functions are pure, deterministic, and operate exclusively on the internal AnalyticsEvent graph. Future provider connectors must normalize into AnalyticsEvent first; the Intelligence Engine never calls external APIs directly.
- Provider Connector Framework (S51): unified adapter architecture for all provider boundaries. `ProviderConnectorRegistryProtocol` + `InMemoryConnectorRegistry` with register/list/get/health/summary. 11 default connectors seeded (5 mock existing boundaries, 5 disconnected future providers, 1 manual always-ready). Provider normalization layer (`normalize_streaming_event`, `normalize_social_event`, `normalize_commerce_event`, `normalize_distribution_event`) converts structured provider data into `AnalyticsEvent`. 5 API routes, 56 tests, Connectors dashboard page, CONNECTORS intent tile. **No real API calls. No auth flows. No ingestion workers. No webhook listeners. No scheduling.** Future providers plug into this registry and normalize into AnalyticsEvent.
- Mock Platform Connector Contracts (S52): concrete mock adapter implementations for Spotify, TikTok, Instagram, SoundCloud, and Shopify. Each adapter produces deterministic normalized `AnalyticsEvent` previews with platform-specific metrics. `preview-sync` now uses adapter-specific events when available, with generic fallback for unsupported connectors. `POST /v1/connectors/{type}/import-demo` imports mock events into the analytics repository (requires operator, explicit POST only). 46 tests, connector preview chips on dashboard. **No real provider API calls. No credentials. No OAuth. No webhooks. No background jobs.** Future real connectors replace mock adapter implementations.
- Analytics Persistence + Connector Import Audit (S53): dual-mode analytics repository (in-memory / Postgres) behind `SOUNDSYSTEM_ANALYTICS_REPOSITORY` env var. `build_analytics_repository()` factory, `PostgresAnalyticsRepository` (delegates to in-memory until real pool wired). Connector Import Audit Log: `ConnectorImportAuditRepository` Protocol + InMemory + Postgres + factory behind `SOUNDSYSTEM_CONNECTOR_IMPORT_AUDIT` env var. Every `import-demo` call creates an audit record with connector_type, operator_id, event_count, event_ids, status. `GET /v1/connectors/import-audit` (filterable by connector_type, operator_id), `GET /v1/connectors/import-audit/summary`. `db/010_analytics.sql` migration. 57 new tests, Import Audit section on Connectors dashboard. **No real database calls in in-memory mode. Postgres mode requires `SOUNDSYSTEM_DATABASE_URL`.**
- Intelligence Snapshot Persistence (S54): frozen point-in-time `IntelligenceOverview` snapshots. `IntelligenceSnapshotRepository` Protocol + InMemory + Postgres + factory behind `SOUNDSYSTEM_INTELLIGENCE_SNAPSHOT_REPOSITORY` env var. `POST /v1/intelligence/snapshots` (requires operator — creates snapshot from current analytics events), `GET /v1/intelligence/snapshots` (list, filterable by status), `GET /v1/intelligence/snapshots/{id}`, `GET /v1/intelligence/snapshots/summary` (includes heat_delta_from_previous). Previous snapshots auto-superseded on new creation. `db/011_intelligence_snapshots.sql` migration. 43 new tests, CREATE SNAPSHOT button + snapshot summary strip + snapshot history on Intelligence dashboard. **No automation. No scheduler. No background workers. Snapshots created only by explicit operator POST. No provider API calls.**
- Intelligence Snapshot Diff View (S55): deterministic read-only comparison between two `IntelligenceSnapshot`s. Pure diff engine at `app/intelligence_snapshot_diff.py` — `compare_snapshots()` produces `IntelligenceSnapshotDiff` with platform deltas (sorted by absolute heat_delta), viral moment changes (matched by title; appeared/disappeared/strength-changed), revenue delta, warning changes, and overall direction heuristic (improved/declined/mixed/unchanged). `GET /v1/intelligence/snapshots/diff/{before_id}/{after_id}`. Schemas: `SnapshotDiffDirection`, `SnapshotMetricDelta`, `SnapshotPlatformDelta`, `SnapshotViralMomentDelta`, `IntelligenceSnapshotDiff`. Dashboard auto-diffs latest two snapshots. 40 new tests. **Read-only. No persistence. No ML. No external calls. No automation.**
- Campaign Persistence (S56): dual-mode campaign repository (in-memory / Postgres) behind `SOUNDSYSTEM_CAMPAIGN_REPOSITORY` env var. `build_campaign_repository()` factory, `PostgresCampaignRepository` with JSONB for channels, tasks, timeline, warnings. `CampaignRepositoryConfigError` for fail-loud on misconfiguration. `db/012_campaigns.sql` migration with indexes on created_at, release_id, status. Capabilities expose `campaign_repository_mode`. 39 new tests (28 in-memory + 11 Postgres lifecycle when TEST_DATABASE_URL set). Existing S45 campaign tests pass unchanged. **Default in_memory. No automation. No scheduler. No social API calls. No destructive deletes.**
- Public Newsletter Subscribe (S66): minimal, privacy-respecting public endpoint at `POST /v1/public/newsletter/subscribe` that forwards to a self-hosted Listmonk instance when configured. Four env vars (`SOUNDSYSTEM_LISTMONK_BASE_URL`, `SOUNDSYSTEM_LISTMONK_USERNAME`, `SOUNDSYSTEM_LISTMONK_PASSWORD`, `SOUNDSYSTEM_LISTMONK_LIST_ID`) — missing any one keeps the route in offline mode. New schemas: `NewsletterSubscribeRequest` (`extra="forbid"` — rejects tracking IDs), `NewsletterSubscribeResponse` (carries SHA-256 hash, never raw email), `NewsletterSubscribeStatus` (subscribed / pending / offline / failed). New module `app/newsletter_subscribe.py` with `normalize_email`, `email_is_valid`, `email_hash`, server-side `ALLOWED_SOURCES` + `ALLOWED_TAGS` allowlists, `ListmonkNewsletterClient` (Basic Auth, single `POST /api/subscribers` call), `_redact()` helper, injectable transport, and `subscribe_to_newsletter()` orchestrator. Listmonk credentials held privately in a tuple, redacted in `__repr__`/`__str__`/error messages. Listmonk 200 → SUBSCRIBED, 200 with `subscriber.status="unconfirmed"` → PENDING (double opt-in), 409 → SUBSCRIBED, otherwise FAILED. HTTP via stdlib `urllib.request` — no new pinned dep. Capabilities expose `newsletter_subscribe_available` + `newsletter_listmonk_configured`. 34 new tests: email validation/hashing/allowlist/redaction/route shape/capability state/offline behaviour, plus negative checks that the module imports no `requests`/`httpx`/`aiohttp`, no `Cookie`/`set_cookie`/`X-Forwarded-For`/`user_agent` API surface, no scheduler/background-worker imports, and no real HTTP calls in CI. **No tracking. No cookies. No IP / user-agent / referrer capture. No email sending — Listmonk owns delivery + double opt-in. Raw email never echoed. Default unconfigured / offline. Listmonk credentials never exposed.**
- Commerce Sync Audit Log (S65): append-only audit log for operator-triggered Shopify + Printful sync actions. New env var `SOUNDSYSTEM_COMMERCE_SYNC_AUDIT` (default `in_memory`, optional `postgres`); fail-loud when `postgres` is selected without `SOUNDSYSTEM_DATABASE_URL`. New schemas: `CommerceSyncAuditAction` (sync_shopify/sync_printful/sync_both), `CommerceSyncAuditRecord`, `CommerceSyncAuditSummary`. `CommerceSyncAuditRepository` Protocol + InMemory + Postgres + `build_commerce_sync_audit_repository()` factory; INSERT-only at the application layer, no `delete`/`remove`/`clear`/`drop` method exists. `db/014_commerce_sync_audit.sql` adds the `commerce_sync_audit` table with indexes on capsule_id/release_id/action/overall_status/created_at. The three operator-triggered sync routes (`/v1/shopify/drafts/by-capsule/{id}/sync-drafts`, `/v1/printful/syncs/by-capsule/{id}/sync-products`, `/v1/commerce/sync/capsules/{id}/sync-both`) now append one audit record each — operator id, per-provider status/counts, provider IDs in `details`, and zero token leakage (assertions enforce that `details` never contains `token`/`secret`/`bearer`/`api_key`/`x-shopify-access-token`). 4 read-only audit routes: `GET /v1/commerce/sync/audit` (most recent first, limit-bounded), `GET .../audit/summary` (by-action / by-status / item totals), `GET /v1/commerce/sync/capsules/{id}/audit` (chronological per capsule), `GET /v1/commerce/sync/releases/{id}/audit` (most recent first per release). Capabilities expose `commerce_sync_audit_available` + `commerce_sync_audit_mode`. Frontend renders the audit log under the Commerce Sync dashboard with action/status chips, operator id, per-provider item counts, warnings, and timestamp. Copy: *"Append-only audit. Records operator-triggered sync intent only."* 27 new tests. **Append-only. Operator-triggered only. No publishing. No provider mutations beyond the existing S62/S63 boundaries. Token never appears in audit records. Default in_memory / optional postgres.**
- Shopify + Printful Operator Sync Dashboard (S64): unified operator dashboard composing S62 (Shopify live drafts) and S63 (Printful live sync) into a single surface. New schemas: `CommerceSyncProvider` (shopify/printful), `CommerceSyncStatus` (not_synced/synced_mock/synced_live/partial/blocked/failed), `CommerceSyncProviderState`, `CommerceCapsuleSyncState`, `CommerceCapsuleSyncResult`, `CommerceSyncSummary`. New `commerce_sync_dashboard.py` module exposes pure read-model aggregation: `build_shopify_provider_state`, `build_printful_provider_state`, `build_commerce_capsule_sync_state`, `build_commerce_sync_summary`, `combine_sync_results`. Status aggregation is deterministic — latest-draft-per-product wins, failures escalate to FAILED, blocked aggregations are recognized. Provider IDs (`shopify_product_id`, `shopify_handle`, `printful_sync_product_id`, `printful_external_id`) are extracted from `provider_payload` for surfacing in the UI. 4 routes: `GET /v1/commerce/sync/capsules`, `GET .../capsules/{capsule_id}`, `GET .../summary`, `POST .../capsules/{capsule_id}/sync-both` (operator required). The sync-both route calls Shopify first then Printful sequentially, stores results into existing repositories, returns combined exports + post-sync state. Capabilities expose `commerce_sync_dashboard_available`. Frontend: `/admin/soundsystem/commerce-sync` page with summary strip, per-capsule cards (overall + per-provider status chips, provider IDs, last-synced timestamp, LIVE/MOCK badges), and `CommerceSyncControls` component with three buttons (Sync Shopify, Sync Printful, Sync Both). New COMMERCE_SYNC operator intent tile. 28 new tests verify empty states, Shopify-only / Printful-only / both-synced aggregation, blocked + failed propagation, latest-draft-wins, provider-ID extraction, summary counts, sequential ordering on sync-both, repository persistence, capsule 404, and the absence of background/scheduler imports + token leakage. **Operator-triggered only. No automatic sync. No background workers. No scheduler. No webhook listener. No storefront publishing. No inventory, order, customer, or webhook mutation. Token never appears in responses.**
- Printful Live Product Sync Boundary (S63): hardened the S41 Printful provider boundary into a production-safe, operator-triggered Printful Store API path. `RealPrintfulSyncProvider` now fails loud at construction without **both** `PRINTFUL_API_TOKEN` and `PRINTFUL_STORE_ID`, holds the token privately in a tuple (no public attribute), and renders a redacted `__repr__`/`__str__`. New `sync_products(capsule)` method calls `POST /store/products` once per product with a payload whose top-level keys are constrained to `ALLOWED_PAYLOAD_KEYS` (sync_product, sync_variants, external_id, name, retail_price, files, options, …). `FORBIDDEN_PAYLOAD_KEYS` is a hard allowlist of fields that must NEVER appear: any inventory, order/recipient/shipment, customer, webhook, or storefront-publishing field is detected by `_payload_violates_safety()` and aborts the call with `FAILED` before any network IO. Vinyl-provider-group products are blocked at this boundary (not POD) with a `vinyl_blocked` warning. Token is scrubbed from every warning via `_redact()` (Bearer header, store-id header, raw token text). HTTP uses stdlib `urllib.request` only (no new pinned dependency); tests inject a `transport` callable so CI never makes real network calls. New route `POST /v1/printful/syncs/by-capsule/{capsule_id}/sync-products` (operator required) calls `sync_products()` in printful mode and falls back to deterministic `export_mock()` in mock mode. Capabilities expose `printful_live_product_sync_available` (true only when real provider active). Frontend: `PrintfulSyncButton` client component on the Command Center detail page beside the Shopify sync button, with `LIVE` / `MOCK` badge and Printful product IDs surfaced from the response. 36 new tests cover mock default, fail-loud config, token redaction, payload allowlist + forbidden-field detection, success/4xx/missing-id response handling, vinyl-blocked boundary, route storage, and the absence of webhook/scheduler/background imports. **Default remains mock. Real mode creates Printful sync products only. NEVER publishes the Shopify storefront. NEVER mutates inventory, orders, customers, or webhooks. NEVER starts background workers. Token never appears in logs, errors, or API responses.**
- Shopify Live Draft Sync Hardening (S62): hardened the S40 Shopify provider boundary into a production-safe, operator-triggered Admin GraphQL draft sync. `RealShopifyDraftProvider` now fails loud at construction without `SHOPIFY_SHOP_DOMAIN` + `SHOPIFY_ADMIN_ACCESS_TOKEN`, holds the token privately inside a tuple (no public attribute), and renders a redacted `__repr__`/`__str__`. New `sync_drafts(capsule)` method runs a single `productCreate` GraphQL mutation per product with `input.status = "DRAFT"` pinned and **no** publish, inventory, order, customer, or webhook fields. Token is scrubbed from every warning emitted from this module via the `_redact()` helper. HTTP uses stdlib `urllib.request` (no new pinned dependency); tests inject a `transport` callable so CI never makes real network calls. New route `POST /v1/shopify/drafts/by-capsule/{capsule_id}/sync-drafts` (operator required) calls `sync_drafts()` in shopify mode and falls back to deterministic `export_mock()` in mock mode. Capabilities expose `shopify_live_draft_sync_available` (true only when the real provider is active). Frontend: `ShopifySyncButton` client component on the Command Center detail page beside each linked merch capsule, with `LIVE` / `MOCK` badge and admin-product IDs surfaced from the response. 35 new tests verify mock default, fail-loud config, token redaction in repr/str/warnings, GraphQL payload shape (no publish/inventory/order/customer fields), success/error response handling, server-returned non-DRAFT status auto-failure, route storage, and the absence of webhook/scheduler/background imports. **Default remains mock. Real mode creates DRAFT products only. NEVER publishes. NEVER mutates inventory, orders, customers, or webhooks. NEVER starts background workers. Token never appears in logs, errors, or API responses.**
- Release-to-Campaign Command Center (S61): single orchestration surface that aggregates state across release, campaign, automation, merch, distribution, vinyl, and analytics into one `ReleaseCommandCenter` read-model. New schemas: `CommandCenterReadinessStatus` (ready/warning/blocked/missing), `CommandCenterReadinessItem`, `CommandCenterRecommendedTemplate`, `ReleaseCommandCenter`, `ReleaseCommandCenterBootstrapResult`. `release_command_center.py` provides pure functions `infer_release_readiness`, `recommend_templates` (core 3 + vinyl-conditional, already-attached detected by trigger+action), `build_release_command_center`, and `bootstrap_release_campaign` (the only mutator entry point). Bootstrap may create one Campaign if none exists and instantiate recommended templates as DRAFT rules — nothing else. 3 routes: `GET /v1/command-center/releases`, `GET /v1/command-center/releases/{release_id}`, `POST /v1/command-center/releases/{release_id}/bootstrap` (operator required). Capabilities expose `release_command_center_available`. Frontend: COMMAND CENTER operator intent tile, `/admin/soundsystem/command-center/` index with command cards (readiness chips, automation rule count, recommendation count, CTA), and `/admin/soundsystem/command-center/releases/[release_id]/` detail page with readiness board, recommended templates panel, bootstrap button, dry-run summary, linked-objects board, and navigation to release/campaign detail. 33 new tests. **Bootstrap creates only Campaign + DRAFT rule definitions. No execution jobs queued. No audit records written. No merch/distribution/vinyl/analytics mutations. No provider calls. No scheduler. No background workers.**
- Automation Rule Templates (S60): curated, definition-only catalogue of `CampaignAutomationRuleTemplate` definitions that operators can instantiate onto a campaign. 6 default templates: `release-ready-mark-campaign-ready`, `campaign-ready-mark-active`, `merch-locked-add-warning`, `vinyl-ready-create-handoff-task`, `intelligence-heat-notify-operator` (default threshold 75), `snapshot-delta-notify-operator` (default threshold 10). Template IDs are deterministic (UUID5 over a fixed namespace + slug) so they stay stable across restarts. `instantiate_template()` is a pure function that builds a draft `CampaignAutomationRule` — the catalogue itself is never mutated, condition/payload dicts are copied not shared. Categories: `release_ops`, `merch_ops`, `vinyl_ops`, `intelligence_ops`, `operator_notification`. 4 routes: `GET /v1/campaign-automation/templates`, `GET /v1/campaign-automation/templates/summary`, `GET /v1/campaign-automation/templates/{slug}`, `POST /v1/campaign-automation/templates/{slug}/instantiate` (operator required). Capabilities expose `campaign_automation_templates_available`. Frontend renders the catalogue in the campaign detail Automation panel with an INSTANTIATE button per template that calls `router.refresh()` on success. Copy: *"Templates create rule definitions only. No automation is executed."* 32 new tests. **No automation execution. No scheduler. No background jobs. No webhooks. No external API calls. No provider mutations. Instantiation stores a DRAFT rule and creates zero execution jobs and zero audit records.**
- Automation Execution Audit Log (S59): durable execution job persistence + immutable transition audit log. Two new env vars: `SOUNDSYSTEM_AUTOMATION_EXECUTION_REPOSITORY` (default `in_memory`, optional `postgres`) and `SOUNDSYSTEM_AUTOMATION_EXECUTION_AUDIT` (default `in_memory`, optional `postgres`); both fail-loud when `postgres` is selected without `SOUNDSYSTEM_DATABASE_URL`. `PostgresAutomationExecutionRepository` upserts/updates execution job state via `psycopg_pool`; `PostgresAutomationExecutionAuditRepository` is INSERT-only (no application code path deletes audit rows). `db/013_automation_execution.sql` adds `automation_execution_jobs` + `automation_execution_audit` tables with indexes on campaign_id/rule_id/status/created_at/to_status. New schemas `AutomationExecutionAuditRecord` + `AutomationExecutionAuditSummary`. Queue-execution and execute-mock routes now append an audit record (reason = `queue_execution` / `execute_mock`) on every state transition. 4 read-only audit routes: `GET /v1/campaign-automation/execution-audit`, `GET /v1/campaign-automation/execution-audit/summary`, `GET /v1/campaign-automation/executions/{execution_id}/audit` (chronological), `GET /v1/campaigns/{campaign_id}/automation/audit` (reverse chronological). Capabilities expose `automation_execution_repository_mode`, `automation_execution_audit_available`, `automation_execution_audit_mode`. Frontend campaign detail page renders audit rows under the execution queue with transition badges, operator id, and reason; copy: *"Audit log is immutable. It records intent and mock transitions only."* 40 new tests. **Execution still disabled by default. No scheduler, background workers, cron, webhooks, external API calls, provider mutations, or campaign mutations. Audit log is append-only — the application never deletes rows. Future real executor remains deferred.**
- Automation Execution Queue Boundary (S58): disabled-by-default execution boundary for Campaign Automation Rules. `SOUNDSYSTEM_AUTOMATION_EXECUTION_MODE` (default `disabled`, optional `mock`). New schemas: `AutomationExecutionMode`, `AutomationExecutionStatus`, `AutomationExecutionJob`, `AutomationExecutionCreateRequest`, `AutomationExecutionResult`, `AutomationExecutionSummary`. `InMemoryAutomationExecutionRepository` (Protocol + InMemory only — no Postgres yet). Pure execution module: `create_execution_job_from_dry_run()` (re-runs dry-run, BLOCKS in disabled mode, QUEUES in mock when dry-run is WOULD_RUN, BLOCKS otherwise), `execute_mock_job()` (only valid in mock mode + queued state, transitions to COMPLETED_MOCK with no side effects). 6 API routes: `POST /v1/campaign-automation/rules/{rule_id}/queue-execution`, `GET /v1/campaign-automation/executions[/summary|/{id}|/by-campaign/{cid}]`, `POST /v1/campaign-automation/executions/{id}/execute-mock`. Capabilities expose `automation_execution_boundary_available` + `automation_execution_mode`. Frontend execution queue + status chips + Queue Execution / Execute Mock buttons on campaign detail page. 44 new tests. **Execution disabled by default. No scheduler. No background workers. No cron. No webhooks. No external API calls. No social posting. No email sending. No provider mutations. Mock execution updates the job record only — campaign and provider state are never touched. Real executor is deferred to a future slice.**
- Campaign Automation Rules Boundary (S57): rule-definition layer for Campaign OS automation — WITHOUT executing automation. `CampaignAutomationRule` model with trigger/action/conditions/action_payload, 8 triggers (release_ready, campaign_ready, campaign_active, distribution_ready, merch_capsule_locked, vinyl_ready, intelligence_heat_above_threshold, snapshot_heat_delta_above_threshold), 6 actions (mark_campaign_ready, mark_campaign_active, create_task, add_warning, notify_operator, no_op). `InMemoryCampaignAutomationRuleRepository` (Protocol + InMemory). Pure deterministic dry-run evaluator (`evaluate_rule`, `evaluate_rules_for_campaign`, `build_automation_context`) — reports what *would* happen, never mutates. 8 API routes: CRUD on `/v1/campaign-automation/rules/*`, single-rule dry-run, campaign-wide dry-run, summary. Capabilities expose `campaign_automation_rules_available`. Automation Rules panel on campaign detail page. 43 new tests. **No automation execution. No scheduler. No background jobs. No cron. No webhooks. No external API calls. No social posting. No email sending. Dry-run only.**
- initial Postgres schema artifact

It does not call ACE-Step, YuE, Stable Audio Open, SonicMaster, Matchering, Supabase, or RunPod yet. The GPT-5.5 lyrics provider is gated behind `SOUNDSYSTEM_LYRICS_PROVIDER=gpt_5_5` + `OPENAI_API_KEY`; the Dropbox provider is gated behind `SOUNDSYSTEM_DROPBOX_SYNC_PROVIDER=dropbox` + `DROPBOX_ACCESS_TOKEN`; the S3 artifact storage is gated behind `SOUNDSYSTEM_ARTIFACT_STORAGE=s3` + S3 env vars; the SoundCloud provider is gated behind `SOUNDSYSTEM_SOUNDCLOUD_PROVIDER=soundcloud` + `SOUNDCLOUD_CLIENT_ID` + `SOUNDCLOUD_CLIENT_SECRET`. Default mode for all remains mock/local.

## Local Run

```bash
cd services/soundsystem-inference
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8010
```

## Routes

- `GET /health`
- `GET /v1/capabilities`
- `POST /v1/prompts/compile`
- `POST /v1/generations`
- `GET /v1/generations/{job_id}`
- `POST /v1/masters`
- `GET /v1/masters/{job_id}`
- `POST /v1/lyrics/prompts/compile`
- `POST /v1/lyrics/generations`
- `POST /v1/lyrics/edits`
- `POST /v1/lyrics/manual-updates`
- `POST /v1/lyrics/selections`
- `GET /v1/lyrics/versions/{version_id}`
- `POST /v1/lyrics/versions/{version_id}/export`
- `POST /v1/lyrics/versions/{version_id}/sections/{section_index}/lock`
- `POST /v1/lyrics/versions/{version_id}/apply-selection-rewrite`
- `GET /v1/lyrics/projects`
- `GET /v1/lyrics/projects/{project_key}`
- `GET /v1/lyrics/projects/{project_key}/versions`
- `GET /v1/lyrics/projects/{project_key}/versions/{version_number}`
- `GET /v1/compliance/summary`
- `GET /v1/compliance/models`
- `GET /v1/compliance/licenses`
- `POST /v1/compliance/licenses`
- `GET /v1/compliance/consent-records`
- `POST /v1/compliance/consent-records`
- `GET /v1/compliance/provenance` (optional `?artifact_id=`)
- `POST /v1/compliance/provenance`
- `GET /v1/compliance/audit-events`
- `POST /v1/compliance/audit-events`
- `POST /v1/compliance/preflight`
- `GET /v1/compliance/release-eligibility/{artifact_id}`
- `POST /v1/compliance/consent-records/{consent_id}/revoke`
- `GET /v1/voice-lab/summary`
- `GET /v1/voice-lab/tags`
- `POST /v1/voice-lab/tags`
- `GET /v1/voice-lab/jobs`
- `GET /v1/voice-lab/jobs/{job_id}`
- `POST /v1/voice-lab/jobs`
- `GET /v1/music-router/summary`
- `POST /v1/music-router/jobs`
- `GET /v1/music-router/jobs`
- `GET /v1/music-router/jobs/{job_id}`
- `GET /v1/music-router/jobs/{job_id}/artifacts`
- `POST /v1/soundgraph/compile`
- `GET /v1/soundgraph/arrangements/{arrangement_id}`
- `GET /v1/soundgraph/by-lyrics-version/{lyrics_version_id}`
- `GET /v1/soundgraph/arrangements`
- `POST /v1/soundgraph/handoff`
- `POST /v1/library/packs`
- `GET /v1/library/packs/{pack_id}`
- `GET /v1/library/entries`
- `GET /v1/library/entries/{entry_id}`
- `GET /v1/library/summary`
- `POST /v1/dropbox/plans`
- `GET /v1/dropbox/plans/{plan_id}`
- `GET /v1/dropbox/plans/by-pack/{pack_id}`
- `GET /v1/dropbox/jobs`
- `GET /v1/dropbox/jobs/{sync_id}`
- `POST /v1/dropbox/jobs/{sync_id}/ready`
- `POST /v1/dropbox/jobs/{sync_id}/execute`
- `GET /v1/dropbox/summary`
- `POST /v1/releases`
- `GET /v1/releases`
- `GET /v1/releases/{release_id}`
- `GET /v1/releases/by-pack/{pack_id}`
- `POST /v1/releases/{release_id}/checklist/{code}`
- `POST /v1/releases/{release_id}/ready`
- `GET /v1/releases/summary`
- `POST /v1/releases/{release_id}/assets/cover`
- `POST /v1/releases/{release_id}/assets/audio-master`
- `POST /v1/releases/{release_id}/assets/stems`
- `POST /v1/releases/{release_id}/export`
- `POST /v1/analytics/events`
- `GET /v1/analytics/events`
- `GET /v1/analytics/summary`
- `GET /v1/analytics/channels`
- `GET /v1/analytics/campaigns/{campaign_id}`
- `GET /v1/analytics/tracks/{track_id}`
- `POST /v1/analytics/demo-seed`
- `GET /v1/intelligence/overview`
- `GET /v1/intelligence/viral-moments`
- `GET /v1/intelligence/heatmap`
- `GET /v1/intelligence/revenue`
- `GET /v1/intelligence/timeline`
- `GET /v1/connectors`
- `GET /v1/connectors/summary`
- `GET /v1/connectors/{connector_type}`
- `GET /v1/connectors/{connector_type}/health`
- `GET /v1/connectors/{connector_type}/preview-sync`
- `POST /v1/connectors/{connector_type}/import-demo`

## Tests

The service ships with a small pytest suite that covers prompt compilation,
job creation, the voice-likeness preflight block, and 404 lookup behavior.

```bash
cd services/soundsystem-inference
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Tests use the in-memory `InMemoryGenerationJobRepository` and do not require a
database, Redis, Dropbox, Supabase, RunPod, or any GPU model.

## Providers

`app/providers/base.py` defines the `MusicEngineProvider` contract. Providers
start jobs with `start()` and report progress through `get_status()`, matching
the async shape expected for ACE-Step, YuE, and Stable Audio Open later.

`app/providers/registry.py` owns provider registration, default selection,
health checks, and mock fallback. The only registered provider today is
`MockMusicProvider`; no live external provider calls are made.

### Lyrics Provider (S13)

`app/providers/lyrics/` implements the Provider Isolation Layer for lyrics:

- **Protocol**: `LyricsProviderProtocol` in `__init__.py`
- **Factory**: `build_lyrics_provider()` reads `SOUNDSYSTEM_LYRICS_PROVIDER`
- **Mock**: `app/lyrics_provider.py` (default, no external deps)
- **GPT-5.5**: `app/providers/lyrics/gpt_5_5.py` (requires `openai` SDK + `OPENAI_API_KEY`)

Four hard rules enforced:

1. **Provider Isolation** — route handlers never see `openai` types; only Protocol methods.
2. **Cost Accounting** — every call records `prompt_tokens`, `completion_tokens`, `estimated_cost_usd`, `latency_ms`, `raw_provider_trace_id`.
3. **Hard Timeout** — `SOUNDSYSTEM_LYRICS_TIMEOUT_MS` (default 30s); no admin UI freeze.
4. **Shadow Prompt Logging** — `raw_operator_prompt`, `system_prompt_version`, `safety_transformations` persisted in provenance.

To enable GPT-5.5 mode locally:

```bash
pip install openai
SOUNDSYSTEM_LYRICS_PROVIDER=gpt_5_5 OPENAI_API_KEY=sk-... uvicorn app.main:app --port 8010
```

### Dropbox Sync Provider (S21)

`app/providers/dropbox/` implements the Provider Isolation Layer for Dropbox sync:

- **Protocol**: `DropboxSyncProviderProtocol` in `__init__.py`
- **Factory**: `build_dropbox_sync_provider()` reads `SOUNDSYSTEM_DROPBOX_SYNC_PROVIDER`
- **Mock**: `app/providers/dropbox/mock.py` (default, no external deps)
- **Real**: `app/providers/dropbox/real.py` (requires `dropbox` SDK + `DROPBOX_ACCESS_TOKEN`)

Four hard rules enforced:

1. **Mock Default** — tests never hit Dropbox; mock provider is selected when env is unset.
2. **No Silent Fallback** — if `dropbox` mode is selected without a token, service fails at startup.
3. **Upload Only** — real provider only writes files listed in the ExportPlan. No arbitrary filesystem access.
4. **No Destructive Deletes** — never calls `files_delete` or any removal API.

To enable real Dropbox mode locally:

```bash
pip install dropbox
SOUNDSYSTEM_DROPBOX_SYNC_PROVIDER=dropbox DROPBOX_ACCESS_TOKEN=sl.xxx uvicorn app.main:app --port 8010
```

### S3/R2 Artifact Storage (S35)

`app/artifact_storage_s3.py` implements an S3-compatible storage backend:

- **Protocol**: `ArtifactStorage` in `app/artifact_storage.py`
- **Factory**: `build_artifact_storage()` reads `SOUNDSYSTEM_ARTIFACT_STORAGE`
- **Local**: `app/artifact_storage.py` `LocalArtifactStorage` (default, no external deps)
- **S3**: `app/artifact_storage_s3.py` `S3ArtifactStorage` (requires `boto3` + S3 env vars)

Five hard rules enforced:

1. **Local Default** — tests never hit S3; local adapter is selected when env is unset.
2. **No Silent Fallback** — if `s3` mode is selected without credentials, service fails at startup.
3. **Upload/Read Only** — never calls `delete_object` or `list_objects_v2`.
4. **No Arbitrary Keys** — storage keys are generated by `_safe_storage_key()`.
5. **Credentials Never Exposed** — no S3 keys in logs, errors, API responses, or UI.

Env vars:

| Variable | Required | Default | Description |
|---|---|---|---|
| `SOUNDSYSTEM_ARTIFACT_STORAGE` | No | `local` | `local` or `s3` |
| `SOUNDSYSTEM_S3_ENDPOINT_URL` | Yes (S3) | — | e.g. `https://<account>.r2.cloudflarestorage.com` |
| `SOUNDSYSTEM_S3_ACCESS_KEY_ID` | Yes (S3) | — | R2/S3 access key |
| `SOUNDSYSTEM_S3_SECRET_ACCESS_KEY` | Yes (S3) | — | R2/S3 secret key |
| `SOUNDSYSTEM_S3_BUCKET` | Yes (S3) | — | Bucket name |
| `SOUNDSYSTEM_S3_REGION` | No | `auto` | Region (`auto` for R2) |
| `SOUNDSYSTEM_S3_FORCE_PATH_STYLE` | No | `true` | Path-style addressing (R2/MinIO need `true`) |
| `SOUNDSYSTEM_S3_PUBLIC_BASE_URL` | No | — | Public CDN base URL for direct downloads |

To enable S3/R2 mode locally:

```bash
pip install -e ".[s3]"
SOUNDSYSTEM_ARTIFACT_STORAGE=s3 \
SOUNDSYSTEM_S3_ENDPOINT_URL=https://xxx.r2.cloudflarestorage.com \
SOUNDSYSTEM_S3_ACCESS_KEY_ID=... \
SOUNDSYSTEM_S3_SECRET_ACCESS_KEY=... \
SOUNDSYSTEM_S3_BUCKET=soundsystem-artifacts \
uvicorn app.main:app --port 8010
```

Recommended production mode:

```
SOUNDSYSTEM_ARTIFACT_STORAGE=s3
SOUNDSYSTEM_ARTIFACT_REGISTRY=postgres
SOUNDSYSTEM_ARTIFACT_ACCESS_MODE=signed
```

### SoundCloud Publishing (S36)

`app/providers/soundcloud/` implements the SoundCloud publishing adapter boundary:

- **Protocol**: `SoundCloudPublishProviderProtocol` in `app/providers/soundcloud/__init__.py`
- **Factory**: `build_soundcloud_publish_provider()` reads `SOUNDSYSTEM_SOUNDCLOUD_PROVIDER`
- **Mock** (default): `app/providers/soundcloud/mock.py` — deterministic metadata previews, marks jobs as `published_mock`
- **Real**: `app/providers/soundcloud/real.py` — config validated, but publish always returns BLOCKED (OAuth not implemented)

Routes:

| Method | Path | Description |
|---|---|---|
| POST | `/v1/soundcloud/preview` | Build metadata preview from ReleasePack |
| POST | `/v1/soundcloud/jobs` | Create a publish job |
| GET | `/v1/soundcloud/jobs` | List all publish jobs |
| GET | `/v1/soundcloud/jobs/{job_id}` | Get a single publish job |
| POST | `/v1/soundcloud/jobs/{job_id}/publish-mock` | Execute mock publish (422 if BLOCKED) |
| GET | `/v1/soundcloud/summary` | Aggregate job counts |

Env vars:

| Variable | Required | Default | Description |
|---|---|---|---|
| `SOUNDSYSTEM_SOUNDCLOUD_PROVIDER` | No | `mock` | `mock` or `soundcloud` |
| `SOUNDCLOUD_CLIENT_ID` | Yes (real) | — | SoundCloud app client ID |
| `SOUNDCLOUD_CLIENT_SECRET` | Yes (real) | — | SoundCloud app client secret |

Real SoundCloud publishing is deferred until OAuth integration. The real provider boundary exists for architectural completeness — it validates credentials at startup but never calls the SoundCloud API.

### Merch Capsule Contract (S37)

`app/merch_capsule.py` implements the merch commerce contract layer:

- **Builder**: `build_merch_capsule_from_release()` converts a ReleasePack into a merch capsule with suggested products
- **Suggestions**: `suggest_products_for_release()` proposes up to 5 products based on release metadata (vinyl only if genre/description contains relevant keywords)
- **Rules**: `enforce_merch_capsule_rules()` validates max 5 active, max 1 always_on, drop window presence, provider routing
- **Export**: `build_mock_provider_export()` produces a mock provider payload with per-group notes

Routes:

| Method | Path | Description |
|---|---|---|
| POST | `/v1/merch/capsules` | Create capsule from ReleasePack |
| GET | `/v1/merch/capsules` | List all capsules |
| GET | `/v1/merch/capsules/{capsule_id}` | Get a single capsule |
| POST | `/v1/merch/capsules/{capsule_id}/lock` | Lock capsule (prevents status regression) |
| POST | `/v1/merch/capsules/{capsule_id}/export-mock` | Build mock provider export payload |
| GET | `/v1/merch/summary` | Aggregate capsule counts |

Product philosophy (from `docs/marketing/merch-os.md`):

- **70/20/10 rule**: 70% unavailable, 20% limited, 10% always-on
- **Max 5 active products** per capsule
- **Three provider groups**: `apparel_provider` (Printful), `premium_drop_provider` (Gelato), `vinyl_provider` (elasticStage/DISC_ARCHIVE)
- **No real commerce calls**: all exports are mock payloads
- **TikTok Shop**: top-of-funnel only, integration deferred
- **Printful/Gelato/vinyl**: future provider adapters, not connected

## Persistence

`app/repository.py` defines `GenerationJobRepository`, the storage boundary for
generation jobs and their events. The default implementation is
`InMemoryGenerationJobRepository`. The Postgres-backed implementation lands
later against the SQL artifact in `db/001_initial_schema.sql`.

`app/master_repository.py` defines `MasterBusRepository`, the parallel
boundary for SNUFFRAGA MASTER BUS jobs. Default is
`InMemoryMasterBusRepository`; the same Postgres path lands later.

`app/lyrics_repository.py` defines `LyricsRepository` with **two** registered
implementations: `InMemoryLyricsRepository` (default) and
`PostgresLyricsRepository` (Slice 7). The selection is controlled by
`SOUNDSYSTEM_LYRICS_REPOSITORY` (`in_memory` | `postgres`); Postgres mode also
requires `SOUNDSYSTEM_DATABASE_URL`. Missing URL in postgres mode fails loudly
at startup. See `docs/soundsystem/lyrics-engine.md` and `db/002_lyrics.sql`.

To enable Postgres mode locally:

```bash
pip install -e ".[postgres]"
psql "$SOUNDSYSTEM_DATABASE_URL" -f db/002_lyrics.sql
SOUNDSYSTEM_LYRICS_REPOSITORY=postgres uvicorn app.main:app --port 8010
```

## Generated TypeScript Types

`apps/web/app/admin/soundsystem/_lib/generated-inference-types.ts` is the
committed TypeScript mirror of `app/schemas.py` + `app/config.py`. It is
produced by a small local Python reflector — no Node-side codegen tool, no
external dependency beyond Pydantic itself.

Regenerate after every Pydantic schema change:

```bash
cd services/soundsystem-inference
python scripts/generate_ts_types.py
```

The pytest suite contains a drift check
(`tests/test_generated_types.py::test_generated_ts_types_match_committed_file`)
that fails if the committed file is stale; it also asserts the generator
output is deterministic across runs. Anyone forgetting to regenerate will
see the drift test fail with a short diff hint pointing at the regenerate
command.

`apps/web/app/admin/soundsystem/_lib/inference-types.ts` is now a thin
re-export of the generated file plus a handful of UI-side aliases (e.g.
`LyricsGenerationInput → LyricsGenerationRequest`). Do not add new hand-
written shapes there. If a new API type is needed, add it to Pydantic and
regenerate.

## SoundGraph + Master Bus

The 12-lane SoundGraph model (kick, drums, percussion, bass, music, lead,
vocals_main, vocals_adlibs, fx, atmosphere, return_delay, return_reverb) is
specified in [docs/soundsystem/sound-model.md](../../docs/soundsystem/sound-model.md).
Schemas land in `app/schemas.py` (`StemLaneType`, `StemSourceType`,
`EffectDeviceType`, `TempoControls`, `DruckControls`, `EffectRack`,
`StemLanePlan`, `StemPlan`, `SoundGraphManifest`).

The MASTER BUS contract layer is specified in
[docs/soundsystem/master-bus.md](../../docs/soundsystem/master-bus.md). Six
mastering modes, five export profiles. No DSP runs yet; the mock provider
synthesizes deterministic artifact paths.

The LYRICS ENGINE contract layer is specified in
[docs/soundsystem/lyrics-engine.md](../../docs/soundsystem/lyrics-engine.md).
Seven section types, three sources (`user`, `gpt_5_5`, `mock`), versioned
drafts, locked sections, manual updates, selection rewrites, SoundGraph
export manifest. `app/lyrics_repository.py` is the persistence boundary; the
mock provider in `app/lyrics_provider.py` produces deterministic text and
imports no external clients.

## Design Boundary

This service owns GPU-facing work only. It should remain internal-only and should not approve release candidates.
