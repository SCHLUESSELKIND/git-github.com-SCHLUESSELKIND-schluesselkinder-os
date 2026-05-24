-- SNUFFRAGA RELEASE PACK persistence (Slice 23).
--
-- Apply manually for local dev:
--   psql "$SOUNDSYSTEM_DATABASE_URL" -f services/soundsystem-inference/db/005_releases.sql
--
-- Idempotent — safe to re-apply.

CREATE TABLE IF NOT EXISTS release_packs (
  release_id                 UUID         PRIMARY KEY,
  pack_id                    UUID         NOT NULL REFERENCES library_packs(pack_id) ON DELETE CASCADE,
  title                      TEXT         NOT NULL,
  artist                     TEXT         NOT NULL,
  status                     TEXT         NOT NULL DEFAULT 'draft',
  description                TEXT         NOT NULL DEFAULT '',
  social_copy                JSONB        NOT NULL DEFAULT '{}'::jsonb,
  compliance_checklist       JSONB        NOT NULL DEFAULT '[]'::jsonb,
  compliance_passed          BOOLEAN      NOT NULL DEFAULT FALSE,
  assets                     JSONB        NOT NULL DEFAULT '[]'::jsonb,
  dropbox_target             TEXT         NULL,
  genre                      TEXT         NULL,
  bpm                        INTEGER      NULL,
  key_signature              TEXT         NULL,
  duration_seconds           DOUBLE PRECISION NULL,
  operator_id                TEXT         NULL,
  created_at                 TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at                 TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS release_packs_created_idx
  ON release_packs (created_at DESC);

CREATE INDEX IF NOT EXISTS release_packs_pack_idx
  ON release_packs (pack_id);

CREATE INDEX IF NOT EXISTS release_packs_status_idx
  ON release_packs (status);
