-- S65: Commerce Sync Audit Log — append-only.
-- Applied by hand for local dev: psql -f db/014_commerce_sync_audit.sql
--
-- The application never deletes rows from this table. Audit rows are
-- INSERT-only at the application layer.

CREATE TABLE IF NOT EXISTS commerce_sync_audit (
    audit_id                UUID PRIMARY KEY,
    capsule_id              UUID NOT NULL,
    release_id              UUID,
    operator_id             TEXT,
    action                  TEXT NOT NULL,
    overall_status          TEXT NOT NULL,
    shopify_status          TEXT,
    printful_status         TEXT,
    shopify_item_count      INTEGER NOT NULL DEFAULT 0,
    printful_item_count     INTEGER NOT NULL DEFAULT 0,
    warnings                JSONB NOT NULL DEFAULT '[]',
    details                 JSONB NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_commerce_sync_audit_capsule_id
    ON commerce_sync_audit (capsule_id);
CREATE INDEX IF NOT EXISTS idx_commerce_sync_audit_release_id
    ON commerce_sync_audit (release_id);
CREATE INDEX IF NOT EXISTS idx_commerce_sync_audit_action
    ON commerce_sync_audit (action);
CREATE INDEX IF NOT EXISTS idx_commerce_sync_audit_overall_status
    ON commerce_sync_audit (overall_status);
CREATE INDEX IF NOT EXISTS idx_commerce_sync_audit_created_at
    ON commerce_sync_audit (created_at DESC);
