"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { bootstrapReleaseCommandCenter } from "../../_lib/inference";
import type { ReleaseCommandCenterBootstrapResult } from "../../_lib/inference-types";

/**
 * S61 — Bootstrap a Release Command Center.
 *
 * Creates the campaign (if missing) + instantiates recommended templates as
 * DRAFT rules. NEVER queues execution jobs. NEVER writes audit records.
 * NEVER mutates merch/distribution/vinyl.
 */
export function BootstrapButton({
  releaseId,
  hasCampaign,
}: Readonly<{ releaseId: string; hasCampaign: boolean }>) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [result, setResult] = useState<ReleaseCommandCenterBootstrapResult | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);

  const handleClick = () => {
    setError(null);
    startTransition(async () => {
      try {
        const res = await bootstrapReleaseCommandCenter(releaseId);
        setResult(res);
        router.refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      }
    });
  };

  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        onClick={handleClick}
        disabled={isPending}
        className="border border-[color:var(--ss-accent)] px-3 py-2 font-mono text-[0.55rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
      >
        {isPending
          ? "Bootstrapping…"
          : hasCampaign
          ? "Attach recommended templates"
          : "Bootstrap campaign + templates"}
      </button>
      {result && (
        <div className="flex flex-col gap-1">
          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-emerald-400">
            {result.created_campaign
              ? "Campaign created"
              : "Campaign already existed"}
          </span>
          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {result.instantiated_rule_ids.length} rules instantiated
          </span>
          {result.warnings.map((w, i) => (
            <span
              key={i}
              className="font-mono text-[0.5rem] uppercase tracking-widest text-orange-400"
            >
              {w}
            </span>
          ))}
        </div>
      )}
      {error && (
        <span className="font-mono text-[0.55rem] uppercase tracking-widest text-orange-400">
          {error}
        </span>
      )}
    </div>
  );
}
