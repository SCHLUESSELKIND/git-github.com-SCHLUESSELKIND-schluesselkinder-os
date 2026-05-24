-- SNUFFRAGA SOUNDSYSTEM Compliance Foundation (Slice 10).
--
-- Apply manually for local dev:
--   psql "$SOUNDSYSTEM_DATABASE_URL" -f services/soundsystem-inference/db/003_compliance.sql
--
-- Idempotent — re-apply safely. No destructive changes to existing tables.
-- The matching Postgres repository implementation ships in S10b. Until then,
-- the inference service runs the in-memory ComplianceRepository.

CREATE TABLE IF NOT EXISTS license_registry (
  license_id           UUID         PRIMARY KEY,
  model_or_dataset_id  TEXT         NOT NULL,
  license_name         TEXT         NOT NULL,
  license_url          TEXT         NULL,
  permits_commercial   BOOLEAN      NOT NULL,
  restrictions         JSONB        NOT NULL DEFAULT '[]'::jsonb,
  reviewed_by          TEXT         NULL,
  reviewed_at          TIMESTAMPTZ  NULL,
  status               TEXT         NOT NULL DEFAULT 'needs_review',
  notes                TEXT         NULL,
  created_at           TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS license_registry_model_idx
  ON license_registry (model_or_dataset_id);

CREATE TABLE IF NOT EXISTS model_registry (
  model_id              UUID         PRIMARY KEY,
  provider_group        TEXT         NOT NULL,
  adapter_key           TEXT         NOT NULL,
  display_name_internal TEXT         NOT NULL,
  commercial_status     TEXT         NOT NULL DEFAULT 'research_only',
  activation_status     TEXT         NOT NULL DEFAULT 'not_wired',
  risk_tier             TEXT         NOT NULL DEFAULT 'amber',
  license_id            UUID         NULL REFERENCES license_registry(license_id) ON DELETE SET NULL,
  notes                 TEXT         NULL,
  created_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
  CONSTRAINT model_registry_group_adapter_unique
    UNIQUE (provider_group, adapter_key)
);

CREATE INDEX IF NOT EXISTS model_registry_adapter_idx
  ON model_registry (adapter_key);
CREATE INDEX IF NOT EXISTS model_registry_group_idx
  ON model_registry (provider_group);
CREATE INDEX IF NOT EXISTS model_registry_status_idx
  ON model_registry (commercial_status, activation_status);

CREATE TABLE IF NOT EXISTS consent_records (
  consent_id      UUID         PRIMARY KEY,
  speaker_label   TEXT         NOT NULL,
  source_type     TEXT         NOT NULL,
  permitted_uses  JSONB        NOT NULL DEFAULT '[]'::jsonb,
  revoked_at      TIMESTAMPTZ  NULL,
  expires_at      TIMESTAMPTZ  NULL,
  notes           TEXT         NULL,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS consent_records_speaker_idx
  ON consent_records (speaker_label);
CREATE INDEX IF NOT EXISTS consent_records_state_idx
  ON consent_records (revoked_at, expires_at);

CREATE TABLE IF NOT EXISTS output_provenance (
  provenance_id              UUID         PRIMARY KEY,
  artifact_id                UUID         NOT NULL,
  artifact_kind              TEXT         NOT NULL,
  parent_provenance_id       UUID         NULL REFERENCES output_provenance(provenance_id) ON DELETE SET NULL,
  provider                   UUID         NULL REFERENCES model_registry(model_id) ON DELETE SET NULL,
  model                      TEXT         NULL,
  model_version              TEXT         NULL,
  prompt                     TEXT         NULL,
  prompt_tokens              INTEGER      NULL,
  completion_tokens          INTEGER      NULL,
  safety_notes               JSONB        NOT NULL DEFAULT '[]'::jsonb,
  rewrite_strategy           TEXT         NOT NULL,
  locked_sections_respected  BOOLEAN      NOT NULL DEFAULT TRUE,
  raw_provider_trace_id      TEXT         NULL,
  license_bundle             JSONB        NOT NULL DEFAULT '[]'::jsonb,
  consent_records            JSONB        NOT NULL DEFAULT '[]'::jsonb,
  consent_required           BOOLEAN      NOT NULL DEFAULT FALSE,
  commercial_status          TEXT         NOT NULL DEFAULT 'research_only',
  safety_review_status       TEXT         NOT NULL DEFAULT 'pending',
  created_at                 TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS output_provenance_artifact_idx
  ON output_provenance (artifact_id);
CREATE INDEX IF NOT EXISTS output_provenance_parent_idx
  ON output_provenance (parent_provenance_id);
CREATE INDEX IF NOT EXISTS output_provenance_status_idx
  ON output_provenance (commercial_status, safety_review_status);

CREATE TABLE IF NOT EXISTS audit_events (
  event_id         UUID         PRIMARY KEY,
  operator_id      TEXT         NULL,
  action           TEXT         NOT NULL,
  entity_type      TEXT         NOT NULL,
  entity_id        UUID         NULL,
  payload_summary  JSONB        NOT NULL DEFAULT '{}'::jsonb,
  created_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS audit_events_entity_idx
  ON audit_events (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS audit_events_action_idx
  ON audit_events (action, created_at DESC);
