-- S59: Automation Execution Audit Log + durable job storage.
-- Applied by hand for local dev: psql -f db/013_automation_execution.sql
--
-- These tables are append-only from the application's perspective. No row is
-- ever deleted by the inference service. Updates only happen on the jobs
-- table (status transitions); the audit log itself is INSERT-only.

CREATE TABLE IF NOT EXISTS automation_execution_jobs (
    execution_id        UUID PRIMARY KEY,
    rule_id             UUID NOT NULL,
    campaign_id         UUID NOT NULL,
    dry_run_status      TEXT NOT NULL,
    status              TEXT NOT NULL,
    proposed_changes    JSONB NOT NULL DEFAULT '[]',
    blocked_reasons     JSONB NOT NULL DEFAULT '[]',
    warnings            JSONB NOT NULL DEFAULT '[]',
    created_by          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_automation_exec_jobs_campaign_id
    ON automation_execution_jobs (campaign_id);
CREATE INDEX IF NOT EXISTS idx_automation_exec_jobs_rule_id
    ON automation_execution_jobs (rule_id);
CREATE INDEX IF NOT EXISTS idx_automation_exec_jobs_status
    ON automation_execution_jobs (status);
CREATE INDEX IF NOT EXISTS idx_automation_exec_jobs_created_at
    ON automation_execution_jobs (created_at DESC);


CREATE TABLE IF NOT EXISTS automation_execution_audit (
    audit_id            UUID PRIMARY KEY,
    execution_id        UUID NOT NULL,
    rule_id             UUID NOT NULL,
    campaign_id         UUID NOT NULL,
    from_status         TEXT,
    to_status           TEXT NOT NULL,
    operator_id         TEXT,
    reason              TEXT,
    details             JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_automation_exec_audit_execution_id
    ON automation_execution_audit (execution_id);
CREATE INDEX IF NOT EXISTS idx_automation_exec_audit_campaign_id
    ON automation_execution_audit (campaign_id);
CREATE INDEX IF NOT EXISTS idx_automation_exec_audit_created_at
    ON automation_execution_audit (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_automation_exec_audit_to_status
    ON automation_execution_audit (to_status);
