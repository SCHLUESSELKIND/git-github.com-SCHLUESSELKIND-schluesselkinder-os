import { SoundsystemShell } from "../_components/SoundsystemShell";
import { InferenceClientError, listConsentRecords } from "../_lib/inference";
import type { ConsentRecord } from "../_lib/inference-types";

export const dynamic = "force-dynamic";

/**
 * Consent record manager — create / list / revoke.
 *
 * This surface is gated under the admin console. The operator registers
 * speaker consent here; voice-lab jobs cite these records at preflight.
 * Revocation is immediate and permanent — any in-flight or future job
 * referencing a revoked consent will fail preflight.
 */
export default async function ConsentManagerPage() {
  let records: ReadonlyArray<ConsentRecord> = [];
  let unreachable = false;

  try {
    records = await listConsentRecords();
  } catch (error) {
    if (error instanceof InferenceClientError) {
      unreachable = true;
    } else {
      throw error;
    }
  }

  const active = records.filter((r) => !r.revoked_at);
  const revoked = records.filter((r) => !!r.revoked_at);

  return (
    <SoundsystemShell title="Consent records." status="COMPLIANCE GATE">
      <p className="mb-8 max-w-3xl font-mono text-xs uppercase leading-6 tracking-widest text-[color:var(--ss-text-secondary)]">
        Speaker consent registry. Every voice-lab job must cite a non-revoked consent record.
        Revocation is immediate — future and in-flight jobs that cite a revoked record will fail
        preflight.
      </p>

      {unreachable ? (
        <p
          className="mb-8 border border-[color:var(--ss-warning-dim)] px-4 py-3 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
        >
          Inference unreachable. Start the inference service to manage consent records.
        </p>
      ) : null}

      <div className="grid gap-12 lg:grid-cols-2">
        {/* Active consent records */}
        <section>
          <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
            <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
              ACTIVE
            </h2>
            <span
              className="font-mono text-[0.6rem] uppercase tracking-widest"
              style={{ color: "var(--ss-accent)" }}
            >
              {active.length} RECORDS
            </span>
          </header>
          {active.length === 0 ? (
            <p className="mt-4 font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              No active consent records. POST to /v1/compliance/consent-records to create one.
            </p>
          ) : (
            <ul className="mt-4 divide-y divide-[color:var(--ss-border)] border border-[color:var(--ss-border)]">
              {active.map((record) => (
                <li
                  key={record.consent_id}
                  className="px-4 py-3 font-mono text-[0.68rem] uppercase tracking-widest"
                  style={{ backgroundColor: "var(--ss-panel)" }}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[color:var(--ss-text-primary)]">
                      {record.speaker_label}
                    </span>
                    <span className="text-[color:var(--ss-text-muted)]">
                      {record.source_type}
                    </span>
                  </div>
                  <div className="mt-1 text-[0.6rem] text-[color:var(--ss-text-muted)]">
                    uses: {record.permitted_uses?.join(", ") || "any"} · id:{" "}
                    {record.consent_id.slice(0, 8)}...
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Revoked records */}
        <section>
          <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
            <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
              REVOKED
            </h2>
            <span
              className="font-mono text-[0.6rem] uppercase tracking-widest"
              style={{ color: "var(--ss-warning)" }}
            >
              {revoked.length} RECORDS
            </span>
          </header>
          {revoked.length === 0 ? (
            <p className="mt-4 font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              No revoked records.
            </p>
          ) : (
            <ul className="mt-4 divide-y divide-[color:var(--ss-border)] border border-[color:var(--ss-border)]">
              {revoked.map((record) => (
                <li
                  key={record.consent_id}
                  className="px-4 py-3 font-mono text-[0.68rem] uppercase tracking-widest"
                  style={{ backgroundColor: "var(--ss-panel)" }}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[color:var(--ss-text-primary)] line-through">
                      {record.speaker_label}
                    </span>
                    <span style={{ color: "var(--ss-warning)" }}>REVOKED</span>
                  </div>
                  <div className="mt-1 text-[0.6rem] text-[color:var(--ss-text-muted)]">
                    id: {record.consent_id.slice(0, 8)}...
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </SoundsystemShell>
  );
}
