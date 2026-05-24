"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { createIntelligenceSnapshot } from "../../_lib/inference";

/**
 * Client component for creating intelligence snapshots via POST.
 * Minimal — only exists because server components cannot fire POSTs.
 */
export function CreateSnapshotButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate() {
    setLoading(true);
    setError(null);
    try {
      await createIntelligenceSnapshot();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Snapshot creation failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={handleCreate}
        disabled={loading}
        className="border border-[color:var(--ss-accent)] px-4 py-2 font-mono text-[0.6rem] font-black uppercase tracking-widest transition-colors hover:bg-[color:var(--ss-accent)] hover:text-black disabled:opacity-40"
        style={{ color: "var(--ss-accent)" }}
      >
        {loading ? "CREATING..." : "CREATE SNAPSHOT"}
      </button>
      <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        Manual snapshot only. No scheduled analytics job.
      </span>
      {error ? (
        <span
          className="font-mono text-[0.5rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
        >
          {error}
        </span>
      ) : null}
    </div>
  );
}
