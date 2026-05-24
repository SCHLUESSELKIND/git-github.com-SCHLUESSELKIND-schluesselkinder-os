import { SoundsystemShell } from "../_components/SoundsystemShell";
import {
  listConnectors,
  getConnectorSummary,
  previewConnectorSync,
  getConnectorImportAuditSummary,
  InferenceClientError,
} from "../_lib/inference";
import type {
  ConnectorImportAuditSummary,
  ConnectorRegistrySummary,
  ConnectorSyncPreview,
  ProviderConnector,
} from "../_lib/inference-types";

export const dynamic = "force-dynamic";

/** Connector types with mock platform adapters (S52). */
const MOCK_ADAPTER_TYPES = new Set([
  "spotify",
  "tiktok",
  "instagram",
  "soundcloud",
  "shopify",
]);

/**
 * Connectors — Provider Connector Framework dashboard (S51 + S52).
 *
 * Unified adapter registry for all provider boundaries.
 * Health states, capabilities, sync preview with mock adapter events.
 * No real API calls. Contract layer only.
 */
export default async function ConnectorsPage() {
  let connectors: ProviderConnector[] = [];
  let summary: ConnectorRegistrySummary | null = null;
  let auditSummary: ConnectorImportAuditSummary | null = null;
  let unreachable = false;

  try {
    [connectors, summary, auditSummary] = await Promise.all([
      listConnectors(),
      getConnectorSummary(),
      getConnectorImportAuditSummary(),
    ]);
  } catch (error) {
    if (error instanceof InferenceClientError) {
      unreachable = true;
    } else {
      throw error;
    }
  }

  // Fetch previews for mock connectors with S52 adapters
  const previewMap: Record<string, ConnectorSyncPreview> = {};
  if (!unreachable) {
    const mockWithAdapters = connectors.filter(
      (c) => c.status === "mock" && MOCK_ADAPTER_TYPES.has(c.connector_type)
    );
    const previews = await Promise.allSettled(
      mockWithAdapters.map((c) => previewConnectorSync(c.connector_type))
    );
    mockWithAdapters.forEach((c, i) => {
      const result = previews[i];
      if (result && result.status === "fulfilled") {
        previewMap[c.connector_type] = result.value;
      }
    });
  }

  const mockConnectors = connectors.filter((c) => c.status === "mock");
  const readyConnectors = connectors.filter((c) => c.status === "ready");
  const disconnectedConnectors = connectors.filter(
    (c) => c.status === "disconnected"
  );
  const blockedConnectors = connectors.filter(
    (c) => c.status === "blocked"
  );

  return (
    <SoundsystemShell title="Connectors." status="ADAPTER REGISTRY">
      <p className="mb-8 max-w-3xl font-mono text-xs uppercase leading-6 tracking-widest text-[color:var(--ss-text-secondary)]">
        Provider connector framework. Unified adapter architecture for all
        provider boundaries. All connectors normalize into AnalyticsEvent.
        No real API calls. Contract layer only.
      </p>

      {unreachable ? (
        <p
          className="mb-8 border border-[color:var(--ss-warning-dim)] px-4 py-3 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
        >
          Inference unreachable. Start uvicorn app.main:app --port 8010 under
          services/soundsystem-inference.
        </p>
      ) : null}

      {/* Summary strip */}
      {summary ? (
        <section className="mb-8 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-3 lg:grid-cols-7">
          <KpiCell label="Total" value={String(summary.total_connectors)} />
          <KpiCell
            label="Enabled"
            value={String(summary.enabled_connectors)}
            color="var(--ss-accent)"
          />
          <KpiCell
            label="Ready"
            value={String(summary.ready_connectors)}
            color="var(--ss-accent)"
          />
          <KpiCell
            label="Mock"
            value={String(summary.mock_connectors)}
            color="var(--ss-text-secondary)"
          />
          <KpiCell
            label="Blocked"
            value={String(summary.blocked_connectors)}
            color="var(--ss-warning)"
          />
          <KpiCell
            label="Capabilities"
            value={String(Object.keys(summary.capability_breakdown).length)}
          />
          <KpiCell
            label="Warnings"
            value={String(summary.warnings.length)}
            color={summary.warnings.length > 0 ? "var(--ss-warning)" : "var(--ss-text-muted)"}
          />
        </section>
      ) : null}

      {/* Empty state */}
      {connectors.length === 0 && !unreachable ? (
        <div
          className="mb-8 border border-[color:var(--ss-border)] px-5 py-6"
          style={{ backgroundColor: "var(--ss-panel)" }}
        >
          <p className="mb-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            NO CONNECTORS REGISTERED
          </p>
          <p className="max-w-xl font-mono text-[0.62rem] leading-5 uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            Provider connector registry is empty. Default connectors are
            seeded on service startup.
          </p>
        </div>
      ) : null}

      {/* Mock connectors — existing boundaries */}
      {mockConnectors.length > 0 ? (
        <section className="mb-8">
          <h2 className="mb-3 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            MOCK ADAPTERS
          </h2>
          <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-2 lg:grid-cols-3">
            {mockConnectors.map((c) => (
              <ConnectorCard
                key={c.connector_type}
                connector={c}
                preview={previewMap[c.connector_type]}
              />
            ))}
          </div>
        </section>
      ) : null}

      {/* Ready connectors */}
      {readyConnectors.length > 0 ? (
        <section className="mb-8">
          <h2 className="mb-3 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)]">
            READY
          </h2>
          <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-2 lg:grid-cols-3">
            {readyConnectors.map((c) => (
              <ConnectorCard key={c.connector_type} connector={c} />
            ))}
          </div>
        </section>
      ) : null}

      {/* Disconnected connectors — future */}
      {disconnectedConnectors.length > 0 ? (
        <section className="mb-8">
          <h2 className="mb-3 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            DISCONNECTED
          </h2>
          <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-2 lg:grid-cols-3">
            {disconnectedConnectors.map((c) => (
              <ConnectorCard key={c.connector_type} connector={c} />
            ))}
          </div>
        </section>
      ) : null}

      {/* Blocked connectors */}
      {blockedConnectors.length > 0 ? (
        <section className="mb-8">
          <h2 className="mb-3 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-warning)]">
            BLOCKED
          </h2>
          <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-2 lg:grid-cols-3">
            {blockedConnectors.map((c) => (
              <ConnectorCard key={c.connector_type} connector={c} />
            ))}
          </div>
        </section>
      ) : null}

      {/* Capability matrix */}
      {summary && Object.keys(summary.capability_breakdown).length > 0 ? (
        <section className="mb-8">
          <h2 className="mb-3 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            CAPABILITY MATRIX
          </h2>
          <div className="flex flex-wrap gap-2">
            {Object.entries(summary.capability_breakdown)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([cap, count]) => (
                <span
                  key={cap}
                  className="border border-[color:var(--ss-border)] px-3 py-1.5 font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-accent)]"
                  style={{ backgroundColor: "var(--ss-panel)" }}
                >
                  {CAPABILITY_LABELS[cap] ?? cap} ({count})
                </span>
              ))}
          </div>
        </section>
      ) : null}

      {/* Import audit (S53) */}
      {auditSummary ? (
        <section className="mb-8">
          <h2 className="mb-3 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            IMPORT AUDIT LOG
          </h2>
          <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-2 lg:grid-cols-4">
            <KpiCell label="Total imports" value={String(auditSummary.total_imports)} />
            <KpiCell
              label="Events imported"
              value={String(auditSummary.total_events_imported)}
              color="var(--ss-accent)"
            />
            <KpiCell
              label="Connectors used"
              value={String(Object.keys(auditSummary.connector_breakdown).length)}
            />
            <KpiCell
              label="Operators"
              value={String(Object.keys(auditSummary.operator_breakdown).length)}
            />
          </div>
          {auditSummary.total_imports > 0 && auditSummary.latest_import_at ? (
            <p className="mt-2 font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              Last import: {new Date(auditSummary.latest_import_at).toISOString().replace("T", " ").slice(0, 19)} UTC
            </p>
          ) : null}
          {auditSummary.total_imports === 0 ? (
            <p className="mt-2 font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              No imports yet. Use import-demo to populate analytics with mock data.
            </p>
          ) : null}
        </section>
      ) : null}

      {/* Read-only notice */}
      <div className="border-t border-[color:var(--ss-border)] pt-4">
        <p className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          Contract layer only. No real provider API calls. No auth flows.
          No ingestion workers. Future adapters plug into this registry and
          normalize into AnalyticsEvent.
        </p>
      </div>
    </SoundsystemShell>
  );
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CONNECTOR_LABELS: Record<string, string> = {
  spotify: "Spotify",
  soundcloud: "SoundCloud",
  tiktok: "TikTok",
  instagram: "Instagram",
  youtube: "YouTube",
  discord: "Discord",
  ditto: "Ditto",
  shopify: "Shopify",
  printful: "Printful",
  tiktok_shop: "TikTok Shop",
  manual: "Manual",
};

const CONNECTOR_COLORS: Record<string, string> = {
  spotify: "#1db954",
  soundcloud: "#ff5500",
  tiktok: "#fe2c55",
  instagram: "#c13584",
  youtube: "#ff0000",
  discord: "#5865f2",
  ditto: "var(--ss-accent)",
  shopify: "#96bf48",
  printful: "#ed5e34",
  tiktok_shop: "#fe2c55",
  manual: "var(--ss-text-secondary)",
};

const STATUS_LABELS: Record<string, string> = {
  disconnected: "DISCONNECTED",
  configured: "CONFIGURED",
  ready: "READY",
  blocked: "BLOCKED",
  mock: "MOCK",
};

const STATUS_COLORS: Record<string, string> = {
  disconnected: "var(--ss-text-muted)",
  configured: "var(--ss-text-secondary)",
  ready: "var(--ss-accent)",
  blocked: "var(--ss-warning)",
  mock: "var(--ss-text-secondary)",
};

const SYNC_MODE_LABELS: Record<string, string> = {
  manual: "MANUAL",
  mock: "MOCK",
  disabled: "DISABLED",
};

const CAPABILITY_LABELS: Record<string, string> = {
  analytics_pull: "Analytics Pull",
  publishing: "Publishing",
  commerce: "Commerce",
  distribution: "Distribution",
  social: "Social",
  streaming: "Streaming",
  merch: "Merch",
  vinyl: "Vinyl",
  campaign_sync: "Campaign Sync",
};

const METRIC_LABELS: Record<string, string> = {
  plays: "Plays",
  streams: "Streams",
  saves: "Saves",
  likes: "Likes",
  reposts: "Reposts",
  comments: "Comments",
  shares: "Shares",
  views: "Views",
  clicks: "Clicks",
  conversions: "Conversions",
  orders: "Orders",
  revenue: "Revenue",
  followers: "Followers",
  engagement_rate: "Engagement",
  cart_adds: "Cart Adds",
};

function formatMetricValue(metric: string, value: number): string {
  if (metric === "revenue") return `$${value.toLocaleString()}`;
  if (metric === "engagement_rate") return `${value}%`;
  if (metric === "conversions") return `${value}%`;
  return value.toLocaleString();
}

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function KpiCell({
  label,
  value,
  color,
}: Readonly<{ label: string; value: string; color?: string }>) {
  return (
    <div
      className="flex flex-col gap-2 p-4"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </span>
      <span
        className="text-2xl font-black uppercase leading-none"
        style={{ color: color ?? "var(--ss-text-primary)" }}
      >
        {value}
      </span>
    </div>
  );
}

function ConnectorCard({
  connector,
  preview,
}: Readonly<{
  connector: ProviderConnector;
  preview?: ConnectorSyncPreview;
}>) {
  const brandColor =
    CONNECTOR_COLORS[connector.connector_type] ?? "var(--ss-text-muted)";
  const statusColor =
    STATUS_COLORS[connector.status] ?? "var(--ss-text-muted)";
  const hasMockAdapter = MOCK_ADAPTER_TYPES.has(connector.connector_type);

  return (
    <div
      className="flex flex-col gap-3 p-4"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <span
          className="font-mono text-[0.7rem] font-black uppercase tracking-widest"
          style={{ color: brandColor }}
        >
          {CONNECTOR_LABELS[connector.connector_type] ??
            connector.connector_type}
        </span>
        <StatusBadge status={connector.status} />
      </div>

      {/* Mock adapter badge */}
      {hasMockAdapter ? (
        <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-accent)]">
          S52 MOCK ADAPTER
        </span>
      ) : null}

      {/* Sync mode */}
      <div className="flex items-center gap-2">
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          SYNC:
        </span>
        <span className="font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
          {SYNC_MODE_LABELS[connector.sync_mode] ?? connector.sync_mode}
        </span>
        {connector.mock_mode ? (
          <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            (MOCK)
          </span>
        ) : null}
      </div>

      {/* Capabilities */}
      {connector.capabilities.length > 0 ? (
        <div className="flex flex-wrap gap-1">
          {connector.capabilities.map((cap) => (
            <span
              key={cap}
              className="border border-[color:var(--ss-border)] px-2 py-0.5 font-mono text-[0.45rem] uppercase tracking-widest"
              style={{
                color:
                  connector.status === "disconnected"
                    ? "var(--ss-text-muted)"
                    : "var(--ss-accent)",
              }}
            >
              {CAPABILITY_LABELS[cap] ?? cap}
            </span>
          ))}
        </div>
      ) : null}

      {/* Preview events (S52) */}
      {preview && preview.event_count > 0 ? (
        <div className="border-t border-[color:var(--ss-border)] pt-2">
          <span className="mb-1.5 block font-mono text-[0.48rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
            PREVIEW ({preview.event_count} events)
          </span>
          <div className="flex flex-wrap gap-1">
            {preview.normalized_events.map((event, i) => (
              <span
                key={i}
                className="border border-[color:var(--ss-border)] px-2 py-0.5 font-mono text-[0.42rem] uppercase tracking-widest text-[color:var(--ss-accent)]"
              >
                {METRIC_LABELS[event.metric] ?? event.metric}:{" "}
                {formatMetricValue(event.metric, event.value)}
              </span>
            ))}
          </div>
          <p className="mt-1 font-mono text-[0.38rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            Deterministic demo events. No provider API called.
          </p>
        </div>
      ) : null}

      {/* Warnings */}
      {connector.warnings.length > 0 ? (
        <div className="space-y-0.5">
          {connector.warnings.map((w, i) => (
            <p
              key={i}
              className="font-mono text-[0.48rem] uppercase tracking-widest"
              style={{ color: statusColor }}
            >
              {w}
            </p>
          ))}
        </div>
      ) : null}

      {/* Metadata hint */}
      {connector.metadata.boundary_slice ? (
        <span className="font-mono text-[0.42rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          BOUNDARY: {connector.metadata.boundary_slice}
        </span>
      ) : null}
    </div>
  );
}

function StatusBadge({ status }: Readonly<{ status: string }>) {
  const color = STATUS_COLORS[status] ?? "var(--ss-text-muted)";
  const dot =
    status === "ready"
      ? "●"
      : status === "mock"
        ? "○"
        : status === "blocked"
          ? "■"
          : "○";

  return (
    <span
      className="font-mono text-[0.5rem] font-black uppercase tracking-widest"
      style={{ color }}
    >
      {dot} {STATUS_LABELS[status] ?? status}
    </span>
  );
}
