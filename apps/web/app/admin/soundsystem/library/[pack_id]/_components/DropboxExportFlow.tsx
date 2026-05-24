"use client";

import { useState, useTransition } from "react";
import {
  createDropboxExportPlan,
  listDropboxJobs,
  markDropboxJobReady,
  executeDropboxSync,
  getDropboxPlanByPack,
  InferenceClientError
} from "../../../_lib/inference";
import type {
  DropboxExportPlan,
  DropboxSyncJob
} from "../../../_lib/generated-inference-types";

type Props = Readonly<{
  packId: string;
}>;

type FlowStage = "idle" | "planned" | "ready" | "synced" | "error";

export function DropboxExportFlow({ packId }: Props) {
  const [stage, setStage] = useState<FlowStage>("idle");
  const [plan, setPlan] = useState<DropboxExportPlan | null>(null);
  const [syncJob, setSyncJob] = useState<DropboxSyncJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleMarkReady(): void {
    if (!syncJob) return;
    setError(null);
    startTransition(async () => {
      try {
        const ready = await markDropboxJobReady(syncJob.sync_id);
        setSyncJob(ready);
        setStage("ready");
      } catch (e) {
        setError(formatError(e));
      }
    });
  }

  function handleExecuteSync(): void {
    if (!syncJob) return;
    setError(null);
    startTransition(async () => {
      try {
        const synced = await executeDropboxSync(syncJob.sync_id);
        setSyncJob(synced);
        setStage("synced");
      } catch (e) {
        setError(formatError(e));
      }
    });
  }

  const handleCreatePlanWithJob = (): void => {
    setError(null);
    startTransition(async () => {
      try {
        let createdPlan: DropboxExportPlan;
        try {
          createdPlan = await getDropboxPlanByPack(packId);
        } catch {
          createdPlan = await createDropboxExportPlan({ pack_id: packId });
        }
        setPlan(createdPlan);
        setStage("planned");

        // Fetch the auto-created job
        const jobs = await listDropboxJobs();
        const job = jobs.find(
          (j) => j.pack_id === packId && j.plan_id === createdPlan.plan_id
        );
        if (job) setSyncJob(job);
      } catch (e) {
        setError(formatError(e));
        setStage("error");
      }
    });
  };

  return (
    <section className="mt-8">
      <header className="mb-4 flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
        <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          DROPBOX EXPORT
        </h2>
        <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {stage === "idle" && "READY"}
          {stage === "planned" && "PLAN CREATED"}
          {stage === "ready" && "READY FOR SYNC"}
          {stage === "synced" && "SYNCED"}
          {stage === "error" && "ERROR"}
        </span>
      </header>

      {/* Stage: idle */}
      {stage === "idle" && (
        <div className="grid gap-3">
          <p className="font-mono text-[0.62rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-muted)]">
            Create a reproducible Dropbox folder structure from this pack.
            Mock sync — no real Dropbox upload until S21.
          </p>
          <button
            type="button"
            onClick={handleCreatePlanWithJob}
            disabled={isPending}
            className="w-full border border-[color:var(--ss-border-accent)] px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
            style={{ minHeight: "var(--ss-tap-target)" }}
          >
            {isPending ? "CREATING…" : "CREATE DROPBOX EXPORT PLAN"}
          </button>
        </div>
      )}

      {/* Stage: planned — show folder structure */}
      {stage === "planned" && plan && (
        <div className="grid gap-3">
          <FolderPlanView plan={plan} />
          {syncJob && syncJob.status === "planned" && (
            <button
              type="button"
              onClick={handleMarkReady}
              disabled={isPending}
              className="w-full border border-[color:var(--ss-border-accent)] px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] disabled:opacity-50"
              style={{ minHeight: "var(--ss-tap-target)" }}
            >
              {isPending ? "MARKING…" : "MARK READY FOR SYNC"}
            </button>
          )}
        </div>
      )}

      {/* Stage: ready — show execute button */}
      {stage === "ready" && plan && syncJob && (
        <div className="grid gap-3">
          <FolderPlanView plan={plan} />
          <SyncJobStatus job={syncJob} />
          <button
            type="button"
            onClick={handleExecuteSync}
            disabled={isPending}
            className="w-full border border-[color:var(--ss-border-accent)] px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] disabled:opacity-50"
            style={{ minHeight: "var(--ss-tap-target)" }}
          >
            {isPending ? "SYNCING…" : "EXECUTE SYNC (MOCK)"}
          </button>
        </div>
      )}

      {/* Stage: synced */}
      {stage === "synced" && plan && syncJob && (
        <div className="grid gap-3">
          <FolderPlanView plan={plan} />
          <SyncJobStatus job={syncJob} />
        </div>
      )}

      {/* Error */}
      {error !== null && (
        <p
          className="mt-2 border border-[color:var(--ss-warning-dim)] px-3 py-2 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
          role="alert"
        >
          {error}
        </p>
      )}
    </section>
  );
}

function FolderPlanView({ plan }: Readonly<{ plan: DropboxExportPlan }>) {
  return (
    <div className="grid gap-2">
      {/* Target root */}
      <div
        className="flex items-center justify-between border border-[color:var(--ss-border)] px-3 py-2"
        style={{ backgroundColor: "var(--ss-panel-elevated)" }}
      >
        <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          TARGET
        </span>
        <span className="font-mono text-[0.65rem] text-[color:var(--ss-text-primary)]">
          {plan.target_root}
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2">
        <StatPill label="FILES" value={String(plan.total_files)} />
        <StatPill label="DIRS" value={String(plan.total_directories)} />
        <StatPill label="ENTRIES" value={String(plan.entries.length)} />
      </div>

      {/* File list */}
      <div className="grid gap-px border border-[color:var(--ss-border)]" style={{ backgroundColor: "var(--ss-border)" }}>
        {plan.entries.map((entry, i) => (
          <div
            key={i}
            className="grid grid-cols-[auto_1fr_auto] items-center gap-2 px-3 py-1.5"
            style={{ backgroundColor: "var(--ss-panel)" }}
          >
            <span className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
              {entry.is_directory ? "DIR" : "FILE"}
            </span>
            <span className="font-mono text-[0.6rem] text-[color:var(--ss-text-primary)]">
              {entry.relative_path}
            </span>
            {entry.size_hint && (
              <span className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
                {entry.size_hint}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function SyncJobStatus({ job }: Readonly<{ job: DropboxSyncJob }>) {
  const statusColor =
    job.status === "synced"
      ? "var(--ss-accent)"
      : job.status === "failed"
        ? "var(--ss-warning)"
        : "var(--ss-text-secondary)";

  return (
    <div
      className="grid grid-cols-3 gap-2 border border-[color:var(--ss-border)] px-3 py-2"
      style={{ backgroundColor: "var(--ss-panel-elevated)" }}
    >
      <div className="grid gap-0.5">
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          STATUS
        </span>
        <span className="font-mono text-[0.65rem] font-black uppercase" style={{ color: statusColor }}>
          {job.status}
        </span>
      </div>
      <div className="grid gap-0.5">
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          FILES
        </span>
        <span className="font-mono text-[0.65rem] text-[color:var(--ss-text-primary)]">
          {job.files_synced}/{job.files_planned}
        </span>
      </div>
      <div className="grid gap-0.5">
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          TARGET
        </span>
        <span className="break-all font-mono text-[0.55rem] text-[color:var(--ss-text-secondary)]">
          {job.target_root}
        </span>
      </div>
    </div>
  );
}

function StatPill({ label, value }: Readonly<{ label: string; value: string }>) {
  return (
    <div
      className="flex items-center justify-between border border-[color:var(--ss-border)] px-2 py-1.5"
      style={{ backgroundColor: "var(--ss-panel-elevated)" }}
    >
      <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </span>
      <span className="font-mono text-[0.7rem] font-black text-[color:var(--ss-text-primary)]">
        {value}
      </span>
    </div>
  );
}

function formatError(error: unknown): string {
  if (error instanceof InferenceClientError) {
    return error.status ? `${error.status} · ${error.message}` : error.message;
  }
  if (error instanceof Error) return error.message;
  return "dropbox_sync_error";
}
