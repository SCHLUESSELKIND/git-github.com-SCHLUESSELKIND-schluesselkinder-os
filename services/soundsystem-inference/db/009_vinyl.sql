-- S47: Vinyl Release Object persistence
-- Collector-vinyl release objects with provider handoff metadata.
-- No real elasticStage/DISC_ARCHIVE API calls. Manual handoff only.

CREATE TABLE IF NOT EXISTS vinyl_releases (
    vinyl_id                UUID        PRIMARY KEY,
    release_id              UUID        NOT NULL,
    title                   TEXT        NOT NULL,
    artist                  TEXT        NOT NULL,
    provider_group          TEXT        NOT NULL,
    status                  TEXT        NOT NULL,
    format                  TEXT        NOT NULL,
    edition_type            TEXT        NOT NULL,
    pressing_quantity       INTEGER     NULL,
    numbered                BOOLEAN     NOT NULL DEFAULT FALSE,
    side_a_tracks           JSONB       NOT NULL DEFAULT '[]'::jsonb,
    side_b_tracks           JSONB       NOT NULL DEFAULT '[]'::jsonb,
    cover_artifact_id       UUID        NULL,
    audio_master_artifact_id UUID       NULL,
    export_artifact_id      UUID        NULL,
    soundcloud_job_id       UUID        NULL,
    readiness_items         JSONB       NOT NULL DEFAULT '[]'::jsonb,
    warnings                JSONB       NOT NULL DEFAULT '[]'::jsonb,
    notes                   TEXT        NULL,
    created_by              TEXT        NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vinyl_releases_created_at
    ON vinyl_releases (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_vinyl_releases_release_id
    ON vinyl_releases (release_id);

CREATE INDEX IF NOT EXISTS idx_vinyl_releases_provider_group
    ON vinyl_releases (provider_group);

CREATE INDEX IF NOT EXISTS idx_vinyl_releases_status
    ON vinyl_releases (status);
