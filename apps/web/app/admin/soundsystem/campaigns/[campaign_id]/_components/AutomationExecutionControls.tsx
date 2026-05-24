"use client";

import { useState, useTransition } from "react";
import {
  executeAutomationExecutionMock,
  queueAutomationExecution,
} from "../../../_lib/inference";
import type {
  AutomationExecutionJob,
  AutomationExecutionResult,
} from "../../../_lib/inference-types";

/**
 * S58 — Automation Execution Queue Boundary (client controls).
 *
 * Provides QUEUE EXECUTION / EXECUTE MOCK buttons for a rule + jobs.
 * Mock execution records intent only. No campaign or provider state is changed.
 * Execution is disabled by default; jobs are BLOCKED unless mode = mock.
 */
export function QueueExecutionButton({ ruleId }: Readonly<{ ruleId: string }>) {
  const [isPending, startTransition] = useTransition();
  const [result, setResult] = useState<AutomationExecutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleClick = () => {
    setError(null);
    startTransition(async () => {
      try {
        const res = await queueAutomationExecution(ruleId);
        setResult(res);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      }
    });
  };

  return (
    <div className="flex flex-col gap-1">
      <button
        type="button"
        onClick={handleClick}
        disabled={isPending}
        className="border border-[color:var(--ss-border-strong)] px-2 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)] hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
      >
        {isPending ? "Queueing…" : "Queue Execution"}
      </button>
      {result && (
        <span
          className="font-mono text-[0.5rem] uppercase tracking-widest"
          style={{
            color:
              result.job.status === "queued"
                ? "var(--ss-accent)"
                : result.job.status === "blocked"
                ? "#f97316"
                : "var(--ss-text-muted)",
          }}
        >
          {result.job.status} — {result.note}
        </span>
      )}
      {error && (
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-orange-400">
          {error}
        </span>
      )}
    </div>
  );
}

export function ExecuteMockButton({
  executionId,
  initialStatus,
}: Readonly<{ executionId: string; initialStatus: string }>) {
  const [isPending, startTransition] = useTransition();
  const [status, setStatus] = useState(initialStatus);
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleClick = () => {
    setError(null);
    startTransition(async () => {
      try {
        const res = await executeAutomationExecutionMock(executionId);
        setStatus(res.job.status);
        setNote(res.note);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      }
    });
  };

  if (status !== "queued") {
    return (
      <span
        className="font-mono text-[0.48rem] uppercase tracking-widest"
        style={{ color: "var(--ss-text-muted)" }}
      >
        {note ?? "Read-only"}
      </span>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      <button
        type="button"
        onClick={handleClick}
        disabled={isPending}
        className="border border-[color:var(--ss-accent)] px-2 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
      >
        {isPending ? "Executing…" : "Execute Mock"}
      </button>
      {note && (
        <span className="font-mono text-[0.48rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {note}
        </span>
      )}
      {error && (
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-orange-400">
          {error}
        </span>
      )}
    </div>
  );
}

export function ExecutionStatusChip({ status }: Readonly<{ status: string }>) {
  const color =
    status === "completed_mock"
      ? "#22c55e"
      : status === "queued"
      ? "var(--ss-accent)"
      : status === "blocked"
      ? "#f97316"
      : status === "failed"
      ? "#ef4444"
      : "var(--ss-text-muted)";

  const label =
    status === "completed_mock"
      ? "COMPLETED MOCK"
      : status.replace(/_/g, " ").toUpperCase();

  return (
    <span
      className="border px-1.5 py-0.5 font-mono text-[0.48rem] font-black uppercase tracking-widest"
      style={{ borderColor: color, color }}
    >
      {label}
    </span>
  );
}
