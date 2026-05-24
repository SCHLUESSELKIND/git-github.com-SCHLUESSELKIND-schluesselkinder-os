import { SoundsystemShell } from "../_components/SoundsystemShell";
import {
  getComplianceSummary,
  getInferenceCapabilities,
  InferenceClientError,
  listComplianceLicenses,
  listComplianceModels
} from "../_lib/inference";
import type {
  ComplianceRegistrySummary,
  InferenceCapabilities,
  LicenseRegistryEntry,
  ModelRegistryEntry
} from "../_lib/inference-types";

export const dynamic = "force-dynamic";

/**
 * Read-only compliance surface. Admin-debug context, so the registry
 * intentionally exposes provider_group / display_name_internal / activation
 * status — this is the one place where the operator should see what is
 * mocked vs. wired. Primary create flows still hide all of this behind
 * intent labels.
 *
 * The page is fail-soft: if the inference service is down it renders a
 * banner instead of throwing.
 */
export default async function SoundsystemSafetyPage() {
  let summary: ComplianceRegistrySummary | null = null;
  let models: ReadonlyArray<ModelRegistryEntry> = [];
  let licenses: ReadonlyArray<LicenseRegistryEntry> = [];
  let capabilities: InferenceCapabilities | null = null;
  let unreachable = false;

  try {
    [summary, models, licenses, capabilities] = await Promise.all([
      getComplianceSummary(),
      listComplianceModels(),
      listComplianceLicenses(),
      getInferenceCapabilities()
    ]);
  } catch (error) {
    if (error instanceof InferenceClientError) {
      unreachable = true;
    } else {
      throw error;
    }
  }

  return (
    <SoundsystemShell title="Safety register." status="READ-ONLY · MOCK SEED">
      <p className="mb-8 max-w-3xl font-mono text-xs uppercase leading-6 tracking-widest text-[color:var(--ss-text-secondary)]">
        Read-only compliance surface. Mock provider seed only — no live model is active. License,
        consent, and provenance entries listed here are the canonical contract any future adapter
        must register against before it can be wired.
      </p>

      {unreachable ? (
        <p
          className="mb-8 border border-[color:var(--ss-warning-dim)] px-4 py-3 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
        >
          Inference unreachable. Start uvicorn app.main:app --port 8010 under
          services/soundsystem-inference to populate the registry.
        </p>
      ) : null}

      {summary ? (
        <section className="mb-10 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-3 lg:grid-cols-6">
          <SummaryCell label="Repo mode" value={summary.repository_mode.toUpperCase()} />
          <SummaryCell label="Models" value={String(summary.model_registry_count)} />
          <SummaryCell label="Licenses" value={String(summary.license_registry_count)} />
          <SummaryCell label="Consent" value={String(summary.consent_records_count)} />
          <SummaryCell label="Provenance" value={String(summary.output_provenance_count)} />
          <SummaryCell label="Audit" value={String(summary.audit_events_count)} />
        </section>
      ) : null}

      {capabilities ? (
        <p className="mb-10 font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          Preflight: {capabilities.compliance_preflight_available ? "AVAILABLE" : "OFFLINE"} ·
          Registry: {capabilities.compliance_registry_available ? "SEEDED" : "EMPTY"}
        </p>
      ) : null}

      <section className="mb-12">
        <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            MODEL REGISTRY
          </h2>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {models.length} ENTRIES
          </span>
        </header>
        {models.length === 0 ? (
          <p className="mt-4 font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            Registry empty.
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto border border-[color:var(--ss-border)]">
            <table className="min-w-full divide-y divide-[color:var(--ss-border)] font-mono text-[0.68rem] uppercase tracking-widest">
              <thead style={{ backgroundColor: "var(--ss-panel-elevated)" }}>
                <tr className="text-[color:var(--ss-text-muted)]">
                  <Th>Group</Th>
                  <Th>Adapter</Th>
                  <Th>Display</Th>
                  <Th>Commercial</Th>
                  <Th>Activation</Th>
                  <Th>Risk</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[color:var(--ss-border)]">
                {models.map((entry) => (
                  <tr key={entry.model_id} style={{ backgroundColor: "var(--ss-panel)" }}>
                    <Td>{entry.provider_group}</Td>
                    <Td>{entry.adapter_key}</Td>
                    <Td className="text-[color:var(--ss-text-primary)]">
                      {entry.display_name_internal}
                    </Td>
                    <Td>{entry.commercial_status}</Td>
                    <Td>{entry.activation_status}</Td>
                    <Td>{entry.risk_tier}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            LICENSE REGISTRY
          </h2>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {licenses.length} ENTRIES
          </span>
        </header>
        {licenses.length === 0 ? (
          <p className="mt-4 font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            No license records.
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto border border-[color:var(--ss-border)]">
            <table className="min-w-full divide-y divide-[color:var(--ss-border)] font-mono text-[0.68rem] uppercase tracking-widest">
              <thead style={{ backgroundColor: "var(--ss-panel-elevated)" }}>
                <tr className="text-[color:var(--ss-text-muted)]">
                  <Th>Model / Dataset</Th>
                  <Th>License</Th>
                  <Th>Commercial</Th>
                  <Th>Status</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[color:var(--ss-border)]">
                {licenses.map((entry) => (
                  <tr key={entry.license_id} style={{ backgroundColor: "var(--ss-panel)" }}>
                    <Td className="text-[color:var(--ss-text-primary)]">
                      {entry.model_or_dataset_id}
                    </Td>
                    <Td>{entry.license_name}</Td>
                    <Td>{entry.permits_commercial ? "YES" : "NO"}</Td>
                    <Td>{entry.status}</Td>
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
    <div
      className="flex flex-col gap-2 p-4"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </span>
      <span className="text-2xl font-black uppercase leading-none text-[color:var(--ss-text-primary)]">
        {value}
      </span>
    </div>
  );
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
