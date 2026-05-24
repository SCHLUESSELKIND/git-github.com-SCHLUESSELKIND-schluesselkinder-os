-- SNUFFRAGA LYRICS ENGINE persistence (Slice 7).
--
-- Apply manually for local dev:
--   psql "$SOUNDSYSTEM_DATABASE_URL" -f services/soundsystem-inference/db/002_lyrics.sql
--
-- This script is idempotent — it can be re-applied to an existing database
-- without error. Keep it simple; no auto-migration runner exists yet.

CREATE TABLE IF NOT EXISTS lyrics_projects (
  id                  UUID         PRIMARY KEY,
  project_key         TEXT         NOT NULL UNIQUE,
  title               TEXT         NULL,
  character_code      TEXT         NOT NULL,
  current_version_id  UUID         NULL,
  created_at          TIMESTAMPTZ  NOT NULL,
  updated_at          TIMESTAMPTZ  NOT NULL
);

-- Backfill for an already-applied 002 without current_version_id.
ALTER TABLE lyrics_projects
  ADD COLUMN IF NOT EXISTS current_version_id UUID NULL;

CREATE TABLE IF NOT EXISTS lyrics_versions (
  id                 UUID         PRIMARY KEY,
  project_id         UUID         NOT NULL REFERENCES lyrics_projects(id) ON DELETE CASCADE,
  version_number     INTEGER      NOT NULL,
  parent_version_id  UUID         NULL REFERENCES lyrics_versions(id) ON DELETE SET NULL,
  structure          JSONB        NOT NULL,
  edit_summary       TEXT         NULL,
  created_at         TIMESTAMPTZ  NOT NULL,
  CONSTRAINT lyrics_versions_project_version_unique
    UNIQUE (project_id, version_number)
);

CREATE INDEX IF NOT EXISTS lyrics_versions_project_idx
  ON lyrics_versions (project_id, version_number);

CREATE INDEX IF NOT EXISTS lyrics_projects_created_idx
  ON lyrics_projects (created_at DESC);
