-- S38: Merch Capsule Persistence
--
-- Stores merch capsule data alongside the in-memory default.
-- No commerce API calls. No inventory mutation. No shop sync.
-- Provider export remains mock-only.

CREATE TABLE IF NOT EXISTS merch_capsules (
    capsule_id          UUID        PRIMARY KEY,
    release_id          UUID        NOT NULL,
    title               TEXT        NOT NULL,
    artist              TEXT        NOT NULL,
    status              TEXT        NOT NULL DEFAULT 'draft',
    availability_strategy TEXT      NOT NULL DEFAULT '70_20_10',
    products            JSONB       NOT NULL DEFAULT '[]'::jsonb,
    max_active_products INTEGER     NOT NULL DEFAULT 5,
    provider_groups     JSONB       NOT NULL DEFAULT '[]'::jsonb,
    drop_window_start   TEXT        NULL,
    drop_window_end     TEXT        NULL,
    notes               TEXT        NULL,
    warnings            JSONB       NOT NULL DEFAULT '[]'::jsonb,
    export_payload      JSONB       NULL,
    created_by          TEXT        NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_merch_capsules_created_at
    ON merch_capsules (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_merch_capsules_release_id
    ON merch_capsules (release_id);

CREATE INDEX IF NOT EXISTS idx_merch_capsules_status
    ON merch_capsules (status);
