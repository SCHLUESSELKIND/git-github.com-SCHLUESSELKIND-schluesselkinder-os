-- S53: Analytics Persistence + Connector Import Audit Log
-- Analytics events table + connector import audit log.

BEGIN;

-- Analytics events (persisted from in-memory analytics repository)
CREATE TABLE IF NOT EXISTS analytics_events (
    id              UUID PRIMARY KEY,
    source          TEXT NOT NULL,
    metric          TEXT NOT NULL,
    value           DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    campaign_id     UUID,
    release_id      UUID,
    track_id        UUID,
    metadata        JSONB NOT NULL DEFAULT '{}',
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analytics_events_source ON analytics_events (source);
CREATE INDEX IF NOT EXISTS idx_analytics_events_metric ON analytics_events (metric);
CREATE INDEX IF NOT EXISTS idx_analytics_events_campaign_id ON analytics_events (campaign_id) WHERE campaign_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_analytics_events_release_id ON analytics_events (release_id) WHERE release_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_analytics_events_track_id ON analytics_events (track_id) WHERE track_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events (timestamp DESC);

-- Connector import audit log
CREATE TABLE IF NOT EXISTS connector_import_audit (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_type  TEXT NOT NULL,
    operator_id     TEXT NOT NULL,
    event_count     INTEGER NOT NULL DEFAULT 0,
    event_ids       UUID[] NOT NULL DEFAULT '{}',
    status          TEXT NOT NULL DEFAULT 'completed',
    error_message   TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_connector_import_audit_connector_type ON connector_import_audit (connector_type);
CREATE INDEX IF NOT EXISTS idx_connector_import_audit_operator_id ON connector_import_audit (operator_id);
CREATE INDEX IF NOT EXISTS idx_connector_import_audit_created_at ON connector_import_audit (created_at DESC);

COMMIT;
