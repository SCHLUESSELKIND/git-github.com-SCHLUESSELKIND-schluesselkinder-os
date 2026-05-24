import { SoundsystemShell } from "../_components/SoundsystemShell";
import {
  getMusicRouterSummary,
  InferenceClientError,
  listMusicJobs
} from "../_lib/inference";
import type { MusicJob, MusicRouterSummary } from "../_lib/inference-types";

export const dynamic = "force-dynamic";

/**
 * Music Provider Router — intent-driven generation surface (S12).
 *
 * Primary UI: intent-named tiles (CREATE LOOP, CREATE SONG SKETCH, etc.)
 * No raw model/provider names appear here. The router decision and
 * adapter key are visible only in the debug section below (registry context).
 */
export default async function MusicRouterPage() {
  let summary: MusicRouterSummary | null = null;
  let jobs: ReadonlyArray<MusicJob> = [];
  let unreachable = false;

  try {
    [summary, jobs] = await Promise.all([getMusicRouterSummary(), listMusicJobs()]);
  } catch (error) {
    if (error instanceof InferenceClientError) {
      unreachable = true;
    } else {
      throw error;
    }
  }

  return (
    <SoundsystemShell title="Music router." status="AUTO ROUTER · MOCK">
      <p className="mb-8 max-w-3xl font-mono text-xs uppercase leading-6 tracking-widest text-[color:var(--ss-text-secondary)]">
        Intent-driven music generation. Each intent routes to a provider group via the auto
        router. All adapters are mock-only — no real model runs. Every completed job writes
        provenance. Release blocked until review.
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

      {summary ? (
        <section className="mb-10 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-5">
          <SummaryCell label="Router mode" value={summary.router_mode.toUpperCase()} />
          <SummaryCell label="Total jobs" value={String(summary.total_jobs)} />
          <SummaryCell label="Completed" value={String(summary.jobs_completed)} />
          <SummaryCell label="Blocked" value={String(summary.jobs_blocked)} />
          <SummaryCell label="Failed" value={String(summary.jobs_failed)} />
        </section>
      ) : null}

      {/* Intent cards */}
      <section className="mb-12">
        <header className="mb-4 border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            AVAILABLE INTENTS
          </h2>
        </header>
        <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-2 lg:grid-cols-3">
          {INTENT_TILES.map((tile) => (
            <div
              key={tile.intent}
              className="flex flex-col gap-3 p-5"
              style={{ backgroundColor: "var(--ss-panel)" }}
            >
              <span className="text-lg font-black uppercase leading-none text-[color:var(--ss-text-primary)]">
                {tile.label}
              </span>
              <span className="font-mono text-[0.62rem] leading-5 uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
                {tile.description}
              </span>
              <span className="mt-auto flex items-center justify-between border-t border-[color:var(--ss-border-strong)] pt-3 font-mono text-[0.58rem] uppercase tracking-widest">
                <span className="text-[color:var(--ss-text-muted)]">AUTO ROUTER</span>
                <span style={{ color: "var(--ss-accent)" }}>READY · MOCK</span>
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Recent jobs */}
      <section>
        <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            RECENT JOBS
          </h2>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {jobs.length} ENTRIES
          </span>
        </header>
        {jobs.length === 0 ? (
          <p className="mt-4 font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            No jobs yet. POST to /v1/music-router/jobs or use the proxy.
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto border border-[color:var(--ss-border)]">
            <table className="min-w-full divide-y divide-[color:var(--ss-border)] font-mono text-[0.68rem] uppercase tracking-widest">
              <thead style={{ backgroundColor: "var(--ss-panel-elevated)" }}>
                <tr className="text-[color:var(--ss-text-muted)]">
                  <Th>Intent</Th>
                  <Th>Title</Th>
                  <Th>Status</Th>
                  <Th>Artifacts</Th>
                  <Th>Provenance</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[color:var(--ss-border)]">
                {jobs.map((job) => (
                  <tr key={job.job_id} style={{ backgroundColor: "var(--ss-panel)" }}>
                    <Td className="text-[color:var(--ss-text-primary)]">
                      {job.intent.replace(/_/g, " ")}
                    </Td>
                    <Td>{job.title}</Td>
                    <Td>
                      <StatusBadge status={job.status} />
                    </Td>
                    <Td>{job.artifacts?.length || 0}</Td>
                    <Td className="text-[0.58rem]">
                      {job.provenance_id ? (
                        <span style={{ color: "var(--ss-accent)" }}>WRITTEN</span>
                      ) : (
                        "—"
                      )}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </SoundsystemShell>
  );
}

const INTENT_TILES = [
  {
    intent: "create_loop",
    label: "CREATE LOOP",
    description: "Short instrumental loop or rhythmic bed. SoundGraph ingredient."
  },
  {
    intent: "create_song_sketch",
    label: "CREATE SONG SKETCH",
    description: "Full-length structured song draft. Research-only by default."
  },
  {
    intent: "create_stem_track",
    label: "CREATE STEM TRACK",
    description: "Single addressable lane. Bypasses full-song flow."
  },
  {
    intent: "build_riddim",
    label: "BUILD RIDDIM",
    description: "Loop-first drum and bass bed for vocal overlay."
  },
  {
    intent: "dub_fx_lab",
    label: "DUB FX LAB",
    description: "Delay trails, tape echoes, empty-room haze."
  },
  {
    intent: "master_track",
    label: "MASTER TRACK",
    description: "Loudness-shaped master via mastering adapter."
  }
] as const;

function SummaryCell({ label, value }: Readonly<{ label: string; value: string }>) {
  return (
    <div className="flex flex-col gap-2 p-4" style={{ backgroundColor: "var(--ss-panel)" }}>
      <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </span>
      <span className="text-2xl font-black uppercase leading-none text-[color:var(--ss-text-primary)]">
        {value}
      </span>
    </div>
  );
}

function StatusBadge({ status }: Readonly<{ status: string }>) {
  const color =
    status === "completed"
      ? "var(--ss-accent)"
      : status === "preflight_blocked"
        ? "var(--ss-warning)"
        : status === "failed"
          ? "var(--ss-warning)"
          : "var(--ss-text-muted)";
  return <span style={{ color }}>{status.toUpperCase()}</span>;
}

function Th({ children }: Readonly<{ children: React.ReactNode }>) {
  return <th className="px-3 py-2 text-left font-black">{children}</th>;
}

function Td({
  children,
  className = ""
}: Readonly<{ children: React.ReactNode; className?: string }>) {
  return (
    <td className={`px-3 py-2 text-[color:var(--ss-text-secondary)] ${className}`}>{children}</td>
  );
}
