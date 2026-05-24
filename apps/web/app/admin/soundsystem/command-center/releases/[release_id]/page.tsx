import Link from "next/link";
import { SoundsystemShell } from "../../../_components/SoundsystemShell";
import {
  getInferenceCapabilities,
  getReleaseCommandCenter,
  InferenceClientError,
} from "../../../_lib/inference";
import type {
  CommandCenterReadinessStatus,
  ReleaseCommandCenter,
} from "../../../_lib/inference-types";
import { BootstrapButton } from "../../_components/BootstrapButton";
import { PrintfulSyncButton } from "../../_components/PrintfulSyncButton";
import { ShopifySyncButton } from "../../_components/ShopifySyncButton";

export const dynamic = "force-dynamic";

const READINESS_COLOR: Record<CommandCenterReadinessStatus, string> = {
  ready: "#22c55e",
  warning: "#facc15",
  blocked: "#f97316",
  missing: "var(--ss-text-muted)",
};

type Props = {
  params: Promise<{ release_id: string }>;
};

/**
 * S61 — Command Center detail for a single release.
 *
 * Readiness board · recommended templates · bootstrap · dry-run summary ·
 * linked objects · navigation. No execution. No provider mutation.
 */
export default async function CommandCenterDetailPage({ params }: Props) {
  const { release_id } = await params;
  let cc: ReleaseCommandCenter | null = null;
  let shopifyProviderMode: "mock" | "shopify" = "mock";
  let printfulProviderMode: "mock" | "printful" = "mock";
  let errorMessage: string | null = null;

  try {
    cc = await getReleaseCommandCenter(release_id);
    const caps = await getInferenceCapabilities();
    shopifyProviderMode = caps.shopify_provider_mode ?? "mock";
    printfulProviderMode = caps.printful_provider_mode ?? "mock";
  } catch (error) {
    if (error instanceof InferenceClientError) {
      errorMessage =
        error.status === 404
          ? "Release not found."
          : `Inference error: ${error.message}`;
    } else {
      throw error;
    }
  }

  if (errorMessage || !cc) {
    return (
      <SoundsystemShell title="Not found." status="COMMAND CENTER">
        <p
          className="border border-orange-500 px-4 py-3 font-mono text-[0.7rem] uppercase tracking-widest text-orange-400"
        >
          {errorMessage || "Release not found."}
        </p>
        <Link
          href="/admin/soundsystem/command-center"
          className="mt-4 inline-block font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
        >
          ← Command Center
        </Link>
      </SoundsystemShell>
    );
  }

  return (
    <SoundsystemShell title={cc.release_title} status="COMMAND CENTER">
      <Link
        href="/admin/soundsystem/command-center"
        className="mb-6 inline-block font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
      >
        ← Command Center
      </Link>

      {/* Header */}
      <div
        className="mb-6 border border-[color:var(--ss-border)] px-5 py-4"
        style={{ backgroundColor: "var(--ss-panel-elevated)" }}
      >
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            REL {String(cc.release_id).slice(0, 8)}
          </span>
          <span
            className="font-mono text-[0.55rem] uppercase tracking-widest"
            style={{
              color: cc.campaign_id ? "#22c55e" : "var(--ss-text-muted)",
            }}
          >
            {cc.campaign_id
              ? `CAMPAIGN: ${cc.campaign_status ?? "—"}`
              : "CAMPAIGN: missing"}
          </span>
        </div>

        {cc.warnings.length > 0 && (
          <div className="mt-3 flex flex-col gap-1">
            {cc.warnings.map((w, i) => (
              <span
                key={i}
                className="font-mono text-[0.55rem] uppercase tracking-widest text-orange-400"
              >
                {w}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Bootstrap action */}
      <div className="mb-8">
        <h3 className="mb-2 font-mono text-[0.65rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          BOOTSTRAP
        </h3>
        <BootstrapButton
          releaseId={String(cc.release_id)}
          hasCampaign={cc.campaign_id !== null}
        />
        <p className="mt-3 font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          Creates campaign + recommended draft rules. No execution. No
          provider mutation. No audit records.
        </p>
      </div>

      {/* Readiness board */}
      <div className="mb-8">
        <h3 className="mb-4 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          READINESS
        </h3>
        <div className="grid gap-2 md:grid-cols-2">
          {cc.readiness_items.map((item) => (
            <div
              key={item.code}
              className="flex flex-col gap-1 border-l-2 px-3 py-2"
              style={{
                borderColor:
                  READINESS_COLOR[item.status] ?? "var(--ss-text-muted)",
                backgroundColor: "var(--ss-panel)",
              }}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-[0.55rem] font-bold uppercase tracking-widest text-[color:var(--ss-text-primary)]">
                  {item.label}
                </span>
                <span
                  className="font-mono text-[0.48rem] font-black uppercase tracking-widest"
                  style={{
                    color:
                      READINESS_COLOR[item.status] ?? "var(--ss-text-muted)",
                  }}
                >
                  {item.status}
                </span>
              </div>
              {item.warnings.length > 0 && (
                <div className="flex flex-col gap-1">
                  {item.warnings.map((w, i) => (
                    <span
                      key={i}
                      className="font-mono text-[0.48rem] text-[color:var(--ss-text-muted)]"
                    >
                      {w}
                    </span>
                  ))}
                </div>
              )}
              {item.linked_object_id && (
                <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                  LINKED: {String(item.linked_object_id).slice(0, 8)}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recommended templates */}
      <div className="mb-8">
        <h3 className="mb-4 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          RECOMMENDED TEMPLATES
        </h3>
        {cc.recommended_templates.length === 0 ? (
          <p className="border border-dashed border-[color:var(--ss-border)] px-4 py-3 font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            No recommendations.
          </p>
        ) : (
          <div className="flex flex-col gap-2">
            {cc.recommended_templates.map((tpl) => (
              <div
                key={tpl.template_slug}
                className="flex flex-wrap items-center justify-between gap-3 border border-[color:var(--ss-border)] px-4 py-3"
                style={{ backgroundColor: "var(--ss-panel)" }}
              >
                <div className="flex max-w-2xl flex-col gap-1">
                  <span className="font-mono text-[0.6rem] font-bold text-[color:var(--ss-text-primary)]">
                    {tpl.name}
                  </span>
                  {tpl.reason && (
                    <span className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
                      {tpl.reason}
                    </span>
                  )}
                  {tpl.warnings.length > 0 && (
                    <span className="font-mono text-[0.48rem] text-orange-400">
                      {tpl.warnings.join(" · ")}
                    </span>
                  )}
                </div>
                <span
                  className="font-mono text-[0.48rem] font-black uppercase tracking-widest"
                  style={{
                    color: tpl.already_attached
                      ? "#22c55e"
                      : "var(--ss-text-muted)",
                  }}
                >
                  {tpl.already_attached ? "ATTACHED" : "AVAILABLE"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Dry-run summary */}
      <div className="mb-8">
        <h3 className="mb-4 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          DRY-RUN SUMMARY
        </h3>
        <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-3">
          <SummaryCell
            label="Would run"
            count={cc.dry_run_summary.would_run ?? 0}
            color="#22c55e"
          />
          <SummaryCell
            label="Blocked"
            count={cc.dry_run_summary.blocked ?? 0}
            color="#f97316"
          />
          <SummaryCell
            label="No match"
            count={cc.dry_run_summary.no_match ?? 0}
          />
        </div>
        <p className="mt-3 font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          Dry-run only. No automation executed.
        </p>
      </div>

      {/* Linked objects */}
      <div className="mb-8">
        <h3 className="mb-4 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          LINKED OBJECTS
        </h3>
        <div className="grid gap-2 md:grid-cols-3">
          <LinkedColumn
            label="Merch capsules"
            ids={cc.linked_merch_capsule_ids}
            renderExtras={(id) => (
              <div className="flex flex-col gap-2">
                <ShopifySyncButton
                  capsuleId={id}
                  providerMode={shopifyProviderMode}
                />
                <PrintfulSyncButton
                  capsuleId={id}
                  providerMode={printfulProviderMode}
                />
              </div>
            )}
          />
          <LinkedColumn
            label="Distribution packs"
            ids={cc.linked_distribution_pack_ids}
          />
          <LinkedColumn label="Vinyl releases" ids={cc.linked_vinyl_ids} />
        </div>
      </div>

      {/* Navigation */}
      <div className="border-t border-[color:var(--ss-border)] pt-4">
        <div className="flex flex-wrap gap-4">
          <Link
            href={`/admin/soundsystem/releases/${cc.release_id}`}
            className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
          >
            → Release detail
          </Link>
          {cc.campaign_id && (
            <Link
              href={`/admin/soundsystem/campaigns/${cc.campaign_id}`}
              className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
            >
              → Campaign detail / automation panel
            </Link>
          )}
        </div>
      </div>
    </SoundsystemShell>
  );
}

function SummaryCell({
  label,
  count,
  color,
}: Readonly<{ label: string; count: number; color?: string }>) {
  return (
    <div
      className="px-4 py-3"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </div>
      <div
        className="mt-1 font-mono text-2xl font-black"
        style={{ color: color ?? "var(--ss-text-primary)" }}
      >
        {count}
      </div>
    </div>
  );
}

function LinkedColumn({
  label,
  ids,
  renderExtras,
}: Readonly<{
  label: string;
  ids: ReadonlyArray<string>;
  renderExtras?: (id: string) => React.ReactNode;
}>) {
  return (
    <div
      className="flex flex-col gap-2 border border-[color:var(--ss-border)] px-3 py-2"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </span>
      {ids.length === 0 ? (
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          none
        </span>
      ) : (
        ids.map((id) => (
          <div key={id} className="flex flex-col gap-1">
            <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-primary)]">
              {String(id).slice(0, 8)}
            </span>
            {renderExtras ? renderExtras(id) : null}
          </div>
        ))
      )}
    </div>
  );
}
