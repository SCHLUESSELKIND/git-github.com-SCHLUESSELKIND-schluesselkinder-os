"use client";

import { useState, useTransition } from "react";
import { syncPrintfulProducts } from "../../_lib/inference";
import type { PrintfulSyncExport } from "../../_lib/inference-types";

/**
 * S63 — Printful Live Product Sync button.
 *
 * Creates Printful sync products via the Store API (POST /store/products).
 * NEVER publishes the Shopify storefront. NEVER mutates inventory,
 * orders, customers, or webhooks. Vinyl products are blocked at the
 * sync boundary (not POD). Token never appears in the response.
 */
export function PrintfulSyncButton({
  capsuleId,
  providerMode,
}: Readonly<{ capsuleId: string; providerMode: "mock" | "printful" }>) {
  const [isPending, startTransition] = useTransition();
  const [result, setResult] = useState<PrintfulSyncExport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleClick = () => {
    setError(null);
    startTransition(async () => {
      try {
        const res = await syncPrintfulProducts(capsuleId);
        setResult(res);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      }
    });
  };

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={handleClick}
          disabled={isPending}
          className="border border-[color:var(--ss-accent)] px-2 py-1 font-mono text-[0.48rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
        >
          {isPending ? "Syncing…" : "Sync Printful Products"}
        </button>
        <span
          className="font-mono text-[0.45rem] font-black uppercase tracking-widest"
          style={{
            color:
              providerMode === "printful"
                ? "#22c55e"
                : "var(--ss-text-muted)",
          }}
        >
          {providerMode === "printful" ? "LIVE" : "MOCK"}
        </span>
      </div>

      <p className="font-mono text-[0.42rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        Creates Printful sync products only. Does not publish storefront. No
        inventory, order, or customer mutation.
      </p>

      {result && (
        <div className="mt-1 flex flex-col gap-0.5">
          <span className="font-mono text-[0.45rem] uppercase tracking-widest text-emerald-400">
            {result.total_products} syncs · mode {result.provider_mode}
          </span>
          {result.syncs.slice(0, 3).map((s) => {
            const productPayload = s.provider_payload as {
              printful_sync_product_id?: string | number;
              printful_external_id?: string;
            } | null;
            const pfId = productPayload?.printful_sync_product_id;
            return (
              <span
                key={s.sync_id}
                className="font-mono text-[0.42rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]"
              >
                {s.status} · {s.title}
                {pfId ? ` · PF#${pfId}` : ""}
              </span>
            );
          })}
          {result.syncs.length > 3 && (
            <span className="font-mono text-[0.42rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              +{result.syncs.length - 3} more
            </span>
          )}
        </div>
      )}

      {error && (
        <span className="font-mono text-[0.45rem] uppercase tracking-widest text-orange-400">
          {error}
        </span>
      )}
    </div>
  );
}
