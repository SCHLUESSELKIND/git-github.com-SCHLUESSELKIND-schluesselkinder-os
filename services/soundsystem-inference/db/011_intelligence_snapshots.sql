-- S54: Intelligence Snapshot Persistence
-- Frozen point-in-time intelligence overview snapshots.
-- Created only by explicit operator POST. No automation.

BEGIN;

CREATE TABLE IF NOT EXISTS intelligence_snapshots (
    snapshot_id              UUID PRIMARY KEY,
    status                   TEXT NOT NULL DEFAULT 'created',
    overview                 JSONB NOT NULL,
    event_count              INTEGER NOT NULL DEFAULT 0,
    source_event_latest_at   TIMESTAMPTZ NULL,
    notes                    TEXT NULL,
    created_by               TEXT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_intelligence_snapshots_created_at ON intelligence_snapshots (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_intelligence_snapshots_status ON intelligence_snapshots (status);

COMMIT;
