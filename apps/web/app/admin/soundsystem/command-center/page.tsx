import Link from "next/link";
import { SoundsystemShell } from "../_components/SoundsystemShell";
import {
  InferenceClientError,
  listReleaseCommandCenters,
} from "../_lib/inference";
import type {
  CommandCenterReadinessStatus,
  ReleaseCommandCenter,
} from "../_lib/inference-types";

export const dynamic = "force-dynamic";

const READINESS_COLOR: Record<CommandCenterReadinessStatus, string> = {
  ready: "#22c55e",
  warning: "#facc15",
  blocked: "#f97316",
  missing: "var(--ss-text-muted)",
};

/**
 * S61 — Release-to-Campaign Command Center.
 *
 * Lists every release alongside readiness chips, automation status, and a CTA
 * to open the detail surface for one-action bootstrap.
 */
export default async function CommandCenterIndexPage() {
  let releases: ReleaseCommandCenter[] = [];
  let errorMessage: string | null = null;

  try {
    releases = await listReleaseCommandCenters();
  } catch (error) {
    if (error instanceof InferenceClientError) {
      errorMessage = `Inference error: ${error.message}`;
    } else {
      throw error;
    }
  }

  return (
    <SoundsystemShell title="Command Center" status="ORCHESTRATION SURFACE">
      <p className="mb-6 font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        One surface per release. Readiness, automation status, bootstrap. No
        execution. No provider mutation.
      </p>

      {errorMessage && (
        <p
          className="mb-6 border border-orange-500 px-4 py-3 font-mono text-[0.6rem] uppercase tracking-widest text-orange-400"
        >
          {errorMessage}
        </p>
      )}

      {releases.length === 0 ? (
        <p className="border border-dashed border-[color:var(--ss-border)] px-5 py-6 text-center font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          No releases yet. Create one in Release Center first.
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {releases.map((release) => (
            <CommandCard key={release.release_id} release={release} />
          ))}
        </div>
      )}
    </SoundsystemShell>
  );
}

function CommandCard({ release }: Readonly<{ release: ReleaseCommandCenter }>) {
  return (
    <Link
      href={`/admin/soundsystem/command-center/releases/${release.release_id}`}
      className="flex flex-col gap-3 border border-[color:var(--ss-border)] px-5 py-4 hover:bg-[color:var(--ss-panel-elevated)]"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[0.62rem] font-bold text-[color:var(--ss-text-primary)]">
          {release.release_title}
        </span>
        <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          REL {String(release.release_id).slice(0, 8)}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <span
          className="font-mono text-[0.5rem] uppercase tracking-widest"
          style={{
            color: release.campaign_id
              ? "#22c55e"
              : "var(--ss-text-muted)",
          }}
        >
          {release.campaign_id
            ? `CAMPAIGN: ${release.campaign_status ?? "—"}`
            : "CAMPAIGN: missing"}
        </span>
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          RULES: {release.automation_rule_count}
        </span>
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          REC: {release.recommended_templates.length}
        </span>
      </div>

      <div className="flex flex-wrap gap-1">
        {release.readiness_items.map((item) => (
          <span
            key={item.code}
            className="border px-1.5 py-0.5 font-mono text-[0.45rem] font-black uppercase tracking-widest"
            style={{
              borderColor: READINESS_COLOR[item.status] ?? "var(--ss-text-muted)",
              color: READINESS_COLOR[item.status] ?? "var(--ss-text-muted)",
            }}
            title={item.warnings.join(" · ")}
          >
            {item.code} · {item.status}
          </span>
        ))}
      </div>

      <span className="mt-1 font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-accent)]">
        OPEN COMMAND CENTER →
      </span>
    </Link>
  );
}
