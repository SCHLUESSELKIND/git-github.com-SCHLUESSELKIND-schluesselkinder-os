"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import {
  syncCommerceCapsuleBoth,
  syncPrintfulProducts,
  syncShopifyDrafts,
} from "../../_lib/inference";
import type { CommerceCapsuleSyncResult } from "../../_lib/inference-types";

/**
 * S64 — Commerce Sync controls.
 *
 * Per-capsule action row: Sync Shopify, Sync Printful, Sync Both.
 * Operator-triggered only. Draft/sync products only. No publishing.
 * Token never appears in the response.
 */
export function CommerceSyncControls({
  capsuleId,
}: Readonly<{ capsuleId: string }>) {
  const router = useRouter();
  const [pendingAction, setPendingAction] = useState<
    "shopify" | "printful" | "both" | null
  >(null);
  const [isPending, startTransition] = useTransition();
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = (
    action: "shopify" | "printful" | "both",
    fn: () => Promise<unknown>
  ) => {
    setError(null);
    setNote(null);
    setPendingAction(action);
    startTransition(async () => {
      try {
        const res = await fn();
        if (action === "both") {
          const r = res as CommerceCapsuleSyncResult;
          setNote(
            `Synced both · ${r.state.shopify.synced_item_count}/${r.state.shopify.item_count} Shopify · ${r.state.printful.synced_item_count}/${r.state.printful.item_count} Printful`
          );
        } else if (action === "shopify") {
          setNote("Shopify sync done");
        } else if (action === "printful") {
          setNote("Printful sync done");
        }
        router.refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setPendingAction(null);
      }
    });
  };

  const disabled = isPending;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => run("shopify", () => syncShopifyDrafts(capsuleId))}
          disabled={disabled}
          className="border border-[color:var(--ss-border-strong)] px-2 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)] hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
        >
          {pendingAction === "shopify" ? "Syncing…" : "Sync Shopify"}
        </button>
        <button
          type="button"
          onClick={() => run("printful", () => syncPrintfulProducts(capsuleId))}
          disabled={disabled}
          className="border border-[color:var(--ss-border-strong)] px-2 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)] hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
        >
          {pendingAction === "printful" ? "Syncing…" : "Sync Printful"}
        </button>
        <button
          type="button"
          onClick={() => run("both", () => syncCommerceCapsuleBoth(capsuleId))}
          disabled={disabled}
          className="border border-[color:var(--ss-accent)] px-2 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
        >
          {pendingAction === "both" ? "Syncing both…" : "Sync Both"}
        </button>
      </div>
      <p className="font-mono text-[0.42rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        Operator-triggered only. Draft/sync products only. No publishing.
      </p>
      {note && (
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-emerald-400">
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
