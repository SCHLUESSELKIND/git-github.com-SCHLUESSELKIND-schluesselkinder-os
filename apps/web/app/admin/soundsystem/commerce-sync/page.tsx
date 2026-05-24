import { SoundsystemShell } from "../_components/SoundsystemShell";
import {
  getCommerceSyncSummary,
  InferenceClientError,
  listCommerceSyncAudit,
  listCommerceSyncCapsules,
} from "../_lib/inference";
import type {
  CommerceCapsuleSyncState,
  CommerceSyncAuditRecord,
  CommerceSyncProviderState,
  CommerceSyncStatus,
  CommerceSyncSummary,
} from "../_lib/inference-types";
import { CommerceSyncControls } from "./_components/CommerceSyncControls";

export const dynamic = "force-dynamic";

const STATUS_COLOR: Record<CommerceSyncStatus, string> = {
  not_synced: "var(--ss-text-muted)",
  synced_mock: "var(--ss-accent)",
  synced_live: "#22c55e",
  partial: "#facc15",
  blocked: "#f97316",
  failed: "#ef4444",
};

/**
 * S64 — Commerce Sync Dashboard.
 *
 * Unified operator screen for syncing each MerchCapsule to Shopify drafts
 * and Printful sync products. Read-only by default; one POST per capsule
 * action. No automatic sync, no publishing, no inventory mutation.
 */
export default async function CommerceSyncPage() {
  let summary: CommerceSyncSummary | null = null;
  let capsules: CommerceCapsuleSyncState[] = [];
  let auditRecords: CommerceSyncAuditRecord[] = [];
  let errorMessage: string | null = null;

  try {
    [summary, capsules, auditRecords] = await Promise.all([
      getCommerceSyncSummary(),
      listCommerceSyncCapsules(),
      listCommerceSyncAudit(50),
    ]);
  } catch (err) {
    if (err instanceof InferenceClientError) {
      errorMessage = `Inference error: ${err.message}`;
    } else {
      throw err;
    }
  }

  return (
    <SoundsystemShell title="Commerce Sync" status="OPERATOR DASHBOARD">
      <p className="mb-6 font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        One capsule, one screen. Shopify drafts + Printful sync products.
        Operator-triggered only. No publishing. No inventory, order, or
        customer mutation.
      </p>

      {errorMessage && (
        <p className="mb-6 border border-orange-500 px-4 py-3 font-mono text-[0.6rem] uppercase tracking-widest text-orange-400">
          {errorMessage}
        </p>
      )}

      {summary && <SummaryStrip summary={summary} />}

      {capsules.length === 0 ? (
        <p className="mt-6 border border-dashed border-[color:var(--ss-border)] px-5 py-6 text-center font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          No merch capsules yet. Build one from a release first.
        </p>
      ) : (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {capsules.map((capsule) => (
            <CapsuleCard key={capsule.capsule_id} capsule={capsule} />
          ))}
        </div>
      )}

      {/* S65 — Audit log */}
      <h3 className="mb-3 mt-10 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
        AUDIT LOG
      </h3>
      <p className="mb-3 font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        Append-only audit. Records operator-triggered sync intent only.
      </p>
      {auditRecords.length === 0 ? (
        <p className="border border-dashed border-[color:var(--ss-border)] px-5 py-6 text-center font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          No audit records yet.
        </p>
      ) : (
        <div className="flex flex-col gap-1">
          {auditRecords.map((r) => (
            <AuditRow key={r.audit_id} record={r} />
          ))}
        </div>
      )}
    </SoundsystemShell>
  );
}

const ACTION_COLOR: Record<string, string> = {
  sync_shopify: "var(--ss-accent)",
  sync_printful: "var(--ss-accent)",
  sync_both: "#22c55e",
};

function AuditRow({ record }: Readonly<{ record: CommerceSyncAuditRecord }>) {
  const actionColor = ACTION_COLOR[record.action] ?? "var(--ss-text-muted)";
  const statusColor = STATUS_COLOR[record.overall_status];
  return (
    <div
      className="flex flex-wrap items-center justify-between gap-3 border-l-2 px-3 py-2"
      style={{
        borderColor: statusColor,
        backgroundColor: "var(--ss-panel)",
      }}
    >
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <span
            className="border px-1 py-0.5 font-mono text-[0.45rem] font-black uppercase tracking-widest"
            style={{ borderColor: actionColor, color: actionColor }}
          >
            {record.action}
          </span>
          <span
            className="border px-1 py-0.5 font-mono text-[0.45rem] font-black uppercase tracking-widest"
            style={{ borderColor: statusColor, color: statusColor }}
          >
            {record.overall_status}
          </span>
          {record.operator_id && (
            <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              by {record.operator_id}
            </span>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-3 text-[color:var(--ss-text-muted)]">
          <span className="font-mono text-[0.42rem] uppercase tracking-widest">
            CAP {String(record.capsule_id).slice(0, 8)}
          </span>
          {record.release_id && (
            <span className="font-mono text-[0.42rem] uppercase tracking-widest">
              REL {String(record.release_id).slice(0, 8)}
            </span>
          )}
          <span className="font-mono text-[0.42rem] uppercase tracking-widest">
            SHOPIFY {record.shopify_item_count} · PRINTFUL{" "}
            {record.printful_item_count}
          </span>
        </div>
        {record.warnings.length > 0 && (
          <span className="font-mono text-[0.45rem] uppercase tracking-widest text-orange-400">
            {record.warnings.join(" · ")}
          </span>
        )}
      </div>
      <span className="font-mono text-[0.42rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {new Date(record.created_at)
          .toISOString()
          .slice(0, 16)
          .replace("T", " ")}
      </span>
    </div>
  );
}

function SummaryStrip({
  summary,
}: Readonly<{ summary: CommerceSyncSummary }>) {
  return (
    <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-7">
      <SummaryCell label="Total" count={summary.total_capsules} />
      <SummaryCell
        label="Not synced"
        count={summary.not_synced}
        color={STATUS_COLOR.not_synced}
      />
      <SummaryCell
        label="Synced mock"
        count={summary.synced_mock}
        color={STATUS_COLOR.synced_mock}
      />
      <SummaryCell
        label="Synced live"
        count={summary.synced_live}
        color={STATUS_COLOR.synced_live}
      />
      <SummaryCell
        label="Partial"
        count={summary.partial}
        color={STATUS_COLOR.partial}
      />
      <SummaryCell
        label="Blocked"
        count={summary.blocked}
        color={STATUS_COLOR.blocked}
      />
      <SummaryCell
        label="Failed"
        count={summary.failed}
        color={STATUS_COLOR.failed}
      />
      <div
        className="col-span-full px-4 py-2"
        style={{ backgroundColor: "var(--ss-panel)" }}
      >
        <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          PROVIDER MODES:{" "}
          <span
            style={{
              color:
                summary.shopify_provider_mode === "shopify"
                  ? "#22c55e"
                  : "var(--ss-text-muted)",
            }}
          >
            SHOPIFY {summary.shopify_provider_mode.toUpperCase()}
          </span>
          {" · "}
          <span
            style={{
              color:
                summary.printful_provider_mode === "printful"
                  ? "#22c55e"
                  : "var(--ss-text-muted)",
            }}
          >
            PRINTFUL {summary.printful_provider_mode.toUpperCase()}
          </span>
        </span>
      </div>
    </div>
  );
}

function SummaryCell({
  label,
  count,
  color,
}: Readonly<{ label: string; count: number; color?: string }>) {
  return (
    <div className="px-3 py-2" style={{ backgroundColor: "var(--ss-panel)" }}>
      <div className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </div>
      <div
        className="font-mono text-xl font-black"
        style={{ color: color ?? "var(--ss-text-primary)" }}
      >
        {count}
      </div>
    </div>
  );
}

function CapsuleCard({
  capsule,
}: Readonly<{ capsule: CommerceCapsuleSyncState }>) {
  return (
    <div
      className="flex flex-col gap-3 border border-[color:var(--ss-border)] px-5 py-4"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-mono text-[0.62rem] font-bold text-[color:var(--ss-text-primary)]">
          {capsule.title}
        </span>
        <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          CAP {String(capsule.capsule_id).slice(0, 8)}
        </span>
      </div>

      <div className="flex items-center gap-2">
        <span
          className="border px-2 py-1 font-mono text-[0.48rem] font-black uppercase tracking-widest"
          style={{
            borderColor: STATUS_COLOR[capsule.overall_status],
            color: STATUS_COLOR[capsule.overall_status],
          }}
        >
          OVERALL · {capsule.overall_status}
        </span>
        <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {capsule.product_count} PRODUCTS
        </span>
      </div>

      <div className="grid gap-2 md:grid-cols-2">
        <ProviderColumn state={capsule.shopify} />
        <ProviderColumn state={capsule.printful} />
      </div>

      {capsule.warnings.length > 0 && (
        <div className="flex flex-col gap-1">
          {capsule.warnings.map((w, i) => (
            <span
              key={i}
              className="font-mono text-[0.45rem] uppercase tracking-widest text-orange-400"
            >
              {w}
            </span>
          ))}
        </div>
      )}

      <CommerceSyncControls capsuleId={String(capsule.capsule_id)} />
    </div>
  );
}

function ProviderColumn({
  state,
}: Readonly<{ state: CommerceSyncProviderState }>) {
  const liveBadge =
    (state.provider === "shopify" && state.provider_mode === "shopify") ||
    (state.provider === "printful" && state.provider_mode === "printful");
  return (
    <div
      className="flex flex-col gap-1 border border-[color:var(--ss-border)] px-3 py-2"
      style={{ backgroundColor: "var(--ss-bg)" }}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          {state.provider}
        </span>
        <span
          className="font-mono text-[0.42rem] font-black uppercase tracking-widest"
          style={{
            color: liveBadge ? "#22c55e" : "var(--ss-text-muted)",
          }}
        >
          {liveBadge ? "LIVE" : "MOCK"}
        </span>
      </div>
      <span
        className="font-mono text-[0.48rem] uppercase tracking-widest"
        style={{ color: STATUS_COLOR[state.status] }}
      >
        {state.status} ({state.synced_item_count}/{state.item_count})
      </span>
      {state.blocked_item_count > 0 && (
        <span className="font-mono text-[0.45rem] uppercase tracking-widest text-orange-400">
          {state.blocked_item_count} blocked
        </span>
      )}
      {state.failed_item_count > 0 && (
        <span className="font-mono text-[0.45rem] uppercase tracking-widest text-red-400">
          {state.failed_item_count} failed
        </span>
      )}
      {state.provider_ids.slice(0, 2).map((pid) => (
        <span
          key={pid}
          className="font-mono text-[0.42rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]"
        >
          {pid}
        </span>
      ))}
      {state.provider_ids.length > 2 && (
        <span className="font-mono text-[0.42rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          +{state.provider_ids.length - 2} more
        </span>
      )}
      {state.last_synced_at && (
        <span className="font-mono text-[0.42rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {new Date(state.last_synced_at)
            .toISOString()
            .slice(0, 16)
            .replace("T", " ")}
        </span>
      )}
    </div>
  );
}
