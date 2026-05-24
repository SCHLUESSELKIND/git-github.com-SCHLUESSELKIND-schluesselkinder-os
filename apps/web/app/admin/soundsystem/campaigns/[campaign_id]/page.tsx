import Link from "next/link";
import { SoundsystemShell } from "../../_components/SoundsystemShell";
import {
  getCampaign,
  getInferenceCapabilities,
  listAutomationExecutionAuditForCampaign,
  listAutomationExecutionsByCampaign,
  listAutomationRuleTemplates,
  listAutomationRulesByCampaign,
  InferenceClientError,
} from "../../_lib/inference";
import type {
  AutomationExecutionAuditRecord,
  AutomationExecutionJob,
  Campaign,
  CampaignAutomationRule,
  CampaignAutomationRuleTemplate,
  CampaignTask,
} from "../../_lib/inference-types";
import {
  ExecuteMockButton,
  ExecutionStatusChip,
  QueueExecutionButton,
} from "./_components/AutomationExecutionControls";
import { AutomationTemplateLibrary } from "./_components/AutomationTemplateLibrary";

export const dynamic = "force-dynamic";

type Props = {
  params: Promise<{ campaign_id: string }>;
};

/**
 * Campaign Detail — channel lanes, task cards, timeline feed (S48).
 *
 * Calendar view only. No automation executed. No scheduling engine.
 * Read-model surface for release operations across all channels.
 */
export default async function CampaignDetailPage({ params }: Props) {
  const { campaign_id } = await params;
  let campaign: Campaign | null = null;
  let automationRules: CampaignAutomationRule[] = [];
  let automationTemplates: CampaignAutomationRuleTemplate[] = [];
  let executionJobs: AutomationExecutionJob[] = [];
  let auditRecords: AutomationExecutionAuditRecord[] = [];
  let executionMode: "disabled" | "mock" = "disabled";
  let errorMessage: string | null = null;

  try {
    campaign = await getCampaign(campaign_id);
    automationRules = await listAutomationRulesByCampaign(campaign_id);
    automationTemplates = await listAutomationRuleTemplates();
    executionJobs = await listAutomationExecutionsByCampaign(campaign_id);
    auditRecords = await listAutomationExecutionAuditForCampaign(campaign_id);
    const caps = await getInferenceCapabilities();
    executionMode = caps.automation_execution_mode ?? "disabled";
  } catch (error) {
    if (error instanceof InferenceClientError) {
      errorMessage =
        error.status === 404
          ? "Campaign not found."
          : `Inference error: ${error.message}`;
    } else {
      throw error;
    }
  }

  if (errorMessage || !campaign) {
    return (
      <SoundsystemShell title="Not found." status="CAMPAIGN TIMELINE">
        <p
          className="border border-[color:var(--ss-warning-dim)] px-4 py-3 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
        >
          {errorMessage || "Campaign not found."}
        </p>
        <Link
          href="/admin/soundsystem/campaigns"
          className="mt-4 inline-block font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
        >
          &larr; Back to Campaigns
        </Link>
      </SoundsystemShell>
    );
  }

  // Group tasks by channel
  const tasksByChannel: Record<string, CampaignTask[]> = {};
  for (const task of campaign.tasks) {
    const ch = task.channel;
    if (!tasksByChannel[ch]) tasksByChannel[ch] = [];
    tasksByChannel[ch].push(task);
  }

  // Task counts
  const totalTasks = campaign.tasks.length;
  const completedTasks = campaign.tasks.filter((t) => t.status === "completed").length;
  const blockedTasks = campaign.tasks.filter((t) => t.status === "blocked").length;
  const pendingTasks = campaign.tasks.filter((t) => t.status === "pending").length;
  const readyTasks = campaign.tasks.filter((t) => t.status === "ready").length;

  // Channel ordering for lane display
  const channelOrder = [
    "distribution",
    "soundcloud",
    "merch",
    "tiktok",
    "instagram",
    "discord",
  ];
  const orderedChannels = channelOrder.filter((ch) => tasksByChannel[ch]);
  // Add any channels not in predefined order
  for (const ch of Object.keys(tasksByChannel)) {
    if (!orderedChannels.includes(ch)) orderedChannels.push(ch);
  }

  return (
    <SoundsystemShell title={campaign.title} status="CAMPAIGN DETAIL">
      {/* Back link */}
      <Link
        href="/admin/soundsystem/campaigns"
        className="mb-6 inline-block font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
      >
        &larr; Campaigns
      </Link>

      {/* Campaign header */}
      <div
        className="mb-6 border border-[color:var(--ss-border)] px-5 py-4"
        style={{ backgroundColor: "var(--ss-panel-elevated)" }}
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <CampaignStatusChip status={campaign.status} />
            <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              REL {String(campaign.release_id).slice(0, 8)}
            </span>
            {campaign.created_by && (
              <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                by {campaign.created_by}
              </span>
            )}
          </div>
          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {new Date(campaign.created_at).toISOString().slice(0, 16).replace("T", " ")}
          </span>
        </div>

        {/* Channel chips */}
        <div className="mt-3 flex flex-wrap gap-2">
          {campaign.channels.map((ch) => (
            <span
              key={ch}
              className="border border-[color:var(--ss-border-strong)] px-2 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)]"
            >
              {CHANNEL_LABELS_FULL[ch] ?? ch}
            </span>
          ))}
        </div>

        {/* Notes */}
        {campaign.notes && (
          <p className="mt-3 font-mono text-[0.6rem] leading-5 text-[color:var(--ss-text-secondary)]">
            {campaign.notes}
          </p>
        )}
      </div>

      {/* Task summary bar */}
      <div className="mb-6 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] grid-cols-2 md:grid-cols-5">
        <TaskCountCell label="Total" count={totalTasks} />
        <TaskCountCell label="Completed" count={completedTasks} color="#22c55e" />
        <TaskCountCell label="Pending" count={pendingTasks} />
        <TaskCountCell label="Ready" count={readyTasks} color="var(--ss-accent)" />
        <TaskCountCell label="Blocked" count={blockedTasks} color="#f97316" />
      </div>

      {/* Warnings */}
      {campaign.warnings.length > 0 && (
        <div className="mb-6 space-y-1">
          <h3 className="mb-2 font-mono text-[0.6rem] font-black uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            WARNINGS
          </h3>
          {campaign.warnings.map((w, i) => (
            <div
              key={i}
              className="border-l-2 border-orange-500 bg-orange-500/5 px-3 py-2 font-mono text-[0.6rem] text-orange-400"
            >
              <span className="font-black uppercase">{w.code}</span>{" "}
              {w.message}
            </div>
          ))}
        </div>
      )}

      {/* Channel lanes */}
      <div className="mb-8">
        <h3 className="mb-4 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          CHANNEL LANES
        </h3>
        <div className="grid gap-6">
          {orderedChannels.map((channel) => (
            <ChannelLane
              key={channel}
              channel={channel}
              tasks={tasksByChannel[channel]}
            />
          ))}
        </div>
      </div>

      {/* Timeline feed */}
      {campaign.timeline.length > 0 && (
        <div className="mb-8">
          <h3 className="mb-4 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            TIMELINE
          </h3>
          <div className="space-y-0">
            {campaign.timeline.map((item, i) => (
              <div
                key={i}
                className="flex items-start gap-4 border-l-2 border-[color:var(--ss-border)] py-3 pl-4"
              >
                <div className="flex flex-col gap-1">
                  <div className="flex items-baseline gap-3">
                    <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                      {new Date(item.timestamp).toISOString().slice(0, 16).replace("T", " ")}
                    </span>
                    <span className="font-mono text-[0.65rem] font-bold text-[color:var(--ss-text-primary)]">
                      {item.event}
                    </span>
                  </div>
                  {item.notes && (
                    <span className="font-mono text-[0.55rem] text-[color:var(--ss-text-muted)]">
                      {item.notes}
                    </span>
                  )}
                  {item.object_id && (
                    <span className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
                      {item.object_type} {String(item.object_id).slice(0, 8)}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Automation Rules (S57) + Execution Queue (S58) */}
      <div className="mb-8">
        <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            AUTOMATION RULES
          </h3>
          <span
            className="font-mono text-[0.5rem] uppercase tracking-widest"
            style={{
              color:
                executionMode === "mock"
                  ? "var(--ss-accent)"
                  : "#f97316",
            }}
          >
            EXECUTION MODE: {executionMode}
          </span>
        </div>
        {executionMode === "disabled" && (
          <p className="mb-3 border-l-2 border-orange-500 bg-orange-500/5 px-3 py-2 font-mono text-[0.55rem] uppercase tracking-widest text-orange-400">
            Execution disabled. Dry-run only. Set
            SOUNDSYSTEM_AUTOMATION_EXECUTION_MODE=mock to enable mock execution.
          </p>
        )}
        {automationRules.length === 0 ? (
          <div
            className="border border-dashed border-[color:var(--ss-border)] px-5 py-6 text-center"
            style={{ backgroundColor: "var(--ss-panel)" }}
          >
            <p className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              No automation rules defined for this campaign.
            </p>
            <p className="mt-2 font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              Dry run only. No automation executed.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {automationRules.map((rule) => (
              <AutomationRuleCard key={rule.rule_id} rule={rule} />
            ))}
            <p className="mt-3 font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              Dry run only. No automation executed.
            </p>
          </div>
        )}

        {/* Template library (S60) */}
        <h4 className="mb-2 mt-6 font-mono text-[0.65rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          RULE TEMPLATES
        </h4>
        {automationTemplates.length === 0 ? (
          <p className="border border-dashed border-[color:var(--ss-border)] px-4 py-3 font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            No automation rule templates available.
          </p>
        ) : (
          <AutomationTemplateLibrary
            campaignId={campaign_id}
            templates={automationTemplates}
          />
        )}
        <p className="mt-3 font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          Templates create rule definitions only. No automation is executed.
        </p>

        {/* Execution jobs */}
        <h4 className="mb-2 mt-6 font-mono text-[0.65rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          EXECUTION QUEUE
        </h4>
        {executionJobs.length === 0 ? (
          <p className="border border-dashed border-[color:var(--ss-border)] px-4 py-3 font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            No execution jobs queued for this campaign.
          </p>
        ) : (
          <div className="space-y-1">
            {executionJobs.map((job) => (
              <AutomationExecutionCard key={job.execution_id} job={job} />
            ))}
          </div>
        )}
        <p className="mt-3 font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          Mock execution records intent only. No campaign or provider state is
          changed.
        </p>

        {/* Audit log (S59) */}
        <h4 className="mb-2 mt-6 font-mono text-[0.65rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          AUDIT LOG
        </h4>
        {auditRecords.length === 0 ? (
          <p className="border border-dashed border-[color:var(--ss-border)] px-4 py-3 font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            No audit records for this campaign.
          </p>
        ) : (
          <div className="space-y-1">
            {auditRecords.map((record) => (
              <AutomationAuditRow key={record.audit_id} record={record} />
            ))}
          </div>
        )}
        <p className="mt-3 font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          Audit log is immutable. It records intent and mock transitions only.
        </p>
      </div>

      {/* Read-only notice */}
      <div className="border-t border-[color:var(--ss-border)] pt-4">
        <p className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          Calendar view only. No automation executed.
        </p>
        <Link
          href={`/admin/soundsystem/releases/${campaign.release_id}`}
          className="mt-2 inline-block font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
        >
          &larr; Release detail (manage campaign)
        </Link>
      </div>
    </SoundsystemShell>
  );
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CHANNEL_LABELS_FULL: Record<string, string> = {
  soundcloud: "SoundCloud",
  distribution: "Distribution",
  merch: "Merch",
  tiktok: "TikTok",
  instagram: "Instagram",
  discord: "Discord",
};

const CHANNEL_ICONS: Record<string, string> = {
  soundcloud: "SC",
  distribution: "DIST",
  merch: "MERCH",
  tiktok: "TT",
  instagram: "IG",
  discord: "DISC",
};

const TASK_STATUS_COLORS: Record<string, string> = {
  pending: "var(--ss-text-muted)",
  ready: "var(--ss-accent)",
  blocked: "#f97316",
  completed: "#22c55e",
};

const CAMPAIGN_STATUS_COLORS: Record<string, string> = {
  planning: "var(--ss-text-muted)",
  ready: "var(--ss-accent)",
  active: "#22c55e",
  completed: "#3b82f6",
  archived: "#6b7280",
};

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function CampaignStatusChip({ status }: Readonly<{ status: string }>) {
  return (
    <span
      className="border px-2 py-0.5 font-mono text-[0.58rem] font-black uppercase tracking-widest"
      style={{
        color: CAMPAIGN_STATUS_COLORS[status] ?? "var(--ss-text-muted)",
        borderColor: CAMPAIGN_STATUS_COLORS[status] ?? "var(--ss-text-muted)",
      }}
    >
      {status}
    </span>
  );
}

function TaskCountCell({
  label,
  count,
  color,
}: Readonly<{ label: string; count: number; color?: string }>) {
  return (
    <div
      className="flex flex-col gap-1 p-3"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </span>
      <span
        className="text-xl font-black leading-none"
        style={{ color: color ?? "var(--ss-text-primary)" }}
      >
        {count}
      </span>
    </div>
  );
}

function ChannelLane({
  channel,
  tasks,
}: Readonly<{ channel: string; tasks: CampaignTask[] }>) {
  const completed = tasks.filter((t) => t.status === "completed").length;
  const blocked = tasks.filter((t) => t.status === "blocked").length;

  return (
    <div>
      {/* Channel header */}
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="border border-[color:var(--ss-border-strong)] px-1.5 py-0.5 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
            {CHANNEL_ICONS[channel] ?? channel.slice(0, 4).toUpperCase()}
          </span>
          <span className="font-mono text-[0.65rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            {CHANNEL_LABELS_FULL[channel] ?? channel}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {completed > 0 && (
            <span className="font-mono text-[0.5rem] uppercase tracking-widest" style={{ color: "#22c55e" }}>
              {completed} DONE
            </span>
          )}
          {blocked > 0 && (
            <span className="font-mono text-[0.5rem] uppercase tracking-widest" style={{ color: "#f97316" }}>
              {blocked} BLOCKED
            </span>
          )}
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {tasks.length} TASKS
          </span>
        </div>
      </div>

      {/* Task cards */}
      <div className="space-y-px border border-[color:var(--ss-border)]">
        {tasks.map((task) => (
          <TaskCard key={task.task_id} task={task} />
        ))}
      </div>
    </div>
  );
}

const RULE_STATUS_COLORS: Record<string, string> = {
  draft: "var(--ss-text-muted)",
  active: "#22c55e",
  paused: "#f97316",
  archived: "var(--ss-text-muted)",
};

function AutomationRuleCard({ rule }: Readonly<{ rule: CampaignAutomationRule }>) {
  return (
    <div
      className="flex flex-wrap items-center justify-between gap-3 border border-[color:var(--ss-border)] px-4 py-3"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[0.62rem] font-bold text-[color:var(--ss-text-primary)]">
            {rule.name}
          </span>
          <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            ID {String(rule.rule_id).slice(0, 8)}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            TRIGGER: {rule.trigger}
          </span>
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            ACTION: {rule.action}
          </span>
        </div>
        {rule.warnings.length > 0 && (
          <span className="font-mono text-[0.5rem] text-orange-400">
            {rule.warnings.join(" · ")}
          </span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <QueueExecutionButton ruleId={String(rule.rule_id)} />
        <span
          className="shrink-0 border px-1.5 py-0.5 font-mono text-[0.48rem] font-black uppercase tracking-widest"
          style={{
            borderColor: RULE_STATUS_COLORS[rule.status] ?? "var(--ss-text-muted)",
            color: RULE_STATUS_COLORS[rule.status] ?? "var(--ss-text-muted)",
          }}
        >
          {rule.status}
        </span>
      </div>
    </div>
  );
}

function AutomationExecutionCard({
  job,
}: Readonly<{ job: AutomationExecutionJob }>) {
  return (
    <div
      className="flex flex-wrap items-center justify-between gap-3 border border-[color:var(--ss-border)] px-4 py-3"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            EXEC {String(job.execution_id).slice(0, 8)}
          </span>
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            RULE {String(job.rule_id).slice(0, 8)}
          </span>
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            DRY-RUN: {job.dry_run_status}
          </span>
        </div>
        {job.proposed_changes.length > 0 && (
          <span className="font-mono text-[0.5rem] text-[color:var(--ss-text-secondary)]">
            {job.proposed_changes.join(" · ")}
          </span>
        )}
        {job.blocked_reasons.length > 0 && (
          <span className="font-mono text-[0.5rem] text-orange-400">
            {job.blocked_reasons.join(" · ")}
          </span>
        )}
        <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {new Date(job.created_at).toISOString().slice(0, 16).replace("T", " ")}
          {job.created_by ? ` · by ${job.created_by}` : ""}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <ExecuteMockButton
          executionId={String(job.execution_id)}
          initialStatus={job.status}
        />
        <ExecutionStatusChip status={job.status} />
      </div>
    </div>
  );
}

const AUDIT_STATUS_COLOR: Record<string, string> = {
  queued: "var(--ss-accent)",
  blocked: "#f97316",
  completed_mock: "#22c55e",
  failed: "#ef4444",
};

function AutomationAuditRow({
  record,
}: Readonly<{ record: AutomationExecutionAuditRecord }>) {
  const fromColor = record.from_status
    ? AUDIT_STATUS_COLOR[record.from_status] ?? "var(--ss-text-muted)"
    : "var(--ss-text-muted)";
  const toColor =
    AUDIT_STATUS_COLOR[record.to_status] ?? "var(--ss-text-muted)";

  return (
    <div
      className="flex flex-wrap items-center justify-between gap-3 border-l-2 border-[color:var(--ss-border)] px-3 py-2"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <span
            className="border px-1 py-0.5 font-mono text-[0.45rem] font-black uppercase tracking-widest"
            style={{ borderColor: fromColor, color: fromColor }}
          >
            {record.from_status ?? "—"}
          </span>
          <span className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
            →
          </span>
          <span
            className="border px-1 py-0.5 font-mono text-[0.45rem] font-black uppercase tracking-widest"
            style={{ borderColor: toColor, color: toColor }}
          >
            {record.to_status}
          </span>
          {record.reason && (
            <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
              {record.reason}
            </span>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-3 text-[color:var(--ss-text-muted)]">
          <span className="font-mono text-[0.45rem] uppercase tracking-widest">
            EXEC {String(record.execution_id).slice(0, 8)}
          </span>
          <span className="font-mono text-[0.45rem] uppercase tracking-widest">
            RULE {String(record.rule_id).slice(0, 8)}
          </span>
          {record.operator_id && (
            <span className="font-mono text-[0.45rem] uppercase tracking-widest">
              by {record.operator_id}
            </span>
          )}
        </div>
      </div>
      <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {new Date(record.created_at).toISOString().slice(0, 16).replace("T", " ")}
      </span>
    </div>
  );
}

function TaskCard({ task }: Readonly<{ task: CampaignTask }>) {
  return (
    <div
      className="flex items-center justify-between px-4 py-3"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[0.62rem] font-bold text-[color:var(--ss-text-primary)]">
            {task.title}
          </span>
          {task.linked_object_id && (
            <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              OBJ {String(task.linked_object_id).slice(0, 8)}
            </span>
          )}
        </div>
        {task.description && (
          <span className="font-mono text-[0.52rem] text-[color:var(--ss-text-muted)]">
            {task.description}
          </span>
        )}
        {task.depends_on.length > 0 && (
          <span className="font-mono text-[0.48rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            DEPENDS: {task.depends_on.join(" + ")}
          </span>
        )}
        {task.warnings.length > 0 && (
          <span className="font-mono text-[0.5rem] text-orange-400">
            {task.warnings.join(" · ")}
          </span>
        )}
      </div>
      <span
        className="ml-3 shrink-0 border px-1.5 py-0.5 font-mono text-[0.48rem] font-black uppercase tracking-widest"
        style={{
          borderColor: TASK_STATUS_COLORS[task.status] ?? "var(--ss-text-muted)",
          color: TASK_STATUS_COLORS[task.status] ?? "var(--ss-text-muted)",
        }}
      >
        {task.status}
      </span>
    </div>
  );
}
