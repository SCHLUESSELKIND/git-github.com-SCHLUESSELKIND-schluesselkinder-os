# Compliance Foundation

The data model, rules, and review gates every model-driven artifact in
SCHLÜSSELKINDER must satisfy before it can leave the system.

This doc is a contract layer, not an implementation. It defines the schemas
that future Postgres migrations and Python repositories will mirror. Until
those land, the operator console must already enforce the same rules
in-memory and the export pipeline must already block when the rules are not
met.

The doc consolidates the rules cited by
[admin-integration-strategy.md](./admin-integration-strategy.md) and
[model-provider-strategy.md](./model-provider-strategy.md). Everything below
is binding before any non-mock provider is activated.

## 1. LicenseRegistry

A canonical catalogue of every license under which we evaluate model code,
weights, or datasets.

```text
LicenseRegistry
  license_id            UUID          primary key
  spdx_id               TEXT          "Apache-2.0" | "MIT" | "CC-BY-NC-4.0" | "Coqui-CPM-1.0" | "custom"
  display_name          TEXT          operator-facing name
  source_url            TEXT          link to the canonical license text
  permits_commercial    BOOLEAN       NOT NULL
  permits_distribution  BOOLEAN       NOT NULL  -- redistribution of weights/code
  permits_modification  BOOLEAN       NOT NULL  -- derived works allowed
  requires_attribution  BOOLEAN       NOT NULL
  share_alike           BOOLEAN       NOT NULL  -- viral copyleft clause
  patent_grant          BOOLEAN       NOT NULL
  notes                 TEXT NULL     free text, especially weight-vs-code mismatches
  reviewed_by           UUID          operator id
  reviewed_at           TIMESTAMPTZ   when the row was last validated
  created_at            TIMESTAMPTZ
```

Rules:

- An entry without `reviewed_by` and `reviewed_at` is not considered usable.
- `permits_commercial = false` ⟹ any `ModelRegistry` row pointing at this
  license cannot reach `commercial_status = ready`.
- Code-vs-weights mismatches are recorded as **separate rows** linked
  through the `ModelRegistry`. A model with `Apache-2.0` code and `CC-BY-NC`
  weights references both; the more restrictive one wins for any decision.
- A license review that includes "depends on which checkpoint" must record
  one row per checkpoint, not a single fuzzy entry.

## 2. ConsentRecord

A per-subject record authorising a specific scope of use of a person's voice
or likeness.

```text
ConsentRecord
  consent_id            UUID          primary key
  subject_name          TEXT          legal/working name of the person
  subject_role          TEXT          owner | operator | session_artist | guest_artist | other
  scope                 TEXT          short description of permitted scope
  permitted_use         TEXT[]        controlled tags + free-text qualifiers
  granted_at            TIMESTAMPTZ   when consent was granted
  expires_at            TIMESTAMPTZ NULL  optional expiry
  revoked_at            TIMESTAMPTZ NULL  set when consent is withdrawn
  proof_uri             TEXT          internal pointer to signed agreement
  reviewed_by           UUID          operator who recorded the consent
  created_at            TIMESTAMPTZ
```

Controlled tags for `permitted_use`:

```text
internal_drafts
character_voice_for_brand        # explicit per-brand
release_pack_export              # gates Dropbox sync
public_streaming_distribution    # gates release to streaming
public_video_synthesis           # never default; explicit
training_data                    # never default; explicit
```

Rules:

- A consent record is **never auto-generated**. Operators record it
  explicitly via `/admin/soundsystem/consent` (planned route).
- `revoked_at IS NOT NULL` ⟹ every dependent provider must immediately
  refuse to produce new outputs citing this record.
- `expires_at IS NOT NULL AND expires_at < now()` ⟹ same as revoked, but
  the operator may re-confirm without rewriting history (a new record is
  added, the old one is preserved).
- A consent record can only be cited from `OutputProvenance` if the cited
  scope matches the job's intent. The matching is rule-checked, not
  free-text inferred.

## 3. OutputProvenance

The audit unit for every produced artifact (lyrics version, generation job,
master bus job, export bundle).

```text
OutputProvenance
  provenance_id              UUID          primary key
  artifact_kind              TEXT          lyrics_version | generation_job | master_bus_job | export_bundle
  artifact_id                UUID          foreign key into the kind-specific table
  provider                   UUID          ModelRegistry.model_id
  model_version              TEXT          exact provider version
  model_checkpoint_sha256    TEXT NULL     when applicable
  prompt_tokens              INT NULL      prompt-side token count (LLM steps only)
  completion_tokens          INT NULL      output-side token count (LLM steps only)
  safety_notes               TEXT[]        list of strings carried from compile_prompt + provider filters
  rewrite_strategy           TEXT          manual | prompt_edit | selection_rewrite | provider_regen | initial_generation
  locked_sections_respected  BOOLEAN       must be true if the parent had locked sections
  raw_provider_trace_id      TEXT NULL     opaque pointer to the provider's request log
  license_bundle             UUID[]        every LicenseRegistry.license_id touching this artifact
  consent_records            UUID[]        every ConsentRecord.consent_id cited at preflight
  parent_provenance_id       UUID NULL     chains across rewrites/edits
  created_at                 TIMESTAMPTZ
```

Rules:

- Every artifact has **at least one** `OutputProvenance` row. Multi-stage
  pipelines (e.g. generate → master) produce a chain via
  `parent_provenance_id`.
- `locked_sections_respected = false` ⟹ artifact is automatically marked
  `release_eligible = false` regardless of other gates.
- `consent_records` must include every cited record at the time of
  generation, frozen. A later consent revocation marks future outputs as
  blocked but does not retroactively flip historical rows.
- `license_bundle` is the union of (provider license) + (any reference
  audio license) + (any dataset attribution required by the model). The
  release pipeline checks that every license in the bundle has
  `permits_commercial = true` if the intended use is commercial.

## 4. CommercialStatus

Per-`ModelRegistry` enum:

```text
CommercialStatus
  research_only        Default for newly catalogued models. Internal drafts only.
  conditional          Cleared for internal use, not yet for release.
  ready                Cleared for release, all gates green.
  blocked              Explicitly disqualified; the registry row exists for documentation only.
```

Transition rules:

- `research_only → conditional` requires a `LicenseRegistry` reference with
  recorded review and a passing safety smoke test.
- `conditional → ready` requires `SafetyReviewStatus = approved` for a
  representative sample plus a documented operator audit ride.
- Any registry row can be moved to `blocked` at any time. Demotion never
  fails silently — the existing `OutputProvenance` rows that reference a
  blocked model are flagged in the release pipeline.

## 5. SafetyReviewStatus

Per-artifact (or per-batch) review state:

```text
SafetyReviewStatus
  review_id           UUID
  artifact_kind       TEXT
  artifact_id         UUID
  status              pending | approved | rejected | needs_changes
  reviewer_id         UUID NULL
  reviewed_at         TIMESTAMPTZ NULL
  rejection_reason    TEXT NULL
  attached_notes      TEXT NULL
  created_at          TIMESTAMPTZ
```

Rules:

- Default status is `pending`. An artifact in `pending` cannot reach the
  release pipeline.
- `approved` requires `reviewer_id IS NOT NULL`. Self-approval is allowed
  (we are a small team) but recorded.
- A `rejected` review locks the artifact: it cannot be revived for release
  until a new version is produced and a new review is attached.

## 6. Blocked Prompt Categories

A controlled vocabulary of prompt content categories the prompt engine
preflight rejects without exception.

```text
blocked_prompt_categories
  named_artist_imitation
  named_track_cloning
  voice_likeness_without_consent
  public_figure_voice
  child_voice
  sexual_content_involving_real_people
  hate_speech_targeting_protected_group
  illegal_activity_instruction
```

Rules:

- The categories are seeded as code in the prompt engine (extending the
  existing `detect_risky_filler` pattern). The list is enumerable so the
  blocking surface is auditable.
- Detection rules can be over-eager (more false positives is acceptable).
  Each rejection records the category and the matched fragment in
  `OutputProvenance.safety_notes` for review.
- A category match in a prompt blocks the job at preflight. No operator
  override.

## 7. Voice Consent Rules

Codified rules layered on top of `ConsentRecord` and `OutputProvenance`:

```text
1. A voice_clone or singing_voice job that references a real human voice
   must cite at least one non-revoked, non-expired ConsentRecord whose
   permitted_use intersects with the job's intent tag.

2. The operator recording their own voice is still a subject. There is no
   shortcut for self-consent.

3. Session/guest artist consent records require an attached proof_uri
   (e.g. signed PDF, signed photo of paper consent). The system does not
   accept "verbal okay".

4. A revoked or expired consent record causes immediate provider refusal
   for any new job citing it. Historical OutputProvenance rows remain
   intact for audit.

5. Public-figure voices are blocked regardless of consent paperwork. The
   public-figure list is short and operator-maintained; it is enforced as
   a Blocked Prompt Category.

6. Bulk operations (batch generation across many subjects) must record
   one ConsentRecord citation per subject, never an aggregate.

7. A character voice (e.g. SHIBARI_KAWAII) tied to a single performer
   inherits the performer's consent record. The character is not a legal
   shield.
```

## 8. Public-Figure / Artist Voice Restrictions

Hard rules, independent of any consent paperwork:

- No model output may imitate or be marketed as imitating a named living
  artist, public figure, or public persona.
- No prompt may use a named artist as a style anchor (`"in the style of
  <name>"`). The negative prompt suppression in `compile_prompt` is the
  enforcement layer; new instances must be added to the prompt engine, not
  to provider adapters.
- No model whose training data is publicly known to include unconsented
  named-artist material may be activated. License reviews must flag this
  in `LicenseRegistry.notes`.
- Voice models trained on public-figure voice data are blocked even if
  their checkpoint license technically permits commercial use.

The system surfaces a clear preflight error code for each violation:

```text
preflight_block_named_artist_imitation
preflight_block_named_track_cloning
preflight_block_voice_public_figure
preflight_block_voice_clone_without_consent
preflight_block_voice_clone_consent_revoked
preflight_block_voice_clone_consent_expired
preflight_block_voice_clone_scope_mismatch
```

These are codified strings used by the inference service (existing pattern:
`voice_likeness_requires_explicit_clearance`).

## 9. Model License Verification Workflow

Sequence required to promote a model in the registry:

```text
1. Operator opens a license review task for a candidate model.
2. Operator records the relevant LicenseRegistry rows (code, weights,
   dataset attributions) with source URLs.
3. Operator answers the contract questions:
     - permits_commercial?
     - permits_distribution?
     - permits_modification?
     - share_alike?
     - patent_grant?
     - special restrictions (weights-only, regional, vendor-API only)?
4. Operator notes any code-vs-weights mismatch explicitly.
5. The reviewed_by / reviewed_at fields are filled.
6. ModelRegistry.commercial_status moves from research_only to conditional.
7. A representative output set is produced via a smoke test.
8. SafetyReviewStatus = approved is attached for the smoke set.
9. ModelRegistry.commercial_status moves from conditional to ready.
```

No step is automated by an LLM. Each step records the operator id.

## 10. Release Approval Gate

The release pipeline (planned `/admin/soundsystem/export` and
`/admin/releases`) checks the following before allowing a bundle to leave
the system:

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

Each `AND` term maps to a column or computed predicate visible in the
release UI. The operator sees exactly which gate is open or closed.

An operator override is allowed only for the `dropbox_sync` term (e.g. when
Dropbox is intentionally bypassed for a manual delivery). Every other term
is non-overridable; failing it requires producing a new artifact and
attaching new compliance rows.

The operator override, when used, is recorded as an `audit_event` with the
operator id, the artifact id, and a written justification. It is never
silent.

## 11. Audit Trail

Independent of any other table, the system writes one `audit_event` per
state-changing operation in `/admin/*`:

```text
audit_event
  event_id              UUID
  operator_id           UUID
  action                TEXT          codified: e.g. lyrics.version.create, lyrics.section.lock,
                                       master_bus.export, release.gate.override
  resource_kind         TEXT
  resource_id           UUID
  payload_summary       JSONB         redacted; secrets are never logged
  created_at            TIMESTAMPTZ
```

Rules:

- The audit log is append-only. It is never edited or deleted.
- Secrets, API keys, full prompt text (when long), and PII never appear in
  `payload_summary`. The log is structured for forensic value, not full
  reproduction.
- The lyrics engine, generation jobs, master bus, and export pipeline
  each contribute their own actions to the same audit stream.

## 12. Preflight Ordering (binding)

Every intent in the operator console is processed by the Intent Router in a
fixed order. Any failed gate short-circuits the request **before** the
provider is selected. Gates must not run in parallel — order is the safety
property.

```text
Operator Intent
  ↓
[1] CompliancePreflight         compliance gates listed below
  ↓
[2] Provider Routing             ModelRegistry → active adapter
  ↓
[3] Adapter Execution            model call (mock or real)
  ↓
[4] Provenance Write             OutputProvenance row created
  ↓
[5] Safety Review (if required)  SafetyReviewStatus = pending → manual approval
  ↓
[6] Release Eligibility (export only)   see release-approval gate
```

`CompliancePreflight` is a single ordered sequence:

```text
1. Intent recognised?             — unknown intent → 400
2. Provider group resolved?       — group with no adapter → 503 routing_unavailable
3. Prompt allowed?                — blocked_prompt_category match → 422 preflight_block_*
4. Voice consent valid?           — required for voice_clone / singing_voice;
                                    revoked / expired / scope-mismatch → 422
5. Model license registered?      — every candidate adapter must reference a
                                    LicenseRegistry row with reviewed_at set
6. Model commercial status?       — must match the operator's intent
                                    (internal_drafts allowed; release flag tightens)
7. Locked sections respected?     — for any version that derives from a parent
                                    with locked sections (lyrics + future surfaces)
```

The router only sees the request after step 7 has passed. The provider
adapter only sees the request after step 7 has passed. This is the
"compliance preflight before provider routing" rule.

### Consent Gate Specifics

A `voice_clone` or `singing_voice` intent **must** cite at least one
non-revoked, non-expired `ConsentRecord` whose `permitted_use` intersects
with the job's intent tag. The router refuses to dispatch otherwise:

```text
intent = CONVERT_APPROVED_VOICE
consent_ids = [consent_id]
preflight check:
  for each id:
    record = ConsentRecord.get(id)
    assert record is not None             → preflight_block_voice_clone_without_consent
    assert record.revoked_at is None      → preflight_block_voice_clone_consent_revoked
    assert record.expires_at is None or future
                                          → preflight_block_voice_clone_consent_expired
    assert intent_tag in record.permitted_use
                                          → preflight_block_voice_clone_scope_mismatch
```

Operators may not stamp their own consent records inside the same request
that consumes them. Consent creation and consent use are separate audit
events.

### License Registry Gate Specifics

Before the router will route to an adapter:

```text
candidate_adapters = ModelRegistry.where(group = intent.provider_group)
for adapter in candidate_adapters:
  license = LicenseRegistry.get(adapter.license_id)
  assert license is not None
  assert license.reviewed_at is not None
  if intent.is_release_flagged:
    assert license.permits_commercial
ready_adapters = [a for a in candidate_adapters if a.commercial_status == "ready"]
fallback = MockAdapter for the group (always present)
```

A model without a reviewed license **cannot** be the active adapter for any
group. The mock adapter is the only safe always-available fallback; it is
labelled as such in the UI (`READY · MOCK`).

### Provenance Gate Specifics

Every adapter execution **must** produce an `OutputProvenance` row before
returning. A successful adapter response without provenance is treated as a
failure; the artifact is quarantined and the operator sees a clear error.

```text
required provenance fields at write time:
  provider                  ModelRegistry.model_id
  model_version             checkpoint hash where applicable
  prompt_tokens             when LLM stages are involved
  completion_tokens         when LLM stages are involved
  safety_notes              from CompiledPrompt + adapter filters
  rewrite_strategy          initial | manual | prompt_edit | selection_rewrite | provider_regen
  locked_sections_respected
  license_bundle            ALL relevant LicenseRegistry rows
  consent_records           ALL cited ConsentRecord rows
  raw_provider_trace_id     opaque pointer (audit-only)
```

This is the audit unit. No artifact leaves the system without one.

## 13. Implementation Order

This doc is contract-level. Implementation lands in the following sequence
(detailed in [roadmap.md](./roadmap.md)):

```text
1. Postgres migrations for LicenseRegistry, ModelRegistry, ConsentRecord,
   OutputProvenance, SafetyReviewStatus, audit_events. Seed with the
   existing in-code provider list.

2. /admin route additions: model registry browser, license registry
   browser, consent record manager (read-only first), provenance viewer.

3. Prompt engine: extend detect_risky_filler with the blocked-prompt
   categories; emit codified preflight error codes instead of free strings.

4. Inference service: route handlers cite consent records and license
   bundles in OutputProvenance. The mock provider seeds these fields so
   the contract is exercised end-to-end.

5. Release pipeline: implement the release_eligible predicate. Initially
   it returns false everywhere; each gate is wired in turn.
```

## 13a. S10 Implementation Status (2026-05-16)

S10 has shipped the in-memory contract layer. Files:

- `services/soundsystem-inference/app/schemas.py` — full enum + model set.
- `services/soundsystem-inference/app/compliance_seed.py` — stable UUID5
  seed; every entry is `research_only` + `not_wired`/`mock` by default.
- `services/soundsystem-inference/app/compliance_repository.py` — Protocol
  + in-memory implementation + factory.
- `services/soundsystem-inference/app/compliance_preflight.py` — pure
  evaluators for `evaluate_preflight` and `evaluate_release_eligibility`,
  emitting the codified `preflight_block_*` codes from §8.
- `services/soundsystem-inference/db/003_compliance.sql` — Postgres
  migration (idempotent; FK chain: model_registry.license_id →
  license_registry, output_provenance.parent_provenance_id →
  output_provenance, output_provenance.provider → model_registry).
- 10 routes at `/v1/compliance/{summary,models,licenses,consent-records,
  provenance,audit-events,preflight,release-eligibility/{artifact_id}}`.
- Capabilities response now exposes `compliance_repository_mode`,
  `compliance_registry_available`, `compliance_preflight_available`.
- Read-only admin surface at `/admin/soundsystem/safety`.

S10b will swap the in-memory repository for a Postgres-backed variant
without changing the route handlers. The route layer consults
`build_default_compliance_repository()` so the swap stays local.

## 14. Cross-References

- [admin-integration-strategy.md](./admin-integration-strategy.md) — host
  surface that consumes these schemas.
- [model-provider-strategy.md](./model-provider-strategy.md) — every
  candidate model is filtered through this compliance layer.
- [copyright-safety.md](./copyright-safety.md) — earlier sketch of safety
  posture; this doc supersedes it for the data model.
- [lyrics-engine.md](./lyrics-engine.md) — first surface where some of
  these contracts are already partially implemented (preflight blocks,
  locked sections).
- [roadmap.md](./roadmap.md) — slice sequence.
