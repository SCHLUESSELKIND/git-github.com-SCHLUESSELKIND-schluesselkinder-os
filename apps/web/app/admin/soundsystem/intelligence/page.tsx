import { SoundsystemShell } from "../_components/SoundsystemShell";
import {
  getAnalyticsSummary,
  getAnalyticsChannels,
  listAnalyticsEvents,
  getIntelligenceOverview,
  getIntelligenceSnapshotSummary,
  listIntelligenceSnapshots,
  getIntelligenceSnapshotDiff,
  InferenceClientError,
} from "../_lib/inference";
import type {
  AnalyticsEvent,
  AnalyticsSummary,
  AudienceHeatmap,
  ChannelPerformance,
  IntelligenceOverview,
  IntelligenceSnapshot,
  IntelligenceSnapshotDiff,
  IntelligenceSnapshotSummary,
  RevenueCorrelation,
  SnapshotPlatformDelta,
  SnapshotViralMomentDelta,
  TimelineCorrelation,
  ViralMoment,
} from "../_lib/inference-types";
import { CreateSnapshotButton } from "./_components/CreateSnapshotButton";

export const dynamic = "force-dynamic";

/**
 * Intelligence — Deep Analytics + Correlation Dashboard (S49 + S50).
 *
 * Unified internal metrics across streaming, social, commerce, and campaigns.
 * Plus: viral moment detection, audience heatmaps, revenue correlations,
 * and timeline fusion. All deterministic. No ML. No AI inference.
 * No provider API calls. Internal normalized event graph only.
 */
export default async function IntelligencePage() {
  let summary: AnalyticsSummary | null = null;
  let channels: ChannelPerformance[] = [];
  let recentEvents: AnalyticsEvent[] = [];
  let overview: IntelligenceOverview | null = null;
  let snapshotSummary: IntelligenceSnapshotSummary | null = null;
  let recentSnapshots: IntelligenceSnapshot[] = [];
  let snapshotDiff: IntelligenceSnapshotDiff | null = null;
  let unreachable = false;

  try {
    [summary, channels, recentEvents, overview, snapshotSummary, recentSnapshots] =
      await Promise.all([
        getAnalyticsSummary(),
        getAnalyticsChannels(),
        listAnalyticsEvents({ limit: 20 }),
        getIntelligenceOverview(),
        getIntelligenceSnapshotSummary(),
        listIntelligenceSnapshots(),
      ]);

    // Auto-diff: compare latest two snapshots if available
    if (recentSnapshots.length >= 2) {
      const sorted = [...recentSnapshots].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      try {
        snapshotDiff = await getIntelligenceSnapshotDiff(
          sorted[1].snapshot_id,
          sorted[0].snapshot_id
        );
      } catch {
        // Diff fetch failed — non-critical, continue without it
      }
    }
  } catch (error) {
    if (error instanceof InferenceClientError) {
      unreachable = true;
    } else {
      throw error;
    }
  }

  return (
    <SoundsystemShell title="Intelligence." status="CORRELATION ENGINE">
      <p className="mb-8 max-w-3xl font-mono text-xs uppercase leading-6 tracking-widest text-[color:var(--ss-text-secondary)]">
        Deep analytics correlation layer. Viral moment detection, audience
        heatmaps, revenue correlations, timeline fusion. All deterministic.
        No ML. No AI. No provider API calls.
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

      {/* Warnings */}
      {overview && overview.warnings.length > 0 ? (
        <div className="mb-6 space-y-1">
          {overview.warnings.map((w, i) => (
            <p
              key={i}
              className="font-mono text-[0.6rem] uppercase tracking-widest"
              style={{ color: "var(--ss-warning)" }}
            >
              {w}
            </p>
          ))}
        </div>
      ) : null}

      {/* KPI strip — merged from summary + overview */}
      {summary ? (
        <section className="mb-8 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-3 lg:grid-cols-6">
          <KpiCell label="Events" value={String(summary.total_events)} />
          <KpiCell
            label="Total Heat"
            value={overview ? String(overview.total_heat) : "—"}
            accent={overview != null && overview.total_heat > 0}
          />
          <KpiCell
            label="Hottest"
            value={
              overview?.hottest_platform
                ? (SOURCE_LABELS[overview.hottest_platform] ?? overview.hottest_platform)
                : "—"
            }
            accent={overview?.hottest_platform != null}
          />
          <KpiCell
            label="Trend"
            value={overview ? TREND_LABELS[overview.trend] ?? overview.trend : "—"}
            accent={overview != null && (overview.trend === "rising" || overview.trend === "exploding")}
          />
          <KpiCell
            label="Viral Spikes"
            value={overview ? String(overview.viral_moments.length) : "0"}
            accent={overview != null && overview.viral_moments.length > 0}
          />
          <KpiCell
            label="Campaigns"
            value={String(summary.total_campaigns)}
          />
        </section>
      ) : null}

      {/* Empty state */}
      {summary && summary.total_events === 0 ? (
        <div className="mb-8 border border-[color:var(--ss-border)] px-5 py-6" style={{ backgroundColor: "var(--ss-panel)" }}>
          <p className="mb-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            NO EVENTS YET
          </p>
          <p className="max-w-xl font-mono text-[0.62rem] leading-5 uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            Seed demo data via POST /v1/analytics/demo-seed or record events
            via POST /v1/analytics/events. Intelligence correlations activate
            automatically once events are present.
          </p>
        </div>
      ) : null}

      {/* Viral Moments */}
      {overview && overview.viral_moments.length > 0 ? (
        <section className="mb-8">
          <h2 className="mb-3 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            VIRAL MOMENTS
          </h2>
          <div className="space-y-px border border-[color:var(--ss-border)]">
            {overview.viral_moments.map((moment) => (
              <ViralMomentCard key={moment.moment_id} moment={moment} />
            ))}
          </div>
        </section>
      ) : null}

      {/* Audience Heatmap */}
      {overview && overview.audience_heatmaps.length > 0 ? (
        <section className="mb-8">
          <h2 className="mb-3 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            PLATFORM HEATMAP
          </h2>
          <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-2 lg:grid-cols-3">
            {overview.audience_heatmaps.map((hm) => (
              <HeatmapCard key={hm.platform} heatmap={hm} />
            ))}
          </div>
        </section>
      ) : null}

      {/* Revenue Correlations */}
      {overview && overview.revenue_correlations.length > 0 ? (
        <section className="mb-8">
          <h2 className="mb-3 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            REVENUE CORRELATIONS
          </h2>
          <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-2 lg:grid-cols-3">
            {overview.revenue_correlations.map((rc) => (
              <RevenueCard key={rc.source} correlation={rc} />
            ))}
          </div>
        </section>
      ) : null}

      {/* Timeline Fusion */}
      {overview && overview.timeline.length > 0 ? (
        <section className="mb-8">
          <header className="mb-3 flex items-center justify-between">
            <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
              TIMELINE FUSION
            </h2>
            <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              {overview.timeline.length} DAYS
            </span>
          </header>
          <div className="space-y-px border border-[color:var(--ss-border)]">
            {overview.timeline.map((point) => (
              <TimelineRow key={point.timestamp} point={point} />
            ))}
          </div>
        </section>
      ) : null}

      {/* Source breakdown */}
      {channels.length > 0 ? (
        <section className="mb-8">
          <h2 className="mb-3 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            SOURCE BREAKDOWN
          </h2>
          <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-2 lg:grid-cols-3">
            {channels.map((ch) => (
              <SourceCard key={ch.source} channel={ch} />
            ))}
          </div>
        </section>
      ) : null}

      {/* Metric breakdown */}
      {summary && Object.keys(summary.metric_breakdown).length > 0 ? (
        <section className="mb-8">
          <h2 className="mb-3 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            METRIC BREAKDOWN
          </h2>
          <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-3 lg:grid-cols-4">
            {Object.entries(summary.metric_breakdown)
              .sort(([, a], [, b]) => b - a)
              .map(([metric, count]) => (
                <MetricCell key={metric} metric={metric} count={count} />
              ))}
          </div>
        </section>
      ) : null}

      {/* Event feed */}
      {recentEvents.length > 0 ? (
        <section className="mb-8">
          <header className="mb-3 flex items-center justify-between">
            <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
              EVENT FEED
            </h2>
            <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              LAST {recentEvents.length} EVENTS
            </span>
          </header>
          <div className="space-y-px border border-[color:var(--ss-border)]">
            {recentEvents.map((event) => (
              <EventRow key={event.event_id} event={event} />
            ))}
          </div>
        </section>
      ) : null}

      {/* Intelligence Snapshots (S54) */}
      {!unreachable ? (
        <section className="mb-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
              SNAPSHOTS
            </h2>
            <CreateSnapshotButton />
          </div>

          {/* Snapshot summary strip */}
          {snapshotSummary ? (
            <div className="mb-4 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-3 lg:grid-cols-6">
              <KpiCell label="Total" value={String(snapshotSummary.total_snapshots)} />
              <KpiCell
                label="Active"
                value={String(snapshotSummary.active_snapshots)}
                accent={snapshotSummary.active_snapshots > 0}
              />
              <KpiCell
                label="Archived"
                value={String(snapshotSummary.archived_snapshots)}
              />
              <KpiCell
                label="Latest Heat"
                value={String(snapshotSummary.latest_total_heat)}
                accent={snapshotSummary.latest_total_heat > 0}
              />
              <KpiCell
                label="Heat Delta"
                value={
                  snapshotSummary.heat_delta_from_previous != null
                    ? `${snapshotSummary.heat_delta_from_previous > 0 ? "+" : ""}${snapshotSummary.heat_delta_from_previous}`
                    : "—"
                }
                accent={snapshotSummary.heat_delta_from_previous != null && snapshotSummary.heat_delta_from_previous > 0}
              />
              <KpiCell
                label="Latest At"
                value={
                  snapshotSummary.latest_snapshot_at
                    ? new Date(snapshotSummary.latest_snapshot_at).toISOString().slice(0, 10)
                    : "—"
                }
              />
            </div>
          ) : null}

          {/* Recent snapshots list */}
          {recentSnapshots.length > 0 ? (
            <div className="space-y-px border border-[color:var(--ss-border)]">
              {recentSnapshots.slice(0, 10).map((snap) => (
                <SnapshotRow key={snap.snapshot_id} snapshot={snap} />
              ))}
            </div>
          ) : (
            <p className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              No snapshots yet. Create one to freeze the current intelligence state.
            </p>
          )}
        </section>
      ) : null}

      {/* Snapshot Diff (S55) */}
      {snapshotDiff ? (
        <section className="mb-8">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
              SNAPSHOT DIFF
            </h2>
            <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              {new Date(snapshotDiff.before_created_at).toISOString().slice(0, 10)} → {new Date(snapshotDiff.after_created_at).toISOString().slice(0, 10)}
            </span>
          </div>

          {/* Diff KPI strip */}
          <div className="mb-4 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-3 lg:grid-cols-5">
            <KpiCell
              label="Direction"
              value={DIRECTION_LABELS[snapshotDiff.overall_direction] ?? snapshotDiff.overall_direction}
              accent={snapshotDiff.overall_direction === "improved"}
            />
            <KpiCell
              label="Heat Delta"
              value={`${snapshotDiff.total_heat_delta > 0 ? "+" : ""}${snapshotDiff.total_heat_delta}`}
              accent={snapshotDiff.total_heat_delta > 0}
            />
            <KpiCell
              label="Heat %"
              value={snapshotDiff.total_heat_delta_percent != null ? `${snapshotDiff.total_heat_delta_percent > 0 ? "+" : ""}${snapshotDiff.total_heat_delta_percent}%` : "—"}
              accent={snapshotDiff.total_heat_delta_percent != null && snapshotDiff.total_heat_delta_percent > 0}
            />
            <KpiCell
              label="Platforms"
              value={String(snapshotDiff.platform_deltas.length)}
            />
            <KpiCell
              label="Viral Changes"
              value={String(snapshotDiff.viral_moment_deltas.length)}
            />
          </div>

          {/* Platform deltas */}
          {snapshotDiff.platform_deltas.length > 0 ? (
            <div className="mb-4">
              <h3 className="mb-2 font-mono text-[0.6rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
                PLATFORM DELTAS
              </h3>
              <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-2 lg:grid-cols-3">
                {snapshotDiff.platform_deltas.map((pd) => (
                  <PlatformDeltaCard key={pd.platform} delta={pd} />
                ))}
              </div>
            </div>
          ) : null}

          {/* Viral moment deltas */}
          {snapshotDiff.viral_moment_deltas.length > 0 ? (
            <div className="mb-4">
              <h3 className="mb-2 font-mono text-[0.6rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
                VIRAL MOMENT CHANGES
              </h3>
              <div className="space-y-px border border-[color:var(--ss-border)]">
                {snapshotDiff.viral_moment_deltas.map((vmd) => (
                  <ViralMomentDeltaRow key={vmd.title} delta={vmd} />
                ))}
              </div>
            </div>
          ) : null}

          {/* Revenue delta */}
          {snapshotDiff.revenue_delta ? (
            <div className="mb-4">
              <h3 className="mb-2 font-mono text-[0.6rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
                REVENUE DELTA
              </h3>
              <div className="flex items-center gap-4 border border-[color:var(--ss-border)] px-4 py-3" style={{ backgroundColor: "var(--ss-panel)" }}>
                <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                  {formatCurrency(snapshotDiff.revenue_delta.before_value)} → {formatCurrency(snapshotDiff.revenue_delta.after_value)}
                </span>
                <span
                  className="font-mono text-[0.7rem] font-black"
                  style={{ color: directionColor(snapshotDiff.revenue_delta.direction) }}
                >
                  {snapshotDiff.revenue_delta.delta > 0 ? "+" : ""}{formatCurrency(snapshotDiff.revenue_delta.delta)}
                </span>
                {snapshotDiff.revenue_delta.delta_percent != null ? (
                  <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                    ({snapshotDiff.revenue_delta.delta_percent > 0 ? "+" : ""}{snapshotDiff.revenue_delta.delta_percent}%)
                  </span>
                ) : null}
              </div>
            </div>
          ) : null}

          {/* Warning changes */}
          {snapshotDiff.warning_changes.length > 0 ? (
            <div className="mb-4">
              <h3 className="mb-2 font-mono text-[0.6rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
                WARNING CHANGES
              </h3>
              <div className="space-y-px border border-[color:var(--ss-border)]">
                {snapshotDiff.warning_changes.map((wc, i) => (
                  <div
                    key={i}
                    className="px-4 py-2"
                    style={{ backgroundColor: "var(--ss-panel)" }}
                  >
                    <span
                      className="font-mono text-[0.55rem] uppercase tracking-widest"
                      style={{ color: wc.startsWith("+") ? "var(--ss-warning)" : "var(--ss-text-muted)" }}
                    >
                      {wc}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {/* Read-only notice */}
      <div className="border-t border-[color:var(--ss-border)] pt-4">
        <p className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          Deterministic correlation engine. No ML. No AI inference. No
          provider API calls. Internal read-model only. Future adapters will
          normalize into AnalyticsEvent.
        </p>
      </div>
    </SoundsystemShell>
  );
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SOURCE_LABELS: Record<string, string> = {
  soundcloud: "SoundCloud",
  spotify: "Spotify",
  tiktok: "TikTok",
  instagram: "Instagram",
  youtube: "YouTube",
  discord: "Discord",
  shopify: "Shopify",
  printful: "Printful",
  tiktok_shop: "TikTok Shop",
  ditto: "Ditto",
  campaign: "Campaign",
  manual: "Manual",
};

const SOURCE_COLORS: Record<string, string> = {
  soundcloud: "#ff5500",
  spotify: "#1db954",
  tiktok: "#fe2c55",
  instagram: "#c13584",
  youtube: "#ff0000",
  discord: "#5865f2",
  shopify: "#96bf48",
  printful: "#ed5e34",
  tiktok_shop: "#fe2c55",
  ditto: "var(--ss-accent)",
  campaign: "var(--ss-text-secondary)",
  manual: "var(--ss-text-muted)",
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
  engagement_rate: "Eng. Rate",
  watch_time: "Watch Time",
  cart_adds: "Cart Adds",
  vinyl_interest: "Vinyl Int.",
  merch_interest: "Merch Int.",
  campaign_heat: "Heat",
};

const TREND_LABELS: Record<string, string> = {
  down: "DOWN",
  stable: "STABLE",
  rising: "RISING",
  exploding: "EXPLODING",
};

const TREND_COLORS: Record<string, string> = {
  down: "var(--ss-warning)",
  stable: "var(--ss-text-muted)",
  rising: "var(--ss-accent)",
  exploding: "#f59e0b",
};

const STRENGTH_LABELS: Record<string, string> = {
  weak: "WEAK",
  medium: "MED",
  strong: "STRONG",
  explosive: "EXPLOSIVE",
};

const STRENGTH_COLORS: Record<string, string> = {
  weak: "var(--ss-text-muted)",
  medium: "var(--ss-text-secondary)",
  strong: "var(--ss-accent)",
  explosive: "#f59e0b",
};

const DIRECTION_LABELS: Record<string, string> = {
  improved: "IMPROVED",
  declined: "DECLINED",
  unchanged: "UNCHANGED",
  mixed: "MIXED",
};

const DIRECTION_COLORS: Record<string, string> = {
  improved: "var(--ss-accent)",
  declined: "var(--ss-warning)",
  unchanged: "var(--ss-text-muted)",
  mixed: "#f59e0b",
};

function directionColor(direction: string): string {
  return DIRECTION_COLORS[direction] ?? "var(--ss-text-muted)";
}

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function KpiCell({
  label,
  value,
  accent = false,
}: Readonly<{ label: string; value: string; accent?: boolean }>) {
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
        style={{
          color: accent ? "var(--ss-accent)" : "var(--ss-text-primary)",
        }}
      >
        {value}
      </span>
    </div>
  );
}

function ViralMomentCard({ moment }: Readonly<{ moment: ViralMoment }>) {
  const sourceColor = SOURCE_COLORS[moment.source] ?? "var(--ss-text-muted)";
  const strengthColor = STRENGTH_COLORS[moment.strength] ?? "var(--ss-text-muted)";
  return (
    <div
      className="flex items-center justify-between px-4 py-3"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex items-center gap-3">
        <span
          className="w-16 shrink-0 font-mono text-[0.5rem] font-black uppercase tracking-widest"
          style={{ color: sourceColor }}
        >
          {(SOURCE_LABELS[moment.source] ?? moment.source).slice(0, 8)}
        </span>
        <span className="font-mono text-[0.58rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
          {METRIC_LABELS[moment.trigger_metric] ?? moment.trigger_metric}
        </span>
        <span className="font-mono text-[0.7rem] font-black text-[color:var(--ss-accent)]">
          +{moment.growth_percent}%
        </span>
      </div>
      <div className="flex items-center gap-3">
        <span
          className="font-mono text-[0.5rem] font-black uppercase tracking-widest"
          style={{ color: strengthColor }}
        >
          {STRENGTH_LABELS[moment.strength] ?? moment.strength}
        </span>
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {formatValue(moment.before_value)} &rarr; {formatValue(moment.after_value)}
        </span>
        <span className="font-mono text-[0.48rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {new Date(moment.timestamp).toISOString().slice(0, 10)}
        </span>
      </div>
    </div>
  );
}

function HeatmapCard({ heatmap }: Readonly<{ heatmap: AudienceHeatmap }>) {
  const color = SOURCE_COLORS[heatmap.platform] ?? "var(--ss-text-muted)";
  const trendColor = TREND_COLORS[heatmap.trend] ?? "var(--ss-text-muted)";
  return (
    <div
      className="flex flex-col gap-2 p-4"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex items-center justify-between">
        <span
          className="font-mono text-[0.65rem] font-black uppercase tracking-widest"
          style={{ color }}
        >
          {SOURCE_LABELS[heatmap.platform] ?? heatmap.platform}
        </span>
        <TrendBadge trend={heatmap.trend} />
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-xl font-black leading-none text-[color:var(--ss-text-primary)]">
          {heatmap.heat_score}
        </span>
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          HEAT
        </span>
      </div>
      {/* Heat bar */}
      <div className="h-1 w-full rounded-full" style={{ backgroundColor: "var(--ss-border)" }}>
        <div
          className="h-1 rounded-full"
          style={{
            width: `${Math.min(heatmap.heat_score, 100)}%`,
            backgroundColor: color,
          }}
        />
      </div>
      <div className="flex gap-4">
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          AUD {formatValue(heatmap.audience_size)}
        </span>
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          ENG {formatValue(heatmap.engagement)}
        </span>
        {heatmap.conversion_rate > 0 && (
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            CVR {heatmap.conversion_rate}%
          </span>
        )}
      </div>
    </div>
  );
}

function RevenueCard({ correlation }: Readonly<{ correlation: RevenueCorrelation }>) {
  const color = SOURCE_COLORS[correlation.source] ?? "var(--ss-text-muted)";
  const strengthColor = STRENGTH_COLORS[correlation.conversion_strength] ?? "var(--ss-text-muted)";
  return (
    <div
      className="flex flex-col gap-2 p-4"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex items-center justify-between">
        <span
          className="font-mono text-[0.65rem] font-black uppercase tracking-widest"
          style={{ color }}
        >
          {SOURCE_LABELS[correlation.source] ?? correlation.source}
        </span>
        <span
          className="font-mono text-[0.5rem] font-black uppercase tracking-widest"
          style={{ color: strengthColor }}
        >
          {STRENGTH_LABELS[correlation.conversion_strength] ?? correlation.conversion_strength}
        </span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-xl font-black leading-none text-[color:var(--ss-text-primary)]">
          {formatCurrency(correlation.revenue)}
        </span>
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          REVENUE
        </span>
      </div>
      {correlation.related_metric && (
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          CORRELATED: {METRIC_LABELS[correlation.related_metric] ?? correlation.related_metric}{" "}
          ({formatValue(correlation.related_metric_value)})
        </span>
      )}
    </div>
  );
}

function TimelineRow({ point }: Readonly<{ point: TimelineCorrelation }>) {
  const sourceColor = point.dominant_source
    ? (SOURCE_COLORS[point.dominant_source] ?? "var(--ss-text-muted)")
    : "var(--ss-text-muted)";
  return (
    <div
      className="flex items-center justify-between px-4 py-2.5"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex items-center gap-3">
        <span className="w-20 shrink-0 font-mono text-[0.55rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          {new Date(point.timestamp).toISOString().slice(0, 10)}
        </span>
        {point.dominant_source && (
          <span
            className="font-mono text-[0.5rem] font-black uppercase tracking-widest"
            style={{ color: sourceColor }}
          >
            {(SOURCE_LABELS[point.dominant_source] ?? point.dominant_source).slice(0, 8)}
          </span>
        )}
        {point.dominant_metric && (
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
            {METRIC_LABELS[point.dominant_metric] ?? point.dominant_metric}
          </span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <HeatBadge heat={point.heat} />
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {point.event_count} EVENTS
        </span>
      </div>
    </div>
  );
}

function TrendBadge({ trend }: Readonly<{ trend: string }>) {
  const color = TREND_COLORS[trend] ?? "var(--ss-text-muted)";
  const arrow = trend === "exploding" ? "▲▲" : trend === "rising" ? "▲" : trend === "down" ? "▼" : "●";
  return (
    <span
      className="font-mono text-[0.5rem] font-black uppercase tracking-widest"
      style={{ color }}
    >
      {arrow} {TREND_LABELS[trend] ?? trend}
    </span>
  );
}

function HeatBadge({ heat }: Readonly<{ heat: number }>) {
  const color = heat >= 60 ? "#f59e0b" : heat >= 30 ? "var(--ss-accent)" : "var(--ss-text-muted)";
  return (
    <span
      className="font-mono text-[0.55rem] font-black uppercase tracking-widest"
      style={{ color }}
    >
      {heat}
    </span>
  );
}

function SourceCard({
  channel,
}: Readonly<{ channel: ChannelPerformance }>) {
  const color = SOURCE_COLORS[channel.source] ?? "var(--ss-text-muted)";
  return (
    <div
      className="flex flex-col gap-2 p-4"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex items-center justify-between">
        <span
          className="font-mono text-[0.65rem] font-black uppercase tracking-widest"
          style={{ color }}
        >
          {SOURCE_LABELS[channel.source] ?? channel.source}
        </span>
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {channel.total_events} EVENTS
        </span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-xl font-black leading-none text-[color:var(--ss-text-primary)]">
          {formatValue(channel.total_value)}
        </span>
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          TOTAL
        </span>
      </div>
      {channel.top_metric && (
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          TOP: {METRIC_LABELS[channel.top_metric] ?? channel.top_metric}{" "}
          ({formatValue(channel.top_metric_value)})
        </span>
      )}
    </div>
  );
}

function MetricCell({
  metric,
  count,
}: Readonly<{ metric: string; count: number }>) {
  return (
    <div
      className="flex items-center justify-between p-3"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
        {METRIC_LABELS[metric] ?? metric}
      </span>
      <span className="font-mono text-[0.7rem] font-black text-[color:var(--ss-text-primary)]">
        {count}
      </span>
    </div>
  );
}

function EventRow({ event }: Readonly<{ event: AnalyticsEvent }>) {
  const sourceColor = SOURCE_COLORS[event.source] ?? "var(--ss-text-muted)";
  return (
    <div
      className="flex items-center justify-between px-4 py-2.5"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex items-center gap-3">
        <span
          className="w-16 shrink-0 font-mono text-[0.5rem] font-black uppercase tracking-widest"
          style={{ color: sourceColor }}
        >
          {(SOURCE_LABELS[event.source] ?? event.source).slice(0, 8)}
        </span>
        <span className="font-mono text-[0.58rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
          {METRIC_LABELS[event.metric] ?? event.metric}
        </span>
        <span className="font-mono text-[0.62rem] font-black text-[color:var(--ss-text-primary)]">
          {formatValue(event.value)}
        </span>
      </div>
      <div className="flex items-center gap-3">
        {event.campaign_id && (
          <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            CAMP {String(event.campaign_id).slice(0, 6)}
          </span>
        )}
        {event.track_id && (
          <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            TRK {String(event.track_id).slice(0, 6)}
          </span>
        )}
        <span className="font-mono text-[0.48rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {new Date(event.timestamp).toISOString().slice(0, 16).replace("T", " ")}
        </span>
      </div>
    </div>
  );
}

function PlatformDeltaCard({ delta }: Readonly<{ delta: SnapshotPlatformDelta }>) {
  const color = SOURCE_COLORS[delta.platform] ?? "var(--ss-text-muted)";
  const dColor = directionColor(delta.direction);
  return (
    <div
      className="flex flex-col gap-2 p-4"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex items-center justify-between">
        <span
          className="font-mono text-[0.65rem] font-black uppercase tracking-widest"
          style={{ color }}
        >
          {SOURCE_LABELS[delta.platform] ?? delta.platform}
        </span>
        <span
          className="font-mono text-[0.5rem] font-black uppercase tracking-widest"
          style={{ color: dColor }}
        >
          {DIRECTION_LABELS[delta.direction] ?? delta.direction}
        </span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {delta.before_heat} → {delta.after_heat}
        </span>
        <span
          className="font-mono text-[0.7rem] font-black"
          style={{ color: dColor }}
        >
          {delta.heat_delta > 0 ? "+" : ""}{delta.heat_delta}
        </span>
      </div>
      <div className="flex gap-4">
        {delta.engagement_delta !== 0 && (
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            ENG {delta.engagement_delta > 0 ? "+" : ""}{delta.engagement_delta}
          </span>
        )}
        {delta.conversion_delta !== 0 && (
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            CVR {delta.conversion_delta > 0 ? "+" : ""}{delta.conversion_delta}
          </span>
        )}
      </div>
    </div>
  );
}

function ViralMomentDeltaRow({ delta }: Readonly<{ delta: SnapshotViralMomentDelta }>) {
  const dColor = directionColor(delta.direction);
  return (
    <div
      className="flex items-center justify-between px-4 py-3"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex items-center gap-3">
        <span className="font-mono text-[0.58rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
          {delta.title}
        </span>
        {delta.appeared && (
          <span className="font-mono text-[0.5rem] font-black uppercase tracking-widest" style={{ color: "var(--ss-accent)" }}>
            NEW
          </span>
        )}
        {delta.disappeared && (
          <span className="font-mono text-[0.5rem] font-black uppercase tracking-widest" style={{ color: "var(--ss-warning)" }}>
            GONE
          </span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {delta.before_strength ?? "—"} → {delta.after_strength ?? "—"}
        </span>
        <span
          className="font-mono text-[0.5rem] font-black uppercase tracking-widest"
          style={{ color: dColor }}
        >
          {DIRECTION_LABELS[delta.direction] ?? delta.direction}
        </span>
      </div>
    </div>
  );
}

function formatValue(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  if (value % 1 !== 0) return value.toFixed(2);
  return String(value);
}

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${value.toFixed(2)}`;
}

function SnapshotRow({ snapshot }: Readonly<{ snapshot: IntelligenceSnapshot }>) {
  const statusColor =
    snapshot.status === "created"
      ? "var(--ss-accent)"
      : snapshot.status === "archived"
        ? "var(--ss-text-muted)"
        : "var(--ss-text-secondary)";
  return (
    <div
      className="flex items-center justify-between px-4 py-3"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex items-center gap-3">
        <span
          className="w-20 shrink-0 font-mono text-[0.5rem] font-black uppercase tracking-widest"
          style={{ color: statusColor }}
        >
          {snapshot.status}
        </span>
        <span className="font-mono text-[0.62rem] font-black text-[color:var(--ss-accent)]">
          {snapshot.overview.total_heat}
        </span>
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          HEAT
        </span>
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {snapshot.event_count} EVENTS
        </span>
        {snapshot.notes ? (
          <span className="font-mono text-[0.48rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
            {snapshot.notes}
          </span>
        ) : null}
      </div>
      <div className="flex items-center gap-3">
        {snapshot.created_by ? (
          <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {snapshot.created_by}
          </span>
        ) : null}
        <span className="font-mono text-[0.48rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {new Date(snapshot.created_at).toISOString().slice(0, 16).replace("T", " ")}
        </span>
      </div>
    </div>
  );
}
