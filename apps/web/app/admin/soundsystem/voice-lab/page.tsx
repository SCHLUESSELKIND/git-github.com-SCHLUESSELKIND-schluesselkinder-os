import { SoundsystemShell } from "../_components/SoundsystemShell";
import {
  getVoiceLabSummary,
  InferenceClientError,
  listConsentRecords,
  listVoiceJobs,
  listVoiceTags
} from "../_lib/inference";
import type {
  ConsentRecord,
  VoiceJob,
  VoiceLabSummary,
  VoiceTag
} from "../_lib/inference-types";

export const dynamic = "force-dynamic";

/**
 * Voice Lab — consent-gated voice tag + spoken vocal + voice convert
 * operator surface (S11). Read/list view; create actions are POST forms
 * that hit the Next.js proxy → inference /v1/voice-lab/* routes.
 */
export default async function VoiceLabPage() {
  let summary: VoiceLabSummary | null = null;
  let tags: ReadonlyArray<VoiceTag> = [];
  let jobs: ReadonlyArray<VoiceJob> = [];
  let consent: ReadonlyArray<ConsentRecord> = [];
  let unreachable = false;

  try {
    [summary, tags, jobs, consent] = await Promise.all([
      getVoiceLabSummary(),
      listVoiceTags(),
      listVoiceJobs(),
      listConsentRecords()
    ]);
  } catch (error) {
    if (error instanceof InferenceClientError) {
      unreachable = true;
    } else {
      throw error;
    }
  }

  return (
    <SoundsystemShell title="Voice Lab." status="MOCK PROVIDER · CONSENT GATE">
      <p className="mb-8 max-w-3xl font-mono text-xs uppercase leading-6 tracking-widest text-[color:var(--ss-text-secondary)]">
        Consent-gated voice operations. Every voice job must cite a non-revoked consent record
        before preflight clears it. Mock provider only — no real TTS or voice-clone model runs.
      </p>

      {unreachable ? (
        <p
          className="mb-8 border border-[color:var(--ss-warning-dim)] px-4 py-3 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
        >
          Inference unreachable. Start uvicorn app.main:app --port 8010 under
          services/soundsystem-inference to populate the voice lab.
        </p>
      ) : null}

      {summary ? (
        <section className="mb-10 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-4">
          <SummaryCell label="Voice tags" value={String(summary.voice_tag_count)} />
          <SummaryCell label="Jobs total" value={String(summary.voice_job_count)} />
          <SummaryCell label="Complete" value={String(summary.jobs_complete)} />
          <SummaryCell label="Blocked" value={String(summary.jobs_blocked)} />
        </section>
      ) : null}

      {/* Consent records section */}
      <section className="mb-12">
        <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            CONSENT RECORDS
          </h2>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {consent.length} ENTRIES
          </span>
        </header>
        {consent.length === 0 ? (
          <p className="mt-4 font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            No consent records. Create one at{" "}
            <code className="text-[color:var(--ss-accent)]">/admin/soundsystem/consent</code>{" "}
            before starting voice jobs.
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto border border-[color:var(--ss-border)]">
            <table className="min-w-full divide-y divide-[color:var(--ss-border)] font-mono text-[0.68rem] uppercase tracking-widest">
              <thead style={{ backgroundColor: "var(--ss-panel-elevated)" }}>
                <tr className="text-[color:var(--ss-text-muted)]">
                  <Th>Speaker</Th>
                  <Th>Source</Th>
                  <Th>Uses</Th>
                  <Th>Status</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[color:var(--ss-border)]">
                {consent.map((record) => (
                  <tr key={record.consent_id} style={{ backgroundColor: "var(--ss-panel)" }}>
                    <Td className="text-[color:var(--ss-text-primary)]">
                      {record.speaker_label}
                    </Td>
                    <Td>{record.source_type}</Td>
                    <Td>{record.permitted_uses?.join(", ") || "—"}</Td>
                    <Td>
                      {record.revoked_at ? (
                        <span style={{ color: "var(--ss-warning)" }}>REVOKED</span>
                      ) : (
                        <span style={{ color: "var(--ss-accent)" }}>ACTIVE</span>
                      )}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Voice tags */}
      <section className="mb-12">
        <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            VOICE TAGS
          </h2>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {tags.length} ENTRIES
          </span>
        </header>
        {tags.length === 0 ? (
          <p className="mt-4 font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            No voice tags registered.
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto border border-[color:var(--ss-border)]">
            <table className="min-w-full divide-y divide-[color:var(--ss-border)] font-mono text-[0.68rem] uppercase tracking-widest">
              <thead style={{ backgroundColor: "var(--ss-panel-elevated)" }}>
                <tr className="text-[color:var(--ss-text-muted)]">
                  <Th>Label</Th>
                  <Th>Provider group</Th>
                  <Th>Consent ID</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[color:var(--ss-border)]">
                {tags.map((tag) => (
                  <tr key={tag.tag_id} style={{ backgroundColor: "var(--ss-panel)" }}>
                    <Td className="text-[color:var(--ss-text-primary)]">{tag.label}</Td>
                    <Td>{tag.provider_group}</Td>
                    <Td className="text-[0.6rem]">{tag.consent_id}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Voice jobs */}
      <section>
        <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            JOBS
          </h2>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {jobs.length} ENTRIES
          </span>
        </header>
        {jobs.length === 0 ? (
          <p className="mt-4 font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            No voice jobs yet. Create a consent record and voice tag first.
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto border border-[color:var(--ss-border)]">
            <table className="min-w-full divide-y divide-[color:var(--ss-border)] font-mono text-[0.68rem] uppercase tracking-widest">
              <thead style={{ backgroundColor: "var(--ss-panel-elevated)" }}>
                <tr className="text-[color:var(--ss-text-muted)]">
                  <Th>Kind</Th>
                  <Th>Status</Th>
                  <Th>Output</Th>
                  <Th>Provenance</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[color:var(--ss-border)]">
                {jobs.map((job) => (
                  <tr key={job.job_id} style={{ backgroundColor: "var(--ss-panel)" }}>
                    <Td className="text-[color:var(--ss-text-primary)]">{job.kind}</Td>
                    <Td>
                      <StatusBadge status={job.status} />
                    </Td>
                    <Td className="text-[0.6rem]">{job.output_artifact_path || "—"}</Td>
                    <Td className="text-[0.6rem]">{job.provenance_id || "—"}</Td>
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
    status === "complete"
      ? "var(--ss-accent)"
      : status === "preflight_blocked"
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
