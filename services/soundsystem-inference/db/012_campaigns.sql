-- S56: Campaign Persistence
-- Applied by hand for local dev: psql -f db/012_campaigns.sql

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id             UUID PRIMARY KEY,
    release_id              UUID NOT NULL,
    title                   TEXT NOT NULL,
    status                  TEXT NOT NULL,
    channels                JSONB NOT NULL DEFAULT '[]',
    tasks                   JSONB NOT NULL DEFAULT '[]',
    timeline                JSONB NOT NULL DEFAULT '[]',
    linked_merch_capsule_ids    JSONB NOT NULL DEFAULT '[]',
    linked_distribution_pack_ids JSONB NOT NULL DEFAULT '[]',
    linked_soundcloud_job_ids   JSONB NOT NULL DEFAULT '[]',
    warnings                JSONB NOT NULL DEFAULT '[]',
    notes                   TEXT,
    created_by              TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_campaigns_release_id ON campaigns (release_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns (status);
