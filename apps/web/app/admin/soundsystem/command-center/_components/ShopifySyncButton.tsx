"use client";

import { useState, useTransition } from "react";
import { syncShopifyDrafts } from "../../_lib/inference";
import type { ShopifyDraftExport } from "../../_lib/inference-types";

/**
 * S62 — Shopify Live Draft Sync button.
 *
 * Creates Shopify products with status=DRAFT via the Admin GraphQL API.
 * NEVER publishes. NEVER mutates inventory, orders, customers, webhooks.
 * Token never appears in the response.
 */
export function ShopifySyncButton({
  capsuleId,
  providerMode,
}: Readonly<{ capsuleId: string; providerMode: "mock" | "shopify" }>) {
  const [isPending, startTransition] = useTransition();
  const [result, setResult] = useState<ShopifyDraftExport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleClick = () => {
    setError(null);
    startTransition(async () => {
      try {
        const res = await syncShopifyDrafts(capsuleId);
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
          {isPending ? "Syncing…" : "Sync Shopify Drafts"}
        </button>
        <span
          className="font-mono text-[0.45rem] font-black uppercase tracking-widest"
          style={{
            color:
              providerMode === "shopify"
                ? "#22c55e"
                : "var(--ss-text-muted)",
          }}
        >
          {providerMode === "shopify" ? "LIVE" : "MOCK"}
        </span>
      </div>

      <p className="font-mono text-[0.42rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        Creates Shopify draft products only. Does not publish. No inventory,
        order, or customer mutation.
      </p>

      {result && (
        <div className="mt-1 flex flex-col gap-0.5">
          <span className="font-mono text-[0.45rem] uppercase tracking-widest text-emerald-400">
            {result.total_products} drafts · mode {result.provider_mode}
          </span>
          {result.drafts.slice(0, 3).map((d) => {
            const productPayload = d.provider_payload as {
              shopify_product_id?: string;
              shopify_handle?: string;
            } | null;
            const adminId = productPayload?.shopify_product_id;
            const handle = productPayload?.shopify_handle;
            return (
              <span
                key={d.draft_id}
                className="font-mono text-[0.42rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]"
              >
                {d.status} · {handle ?? d.title}
                {adminId ? ` · ${adminId.split("/").pop()}` : ""}
              </span>
            );
          })}
          {result.drafts.length > 3 && (
            <span className="font-mono text-[0.42rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              +{result.drafts.length - 3} more
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
