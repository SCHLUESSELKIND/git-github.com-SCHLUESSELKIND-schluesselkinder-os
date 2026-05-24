-- SNUFFRAGA ARTIFACT REGISTRY persistence (Slice 29).
--
-- Metadata-only persistence for artifact records. File bytes remain
-- in local storage (or S3 later) — never stored in Postgres.
--
-- Apply manually for local dev:
--   psql "$SOUNDSYSTEM_DATABASE_URL" -f services/soundsystem-inference/db/006_artifacts.sql
--
-- Idempotent — safe to re-apply.

CREATE TABLE IF NOT EXISTS artifact_records (
  artifact_id                UUID         PRIMARY KEY,
  kind                       TEXT         NOT NULL,
  status                     TEXT         NOT NULL DEFAULT 'planned',
  storage_mode               TEXT         NOT NULL DEFAULT 'local',
  logical_path               TEXT         NOT NULL,
  storage_key                TEXT         NOT NULL,
  content_type               TEXT         NOT NULL DEFAULT 'application/octet-stream',
  size_bytes                 BIGINT       NOT NULL DEFAULT 0,
  checksum_sha256            TEXT         NULL,
  operator_id                TEXT         NULL,
  source_entity_type         TEXT         NULL,
  source_entity_id           TEXT         NULL,
  provenance_id              UUID         NULL,
  created_at                 TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at                 TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS artifact_records_created_idx
  ON artifact_records (created_at DESC);

CREATE INDEX IF NOT EXISTS artifact_records_kind_idx
  ON artifact_records (kind);

CREATE INDEX IF NOT EXISTS artifact_records_status_idx
  ON artifact_records (status);

CREATE INDEX IF NOT EXISTS artifact_records_source_idx
  ON artifact_records (source_entity_type, source_entity_id);

CREATE INDEX IF NOT EXISTS artifact_records_provenance_idx
  ON artifact_records (provenance_id);
