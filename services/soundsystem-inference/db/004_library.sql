-- SNUFFRAGA PROJECT LIBRARY persistence (Slice 19).
--
-- Apply manually for local dev:
--   psql "$SOUNDSYSTEM_DATABASE_URL" -f services/soundsystem-inference/db/004_library.sql
--
-- Idempotent — safe to re-apply.

CREATE TABLE IF NOT EXISTS library_packs (
  pack_id                    UUID         PRIMARY KEY,
  title                      TEXT         NOT NULL,
  status                     TEXT         NOT NULL DEFAULT 'draft',
  music_job_id               UUID         NOT NULL,
  lyrics_version_id          UUID         NULL,
  arrangement_id             UUID         NULL,
  provenance_id              UUID         NULL,
  components                 JSONB        NOT NULL DEFAULT '[]'::jsonb,
  total_components           INTEGER      NOT NULL DEFAULT 0,
  estimated_duration_seconds DOUBLE PRECISION NULL,
  bpm                        INTEGER      NULL,
  key_signature              TEXT         NULL,
  intent                     TEXT         NULL,
  operator_id                TEXT         NULL,
  notes                      TEXT         NULL,
  created_at                 TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS library_packs_created_idx
  ON library_packs (created_at DESC);

CREATE INDEX IF NOT EXISTS library_packs_music_job_idx
  ON library_packs (music_job_id);

CREATE TABLE IF NOT EXISTS library_entries (
  entry_id                   UUID         PRIMARY KEY,
  pack_id                    UUID         NOT NULL REFERENCES library_packs(pack_id) ON DELETE CASCADE,
  title                      TEXT         NOT NULL,
  slug                       TEXT         NOT NULL,
  intent                     TEXT         NULL,
  status                     TEXT         NOT NULL DEFAULT 'complete',
  bpm                        INTEGER      NULL,
  key_signature              TEXT         NULL,
  estimated_duration_seconds DOUBLE PRECISION NULL,
  component_count            INTEGER      NOT NULL DEFAULT 0,
  artifact_count             INTEGER      NOT NULL DEFAULT 0,
  has_lyrics                 BOOLEAN      NOT NULL DEFAULT FALSE,
  has_arrangement            BOOLEAN      NOT NULL DEFAULT FALSE,
  has_provenance             BOOLEAN      NOT NULL DEFAULT FALSE,
  operator_id                TEXT         NULL,
  created_at                 TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS library_entries_created_idx
  ON library_entries (created_at DESC);

CREATE INDEX IF NOT EXISTS library_entries_pack_idx
  ON library_entries (pack_id);

CREATE INDEX IF NOT EXISTS library_entries_slug_idx
  ON library_entries (slug);
