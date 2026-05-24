import Link from "next/link";
import { SoundsystemShell } from "../_components/SoundsystemShell";
import {
  getCampaignSummary,
  listCampaigns,
  InferenceClientError,
} from "../_lib/inference";
import type {
  Campaign,
  CampaignSummary,
} from "../_lib/inference-types";

export const dynamic = "force-dynamic";

/**
 * Campaign Timeline — browse all campaigns across releases (S48).
 *
 * Calendar view only. No automation executed. No scheduling engine.
 * Each campaign links a ReleasePack to operational tasks across channels.
 */
export default async function CampaignsPage() {
  let summary: CampaignSummary | null = null;
  let campaigns: Campaign[] = [];
  let unreachable = false;

  try {
    [summary, campaigns] = await Promise.all([
      getCampaignSummary(),
      listCampaigns(),
    ]);
  } catch (error) {
    if (error instanceof InferenceClientError) {
      unreachable = true;
    } else {
      throw error;
    }
  }

  return (
    <SoundsystemShell title="Campaigns." status="CAMPAIGN TIMELINE">
      <p className="mb-8 max-w-3xl font-mono text-xs uppercase leading-6 tracking-widest text-[color:var(--ss-text-secondary)]">
        Release operations by channel and status. Each campaign orchestrates
        tasks across SoundCloud, Distribution, Merch, TikTok, Instagram,
        and Vinyl. Calendar view only. No automation executed.
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

      {/* Summary grid */}
      {summary ? (
        <section className="mb-10 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-3 lg:grid-cols-5">
          <SummaryCell
            label="Total"
            value={String(summary.total_campaigns)}
          />
          <SummaryCell
            label="Planning"
            value={String(summary.planning)}
          />
          <SummaryCell
            label="Ready"
            value={String(summary.ready)}
            accent={summary.ready > 0}
          />
          <SummaryCell
            label="Active"
            value={String(summary.active)}
            accent={summary.active > 0}
          />
          <SummaryCell
            label="Completed"
            value={String(summary.completed)}
          />
        </section>
      ) : null}

      {/* Task summary bar */}
      {summary && summary.total_tasks > 0 ? (
        <section className="mb-8 flex items-center gap-4 border border-[color:var(--ss-border)] px-4 py-3" style={{ backgroundColor: "var(--ss-panel)" }}>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            TASKS
          </span>
          <span className="font-mono text-[0.7rem] font-black text-[color:var(--ss-text-primary)]">
            {summary.total_tasks}
          </span>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            COMPLETED
          </span>
          <span className="font-mono text-[0.7rem] font-black" style={{ color: "#22c55e" }}>
            {summary.completed_tasks}
          </span>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            BLOCKED
          </span>
          <span className="font-mono text-[0.7rem] font-black" style={{ color: "#f97316" }}>
            {summary.blocked_tasks}
          </span>
          {/* Progress bar */}
          <div className="ml-auto flex h-1.5 w-32 overflow-hidden border border-[color:var(--ss-border)]">
            <div
              className="h-full"
              style={{
                width: `${(summary.completed_tasks / summary.total_tasks) * 100}%`,
                backgroundColor: "#22c55e",
              }}
            />
            <div
              className="h-full"
              style={{
                width: `${(summary.blocked_tasks / summary.total_tasks) * 100}%`,
                backgroundColor: "#f97316",
              }}
            />
          </div>
        </section>
      ) : null}

      {/* Campaign list */}
      <section>
        <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            ALL CAMPAIGNS
          </h2>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {campaigns.length} CAMPAIGNS
          </span>
        </header>

        {campaigns.length === 0 ? (
          <div className="mt-6 grid gap-3">
            <p className="font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              No campaigns yet.
            </p>
            <p className="max-w-xl font-mono text-[0.62rem] leading-5 uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              Create a campaign from a release detail view. Each campaign
              scaffolds operational tasks for a release across all channels.
            </p>
          </div>
        ) : (
          <div className="mt-4 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)]">
            {campaigns.map((campaign) => (
              <CampaignCard key={campaign.campaign_id} campaign={campaign} />
            ))}
          </div>
        )}
      </section>
    </SoundsystemShell>
  );
}

// ---------------------------------------------------------------------------
// Campaign Card
// ---------------------------------------------------------------------------

const CAMPAIGN_STATUS_COLORS: Record<string, string> = {
  planning: "var(--ss-text-muted)",
  ready: "var(--ss-accent)",
  active: "#22c55e",
  completed: "#3b82f6",
  archived: "#6b7280",
};

const CHANNEL_LABELS: Record<string, string> = {
  soundcloud: "SC",
  distribution: "DIST",
  merch: "MERCH",
  tiktok: "TT",
  instagram: "IG",
  discord: "DISC",
};

function CampaignCard({ campaign }: Readonly<{ campaign: Campaign }>) {
  const totalTasks = campaign.tasks.length;
  const completedTasks = campaign.tasks.filter((t) => t.status === "completed").length;
  const blockedTasks = campaign.tasks.filter((t) => t.status === "blocked").length;
  const warningCount = campaign.warnings.length;

  return (
    <Link
      href={`/admin/soundsystem/campaigns/${campaign.campaign_id}`}
      className="grid gap-3 p-5 hover:bg-[color:var(--ss-panel-elevated)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)]"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      {/* Title row */}
      <div className="flex items-center justify-between gap-3">
        <span className="text-lg font-black uppercase leading-none text-[color:var(--ss-text-primary)]">
          {campaign.title}
        </span>
        <span
          className="border px-2 py-0.5 font-mono text-[0.58rem] font-black uppercase tracking-widest"
          style={{
            color: CAMPAIGN_STATUS_COLORS[campaign.status] ?? "var(--ss-text-muted)",
            borderColor: CAMPAIGN_STATUS_COLORS[campaign.status] ?? "var(--ss-text-muted)",
          }}
        >
          {campaign.status}
        </span>
      </div>

      {/* Channel chips + release ID */}
      <div className="flex flex-wrap items-center gap-2">
        {campaign.channels.map((ch) => (
          <span
            key={ch}
            className="border border-[color:var(--ss-border-strong)] px-1.5 py-0.5 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)]"
          >
            {CHANNEL_LABELS[ch] ?? ch}
          </span>
        ))}
        <span className="ml-auto font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          REL {String(campaign.release_id).slice(0, 8)}
        </span>
      </div>

      {/* Bottom row: task counts + warnings + date */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {completedTasks}/{totalTasks} TASKS
          </span>
          {blockedTasks > 0 && (
            <span className="font-mono text-[0.55rem] uppercase tracking-widest" style={{ color: "#f97316" }}>
              {blockedTasks} BLOCKED
            </span>
          )}
          {warningCount > 0 && (
            <span className="font-mono text-[0.55rem] uppercase tracking-widest" style={{ color: "#f59e0b" }}>
              {warningCount} WARN
            </span>
          )}
        </div>
        <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {new Date(campaign.created_at).toISOString().slice(0, 16).replace("T", " ")}
        </span>
      </div>
    </Link>
  );
}

// ---------------------------------------------------------------------------
// Summary cell
// ---------------------------------------------------------------------------

function SummaryCell({
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
