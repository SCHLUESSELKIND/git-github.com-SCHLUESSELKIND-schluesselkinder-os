-- S38: Distribution Pack Persistence
--
-- Stores Ditto Music distribution pack data alongside the in-memory default.
-- No real Ditto API calls. No auto-publishing. No OAuth.
-- Distribution status remains manually tracked by the operator.

CREATE TABLE IF NOT EXISTS distribution_packs (
    distribution_id     UUID        PRIMARY KEY,
    release_id          UUID        NOT NULL,
    provider            TEXT        NOT NULL DEFAULT 'ditto',
    status              TEXT        NOT NULL DEFAULT 'draft',
    metadata            JSONB       NOT NULL DEFAULT '{}'::jsonb,
    readiness_checklist JSONB       NOT NULL DEFAULT '[]'::jsonb,
    readiness_passed    BOOLEAN     NOT NULL DEFAULT false,
    store_targets       JSONB       NOT NULL DEFAULT '[]'::jsonb,
    operator_notes      TEXT        NULL,
    created_by          TEXT        NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_distribution_packs_created_at
    ON distribution_packs (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_distribution_packs_release_id
    ON distribution_packs (release_id);

CREATE INDEX IF NOT EXISTS idx_distribution_packs_provider
    ON distribution_packs (provider);

CREATE INDEX IF NOT EXISTS idx_distribution_packs_status
    ON distribution_packs (status);
